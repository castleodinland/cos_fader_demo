#include "cos_fade.h"
#include "dsp_math.h"   /* provides nds32_cos_q15, nds32_cos_q31 */

#define ONE_Q15  32767
#define ONE_Q31  2147483647

/* =================================================================
 * 16-bit path — use nds32_cos_q15
 *
 * Input angle range:  [0, 0x7FFF]  →  [0, π]
 * Output cos range:   cos(0)=32767  →  cos(π)=-32768
 *
 * Fade-out multiplier (Q15):  ( ONE_Q15 + cos + 1 ) >> 1
 * Fade-in  multiplier (Q15):  ( ONE_Q15 - cos + 1 ) >> 1  (capped)
 * ================================================================= */
static int16_t fade_mult_q15(uint32_t i, uint32_t denom, int32_t direction)
{
    if (i == 0 && direction > 0)   return 0;          /* fade-in  start */
    if (i == denom && direction < 0) return 0;         /* fade-out end   */
    if (i == denom && direction > 0) return ONE_Q15;  /* fade-in  end   */

    /* angle in Q15:  i/denom * π  →  [0, 32767] */
    q15_t angle = (q15_t)((i * (uint32_t)ONE_Q15) / denom);
    q15_t cosv = nds32_cos_q15(angle);
    int32_t tmp;

    if (direction < 0)                                  /* fade-out */
        tmp = ((int32_t)ONE_Q15 + cosv + 1) >> 1;
    else                                                /* fade-in  */
        tmp = ((int32_t)ONE_Q15 - cosv + 1) >> 1;

    if (tmp > ONE_Q15) tmp = ONE_Q15;
    return (int16_t)tmp;
}

/* =================================================================
 * 32-bit path — use nds32_cos_q31
 *
 * Input angle range:  [0, 0x7FFFFFFF]  →  [0, π]
 * Output cos range:   cos(0)=0x7FFFFFFF  →  cos(π)=0x80000000
 * ================================================================= */
static q31_t fade_mult_q31(uint32_t i, uint32_t denom, int32_t direction)
{
    if (i == 0 && direction > 0)   return 0;           /* fade-in  start */
    if (i == denom && direction < 0) return 0;          /* fade-out end   */
    if (i == denom && direction > 0) return ONE_Q31;   /* fade-in  end   */

    /* angle in Q31:  i/denom * π */
    q31_t angle = (q31_t)(((uint64_t)i * (uint64_t)ONE_Q31) / denom);
    q31_t cosv = nds32_cos_q31(angle);
    int64_t tmp;

    if (direction < 0)                                  /* fade-out */
        tmp = ((int64_t)ONE_Q31 + cosv + 1) >> 1;
    else                                                /* fade-in  */
        tmp = ((int64_t)ONE_Q31 - cosv + 1) >> 1;

    if (tmp > ONE_Q31) tmp = ONE_Q31;
    return (q31_t)tmp;
}

/* =================================================================
 * Public API
 * ================================================================= */
void cos_fade_out(void *pcm_buf, int32_t num_channels,
                  int32_t bit_width, uint32_t fade_points)
{
    if (!pcm_buf || num_channels <= 0 || fade_points == 0)
        return;

    if (fade_points == 1) {
        for (int32_t ch = 0; ch < num_channels; ch++) {
            if (bit_width == 16)
                ((int16_t *)pcm_buf)[ch] = 0;
            else
                ((int32_t *)pcm_buf)[ch] = 0;  /* 24-bit/32-bit 都是 int32_t 容器 */
        }
        return;
    }

    uint32_t denom = fade_points - 1;

    for (uint32_t i = 0; i < fade_points; i++) {
        q15_t m15 = 0;
        q31_t m31 = 0;

        if (bit_width == 16)
            m15 = fade_mult_q15(i, denom, -1);
        else
            m31 = fade_mult_q31(i, denom, -1);

        for (int32_t ch = 0; ch < num_channels; ch++) {
            uint32_t si = i * (uint32_t)num_channels + (uint32_t)ch;

            if (bit_width == 16) {
                int16_t *buf = (int16_t *)pcm_buf;
                buf[si] = (int16_t)__nds32__khmbb(
                    (uint32_t)buf[si], (uint32_t)m15);
            } else if (bit_width == 24) {
                /* 24-bit right-aligned in int32_t container.
                 * mask + manual sign-extend from bit 23, then kwmmul directly. */
                int32_t *buf = (int32_t *)pcm_buf;
                int32_t s = buf[si] & 0x00FFFFFF;
                if (s & 0x00800000) s |= 0xFF000000;
                buf[si] = (int32_t)__nds32__kwmmul(s, m31);
            } else {
                int32_t *buf = (int32_t *)pcm_buf;
                buf[si] = (int32_t)__nds32__kwmmul(
                    (int32_t)buf[si], m31);
            }
        }
    }
}

void cos_fade_in(void *pcm_buf, int32_t num_channels,
                  int32_t bit_width, uint32_t fade_points)
{
    if (!pcm_buf || num_channels <= 0 || fade_points == 0)
        return;

    if (fade_points == 1) {
        for (int32_t ch = 0; ch < num_channels; ch++) {
            if (bit_width == 16)
                ((int16_t *)pcm_buf)[ch] = 0;
            else
                ((int32_t *)pcm_buf)[ch] = 0;  /* 24-bit/32-bit 都是 int32_t 容器 */
        }
        return;
    }

    uint32_t denom = fade_points - 1;

    for (uint32_t i = 0; i < fade_points; i++) {
        q15_t m15 = 0;
        q31_t m31 = 0;

        if (bit_width == 16)
            m15 = fade_mult_q15(i, denom, +1);
        else
            m31 = fade_mult_q31(i, denom, +1);

        for (int32_t ch = 0; ch < num_channels; ch++) {
            uint32_t si = i * (uint32_t)num_channels + (uint32_t)ch;

            if (bit_width == 16) {
                int16_t *buf = (int16_t *)pcm_buf;
                buf[si] = (int16_t)__nds32__khmbb(
                    (uint32_t)buf[si], (uint32_t)m15);
            } else if (bit_width == 24) {
                /* 24-bit right-aligned in int32_t container.
                 * mask + manual sign-extend from bit 23, then kwmmul directly. */
                int32_t *buf = (int32_t *)pcm_buf;
                int32_t s = buf[si] & 0x00FFFFFF;
                if (s & 0x00800000) s |= 0xFF000000;
                buf[si] = (int32_t)__nds32__kwmmul(s, m31);
            } else {
                int32_t *buf = (int32_t *)pcm_buf;
                buf[si] = (int32_t)__nds32__kwmmul(
                    (int32_t)buf[si], m31);
            }
        }
    }
}
