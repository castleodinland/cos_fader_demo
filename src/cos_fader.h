/**
 * @file    cos_fader.h
 * @brief   Raised-cosine fade-in / fade-out with Bresenham angle accumulator
 *
 * Digitally-controlled fade using the raised-cosine window function:
 *   fade-out: y(t) = x(t) * (1 + cos(pi*t/T)) / 2
 *   fade-in:  y(t) = x(t) * (1 - cos(pi*t/T)) / 2
 *
 * The angle sequence t/T is generated via a Bresenham-style integer
 * accumulator, eliminating per-sample division at no memory cost.
 * Cosine values are supplied by the DSP library (nds32_cos_q15).
 *
 * Supports 16-bit, 24-bit (right-aligned in int32_t), and 32-bit PCM.
 * In-place operation is allowed (pcm_in == pcm_out).
 *
 * @note Call cos_fader_init() to begin a new fade cycle.
 *       Once the fade duration elapses, the output holds:
 *         fade-out → zero (muted)
 *         fade-in  → passthrough (input copied to output)
 */

#ifndef COS_FADER_H
#define COS_FADER_H

#include <stdint.h>

/** Error codes */
typedef enum {
    COS_FADER_ERROR_OK                = 0,  /**< no error */
    COS_FADER_ERROR_NULL_POINTER      = 1,  /**< null context or buffer pointer */
    COS_FADER_ERROR_NUM_CHANNELS      = 2,  /**< num_channels <= 0 */
    COS_FADER_ERROR_BIT_WIDTH         = 3,  /**< bit_width not in {16, 24, 32} */
    COS_FADER_ERROR_FADE_SAMPLES      = 4,  /**< fade_samples < 1 */
    COS_FADER_ERROR_FADE_TYPE         = 5,  /**< fade_type out of range */
} CosFaderError;

/** Fade type identifiers */
#define COS_FADER_BYPASS    0   /**< passthrough, no fade applied */
#define COS_FADER_FADE_IN   1   /**< raised-cosine fade-in  (0 → 1) */
#define COS_FADER_FADE_OUT  2   /**< raised-cosine fade-out (1 → 0) */

/**
 * CosFader context structure.
 *
 * Configuration is written once by cos_fader_init() and must not be
 * modified afterwards.  The runtime fields (fade_counter and the
 * Bresenham accumulator) are updated by cos_fader_apply() and allow
 * seamless cross-frame processing across an arbitrary number of calls.
 */
typedef struct {
    /* --- configuration (read-only after init) --- */
    int32_t num_channels;       /**< number of interleaved channels (>= 1) */
    int32_t fade_type;          /**< COS_FADER_BYPASS / _FADE_IN / _FADE_OUT */
    int32_t bit_width;          /**< 16, 24, or 32 bits per sample */
    int32_t fade_samples;       /**< fade duration in per-channel samples */

    /* --- runtime state --- */
    int32_t fade_counter;       /**< per-channel samples processed so far */

    /* --- Bresenham angle-accumulator state (resumed across frames) --- */
    uint16_t angle_x;           /**< current Q15 angle, range [0..32767] */
    uint32_t delta_base;        /**< per-step integer increment = ONE_Q15 / denom */
    uint32_t rem_step;          /**< per-step remainder    = ONE_Q15 % denom */
    uint32_t rem_accum;         /**< remainder accumulator */
    uint32_t denom;             /**< denominator = fade_samples - 1 */
} CosFaderContext;

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief   Initialise the cos-fader for a new fade cycle.
 * @param   ct            Pointer to a CosFaderContext object.
 * @param   num_channels  Number of interleaved channels (1, 2, ...).
 * @param   bit_width     Sample bit-width: 16, 24, or 32.
 * @param   fade_type     COS_FADER_BYPASS, COS_FADER_FADE_IN, or
 *                        COS_FADER_FADE_OUT.
 * @param   fade_samples  Fade duration in per-channel samples (>= 1).
 * @return  Error code (COS_FADER_ERROR_OK on success).
 * @note    Call this function again to restart the fade from the beginning.
 */
int32_t cos_fader_init(CosFaderContext *ct, int32_t num_channels,
                       int32_t bit_width, int32_t fade_type,
                       int32_t fade_samples);

/**
 * @brief   Apply the fade effect to a PCM block.
 *
 * Processes @p n per-channel samples from @p pcm_in and writes the
 * faded result to @p pcm_out.  If @p pcm_in == @p pcm_out the
 * operation is performed in-place.
 *
 * The fade counter advances sample-by-sample.  Once the configured
 * fade duration (@c fade_samples) is exhausted, subsequent calls
 * hold the final state:
 *   - fade-out : output is zeroed
 *   - fade-in  : output equals input (passthrough)
 *   - bypass   : output equals input (passthrough, counter unchanged)
 *
 * @param   ct      Pointer to a CosFaderContext object.
 * @param   pcm_in  Input PCM buffer (interleaved channels).
 * @param   pcm_out Output PCM buffer (may be the same as pcm_in).
 * @param   n       Number of per-channel samples to process in this call.
 * @return  Error code (COS_FADER_ERROR_OK on success).
 */
int32_t cos_fader_apply(CosFaderContext *ct, void *pcm_in,
                        void *pcm_out, int32_t n);

/**
 * @brief   Check whether the current fade cycle has completed.
 * @param   ct  Pointer to a CosFaderContext object.
 * @return  0 if the fade is still in progress, 1 if it has finished.
 * @note    Returns 1 for null pointer (treated as done).
 */
int32_t cos_fader_is_done(CosFaderContext *ct);

#ifdef __cplusplus
}
#endif

#endif /* COS_FADER_H */
