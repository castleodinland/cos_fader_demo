#ifndef COS_FADE_H
#define COS_FADE_H

#include <stdint.h>

void cos_fade_out(void *pcm_buf, int32_t num_channels, int32_t bit_width, uint32_t fade_points);

void cos_fade_in(void *pcm_buf, int32_t num_channels, int32_t bit_width, uint32_t fade_points);

#endif
