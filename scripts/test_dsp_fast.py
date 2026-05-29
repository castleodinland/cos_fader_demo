"""
验证 cos_fade_dsp_fast.c: Bresenham 角度累加器 + nds32_cos_q15
对照:  i*ONE_Q15/denom + nds32_cos_q15
"""

import numpy as np

ONE_Q15 = 32767

def nds32_cos_q15_sim(angle_q15):
    rad = angle_q15 * np.pi / 32768.0
    return max(-32768, min(32767, int(round(np.cos(rad) * 32768))))

def reference(N, direction):
    if N == 0: return []
    if N == 1: return [0]
    denom = N - 1
    mults = []
    for i in range(N):
        if direction < 0 and i == denom:
            mults.append(0)
        elif direction > 0 and i == 0:
            mults.append(0)
        elif direction > 0 and i == denom:
            mults.append(ONE_Q15)
        else:
            angle = (i * ONE_Q15) // denom
            cosv = nds32_cos_q15_sim(angle)
            if direction < 0:
                mults.append((ONE_Q15 + cosv + 1) >> 1)
            else:
                tmp = (ONE_Q15 - cosv + 1) >> 1
                mults.append(min(ONE_Q15, tmp))
    return mults

def fast(N, direction):
    if N == 0: return []
    if N == 1: return [0]
    step_max = N - 1
    denom = step_max

    db = ONE_Q15 // denom
    rs = ONE_Q15 % denom
    x, ra = 0, 0
    def nxt():
        nonlocal x, ra
        v = x
        x += db; ra += rs
        if ra >= denom: x += 1; ra -= denom
        return v

    mults = []
    if direction < 0:
        for i in range(step_max):
            angle = nxt()
            cosv = nds32_cos_q15_sim(angle)
            mults.append((ONE_Q15 + cosv + 1) >> 1)
        mults.append(0)
    else:
        mults.append(0)
        nxt()
        for i in range(1, step_max):
            angle = nxt()
            cosv = nds32_cos_q15_sim(angle)
            tmp = (ONE_Q15 - cosv + 1) >> 1
            mults.append(min(ONE_Q15, tmp))
        mults.append(ONE_Q15)
    return mults

print("=" * 60)
print("验证: Bresenham + nds32_cos_q15")
print("=" * 60)

all_ok = True
for N in [1,2,3,4,5,8,10,16,32,64,100,256,512,1000,44100]:
    ro = reference(N, -1); rf = fast(N, -1)
    ri = reference(N, +1); rfi = fast(N, +1)
    eo = max(abs(a-b) for a,b in zip(ro,rf))
    ei = max(abs(a-b) for a,b in zip(ri,rfi))
    ok = (eo == 0 and ei == 0)
    if not ok: all_ok = False
    print(f"  N={N:5d}:  out_err={eo:2d}  in_err={ei:2d}  {'OK' if ok else '!!'}")

print(f"\n{'ALL PASS' if all_ok else 'ISSUES FOUND'}")
