# cos_fader_demo

Raised-cosine audio fade-in / fade-out library for the Andes NDS32 DSP platform.

## Overview

Smooth audio volume transitions using raised-cosine windowing, avoiding the click/pop artifacts caused by abrupt waveform truncation.

```
fade-out:  y(t) = x(t) × (1 + cos(π·t/T)) / 2    (1 → 0)
fade-in:   y(t) = x(t) × (1 − cos(π·t/T)) / 2    (0 → 1)
```

The raised-cosine window has **zero derivative at both endpoints**, producing a cleaner spectrum than linear fades.

## Key Features

- **Bresenham angle accumulator** — pure integer addition, zero divisions per sample
- **No LUT required** — uses DSP library `nds32_cos_q15` (or optional 257-entry lookup table with interpolation)
- **16 / 24 / 32-bit PCM** — interleaved multi-channel support, in-place capable
- **Cross-frame state machine** (`cos_fader.c`) — resume fade across arbitrary block boundaries

## File Map

### `src/`

| File | Description |
|---|---|
| `cos_fade.c` | LUT-based cosine with linear interpolation (baseline) |
| `cos_fade_dsp.c` | DSP library `nds32_cos_q15` (ROM-free baseline) |
| `cos_fade_fast.c` | LUT + Bresenham accumulator + DSP interpolation |
| `cos_fade_dsp_fast.c` | DSP library + Bresenham accumulator (**recommended**) |
| `cos_fader.c` / `.h` | Full fader with init/apply/is_done state machine |
| `cos_table.inc` | 257-point Q15 cosine LUT |
| `fader.h` | Original linear fade interface (v1.0, reference only) |

### `scripts/`

Python verification tests and MATLAB simulation matching the C algorithm bit-exactly.

### `docs/`

A step-by-step tutorial (`fade_tutorial.md`, in Chinese) covering derivatives, AM modulation, convolution, and window frequency response — written for a high-school audience.

## Platform

- **Target**: Andes NDS32 DSP (RV32-like ISA)
- **DSP intrinsics**: `__nds32__khmbb`, `__nds32__kwmmul`, `__nds32__smmul_u`
- **Reference**: Andes DSP Library v3 User Manual (included in `docs/`)
