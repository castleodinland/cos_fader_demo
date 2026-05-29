#include "cos_fade.h"
#include "dsp_math.h"

#define ONE_Q15         32767
#define ONE_Q31         2147483647

/*
 * ========================================================================
 * cos_fade_dsp_fast.c  — 基于 cos_fade_dsp.c 的算力优化版本
 *
 * 不引入 LUT / 额外 ROM，仅依赖 DSP 库 nds32_cos_q15。
 *
 * 优化 1：Bresenham 增量角度累计
 *   (i * ONE_Q15) / denom  →  加法 + 条件判断，无乘除法
 *   每样本省去 ~20-35 cycles 的 32-bit 除法
 *
 * 优化 2：Q31 复用 Q15 结果
 *   fade_mult_q31 = fade_mult_q15 << 16
 *   消除 64-bit 除法及 nds32_cos_q31 调用
 *
 * 注意：余弦递推 (Chebyshev) 经验证在定点算术中数值不稳定，
 *       (-1)^i 寄生模式被舍入误差激励后线性发散，故不采用。
 * ========================================================================
 */

/* --------------------------------------------------------------------
 * Bresenham 角度累加器
 * 精确产生 x_q15[i] = floor(i * ONE_Q15 / denom), i = 0 .. denom-1
 * 仅用 32-bit 加法 + 一次条件分支
 * -------------------------------------------------------------------- */
typedef struct {
    uint16_t x_q15;
    uint32_t delta_base;
    uint32_t rem_step;
    uint32_t rem_accum;
    uint32_t denom;
} AngleAccum;

static void angle_init(AngleAccum *a, uint32_t denom)
{
    a->x_q15      = 0;
    a->denom      = denom;
    if (denom > 0) {
        a->delta_base = ONE_Q15 / denom;
        a->rem_step   = ONE_Q15 % denom;
    } else {
        a->delta_base = 0;
        a->rem_step   = 0;
    }
    a->rem_accum  = 0;
}

static uint16_t angle_next(AngleAccum *a)
{
    uint16_t x = a->x_q15;
    a->x_q15   += a->delta_base;
    a->rem_accum += a->rem_step;
    if (a->rem_accum >= a->denom) {
        a->x_q15++;
        a->rem_accum -= a->denom;
    }
    return x;
}

/* --------------------------------------------------------------------
 * fade_apply — 对 PCM 缓冲区应用 fade_mult
 *
 * bit_width=16: khmbb (Q15 * Q15 → Q15)
 * bit_width=24: packed 24-bit LE, 用 kwmmul (Q31 * Q31 → Q31)
 * bit_width=32: kwmmul (Q31 * Q31 → Q31)
 *
 * 24-bit 音频约定:
 *   - 每个采样 3 字节, 连续存放 (packed, little-endian)
 *   - 有符号 24-bit, 读入后左对齐到 Q31, kwmmul 乘算, 再右对齐写回
 * -------------------------------------------------------------------- */
static void fade_apply(void *pcm_buf, int32_t num_channels,
                       int32_t bit_width, uint32_t idx, int16_t fade_mult)
{
    int32_t fade_q31 = ((int32_t)fade_mult) << 16;   /* Q15 → Q31 */

    for (int32_t ch = 0; ch < num_channels; ch++) {
        uint32_t si = idx * (uint32_t)num_channels + (uint32_t)ch;

        if (bit_width == 16) {
            int16_t *buf = (int16_t *)pcm_buf;
            buf[si] = (int16_t)__nds32__khmbb(
                (uint32_t)buf[si], (uint32_t)fade_mult);
        }
        else if (bit_width == 24) {
            /* 24-bit right-aligned in int32_t container.
             * 高位可能未做符号扩展，先 mask 再手动 sign-extend bit 23。
             * 之后直接用 kwmmul，无需移位。 */
            int32_t *buf = (int32_t *)pcm_buf;
            int32_t s = buf[si] & 0x00FFFFFF;
            if (s & 0x00800000) s |= 0xFF000000;
            buf[si] = (int32_t)__nds32__kwmmul(s, fade_q31);
        }
        else {    /* bit_width == 32 (or any >= 32) */
            int32_t *buf = (int32_t *)pcm_buf;
            buf[si] = (int32_t)__nds32__kwmmul(
                (int32_t)buf[si], fade_q31);
        }
    }
}

/* =================================================================
 * cos_fade_out
 * ================================================================= */
void cos_fade_out(void *pcm_buf, int32_t num_channels,
                  int32_t bit_width, uint32_t fade_points)
{
    if (!pcm_buf || num_channels <= 0 || fade_points == 0)
        return;

    if (fade_points == 1) {
        fade_apply(pcm_buf, num_channels, bit_width, 0, 0);
        return;
    }

    uint32_t step_max = fade_points - 1;
    AngleAccum accum;
    angle_init(&accum, step_max);

    for (uint32_t i = 0; i < step_max; i++) {
        uint16_t angle  = angle_next(&accum);
        int16_t cosv    = nds32_cos_q15((q15_t)angle);
        int16_t fade_mult = (int16_t)(((int32_t)ONE_Q15 + cosv + 1) >> 1);
        fade_apply(pcm_buf, num_channels, bit_width, i, fade_mult);
    }

    fade_apply(pcm_buf, num_channels, bit_width, step_max, 0);
}

/* =================================================================
 * cos_fade_in
 * ================================================================= */
void cos_fade_in(void *pcm_buf, int32_t num_channels,
                 int32_t bit_width, uint32_t fade_points)
{
    if (!pcm_buf || num_channels <= 0 || fade_points == 0)
        return;

    if (fade_points == 1) {
        fade_apply(pcm_buf, num_channels, bit_width, 0, 0);
        return;
    }

    uint32_t step_max = fade_points - 1;
    AngleAccum accum;
    angle_init(&accum, step_max);

    /* i=0 强制为 0 */
    fade_apply(pcm_buf, num_channels, bit_width, 0, 0);
    (void)angle_next(&accum);          /* 推进到 i=1 的角度 */

    for (uint32_t i = 1; i < step_max; i++) {
        uint16_t angle  = angle_next(&accum);
        int16_t cosv    = nds32_cos_q15((q15_t)angle);
        int32_t tmp     = ((int32_t)ONE_Q15 - cosv + 1) >> 1;
        int16_t fade_mult = (tmp > ONE_Q15) ? ONE_Q15 : (int16_t)tmp;
        fade_apply(pcm_buf, num_channels, bit_width, i, fade_mult);
    }

    fade_apply(pcm_buf, num_channels, bit_width, step_max, ONE_Q15);
}
