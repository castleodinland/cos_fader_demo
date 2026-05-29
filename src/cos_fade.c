#include "cos_fade.h"

/* lookup table: cos(k * PI / 256) in Q15, k=0..256 */
#define COS_TABLE_BITS 8
#define COS_TABLE_SIZE ((1 << COS_TABLE_BITS) + 1)
#define ONE_Q15 32767
#define ROUND_Q15 16384

static const int16_t cos_table[COS_TABLE_SIZE] = {
#include "cos_table.inc"
};

/* Q15 cosine lookup, x_q15 in [0, 32767] maps to [0, PI] */
static inline int16_t cos_lookup_q15(uint16_t x_q15)
{
    uint32_t idx_frac = (uint32_t)x_q15 << COS_TABLE_BITS;
    uint16_t idx = (uint16_t)(idx_frac >> 15);
    uint16_t frac = (uint16_t)(idx_frac & 0x7FFF);
    int16_t y0 = cos_table[idx];
    int16_t y1 = cos_table[idx + 1];
    int32_t diff = (int32_t)y1 - (int32_t)y0;
    int32_t interp = ((int32_t)frac * diff + ROUND_Q15) >> 15;
    return (int16_t)((int32_t)y0 + interp);
}

void cos_fade_out(void *pcm_buf, int32_t num_channels, int32_t bit_width, uint32_t fade_points)
{
    if (!pcm_buf || num_channels <= 0 || fade_points == 0)
        return;

    if (fade_points == 1)
    {
        for (int32_t ch = 0; ch < num_channels; ch++)
        {
            if (bit_width == 16)
                ((int16_t *)pcm_buf)[ch] = 0;
            else
                ((int32_t *)pcm_buf)[ch] = 0;   /* 24-bit/32-bit 都是 int32_t 容器 */
        }
        return;
    }

    uint32_t step_max = fade_points - 1;
    uint32_t denom = step_max;

    for (uint32_t i = 0; i < fade_points; i++)
    {
        int16_t fade_mult;

        if (i == step_max)
        {
            fade_mult = 0;
        }
        else
        {
            uint16_t x_q15 = (uint16_t)((i * (uint32_t)ONE_Q15) / denom);
            int16_t cos_val = cos_lookup_q15(x_q15);
            fade_mult = (int16_t)(((int32_t)ONE_Q15 + cos_val + 1) >> 1);
        }

        for (int32_t ch = 0; ch < num_channels; ch++)
        {
            uint32_t si = i * (uint32_t)num_channels + (uint32_t)ch;

            if (bit_width == 16)
            {
                int16_t *buf = (int16_t *)pcm_buf;
                buf[si] = (int16_t)__nds32__khmbb((uint32_t)buf[si], (uint32_t)fade_mult);
            }
            else if (bit_width == 24)
            {
                /* 24-bit right-aligned in int32_t container.
                 * mask + manual sign-extend from bit 23, then kwmmul directly. */
                int32_t *buf = (int32_t *)pcm_buf;
                int32_t fade_q31 = ((int32_t)fade_mult) << 16;
                int32_t s = buf[si] & 0x00FFFFFF;
                if (s & 0x00800000) s |= 0xFF000000;
                buf[si] = (int32_t)__nds32__kwmmul(s, fade_q31);
            }
            else
            {
                int32_t *buf = (int32_t *)pcm_buf;
                int32_t fade_q31 = ((int32_t)fade_mult) << 16;
                buf[si] = (int32_t)__nds32__kwmmul((int32_t)buf[si], (int32_t)fade_q31);
            }
        }
    }
}

void cos_fade_in(void *pcm_buf, int32_t num_channels, int32_t bit_width, uint32_t fade_points)
{
    if (!pcm_buf || num_channels <= 0 || fade_points == 0)
        return;

    if (fade_points == 1)
    {
        for (int32_t ch = 0; ch < num_channels; ch++)
        {
            if (bit_width == 16)
                ((int16_t *)pcm_buf)[ch] = 0;
            else
                ((int32_t *)pcm_buf)[ch] = 0;   /* 24-bit/32-bit 都是 int32_t 容器 */
        }
        return;
    }

    uint32_t step_max = fade_points - 1;
    uint32_t denom = step_max;

    for (uint32_t i = 0; i < fade_points; i++)
    {
        int16_t fade_mult;

        if (i == 0)
        {
            fade_mult = 0;
        }
        else if (i == step_max)
        {
            fade_mult = ONE_Q15;
        }
        else
        {
            uint16_t x_q15 = (uint16_t)((i * (uint32_t)ONE_Q15) / denom);
            int16_t cos_val = cos_lookup_q15(x_q15);
            int32_t tmp = ((int32_t)ONE_Q15 - cos_val + 1) >> 1;
            fade_mult = (tmp > ONE_Q15) ? ONE_Q15 : (int16_t)tmp;
        }

        for (int32_t ch = 0; ch < num_channels; ch++)
        {
            uint32_t si = i * (uint32_t)num_channels + (uint32_t)ch;

            if (bit_width == 16)
            {
                int16_t *buf = (int16_t *)pcm_buf;
                buf[si] = (int16_t)__nds32__khmbb((uint32_t)buf[si], (uint32_t)fade_mult);
            }
            else if (bit_width == 24)
            {
                /* 24-bit right-aligned in int32_t container.
                 * mask + manual sign-extend from bit 23, then kwmmul directly. */
                int32_t *buf = (int32_t *)pcm_buf;
                int32_t fade_q31 = ((int32_t)fade_mult) << 16;
                int32_t s = buf[si] & 0x00FFFFFF;
                if (s & 0x00800000) s |= 0xFF000000;
                buf[si] = (int32_t)__nds32__kwmmul(s, fade_q31);
            }
            else
            {
                int32_t *buf = (int32_t *)pcm_buf;
                int32_t fade_q31 = ((int32_t)fade_mult) << 16;
                buf[si] = (int32_t)__nds32__kwmmul((int32_t)buf[si], (int32_t)fade_q31);
            }
        }
    }
}
