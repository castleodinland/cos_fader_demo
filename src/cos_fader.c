#include "cos_fader.h"
#include "dsp_math.h"
#include <string.h>

#define ONE_Q15  32767
#define ONE_Q31  2147483647

/* ===================================================================
 * 内部工具
 * =================================================================== */

/* 返回每种 bit_width 每 sample 的字节数 */
/* 注意：24-bit 在 DSP 中用 int32_t 容器、右对齐，故 bps=4 */
static inline int32_t bytes_per_smp(int32_t bit_width)
{
    if (bit_width == 16) return 2;
    return 4;  /* 24-bit 和 32-bit 都占 4 字节 */
}

/* Bresenham 角度步进：返回当前 x_q15，然后前进 1 步 */
static inline uint16_t angle_next(CosFaderContext *ct)
{
    uint16_t x = ct->angle_x;
    ct->angle_x  += ct->delta_base;
    ct->rem_accum += ct->rem_step;
    if (ct->rem_accum >= ct->denom) {
        ct->angle_x++;
        ct->rem_accum -= ct->denom;
    }
    return x;
}

/* ===================================================================
 * 单帧 apply：对 frame_idx 帧（所有声道）应用 fade_mult
 *
 * fade_mult 为 Q15 格式，其中：
 *   ONE_Q15 (~1.0) = 原值直通
 *   0             = 静音
 *
 * bit_width=16：khmbb (Q15×Q15 → Q15)
 * bit_width=24：int32_t 容器右对齐 → 左移 8 位入 Q31 → kwmmul → 右移 8 位写回
 * bit_width=32：kwmmul (Q31×Q31 → Q31)
 * =================================================================== */
static void apply_frame(CosFaderContext *ct,
                        uint8_t *in, uint8_t *out,
                        int32_t frame_idx, int16_t fade_mult)
{
    int32_t bw   = ct->bit_width;
    int32_t bps  = bytes_per_smp(bw);
    int32_t nc   = ct->num_channels;
    int32_t base = frame_idx * nc * bps;

    if (fade_mult == ONE_Q15) {
        /* 直通：整帧 memcpy */
        memcpy(out + base, in + base, (size_t)(nc * bps));
        return;
    }

    if (fade_mult == 0) {
        /* 静音：整帧写 0 */
        memset(out + base, 0, (size_t)(nc * bps));
        return;
    }

    int32_t fade_q31 = ((int32_t)fade_mult) << 16;  /* Q15 → Q31 */

    for (int32_t ch = 0; ch < nc; ch++) {
        int32_t off = base + ch * bps;

        if (bw == 16) {
            int16_t s = *(int16_t *)(in + off);
            int16_t r = (int16_t)__nds32__khmbb((uint32_t)s, (uint32_t)fade_mult);
            *(int16_t *)(out + off) = r;
        }
        else if (bw == 24) {
            /* 24-bit right-aligned in int32_t container.
             * mask + manual sign-extend from bit 23, then kwmmul directly. */
            int32_t s = *(int32_t *)(in + off) & 0x00FFFFFF;
            if (s & 0x00800000) s |= 0xFF000000;
            *(int32_t *)(out + off) = (int32_t)__nds32__kwmmul(s, fade_q31);
        }
        else {  /* bw == 32 */
            int32_t s = *(int32_t *)(in + off);
            int32_t r = (int32_t)__nds32__kwmmul(s, fade_q31);
            *(int32_t *)(out + off) = r;
        }
    }
}

/* ===================================================================
 * cos_fader_init
 * =================================================================== */
int32_t cos_fader_init(CosFaderContext *ct, int32_t num_channels,
                       int32_t bit_width, int32_t fade_type,
                       int32_t fade_samples)
{
    if (!ct)   return COS_FADER_ERROR_NULL_POINTER;
    if (num_channels <= 0) return COS_FADER_ERROR_NUM_CHANNELS;
    if (bit_width != 16 && bit_width != 24 && bit_width != 32)
        return COS_FADER_ERROR_BIT_WIDTH;
    if (fade_samples < 1)  return COS_FADER_ERROR_FADE_SAMPLES;
    if (fade_type < 0 || fade_type > 2)
        return COS_FADER_ERROR_FADE_TYPE;

    ct->num_channels  = num_channels;
    ct->bit_width     = bit_width;
    ct->fade_type     = fade_type;
    ct->fade_samples  = fade_samples;

    /* 运行状态 */
    ct->fade_counter  = 0;

    /* Bresenham 角度累加器初始化 */
    ct->denom = (fade_samples > 1)
                ? (uint32_t)(fade_samples - 1) : 1;
    ct->angle_x    = 0;
    ct->delta_base = ONE_Q15 / ct->denom;
    ct->rem_step   = ONE_Q15 % ct->denom;
    ct->rem_accum  = 0;

    return COS_FADER_ERROR_OK;
}

/* ===================================================================
 * cos_fader_apply
 *
 * 逐 per-channel sample 处理，自动跨帧。
 *
 *
 * 24-bit 约定：int32_t 容器、右对齐（DSP 惯例）。
 *
 * fade 完成前：按升余弦公式计算 fade_mult 并应用到每一帧。
 * fade 完成后：
 *   fade-out → 输出全部写 0
 *   fade-in  → 输出 = 输入（直通）
 *   bypass   → 输出 = 输入（直通）
 *
 * fade
 *   counter=0..fade_samples-2：Bresenham 角度步进 + nds32_cos_q15
 *   counter=fade_samples-1   ：显式端点值（out=0, in=ONE_Q15）
 *   counter>=fade_samples    ：保持（hold）
 * =================================================================== */
int32_t cos_fader_apply(CosFaderContext *ct, void *pcm_in,
                        void *pcm_out, int32_t n)
{
    if (!ct || !pcm_in || !pcm_out)
        return COS_FADER_ERROR_NULL_POINTER;
    if (n <= 0) return COS_FADER_ERROR_OK;  /* 空调用 */

    uint8_t *in  = (uint8_t *)pcm_in;
    uint8_t *out = (uint8_t *)pcm_out;
    int32_t bps  = bytes_per_smp(ct->bit_width);
    int32_t nc   = ct->num_channels;
    int32_t fs   = ct->fade_samples;
    int32_t last = fs - 1;

    /* bypass：直通，不更新 counter */
    if (ct->fade_type == COS_FADER_BYPASS) {
        memcpy(out, in, (size_t)(n * nc * bps));
        return COS_FADER_ERROR_OK;
    }

    for (int32_t i = 0; i < n; i++) {
        int32_t pos = ct->fade_counter;

        if (pos >= fs) {
            /* ——— fade 完成，持续保持 ——— */
            if (ct->fade_type == COS_FADER_FADE_OUT) {
                memset(out + i * nc * bps, 0, (size_t)(nc * bps));
            } else {
                memcpy(out + i * nc * bps, in + i * nc * bps,
                       (size_t)(nc * bps));
            }
            continue;
        }

        /* ——— fade 进行中 ——— */
        int16_t fade_mult;

        if (pos == last) {
            /* 最后一个 sample：显式端点 */
            fade_mult = (ct->fade_type == COS_FADER_FADE_OUT) ? 0 : ONE_Q15;
        }
        else if (ct->fade_type == COS_FADER_FADE_OUT) {
            uint16_t angle = angle_next(ct);
            int16_t cosv   = nds32_cos_q15((q15_t)angle);
            fade_mult = (int16_t)(((int32_t)ONE_Q15 + cosv + 1) >> 1);
        }
        else {  /* COS_FADER_FADE_IN */
            if (pos == 0) {
                fade_mult = 0;
                (void)angle_next(ct);   /* 跳过位置 0，前进到位置 1 */
            } else {
                uint16_t angle = angle_next(ct);
                int16_t cosv   = nds32_cos_q15((q15_t)angle);
                int32_t tmp    = ((int32_t)ONE_Q15 - cosv + 1) >> 1;
                fade_mult = (tmp > ONE_Q15) ? ONE_Q15 : (int16_t)tmp;
            }
        }

        apply_frame(ct, in, out, i, fade_mult);
        ct->fade_counter++;
    }

    return COS_FADER_ERROR_OK;
}

/* ===================================================================
 * cos_fader_is_done
 * =================================================================== */
int32_t cos_fader_is_done(CosFaderContext *ct)
{
    if (!ct) return 1;  /* 空指针视为 done */
    return (ct->fade_counter >= ct->fade_samples) ? 1 : 0;
}
