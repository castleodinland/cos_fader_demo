#include "cos_fade.h"
#include <stdint.h>

/* ================================================================
 * Optimized fade-in / fade-out using:
 *   1. LUT-based cosine (257-entry, linear interpolation)
 *   2. Incremental angle accumulation (eliminates per-sample division)
 *   3. DSP : __nds32__khmbb     for Q15 PCM multiplication
 *   4. DSP : __nds32__kwmmul    for Q31 PCM multiplication
 *   5. DSP : __nds32__smmul_u   for LUT interpolation (frac*diff)>>15
 * ================================================================ */

#define COS_TABLE_BITS  8
#define COS_TABLE_SIZE  ((1 << COS_TABLE_BITS) + 1)   /* 257 */
#define ONE_Q15         32767

/* Rounding constant for smmul_u:  (a * b + 2^31) >> 32  */
/* For interpolation we need:     (frac*diff + 2^14) >> 15
 * smmul_u(frac<<16, diff<<1) gives exactly this.
 */

static const int16_t cos_table[COS_TABLE_SIZE] = {
#include "cos_table.inc"
};

/* ------------------------------------------------------------------
 * cos_lookup_q15_fast  — LUT lookup with DSP-accelerated interpolation
 *
 * x_q15 : 0 .. 32767  →  angle 0 .. π
 * return: cos(angle) in Q15  (-32768 .. 32767)
 *
 * Uses __nds32__smmul_u for the fractional interpolation multiply,
 * replacing a generic 32-bit multiply + shift + add with a single
 * DSP instruction that does (32x32 + rounding) >> 32.
 * ------------------------------------------------------------------ */
static inline int16_t cos_lookup_q15_fast(uint16_t x_q15)
{
    uint32_t idx_frac = (uint32_t)x_q15 << COS_TABLE_BITS;
    uint16_t idx = (uint16_t)(idx_frac >> 15);
    uint16_t frac = (uint16_t)(idx_frac & 0x7FFF);

    int16_t y0 = cos_table[idx];
    int16_t y1 = cos_table[idx + 1];
    int32_t diff = (int32_t)y1 - (int32_t)y0;

    /* smmul_u(a, b) = (a * b + 2^31) >> 32
     * With a = frac << 16,  b = diff << 1:
     *   ((frac<<16) * (diff<<1) + 2^31) >> 32
     * = (frac * diff * 2^17 + 2^31) / 2^32
     * = (frac * diff + 2^14) / 2^15    ← exactly our rounding rule
     */
    int32_t interp = __nds32__smmul_u(
        (int32_t)((uint32_t)frac << 16),
        diff << 1);

    return (int16_t)((int32_t)y0 + interp);
}

/* ------------------------------------------------------------------
 * Bresenham-style angle accumulator  (exact, no division per sample)
 *
 * Instead of computing  x_q15 = i * ONE_Q15 / (N-1)  for every i
 * (which requires a slow 32-bit divide per sample), we decompose:
 *
 *   ONE_Q15 = delta_base * (N-1) + rem_step    (integer division)
 *
 * Then:
 *   x_q15_i = delta_base * i  +  (rem_step * i) / (N-1)
 *
 * We track  rem_accum += rem_step  and increment x_q15 + 1 each
 * time rem_accum crosses (N-1).  This produces EXACTLY the same
 * sequence as  i * ONE_Q15 / (N-1)  for all i, using only 32-bit
 * addition + one conditional per step — no division, no multiply.
 * ------------------------------------------------------------------ */
typedef struct {
    uint16_t x_q15;
    uint32_t delta_base;
    uint32_t rem_step;
    uint32_t rem_accum;
    uint32_t denom;
} AngleAccum;

static inline void angle_init(AngleAccum *a, uint32_t denom)
{
    a->x_q15 = 0;
    a->denom = denom;
    if (denom > 0) {
        a->delta_base = ONE_Q15 / denom;   /* integer part */
        a->rem_step   = ONE_Q15 % denom;   /* fractional remainder */
    } else {
        a->delta_base = 0;
        a->rem_step   = 0;
    }
    a->rem_accum = 0;
}

static inline uint16_t angle_next(AngleAccum *a)
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

/* ------------------------------------------------------------------
 * Common per-step logic shared by fade_out and fade_in
 * ------------------------------------------------------------------ */
static inline int16_t fade_calc_mult(uint16_t x_q15, int32_t direction)
{
    int16_t cosv = cos_lookup_q15_fast(x_q15);
    int32_t tmp;

    if (direction < 0)                       /* fade-out: (1 + cos) / 2 */
        tmp = ((int32_t)ONE_Q15 + cosv + 1) >> 1;
    else                                     /* fade-in:  (1 - cos) / 2 */
        tmp = ((int32_t)ONE_Q15 - cosv + 1) >> 1;

    if (tmp > ONE_Q15) tmp = ONE_Q15;
    return (int16_t)tmp;
}

/* =================================================================
 * Public API
 * ================================================================= */

static void fade_apply(void *pcm_buf, int32_t num_channels,
                       int32_t bit_width, uint32_t idx, int16_t fade_mult)
{
    int32_t fade_q31 = ((int32_t)fade_mult) << 16;

    for (int32_t ch = 0; ch < num_channels; ch++)
    {
        uint32_t si = idx * (uint32_t)num_channels + (uint32_t)ch;

        if (bit_width == 16)
        {
            int16_t *buf = (int16_t *)pcm_buf;
            buf[si] = (int16_t)__nds32__khmbb(
                (uint32_t)buf[si], (uint32_t)fade_mult);
        }
        else if (bit_width == 24)
        {
            /* 24-bit right-aligned in int32_t container.
             * mask + manual sign-extend from bit 23, then kwmmul directly. */
            int32_t *buf = (int32_t *)pcm_buf;
            int32_t s = buf[si] & 0x00FFFFFF;
            if (s & 0x00800000) s |= 0xFF000000;
            buf[si] = (int32_t)__nds32__kwmmul(s, fade_q31);
        }
        else
        {
            int32_t *buf = (int32_t *)pcm_buf;
            buf[si] = (int32_t)__nds32__kwmmul(
                (int32_t)buf[si], fade_q31);
        }
    }
}

void cos_fade_out(void *pcm_buf, int32_t num_channels,
                  int32_t bit_width, uint32_t fade_points)
{
    if (!pcm_buf || num_channels <= 0 || fade_points == 0)
        return;

    if (fade_points == 1)
    {
        fade_apply(pcm_buf, num_channels, bit_width, 0, 0);
        return;
    }

    uint32_t step_max = fade_points - 1;
    AngleAccum accum;
    angle_init(&accum, step_max);

    for (uint32_t i = 0; i < step_max; i++)
    {
        uint16_t x_q15   = angle_next(&accum);
        int16_t fade_mult = fade_calc_mult(x_q15, -1);
        fade_apply(pcm_buf, num_channels, bit_width, i, fade_mult);
    }
    fade_apply(pcm_buf, num_channels, bit_width, step_max, 0);
}

void cos_fade_in(void *pcm_buf, int32_t num_channels,
                 int32_t bit_width, uint32_t fade_points)
{
    if (!pcm_buf || num_channels <= 0 || fade_points == 0)
        return;

    if (fade_points == 1)
    {
        fade_apply(pcm_buf, num_channels, bit_width, 0, 0);
        return;
    }

    uint32_t step_max = fade_points - 1;
    AngleAccum accum;
    angle_init(&accum, step_max);

    fade_apply(pcm_buf, num_channels, bit_width, 0, 0);
    (void)angle_next(&accum);                         /* advance past i=0 */

    for (uint32_t i = 1; i < step_max; i++)
    {
        uint16_t x_q15   = angle_next(&accum);
        int16_t fade_mult = fade_calc_mult(x_q15, +1);
        fade_apply(pcm_buf, num_channels, bit_width, i, fade_mult);
    }
    fade_apply(pcm_buf, num_channels, bit_width, step_max, ONE_Q15);
}
