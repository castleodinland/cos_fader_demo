import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

try:
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

DPI = 150
OUT_DIR = 'figures'
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# Helper: Chinese text fallback
# ============================================================
def ch(text_cn, text_en):
    """Try Chinese, fallback to English"""
    try:
        fig, ax = plt.subplots(figsize=(0.1, 0.1))
        t = ax.text(0, 0, text_cn)
        fig.canvas.draw()
        plt.close(fig)
        return text_cn
    except:
        return text_en

# ============================================================
# fig 01: 连续 vs 不连续
# ============================================================
def fig_01_sine_discontinuity():
    fs = 1000
    t = np.linspace(0, 3, fs*3)
    x = np.sin(2*np.pi*3*t)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5), sharex=True)

    ax1.plot(t, x, 'b-', linewidth=1.5)
    ax1.set_ylabel('x(t)')
    ax1.set_title(ch('连续信号：平滑的正弦波', 'Continuous: Smooth Sine Wave'))
    ax1.set_ylim(-1.5, 1.5)
    ax1.axhline(0, color='gray', linewidth=0.5)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 3)

    x2 = x.copy()
    x2[t > 2.0] = 0
    ax2.plot(t, x2, 'r-', linewidth=1.5)
    ax2.set_ylabel('x(t)')
    ax2.set_title(ch('不连续信号：在 t=2.0 处被"一刀切"', 'Discontinuous: abruptly cut at t=2.0'))
    ax2.set_ylim(-1.5, 1.5)
    ax2.axhline(0, color='gray', linewidth=0.5)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlabel('t (seconds)')

    ax2.annotate(ch('不连续点!\n值从≈0跳变到0', 'Discontinuity!'),
                xy=(2.0, 0), xytext=(2.4, -1.0),
                arrowprops=dict(arrowstyle='->', color='darkred', lw=2),
                fontsize=10, color='darkred', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', edgecolor='darkred'))

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_01_sine_discontinuity.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_01_sine_discontinuity")

# ============================================================
# fig 02: 导数 - 切线
# ============================================================
def fig_02_derivative_tangent():
    x = np.linspace(-2, 2, 400)
    y = 0.5 * x**3 - x + 0.5

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, y, 'b-', linewidth=2, label=ch('曲线 f(x) = 0.5x³-x+0.5', 'f(x) = 0.5x³-x+0.5'))

    pts = [-1.5, -0.5, 0.5, 1.5]
    colors = ['green', 'orange', 'red', 'purple']
    for pt, c in zip(pts, colors):
        # derivative at point
        slope = 1.5 * pt**2 - 1
        y0 = 0.5 * pt**3 - pt + 0.5
        x_tan = np.linspace(pt-0.6, pt+0.6, 10)
        y_tan = slope * (x_tan - pt) + y0
        ax.plot(x_tan, y_tan, '--', color=c, linewidth=1.5, alpha=0.8)
        ax.plot(pt, y0, 'o', color=c, markersize=8, zorder=5)
        ax.text(pt+0.08, y0-0.15, f"f'({pt:.1f})={slope:.1f}", fontsize=9,
                color=c, fontweight='bold')

    ax.axhline(0, color='gray', linewidth=0.5)
    ax.axvline(0, color='gray', linewidth=0.5)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('x')
    ax.set_ylabel('f(x)')
    ax.set_title(ch('导数 = 曲线在某点的"瞬时斜率"（切线）', 'Derivative = Instantaneous Slope (Tangent Line)'))
    ax.legend(fontsize=10)
    ax.set_ylim(-2, 2.5)

    ax.text(0.02, 0.98, ch('切线越陡 → 导数的绝对值越大', 'Steeper tangent → Larger |derivative|'),
            transform=ax.transAxes, fontsize=10, va='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='gray'))

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_02_derivative_tangent.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_02_derivative_tangent")

# ============================================================
# fig 03: 淡入淡出曲线对比
# ============================================================
def fig_03_fade_compare():
    N = 100
    i = np.arange(N)
    t = i / (N-1)

    rect = np.where(t < 1, 1, 0)
    rect[-1] = 0

    linear = 1 - t

    raised_cos = 0.5 * (1 + np.cos(np.pi * t))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))

    # fade out
    ax1.plot(t, rect, 'gray', linewidth=2, linestyle=':', label=ch('矩形（一刀切）', 'Rectangular'))
    ax1.plot(t, linear, 'orange', linewidth=2, linestyle='--', label=ch('线性（直线降）', 'Linear'))
    ax1.plot(t, raised_cos, 'blue', linewidth=3, label=ch('升余弦（平滑降）', 'Raised Cosine'))
    ax1.set_title(ch('淡出曲线对比 (Fade Out)', 'Fade Out Curve Comparison'))
    ax1.set_ylabel(ch('音量倍率', 'Volume'))
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)

    ann_y = 0.75
    ax1.annotate(ch('导数=0，水平进入', "f'(0)=0, smooth enter"),
                xy=(0, 1), xytext=(0.15, ann_y),
                arrowprops=dict(arrowstyle='->', color='blue'), fontsize=8, color='blue')
    ax1.annotate(ch('导数≠0，有斜率跳变', "f'(0)≠0, slope jump"),
                xy=(0, 1), xytext=(0.15, ann_y-0.12),
                arrowprops=dict(arrowstyle='->', color='orange'), fontsize=8, color='orange')

    # fade in
    raised_cos_in = 0.5 * (1 - np.cos(np.pi * t))
    linear_in = t
    rect_in = np.where(t < 1, 1, 0)
    rect_in[0] = 0

    ax2.plot(t, rect_in, 'gray', linewidth=2, linestyle=':', label=ch('矩形', 'Rectangular'))
    ax2.plot(t, linear_in, 'orange', linewidth=2, linestyle='--', label=ch('线性', 'Linear'))
    ax2.plot(t, raised_cos_in, 'blue', linewidth=3, label=ch('升余弦', 'Raised Cosine'))
    ax2.set_title(ch('淡入曲线对比 (Fade In)', 'Fade In Curve Comparison'))
    ax2.set_ylabel(ch('音量倍率', 'Volume'))
    ax2.set_xlabel(ch('归一化时间 t/T', 'Normalized Time t/T'))
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)

    ax2.annotate(ch('从0开始，导数0', "f(0)=0, f'(0)=0"),
                xy=(0, 0), xytext=(0.08, 0.12),
                arrowprops=dict(arrowstyle='->', color='blue'), fontsize=8, color='blue')
    ax2.annotate(ch('导数=0，水平到达', "f'(T)=0, smooth arrival"),
                xy=(1, 1), xytext=(0.7, 0.82),
                arrowprops=dict(arrowstyle='->', color='blue'), fontsize=8, color='blue')

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_03_fade_compare.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_03_fade_compare")

# ============================================================
# fig 04: 升余弦曲线详解
# ============================================================
def fig_04_raised_cosine_detail():
    N = 100
    t = np.linspace(0, 1, N)
    cos_part = np.cos(np.pi * t)
    raised = 0.5 * (1 + cos_part)
    fade_in = 0.5 * (1 - np.cos(np.pi * t))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # fade out
    ax1.plot(t, cos_part, 'r--', linewidth=1.5, alpha=0.6, label=ch('cos(πt/T) 部分', 'cos(πt/T) component'))
    ax1.plot(t, raised, 'b-', linewidth=3, label=ch('升余弦淡出', 'Raised Cosine Fade Out'))
    ax1.axhline(0.5, color='gray', linewidth=0.5, linestyle='--')
    ax1.axhline(0, color='gray', linewidth=0.5)
    ax1.axhline(1, color='gray', linewidth=0.5)
    ax1.set_title(ch('升余弦 = (1 + cos(πt/T)) / 2', 'Raised Cosine = (1 + cos(πt/T)) / 2'))
    ax1.set_xlabel(ch('t/T', 't/T'))
    ax1.set_ylabel(ch('幅值', 'Amplitude'))
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(-0.1, 1.1)

    # annotate key points
    ax1.annotate('f(0)=1', xy=(0, 1), xytext=(-0.08, 0.85),
                fontsize=10, color='blue', fontweight='bold')
    ax1.annotate('f(T)=0', xy=(1, 0), xytext=(0.85, -0.1),
                fontsize=10, color='blue', fontweight='bold')
    ax1.annotate("f'(0)=0", xy=(0.02, 0.98), xytext=(0.12, 0.92),
                arrowprops=dict(arrowstyle='->', color='green'), fontsize=9, color='green')
    ax1.annotate("f'(T)=0", xy=(0.98, 0.02), xytext=(0.8, 0.15),
                arrowprops=dict(arrowstyle='->', color='green'), fontsize=9, color='green')

    # fade in
    ax2.plot(t, -cos_part, 'r--', linewidth=1.5, alpha=0.6, label=ch('-cos(πt/T) 部分', '-cos(πt/T) component'))
    ax2.plot(t, fade_in, 'b-', linewidth=3, label=ch('升余弦淡入', 'Raised Cosine Fade In'))
    ax2.axhline(0.5, color='gray', linewidth=0.5, linestyle='--')
    ax2.axhline(0, color='gray', linewidth=0.5)
    ax2.axhline(1, color='gray', linewidth=0.5)
    ax2.set_title(ch('升余弦淡入 = (1 - cos(πt/T)) / 2', 'Fade In = (1 - cos(πt/T)) / 2'))
    ax2.set_xlabel(ch('t/T', 't/T'))
    ax2.set_ylabel(ch('幅值', 'Amplitude'))
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(-0.1, 1.1)

    ax2.annotate('f(0)=0', xy=(0, 0), xytext=(-0.08, 0.08),
                fontsize=10, color='blue', fontweight='bold')
    ax2.annotate('f(T)=1', xy=(1, 1), xytext=(0.82, 0.88),
                fontsize=10, color='blue', fontweight='bold')
    ax2.annotate("f'(0)=0", xy=(0.02, 0.02), xytext=(0.1, 0.08),
                arrowprops=dict(arrowstyle='->', color='green'), fontsize=9, color='green')
    ax2.annotate("f'(T)=0", xy=(0.98, 0.98), xytext=(0.72, 0.85),
                arrowprops=dict(arrowstyle='->', color='green'), fontsize=9, color='green')

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_04_raised_cosine_detail.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_04_raised_cosine_detail")

# ============================================================
# fig 05: C⁰ vs C¹ 连续性
# ============================================================
def fig_05_continuity_c0_c1():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # C0 only: value matches, slope jumps
    t_left = np.linspace(-1, 0, 100)
    t_right = np.linspace(0, 1, 100)
    y_left = np.sin(2*np.pi*0.5*t_left)
    y_right = -1.5 * t_right + 0.0

    ax1.plot(t_left, y_left, 'b-', linewidth=2.5, label=ch('原始信号', 'Original Signal'))
    ax1.plot(t_right, y_right, 'r-', linewidth=2.5, label=ch('淡出（线性）', 'Fade (Linear)'))
    ax1.axvline(0, color='gray', linewidth=1, linestyle='--')
    ax1.plot(0, 0, 'ko', markersize=6)

    ax1.annotate(ch('值连续 (C⁰)\n但斜率跳变', 'C⁰: value OK\nslope jumps!'),
                xy=(0, 0), xytext=(0.3, -0.6),
                arrowprops=dict(arrowstyle='->', color='darkred'),
                fontsize=10, color='darkred', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='wheat', edgecolor='darkred'))

    ax1.set_title(ch('C⁰ 连续：值匹配但斜率不匹配', 'C⁰: Value matches, slope does not'))
    ax1.set_ylim(-1.2, 1.2)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)
    ax1.axhline(0, color='gray', linewidth=0.5)

    ax1.text(0.5, -1.1, ch('f(0⁻) = f(0⁺) = 0  ✓', 'f(0⁻) = f(0⁺) = 0  ✓'), fontsize=9,
            bbox=dict(facecolor='lightgreen', alpha=0.5))
    ax1.text(0.5, -1.3, ch("f'(0⁻) ≠ f'(0⁺)  ✗", "f'(0⁻) ≠ f'(0⁺)  ✗"), fontsize=9,
            bbox=dict(facecolor='lightcoral', alpha=0.5))

    # C1: value and slope both match
    y_left2 = np.sin(2*np.pi*0.5*t_left)

    def raised_cosine_transition(t):
        return np.where(t >= 0,
                        0.5 * (1 + np.cos(np.pi * t)),
                        1.0)
    y_right2 = raised_cosine_transition(t_right) * y_left2[0]

    ax2.plot(t_left, y_left2, 'b-', linewidth=2.5, label=ch('原始信号', 'Original Signal'))
    y_right_smooth = y_left2[0] * (0.5 * (1 + np.cos(np.pi * t_right)))
    ax2.plot(t_right, y_right_smooth, 'green', linewidth=2.5, label=ch('淡出（升余弦）', 'Fade (Raised Cosine)'))
    ax2.axvline(0, color='gray', linewidth=1, linestyle='--')
    ax2.plot(0, y_left2[0], 'ko', markersize=6)

    ax2.annotate(ch('值连续 + 斜率连续 (C¹)\n完美拟合', 'C¹: value & slope\nboth match!'),
                xy=(0, y_left2[0]), xytext=(0.3, y_left2[0]-0.5),
                arrowprops=dict(arrowstyle='->', color='darkgreen'),
                fontsize=10, color='darkgreen', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='lightgreen', edgecolor='darkgreen'))

    ax2.set_title(ch('C¹ 连续：值和斜率都匹配', 'C¹: Value AND Slope both match'))
    ax2.set_ylim(-1.2, 1.2)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)
    ax2.axhline(0, color='gray', linewidth=0.5)

    ax2.text(0.5, -1.1, ch('f(0⁻) = f(0⁺)  ✓', 'f(0⁻) = f(0⁺)  ✓'), fontsize=9,
            bbox=dict(facecolor='lightgreen', alpha=0.5))
    ax2.text(0.5, -1.3, ch("f'(0⁻) = f'(0⁺)  ✓", "f'(0⁻) = f'(0⁺)  ✓"), fontsize=9,
            bbox=dict(facecolor='lightgreen', alpha=0.5))

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_05_continuity_c0_c1.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_05_continuity_c0_c1")

# ============================================================
# fig 06: 振幅调制
# ============================================================
def fig_06_am_modulation():
    fs = 2000
    t = np.linspace(0, 2, fs*2)
    # carrier: audio signal
    carrier = np.sin(2*np.pi*10*t)
    # envelope: raised cosine fade out
    N = len(t)
    fade_N = int(N * 0.7)
    envelope = np.ones(N)
    fade_curve = 0.5 * (1 + np.cos(np.pi * np.arange(fade_N) / fade_N))
    envelope[:fade_N] = fade_curve
    envelope[fade_N:] = 0
    output = carrier * envelope

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 7), sharex=True)

    ax1.plot(t, carrier, 'b-', linewidth=1)
    ax1.set_ylabel('x(t)')
    ax1.set_title(ch('载波 x(t)：音频信号', 'Carrier x(t): Audio Signal'))
    ax1.set_ylim(-1.3, 1.3)
    ax1.grid(True, alpha=0.3)

    ax2.fill_between(t, envelope, alpha=0.3, color='green')
    ax2.plot(t, envelope, 'g-', linewidth=2.5, label=ch('包络 f(t)：淡出曲线', 'Envelope f(t): Fade Curve'))
    ax2.set_ylabel('f(t)')
    ax2.set_title(ch('调制信号（包络）f(t)：音量旋钮', 'Modulating Signal (Envelope) f(t)'))
    ax2.set_ylim(-0.1, 1.3)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    ax3.plot(t, output, 'purple', linewidth=1)
    ax3.set_ylabel('y(t)')
    ax3.set_title(ch('输出 y(t) = x(t) × f(t) ：淡出后的音频', 'Output y(t) = x(t) × f(t)'))
    ax3.set_ylim(-1.3, 1.3)
    ax3.set_xlabel('t (seconds)')
    ax3.grid(True, alpha=0.3)

    ax3.text(0.02, 0.95, ch('y(t) 的包络正是淡出曲线', 'y(t) envelope = fade curve'),
            transform=ax3.transAxes, fontsize=10, va='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow'))

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_06_am_modulation.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_06_am_modulation")

# ============================================================
# fig 07: 窗函数频响对比
# ============================================================
def fig_07_window_freq_response():
    N = 256
    n = np.arange(N)
    rect = np.ones(N)
    triang = 1 - np.abs(2*n/N - 1)
    hann = 0.5 * (1 - np.cos(2*np.pi*n/N))

    def freq_resp_log(win, title, ax):
        W = np.fft.fft(win, 4096)
        W = np.fft.fftshift(W)
        freq = np.linspace(-0.5, 0.5, len(W))
        mag_db = 20 * np.log10(np.maximum(np.abs(W), 1e-10) / np.sum(win))
        ax.plot(freq, mag_db, linewidth=1.5)
        ax.set_xlim(0, 0.5)
        ax.set_ylim(-120, 10)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel(ch('归一化频率', 'Normalized Frequency'))
        ax.set_ylabel('dB')
        ax.set_title(title, fontsize=10)
        ax.axhline(-13, color='red', linestyle=':', alpha=0.5, label=ch('主瓣宽度', 'Main lobe ref'))
        # find peak sidelobe
        mid = len(W) // 2
        sidelobe = np.max(mag_db[mid+50:])
        ax.text(0.98, 0.05, f'PSL={sidelobe:.1f} dB', transform=ax.transAxes,
                fontsize=9, ha='right', va='bottom',
                bbox=dict(boxstyle='round', facecolor='lightyellow'))

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    freq_resp_log(rect, ch('矩形窗（一刀切）', 'Rectangular Window'), axes[0])
    axes[0].text(0.1, -25, ch('旁瓣高 → "啪"明显', 'High sidelobes → audible click'),
                fontsize=8, color='darkred')

    freq_resp_log(triang, ch('三角窗（线性淡出）', 'Triangular Window'), axes[1])
    axes[1].text(0.1, -40, ch('旁瓣降低', 'Sidelobes reduced'),
                fontsize=8, color='darkgreen')

    freq_resp_log(hann, ch('升余弦窗（汉宁窗）', 'Raised Cosine / Hann Window'), axes[2])
    axes[2].text(0.1, -60, ch('旁瓣最低 → 最平滑！', 'Lowest sidelobes = smoothest!'),
                fontsize=8, color='darkgreen')

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_07_window_freq_response.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_07_window_freq_response")

# ============================================================
# fig 08: Q15 定点数
# ============================================================
def fig_08_q15_number_line():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))

    # Subplot 1: Q15 数轴
    ax1.set_xlim(-1.15, 1.15)
    ax1.set_ylim(-0.3, 1.3)
    ax1.axhline(0, color='black', linewidth=1.5)
    ax1.set_title(ch('Q15 定点数格式：1 位符号 + 15 位小数 = 16 位', 'Q15 Fixed-Point: 1 sign + 15 fractional = 16-bit'),
                 fontsize=11)
    ax1.set_yticks([])
    ax1.set_xlabel(ch('实际值 = 整数值 / 32768', 'Real Value = Integer / 32768'))

    # Markers
    markers = [
        (-1.0, '-1.0', '0x8000', 'red'),
        (-0.5, '-0.5', '0xC000', 'orange'),
        (0, '0', '0x0000', 'black'),
        (0.5, '0.5', '0x4000', 'orange'),
        (0.99997, '~1.0', '0x7FFF', 'red'),
    ]
    for pos, label, hexval, color in markers:
        ax1.plot(pos, 0, 'v', color=color, markersize=12, zorder=5)
        ax1.text(pos, -0.12, f'{label}', ha='center', fontsize=9, color=color, fontweight='bold')
        ax1.text(pos, 0.08, f'({hexval})', ha='center', fontsize=8, color=color)

    ax1.text(0.02, 0.95, ch('整数值范围: -32768 ~ 32767', 'Integer range: -32768 ~ 32767'),
            transform=ax1.transAxes, fontsize=8, va='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow'))

    # Subplot 2: Q15 乘法示例
    ax2.axis('off')
    examples = [
        ('0.5 × 0.5', '16384 × 16384', '(16384 × 16384 + 16384) >> 15', '0.25 (8192)'),
        ('1.0 × 0.5', '32767 × 16384', '(32767 × 16384 + 16384) >> 15', '~0.5 (16384)'),
        ('0.5 × -0.5', '16384 × -16384', '(16384 × -16384 + 16384) >> 15', '-0.25 (-8192)'),
    ]
    table_data = [[ch(a, a), ch(b, b), ch(c, c), ch(d, d)]
                  for a, b, c, d in examples]
    col_labels = [ch('实际乘法', 'Real Mult'), ch('Q15 整数', 'Q15 Ints'),
                  ch('运算', 'Operation'), ch('结果', 'Result')]

    table = ax2.table(cellText=table_data, colLabels=col_labels,
                      loc='center', cellLoc='center', colWidths=[0.12, 0.16, 0.45, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    ax2.set_title(ch('Q15 乘法示例', 'Q15 Multiplication Examples'), fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_08_q15_number_line.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_08_q15_number_line")

# ============================================================
# fig 09: 查表与插值
# ============================================================
def fig_09_lookup_table():
    # Generate cos table (257 entries, 0 to PI)
    N_table = 257
    table_angle = np.linspace(0, np.pi, N_table)
    cos_table = np.cos(table_angle)

    # 4x zoom of interpolation
    fine = np.linspace(0, np.pi, 1000)
    cos_fine = np.cos(fine)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    ax1.plot(fine, cos_fine, 'b-', linewidth=1.5, alpha=0.7, label=ch('真实的 cos 曲线', 'True cos curve'))
    ax1.plot(table_angle, cos_table, 'ro', markersize=3, label=ch('查表点 (257个)', 'Table entries (257 pts)'))
    ax1.set_title(ch('余弦查表：存储关键点', 'Cosine Lookup Table: Store Key Points'))
    ax1.set_xlabel(ch('角度 (弧度)', 'Angle (radians)'))
    ax1.set_ylabel(ch('cos 值', 'cos value'))
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, np.pi)

    # Zoom in to show interpolation
    zoom_start = 1.0
    zoom_end = 1.2
    ax2.set_xlim(zoom_start, zoom_end)
    ax2.set_ylim(np.cos(zoom_end)-0.05, np.cos(zoom_start)+0.05)

    idx_start = int(zoom_start / np.pi * N_table)
    idx_end = int(zoom_end / np.pi * N_table) + 2

    fine_zoom = np.linspace(zoom_start, zoom_end, 500)
    cos_fine_zoom = np.cos(fine_zoom)

    ax2.plot(fine_zoom, cos_fine_zoom, 'b-', linewidth=1.5, alpha=0.4,
             label=ch('真实值', 'True value'))

    table_zoom = table_angle[idx_start:idx_end]
    cos_table_zoom = cos_table[idx_start:idx_end]
    ax2.plot(table_zoom, cos_table_zoom, 'ro', markersize=8, zorder=5,
             label=ch('查表点', 'Table points'))

    # Draw linear interpolation between two adjacent points
    mid = len(table_zoom) // 2 - 1
    if mid >= 0 and mid+1 < len(table_zoom):
        x0, x1 = table_zoom[mid], table_zoom[mid+1]
        y0, y1 = cos_table_zoom[mid], cos_table_zoom[mid+1]
        interp_x = np.linspace(x0, x1, 20)
        interp_y = y0 + (interp_x - x0) * (y1 - y0) / (x1 - x0)
        ax2.plot(interp_x, interp_y, 'g--', linewidth=2, label=ch('线性插值', 'Linear Interpolation'))

        # error area
        true_interp = np.cos(interp_x)
        ax2.fill_between(interp_x, interp_y, true_interp, alpha=0.2, color='red',
                         label=ch('插值误差', 'Interpolation Error'))

        ax2.annotate('', xy=(x0, y0), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='<->', color='green', lw=2))

        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2
        ax2.text(mid_x, mid_y + 0.015, ch('直线近似', 'Linear approx'),
                ha='center', fontsize=8, color='green', fontweight='bold')

    ax2.set_title(ch('插值细节：用直线"填补"表项之间的空隙', 'Detail: Linear interpolation between table entries'))
    ax2.set_xlabel(ch('角度 (弧度)', 'Angle (radians)'))
    ax2.set_ylabel('cos')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_09_lookup_table.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_09_lookup_table")

# ============================================================
# fig 10: 白噪声 - 处处不可导
# ============================================================
def fig_10_white_noise():
    np.random.seed(42)
    N = 1000
    t = np.arange(N)

    noise = np.random.randn(N)

    fig, axes = plt.subplots(3, 1, figsize=(12, 7))

    axes[0].plot(t[:N], noise[:N], 'b-', linewidth=0.8)
    axes[0].set_title(ch('白噪声：看似有规律的波形（实际完全随机）', 'White Noise: Looks structured, but is purely random'))
    axes[0].set_ylabel('x(t)')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xlim(0, N-1)

    # zoom 1: 10x
    z1_start = 200
    z1_end = 300
    axes[1].plot(t[z1_start:z1_end], noise[z1_start:z1_end], 'r-', linewidth=1.2)
    axes[1].set_title(ch('放大 10 倍：仍然锯齿状，没有平滑趋势', '10x Zoom: Still jagged, no smoothness'))
    axes[1].set_ylabel('x(t)')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim(z1_start, z1_end-1)

    # zoom 2: 100x
    z2_start = 240
    z2_end = 250
    axes[2].plot(t[z2_start:z2_end], noise[z2_start:z2_end], 'g-', linewidth=2)
    axes[2].set_title(ch('放大 100 倍：仍然无法找到"切线"——处处不可导！', '100x Zoom: Still no tangent possible — nowhere differentiable!'))
    axes[2].set_ylabel('x(t)')
    axes[2].set_xlabel('t (sample index)')
    axes[2].grid(True, alpha=0.3)
    axes[2].set_xlim(z2_start, z2_end-1)

    # Add annotations
    for i, (label, ypos) in enumerate([('选两个点', 0.88), ('画切线？', 0.82)]):
        if i == 0:
            axes[2].annotate(ch('任意取两点连线', 'Pick 2 nearby points'),
                            xy=(z2_start+3, noise[z2_start+3]),
                            xytext=(z2_start-1, 2.5),
                            arrowprops=dict(arrowstyle='->', color='darkred'), fontsize=8, color='darkred')
        else:
            axes[2].annotate(ch('换两个点，斜率完全不同', 'Pick 2 others, slope completely different'),
                            xy=(z2_start+7, noise[z2_start+7]),
                            xytext=(z2_start+4, 2.5),
                            arrowprops=dict(arrowstyle='->', color='purple'), fontsize=8, color='purple')

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_10_white_noise.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_10_white_noise")

# ============================================================
# fig 11: 升余弦频谱
# ============================================================
def fig_11_raised_cosine_spectrum():
    N = 512
    n = np.arange(N)

    rect = np.ones(N)
    hann = 0.5 * (1 - np.cos(2*np.pi*n/N))

    def spectrum(win, ax, color, label_text):
        W = np.fft.fft(win, 4096)
        W = np.fft.fftshift(W)
        freq = np.linspace(-0.5, 0.5, len(W))
        mag_db = 20 * np.log10(np.maximum(np.abs(W), 1e-10) / np.sum(win))
        ax.plot(freq, mag_db, color=color, linewidth=1.5, label=label_text)
        ax.set_xlim(0, 0.5)
        ax.set_ylim(-120, 10)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)
        ax.set_xlabel(ch('归一化频率', 'Normalized Frequency'))
        ax.set_ylabel('dB')

    fig, ax = plt.subplots(figsize=(10, 5))
    spectrum(rect, ax, 'red', ch('矩形窗（一刀切）', 'Rectangular (abrupt cut)'))
    spectrum(hann, ax, 'blue', ch('升余弦窗（汉宁）', 'Raised Cosine (Hann)'))

    ax.axhline(-13, color='red', linestyle=':', alpha=0.4)
    ax.axhline(-32, color='blue', linestyle=':', alpha=0.4)
    ax.text(0.02, -10, '-13 dB', fontsize=8, color='red')
    ax.text(0.02, -29, '-32 dB', fontsize=8, color='blue')

    ax.set_title(ch('矩形 vs 升余弦窗的频谱对比\n升余弦的旁瓣低 19 dB，因此"啪"声小得多',
                    'Spectrum Comparison: Rect vs Raised Cosine\n19 dB lower sidelobes = much less audible click'))

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_11_raised_cosine_spectrum.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_11_raised_cosine_spectrum")

# ============================================================
# fig 12: Cⁿ 连续性阶梯图
# ============================================================
def fig_12_cn_continuity():
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    params = [
        (ch('C⁰ 连续\n位置匹配，斜率可能跳\n→ 消除"啪"', 'C⁰ Continuous\nPosition matches\nSlope may jump'),
         'orange', [-1, 1], [0.5, -0.3]),
        (ch('C¹ 连续\n斜率和位置都匹配\n→ 消除"小啪"', 'C¹ Continuous\nPosition & slope match\nSmooth at boundaries'),
         'green', [1, 0], [2, 1]),
        (ch('C² 连续\n位置、斜率、曲率都匹配\n→ 极致平滑', 'C² Continuous\nPos, slope & curvature\nUltra smooth'),
         'purple', [2, 0], [2, 0.5]),
    ]

    for ax, (text, color, _, _) in zip(axes, params):
        ax.text(0.5, 0.5, text, ha='center', va='center', fontsize=12,
               transform=ax.transAxes,
               bbox=dict(boxstyle='round,pad=1', facecolor='lightyellow', edgecolor=color, linewidth=2))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

    # add arrow between boxes
    for i in range(2):
        axes[i].annotate('', xy=(1, 0.5), xytext=(0, 0.5),
                        xycoords=axes[i].transAxes, textcoords=axes[i+1].transAxes,
                        arrowprops=dict(arrowstyle='->', color='gray', lw=2))

    fig.suptitle(ch('连续性阶梯：C⁰ → C¹ → C²', 'Continuity Ladder: C⁰ → C¹ → C²'),
                fontsize=14, fontweight='bold', y=1.08)

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_12_cn_continuity.png', dpi=DPI, bbox_inches='tight')
    plt.close()
    print("  [OK] fig_12_cn_continuity")

# ============================================================
# fig 13: 信号处理四大基石
# ============================================================
def fig_13_foundations():
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))

    concepts = [
        (ch('基石一：时域与频域\n\n时域看波形\n频域看频率成分\n升余弦在两个域都优秀',
            'Foundation 1: Time & Frequency\n\nTime: waveform view\nFreq: spectrum view\nRaised cosine excels in both'),
         '#4ECDC4'),
        (ch('基石二：调制\n\n乘法 = 振幅调制(AM)\n时域相乘 = 频域卷积\n好的包络引入少量调制产物',
            'Foundation 2: Modulation\n\nMultiplication = AM\nTime multiply = Freq convolution\nGood envelope = few artifacts'),
         '#FF6B6B'),
        (ch('基石三：连续性\n\nC⁰: 值连续\nC¹: 斜率也连续\nC¹ 对人耳已经足够好',
            'Foundation 3: Continuity\n\nC⁰: value\nC¹: + slope\nC¹ is good enough for human ear'),
         '#45B7D1'),
        (ch('基石四：采样与量化\n\n连续 → 离散（ADC）\n浮点 → 定点（量化）\n查表 + 插值（工程近似）',
            'Foundation 4: Sampling & Quantization\n\nContinuous → Discrete (ADC)\nFloat → Fixed-point (Quant)\nLUT + Interpolation (Approx)'),
         '#F9CA24'),
    ]

    for ax, (text, color) in zip(axes.flat, concepts):
        ax.text(0.5, 0.5, text, ha='center', va='center', fontsize=11,
               transform=ax.transAxes,
               bbox=dict(boxstyle='round,pad=0.8', facecolor=color, alpha=0.2, edgecolor=color, linewidth=2))
        ax.axis('off')

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_13_foundations.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_13_foundations")

# ============================================================
# fig 14: 淡出/淡入效果的频谱瀑布图
# ============================================================
def fig_14_spectrogram_concept():
    t = np.linspace(0, 2, 2000)
    x = np.sin(2*np.pi*50*t) + 0.5*np.sin(2*np.pi*120*t) + 0.3*np.sin(2*np.pi*200*t)
    N = len(x)
    fade_N = 1000
    fade_curve = 0.5 * (1 + np.cos(np.pi * np.arange(fade_N) / fade_N))
    envelope = np.ones(N)
    envelope[:fade_N] = fade_curve
    envelope[N-fade_N:] = np.flip(fade_curve)
    y = x * envelope

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 5))

    ax1.plot(t, x, 'b-', alpha=0.4, label=ch('原始', 'Original'))
    ax1.plot(t, y, 'purple', linewidth=1.5, label=ch('淡入+淡出后', 'After fade in/out'))
    ax1.plot(t, envelope, 'g-', linewidth=2, label=ch('包络', 'Envelope'))
    ax1.set_title(ch('包含多个频率分量的信号淡入淡出', 'Fade In/Out on Multi-tone Signal'))
    ax1.set_ylabel(ch('幅值', 'Amplitude'))
    ax1.legend(fontsize=8)
    ax1.set_xlim(0, 2)
    ax1.grid(True, alpha=0.3)

    # simplistic spectrogram representation
    ax2.specgram(y, NFFT=256, Fs=2000, noverlap=200,
                 cmap='plasma', vmin=-40, vmax=0)
    ax2.set_title(ch('频谱图：淡入和淡出可见的幅度渐变', 'Spectrogram: Gradual amplitude change visible'))
    ax2.set_xlabel('t (seconds)')
    ax2.set_ylabel(ch('频率 (Hz)', 'Frequency (Hz)'))
    ax2.set_ylim(0, 500)

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_14_spectrogram_concept.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_14_spectrogram_concept")

# ============================================================
# fig 15: 实际算法流程图
# ============================================================
def fig_15_algorithm_flow():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.axis('off')

    boxes = [
        (0.5, 0.92, ch('开始 cos_fade_out/in\n输入：pcm_buf, num_channels, bit_width, fade_points',
                       'Start cos_fade_out/in\nInput: pcm_buf, ch, bit_width, fade_points'), '#3498db'),
        (0.5, 0.78, ch('fade_points == 0?', 'fade_points == 0?'), '#f39c12'),
        (0.5, 0.64, ch('对每个采样点 i (0 ~ fade_points-1)',
                       'For each sample i (0 ~ fade_points-1)'), '#2ecc71'),
        (0.5, 0.50, ch('计算 x_q15 = (i × 32767) / (N-1)\ncos_val = cos_lookup(x_q15)\nfade_mult = (32767 ± cos_val + 1) >> 1',
                       'x_q15 = (i × 32767) / (N-1)\ncos_val = cos_lookup(x_q15)\nfade_mult = (32767 ± cos_val + 1) >> 1'), '#e74c3c'),
        (0.5, 0.34, ch('对每个通道 ch (0 ~ num_channels-1):\nsample_idx = i × num_channels + ch\npcm[sample_idx] = Q15/Q31_MUL(orig, mult)',
                       'For each ch (0 ~ num_channels-1):\nidx = i × channels + ch\npcm[idx] = Q15/Q31_MUL(orig, mult)'), '#9b59b6'),
        (0.5, 0.18, ch('所有采样点处理完毕，返回',
                       'All samples processed, return'), '#2ecc71'),
    ]

    for x, y, text, color in boxes:
        ax.text(x, y, text, ha='center', va='center', fontsize=9,
               transform=ax.transAxes,
               bbox=dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5))

    # arrows
    ax.annotate('', xy=(0.5, 0.86), xytext=(0.5, 0.78),
               arrowprops=dict(arrowstyle='->', color='gray', lw=1.5), transform=ax.transAxes)
    ax.annotate(ch('是→各通道置0并返回', 'Yes→zero ch, return'),
               xy=(0.5, 0.78), xytext=(0.78, 0.78),
               arrowprops=dict(arrowstyle='->', color='red', lw=1), fontsize=7, color='red',
               transform=ax.transAxes)
    ax.annotate(ch('否→继续', 'No→continue'),
               xy=(0.62, 0.78), xytext=(0.5, 0.72),
               arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=7, color='green',
               transform=ax.transAxes)
    ax.annotate('', xy=(0.5, 0.72), xytext=(0.5, 0.64),
               arrowprops=dict(arrowstyle='->', color='gray', lw=1.5), transform=ax.transAxes)
    ax.annotate('', xy=(0.5, 0.58), xytext=(0.5, 0.50),
               arrowprops=dict(arrowstyle='->', color='gray', lw=1.5), transform=ax.transAxes)
    ax.annotate('', xy=(0.5, 0.44), xytext=(0.5, 0.34),
               arrowprops=dict(arrowstyle='->', color='gray', lw=1.5), transform=ax.transAxes)
    ax.annotate('', xy=(0.5, 0.28), xytext=(0.5, 0.18),
               arrowprops=dict(arrowstyle='->', color='gray', lw=1.5), transform=ax.transAxes)

    ax.set_title(ch('算法流程图', 'Algorithm Flow Chart'), fontsize=13, fontweight='bold', pad=10)

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_15_algorithm_flow.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_15_algorithm_flow")

# ============================================================
# fig 17: 卷积可视化
# ============================================================
def fig_17_convolution_visual():
    N = 512
    freq = np.linspace(-0.5, 0.5, N)

    # Window spectrum (Hann)
    n = np.arange(256)
    hann = 0.5 * (1 - np.cos(2 * np.pi * n / 256))
    H = np.fft.fft(hann, N)
    H = np.fft.fftshift(H)
    H_dB = 20 * np.log10(np.maximum(np.abs(H), 1e-10) / np.sum(hann))

    # Original spectrum: three discrete tones
    X = np.zeros(N, dtype=float)
    X[N // 2 + int(-0.2 * N)], X[N // 2], X[N // 2 + int(0.25 * N)] = 1.0, 0.8, 0.6
    X_dB = 20 * np.log10(np.maximum(X, 1e-10))

    # Convolution: Y = X * H
    from numpy import convolve
    Y = convolve(X, np.abs(H) / np.max(np.abs(H)), mode='same')
    Y_dB = 20 * np.log10(np.maximum(Y, 1e-10))

    fig, axes = plt.subplots(3, 1, figsize=(12, 7))

    axes[0].plot(freq, H_dB, 'g-', linewidth=1.5)
    axes[0].set_ylim(-80, 10)
    axes[0].set_xlim(-0.5, 0.5)
    axes[0].set_ylabel('dB')
    axes[0].set_title(ch('窗口频谱 F(ω)——低旁瓣', 'Window Spectrum F(ω) — Low Sidelobes'))
    axes[0].grid(True, alpha=0.3)
    axes[0].axhline(-32, color='green', linestyle=':', alpha=0.5)
    axes[0].text(0.35, -30, '-32 dB', fontsize=8, color='green')

    axes[1].stem(freq, X_dB, linefmt='b-', markerfmt='bo', basefmt='gray')
    axes[1].set_ylim(-80, 10)
    axes[1].set_xlim(-0.5, 0.5)
    axes[1].set_ylabel('dB')
    axes[1].set_title(ch('原始信号频谱 X(ω)——三个离散频率分量', 'Original Spectrum X(ω) — Three Discrete Tones'))
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(freq, Y_dB, 'purple', linewidth=1.5)
    axes[2].set_ylim(-80, 10)
    axes[2].set_xlim(-0.5, 0.5)
    axes[2].set_ylabel('dB')
    axes[2].set_xlabel(ch('归一化频率', 'Normalized Frequency'))
    axes[2].set_title(ch('卷积结果 Y(ω) = X(ω) * F(ω)', 'Convolved Spectrum Y(ω) = X(ω) * F(ω)'))
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/fig_17_convolution_visual.png', dpi=DPI)
    plt.close()
    print("  [OK] fig_17_convolution_visual")


# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    print("Generating figures...")
    fig_01_sine_discontinuity()
    fig_02_derivative_tangent()
    fig_03_fade_compare()
    fig_04_raised_cosine_detail()
    fig_05_continuity_c0_c1()
    fig_06_am_modulation()
    fig_07_window_freq_response()
    fig_08_q15_number_line()
    fig_09_lookup_table()
    fig_10_white_noise()
    fig_11_raised_cosine_spectrum()
    fig_12_cn_continuity()
    fig_13_foundations()
    fig_14_spectrogram_concept()
    fig_15_algorithm_flow()
    fig_17_convolution_visual()
    print(f"\nAll figures generated in '{OUT_DIR}/'")
