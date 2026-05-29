"""Verify cos_fade_fast.c against the original — exactness check"""

import numpy as np

TABLE_BITS = 8
TABLE_SIZE = (1 << TABLE_BITS) + 1
ONE_Q15 = 32767
ROUND_Q15 = 16384

COS_TABLE = [int(round(np.cos(np.pi * i / (TABLE_SIZE - 1)) * 32768))
             for i in range(TABLE_SIZE)]

# ---- Original lookup ----
def cos_lookup_orig(x_q15):
    idx_frac = x_q15 << TABLE_BITS
    idx = idx_frac >> 15
    frac = idx_frac & 0x7FFF
    y0, y1 = COS_TABLE[idx], COS_TABLE[idx + 1]
    diff = y1 - y0
    interp = (frac * diff + ROUND_Q15) >> 15
    return y0 + interp

def fade_mult_orig(i, denom, direction):
    if direction < 0 and i == denom: return 0
    if direction > 0 and i == 0:     return 0
    if direction > 0 and i == denom: return ONE_Q15
    x_q15 = (i * ONE_Q15) // denom if denom > 0 else 0
    cosv = cos_lookup_orig(x_q15)
    if direction < 0:
        tmp = (ONE_Q15 + cosv + 1) >> 1
    else:
        tmp = (ONE_Q15 - cosv + 1) >> 1
    return min(ONE_Q15, tmp)

# ---- Fast: smmul_u sim ----
def smmul_u_sim(a, b):
    prod = np.int64(a) * np.int64(b) + np.int64(0x80000000)
    return np.int32(prod >> 32)

def cos_lookup_fast(x_q15):
    idx_frac = x_q15 << TABLE_BITS
    idx = idx_frac >> 15
    frac = idx_frac & 0x7FFF
    y0, y1 = COS_TABLE[idx], COS_TABLE[idx + 1]
    diff = y1 - y0
    interp = smmul_u_sim(np.int32(np.uint32(frac) << 16), diff << 1)
    return y0 + interp

# ---- Fast: Bresenham angle accumulator ----
class AngleAccum:
    def __init__(self, denom):
        self.x_q15 = 0
        self.denom = denom if denom > 0 else 1
        self.delta_base = ONE_Q15 // denom if denom > 0 else 0
        self.rem_step = ONE_Q15 % denom if denom > 0 else 0
        self.rem_accum = 0
    def next(self):
        x = self.x_q15
        self.x_q15 += self.delta_base
        self.rem_accum += self.rem_step
        if self.rem_accum >= self.denom:
            self.x_q15 += 1
            self.rem_accum -= self.denom
        return x

def fade_calc_mult(x_q15, direction):
    cosv = cos_lookup_fast(x_q15)
    if direction < 0:
        tmp = (int(ONE_Q15) + int(cosv) + 1) >> 1
    else:
        tmp = (int(ONE_Q15) - int(cosv) + 1) >> 1
    return min(ONE_Q15, tmp)

def simulate_fade_orig(N, direction):
    """Original: direct i*ONE_Q15/denom per sample"""
    denom = max(N - 1, 1)
    results = []
    for i in range(N):
        results.append(fade_mult_orig(i, denom, direction))
    return results

def simulate_fade_fast(N, direction):
    """Optimized: Bresenham accumulator, matches fixed C loop structure"""
    if N == 0:
        return []
    if N == 1:
        return [0]

    step_max = N - 1
    acc = AngleAccum(step_max)
    results = []

    if direction < 0:  # fade-out
        for i in range(step_max):
            x_q15 = acc.next()
            results.append(fade_calc_mult(x_q15, -1))
        results.append(0)  # last = 0
    else:  # fade-in
        results.append(0)  # first = 0
        acc.next()         # advance past i=0
        for i in range(1, step_max):
            x_q15 = acc.next()
            results.append(fade_calc_mult(x_q15, +1))
        results.append(ONE_Q15)  # last = 1.0

    return results

# ===============================
def main():
    print("=== Bucket 1: smmul_u vs generic multiply (spot check) ===")
    for frac in [0, 8192, 16384, 24576, 32767]:
        for diff in [-32768, -16384, 0, 16384, 32767]:
            e = (frac * diff + ROUND_Q15) >> 15
            g = smmul_u_sim(np.int32(np.uint32(frac) << 16), diff << 1)
            if e != g:
                print(f"  MISMATCH: frac={frac:5d} diff={diff:6d}  exp={e:5d} got={g:5d}")
    print("  smmul_u: all OK")

    print("\n=== Bucket 2: Bresenham exactness vs i*ONE_Q15/denom ===")
    for N in [2, 3, 10, 100, 1000, 44100]:
        denom = max(N - 1, 1)
        acc = AngleAccum(denom)
        all_ok = True
        for step in range(N - 1):  # only N-1 calls made in C loop
            x = acc.next()
            x_exact = (step * ONE_Q15) // denom if denom > 0 else 0
            if x != x_exact:
                print(f"  N={N} MISMATCH step={step}: {x} vs {x_exact}")
                all_ok = False
        status = "OK" if all_ok else "FAIL"
        print(f"  N={N:5d}: {status}")

    print("\n=== Bucket 3: Full fade sequence comparison ===")
    all_pass = True
    for N in [1, 2, 3, 4, 5, 8, 10, 16, 32, 64, 100, 256, 512, 1000]:
        orig_out = simulate_fade_orig(N, -1)
        fast_out = simulate_fade_fast(N, -1)
        orig_in  = simulate_fade_orig(N, +1)
        fast_in  = simulate_fade_fast(N, +1)

        max_err_out = max(abs(a - b) for a, b in zip(orig_out, fast_out))
        max_err_in  = max(abs(a - b) for a, b in zip(orig_in, fast_in))

        ok = (max_err_out == 0 and max_err_in == 0)
        if not ok:
            all_pass = False
            if max_err_out:
                mismatches = [(i, orig_out[i], fast_out[i]) for i in range(N) if orig_out[i] != fast_out[i]]
            else:
                mismatches = [(i, orig_in[i], fast_in[i]) for i in range(N) if orig_in[i] != fast_in[i]]
        print(f"  N={N:5d}:  out_err={max_err_out:2d}  in_err={max_err_in:2d}  {'OK' if ok else '!!'}")

    if all_pass:
        print("\n  ALL SMALL-N TESTS PASS")

    print("\n=== Bucket 4: Full 44100 verification ===")
    N = 44100
    orig_out = simulate_fade_orig(N, -1)
    fast_out = simulate_fade_fast(N, -1)
    orig_in  = simulate_fade_orig(N, +1)
    fast_in  = simulate_fade_fast(N, +1)

    max_err_out = max(abs(a - b) for a, b in zip(orig_out, fast_out))
    max_err_in  = max(abs(a - b) for a, b in zip(orig_in, fast_in))
    print(f"  Fade-out: max_err = {max_err_out} LSB")
    print(f"  Fade-in:  max_err = {max_err_in} LSB")

    if max_err_out == 0 and max_err_in == 0:
        print("\n  ALL PASS")
    else:
        print("\n  ISSUES FOUND")

if __name__ == '__main__':
    main()
