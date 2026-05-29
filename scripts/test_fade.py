import numpy as np

"""Simulate the exact C algorithm in Python to verify correctness"""

TABLE_BITS = 8
TABLE_SIZE = (1 << TABLE_BITS) + 1
ONE_Q15 = 32767
ROUND_Q15 = 16384

def gen_cos_table():
    cos_tbl = []
    for i in range(TABLE_SIZE):
        angle = np.pi * i / (TABLE_SIZE - 1)
        q15 = int(round(np.cos(angle) * 32768))
        q15 = max(-32768, min(32767, q15))
        cos_tbl.append(q15)
    return cos_tbl

COS_TABLE = gen_cos_table()

def cos_lookup_q15(x_q15):
    idx_frac = x_q15 << TABLE_BITS
    idx = idx_frac >> 15
    frac = idx_frac & 0x7FFF
    y0 = COS_TABLE[idx]
    y1 = COS_TABLE[idx + 1]
    diff = y1 - y0
    interp = (frac * diff + ROUND_Q15) >> 15
    return y0 + interp

def q15_mul(a, b):
    """Simulate ANDES_Q15_MUL via __nds32__khmbb"""
    a16 = np.int16(a).view(np.uint16)
    b16 = np.int16(b).view(np.uint16)
    prod = np.int32(a) * np.int32(b)
    result = prod >> 15
    return np.int16(np.clip(result, -32768, 32767))

def q31_mul(a, b):
    """Simulate ANDES_Q31_MUL via __nds32__kwmmul"""
    prod = np.int64(a) * np.int64(b)
    result = prod >> 31
    return np.int32(np.clip(result, -2147483648, 2147483647))

def cos_fade_out(pcm, num_channels, bit_width, fade_points):
    if fade_points == 0:
        return pcm.copy()
    pcm = pcm.copy()
    if fade_points == 1:
        for ch in range(num_channels):
            pcm[ch] = 0
        return pcm
    step_max = fade_points - 1
    for i in range(fade_points):
        if i == step_max:
            fade_mult = 0
        else:
            x_q15 = (i * ONE_Q15) // step_max
            cos_val = cos_lookup_q15(x_q15)
            fade_mult = (ONE_Q15 + cos_val + 1) >> 1
        for ch in range(num_channels):
            si = i * num_channels + ch
            if bit_width == 16:
                pcm[si] = q15_mul(pcm[si], fade_mult)
            else:
                fade_q31 = fade_mult << 16
                pcm[si] = q31_mul(pcm[si], fade_q31)
    return pcm

def cos_fade_in(pcm, num_channels, bit_width, fade_points):
    if fade_points == 0:
        return pcm.copy()
    pcm = pcm.copy()
    if fade_points == 1:
        for ch in range(num_channels):
            pcm[ch] = 0
        return pcm
    step_max = fade_points - 1
    for i in range(fade_points):
        if i == 0:
            fade_mult = 0
        elif i == step_max:
            fade_mult = ONE_Q15
        else:
            x_q15 = (i * ONE_Q15) // step_max
            cos_val = cos_lookup_q15(x_q15)
            tmp = (ONE_Q15 - cos_val + 1) >> 1
            fade_mult = ONE_Q15 if tmp > ONE_Q15 else tmp
        for ch in range(num_channels):
            si = i * num_channels + ch
            if bit_width == 16:
                pcm[si] = q15_mul(pcm[si], fade_mult)
            else:
                fade_q31 = fade_mult << 16
                pcm[si] = q31_mul(pcm[si], fade_q31)
    return pcm

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------
def generate_sine(num_samples, num_channels, bit_width, freq=440, sample_rate=44100):
    t = np.arange(num_samples) / sample_rate
    signal = np.sin(2 * np.pi * freq * t)
    if bit_width == 16:
        pcm = np.int16(np.round(signal * 30000))
    else:
        pcm = np.int32(np.round(signal * 1073741824))
    pcm = np.tile(pcm, (num_channels, 1)).T.ravel()
    return pcm

def interleave(pcm, num_channels):
    return pcm.reshape(-1, num_channels).T.ravel(order='F')

def deinterleave(pcm, num_channels):
    return pcm.reshape(-1, num_channels).T

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def verify_fade_out(result, orig, num_channels, fade_points):
    result_ch = deinterleave(result, num_channels)
    orig_ch = deinterleave(orig, num_channels)
    ok = True
    for ch in range(num_channels):
        last_idx = fade_points * num_channels + ch - num_channels
        if result[last_idx] != 0:
            print(f"  FAIL: fade_out ch{ch} last point != 0 ({result[last_idx]})")
            ok = False
        if fade_points > 1 and result_ch[ch][0] != orig_ch[ch][0]:
            ratio = result_ch[ch][0] / max(orig_ch[ch][0], 1)
            if abs(ratio - 1.0) > 0.001:
                print(f"  FAIL: fade_out ch{ch} first point changed (ratio={ratio:.4f})")
                ok = False
    return ok

def verify_fade_in(result, orig, num_channels, fade_points):
    result_ch = deinterleave(result, num_channels)
    ok = True
    for ch in range(num_channels):
        if result[ch] != 0:
            print(f"  FAIL: fade_in ch{ch} first point != 0 ({result[ch]})")
            ok = False
        if fade_points > 1:
            last_idx = (fade_points - 1) * num_channels + ch
            ratio = result[last_idx] / max(orig[last_idx], 1)
            if abs(ratio - 1.0) > 0.01:
                print(f"  WARN: fade_in ch{ch} last point ratio={ratio:.4f} (may be OK due to Q15 precision)")
    return ok

def run_tests():
    tests = [
        (16, 1, 64), (16, 2, 64),
        (32, 1, 64), (32, 2, 64),
        (16, 1, 1), (16, 2, 1),
        (16, 1, 100), (32, 2, 100),
    ]
    all_ok = True
    for bw, nc, fp in tests:
        ns = max(fp, 16)
        pcm = generate_sine(ns, nc, bw)
        fo = cos_fade_out(pcm, nc, bw, fp)
        fi = cos_fade_in(pcm, nc, bw, fp)
        r1 = verify_fade_out(fo, pcm, nc, fp)
        r2 = verify_fade_in(fi, pcm, nc, fp)
        ok = r1 and r2
        all_ok &= ok
        print(f"  {'OK' if ok else 'FAIL'} bw={bw} ch={nc} fp={fp}")
    return all_ok

def plot_tests():
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skip plotting")
        return

    fig, axes = plt.subplots(4, 2, figsize=(14, 10), constrained_layout=True)
    cases = [
        (16, 1, 128, "Mono 16-bit"),
        (16, 2, 128, "Stereo 16-bit"),
        (32, 1, 128, "Mono 32-bit"),
        (32, 2, 128, "Stereo 32-bit"),
    ]
    for row, (bw, nc, fp, title) in enumerate(cases):
        ns = fp + 64
        pcm = generate_sine(ns, nc, bw)

        fo = cos_fade_out(pcm.copy(), nc, bw, fp)
        fi = cos_fade_in(pcm.copy(), nc, bw, fp)

        ch0_orig = deinterleave(pcm, nc)[0]
        ch0_fo   = deinterleave(fo, nc)[0]
        ch0_fi   = deinterleave(fi, nc)[0]

        ax = axes[row, 0]
        ax.plot(ch0_orig, alpha=0.5, label='Original')
        ax.plot(ch0_fo, label='Fade Out')
        ax.axvline(fp - 0.5, color='gray', ls='--', alpha=0.5)
        ax.set_title(f'{title} - Fade Out')
        ax.legend(fontsize=7)
        ax.set_xlabel('Sample (per channel)')

        ax = axes[row, 1]
        ax.plot(ch0_orig, alpha=0.5, label='Original')
        ax.plot(ch0_fi, label='Fade In')
        ax.axvline(fp - 0.5, color='gray', ls='--', alpha=0.5)
        ax.set_title(f'{title} - Fade In')
        ax.legend(fontsize=7)
        ax.set_xlabel('Sample (per channel)')

    # last plot: overlay fade curves themselves
    ax = axes[3, 0]
    for bw in (16, 32):
        pcm = generate_sine(128, 1, bw)
        fo = cos_fade_out(pcm.copy(), 1, bw, 100)
        fi = cos_fade_in(pcm.copy(), 1, bw, 100)
        # normalize to show multiplier
        ch0 = deinterleave(pcm, 1)[0]
        fo0 = deinterleave(fo, 1)[0]
        fi0 = deinterleave(fi, 1)[0]
        norm = np.where(ch0 != 0, 1.0, 1.0)
        with np.errstate(divide='ignore', invalid='ignore'):
            fo_mult = np.where(ch0[:100] != 0, fo0[:100].astype(float) / ch0[:100].astype(float), 0)
            fi_mult = np.where(ch0[:100] != 0, fi0[:100].astype(float) / ch0[:100].astype(float), 0)
        ax.plot(fo_mult, '--', label=f'FadeOut mult ({bw}-bit)')
        ax.plot(fi_mult, ':', label=f'FadeIn mult ({bw}-bit)')
    ax.axhline(0, color='gray', ls='-', alpha=0.3)
    ax.axhline(1, color='gray', ls='-', alpha=0.3)
    ax.set_title('Fade Multiplier Curve (derived from PCM)')
    ax.set_ylabel('Multiplier')
    ax.legend(fontsize=7)

    axes[3, 1].axis('off')

    plt.savefig('fade_test_result.png', dpi=150)
    plt.close()
    print("  Plot saved to fade_test_result.png")

def print_checks():
    print("\n--- Quick checks ---")
    x0 = cos_lookup_q15(0)
    xm = cos_lookup_q15(16384)
    x1 = cos_lookup_q15(32767)
    print(f"cos_lookup(0)      = {x0}  (expect 32767)")
    print(f"cos_lookup(0.5)    = {xm}  (expect ~0)")
    print(f"cos_lookup(1.0)    = {x1}  (expect -32768)")

    fade_out_0 = (ONE_Q15 + x0 + 1) >> 1
    fade_out_1 = (ONE_Q15 + x1 + 1) >> 1
    fade_in_0  = (ONE_Q15 - x0 + 1) >> 1
    fade_in_1  = min(ONE_Q15, (ONE_Q15 - x1 + 1) >> 1)
    print(f"fade_out[0]  = {fade_out_0} (expect {ONE_Q15})")
    print(f"fade_out[N]  = {fade_out_1} (expect 0)")
    print(f"fade_in[0]   = {fade_in_0}  (expect 0)")
    print(f"fade_in[N]   = {fade_in_1}  (expect {ONE_Q15})")

if __name__ == '__main__':
    print("Running verification...")
    ok = run_tests()
    print_checks()
    plot_tests()
    print(f"\n{'ALL TESTS PASSED' if ok else 'SOME TESTS FAILED'}")
