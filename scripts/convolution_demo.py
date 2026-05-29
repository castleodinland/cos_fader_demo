#!/usr/bin/env python3
"""
信号卷积原理演示 — 面向初学者的交互式可视化教程

核心概念:
    时域相乘 ⇔ 频域卷积
    (加窗 = 时域乘窗函数 = 频域与窗谱卷积)

本脚本演示:
    1. 正弦波 × 升余弦窗 → 频谱从单根线变成带旁瓣的形状
    2. 时域卷积的逐步滑动过程（动画）
    3. 频域卷积如何产生旁瓣（动画）
    4. 最终加窗后的信号和频谱

用法: python convolution_demo.py
依赖: numpy, matplotlib
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import FancyBboxPatch
from numpy.fft import fft, fftshift, fftfreq

# 设置控制台 UTF-8 编码 (Windows 终端兼容)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 配置 matplotlib 中文字体
_font_candidates = ["Microsoft YaHei", "SimHei", "Noto Sans SC", "STXihei"]
_font_name = None
for _f in _font_candidates:
    if _f in {f.name for f in fm.fontManager.ttflist}:
        _font_name = _f
        break
if _font_name:
    plt.rcParams["font.sans-serif"] = [_font_name, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    # 清除字体缓存以确保生效
    fm._load_fontmanager(try_read_cache=False)
    print(f"[INFO] 使用中文字体: {_font_name}")
else:
    print("[WARN] 未找到中文字体，图表中文可能显示为方块")

# ── 全局参数 ────────────────────────────────────────────────
FS = 1000              # 采样率 (Hz) — 信号每秒钟采样点数
DURATION = 1.0         # 信号时长 (秒)
F_SINE = 50            # 正弦波频率 (Hz) — 一个 50 Hz 的纯音
N = int(FS * DURATION) # 总采样点数 = 1000
T = np.arange(N) / FS  # 时间轴: [0, 0.001, 0.002, ..., 0.999]

# 频率轴 (用于画频谱)
FREQ = fftshift(fftfreq(N, 1 / FS))  # [-500, -499, ..., 0, ..., 499] Hz
DF = FREQ[1] - FREQ[0]               # 频率分辨率 = 1 Hz

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 14,
    "figure.dpi": 100,
    "savefig.dpi": 150,
    "animation.html": "jshtml",
})


# ╔══════════════════════════════════════════════════════════╗
# ║  第 1 部分: 静态概览 — 建立直觉                          ║
# ╚══════════════════════════════════════════════════════════╝

def static_overview():
    """
    四张子图展示核心关系:

    [时域信号]          [频域幅度]
    正弦波  ──FFT──→   单根谱线 (δ-like)
    升余弦窗 ──FFT──→  主瓣 + 旁瓣
    加窗信号 ──FFT──→  主瓣 + 旁瓣 (窗频谱搬移到正弦频率处!)
    """
    # 信号
    sine = np.sin(2 * np.pi * F_SINE * T)
    window = 0.5 * (1 - np.cos(2 * np.pi * np.arange(N) / (N - 1)))  # Hann窗

    # 也可用 Hamming 窗形式
    window = np.hanning(N)

    windowed = sine * window

    # FFT
    def mag(x):
        """归一化幅度谱, dB"""
        s = np.abs(fftshift(fft(x)))
        s = s / s.max()
        return 20 * np.log10(np.clip(s, 1e-12, None))  # dB, 裁剪防止 log(0)

    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle("信号卷积核心关系: 时域相乘 <-> 频域卷积", fontsize=16, fontweight="bold")

    # ── 第1行: 原始正弦波 ──
    axes[0, 0].plot(T, sine, lw=1, color="#1f77b4")
    axes[0, 0].set_title(f"时域: {F_SINE} Hz 正弦波", fontweight="bold")
    axes[0, 0].set_xlabel("时间 (秒)")
    axes[0, 0].set_ylabel("幅度")
    axes[0, 0].set_xlim(0, 0.3)
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(FREQ, mag(sine), lw=1.2, color="#1f77b4")
    axes[0, 1].set_title("频域: 纯净「单根谱线」", fontweight="bold")
    axes[0, 1].set_xlabel("频率 (Hz)")
    axes[0, 1].set_ylabel("幅度 (dB)")
    axes[0, 1].set_xlim(-200, 200)
    axes[0, 1].set_ylim(-120, 5)
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].annotate("纯音没有旁瓣!", xy=(F_SINE, 0), xytext=(100, -20),
                        arrowprops=dict(arrowstyle="->", color="red"), color="red")

    # ── 第2行: 窗函数 ──
    axes[1, 0].plot(T, window, lw=1, color="#ff7f0e")
    axes[1, 0].set_title("时域: 升余弦窗 (Hann)", fontweight="bold")
    axes[1, 0].set_xlabel("时间 (秒)")
    axes[1, 0].set_ylabel("幅度")
    axes[1, 0].set_xlim(0, 0.3)
    axes[1, 0].set_ylim(0, 1.1)
    axes[1, 0].grid(True, alpha=0.3)

    ax_winf = axes[1, 1]
    ax_winf.plot(FREQ, mag(window), lw=1.2, color="#ff7f0e")
    ax_winf.set_title("频域: 窗频谱 = 主瓣 + 旁瓣", fontweight="bold")
    ax_winf.set_xlabel("频率 (Hz)")
    ax_winf.set_ylabel("幅度 (dB)")
    ax_winf.set_xlim(-200, 200)
    ax_winf.set_ylim(-120, 5)
    ax_winf.grid(True, alpha=0.3)
    # 标注主瓣和旁瓣
    ax_winf.annotate("主瓣", xy=(0, 0), xytext=(3, -15),
                     arrowprops=dict(arrowstyle="->"), fontsize=10, color="green")
    ax_winf.annotate("旁瓣", xy=(10, -35), xytext=(30, -40),
                     arrowprops=dict(arrowstyle="->"), fontsize=10, color="red")
    ax_winf.annotate("旁瓣", xy=(20, -50), xytext=(50, -55),
                     arrowprops=dict(arrowstyle="->"), fontsize=10, color="red")

    # ── 第3行: 加窗信号 ──
    axes[2, 0].plot(T, windowed, lw=1, color="#2ca02c")
    axes[2, 0].set_title("时域: 正弦波 × 窗", fontweight="bold")
    axes[2, 0].set_xlabel("时间 (秒)")
    axes[2, 0].set_ylabel("幅度")
    axes[2, 0].set_xlim(0, 0.3)
    axes[2, 0].grid(True, alpha=0.3)

    ax_winr = axes[2, 1]
    ax_winr.plot(FREQ, mag(windowed), lw=1.2, color="#2ca02c")
    ax_winr.set_title("频域: 窗谱搬移到正弦频率处!", fontweight="bold")
    ax_winr.set_xlabel("频率 (Hz)")
    ax_winr.set_ylabel("幅度 (dB)")
    ax_winr.set_xlim(-200, 200)
    ax_winr.set_ylim(-120, 5)
    ax_winr.grid(True, alpha=0.3)
    ax_winr.annotate("主瓣(在正弦频率处)", xy=(F_SINE, 0), xytext=(100, -15),
                     arrowprops=dict(arrowstyle="->"), fontsize=10, color="green")
    ax_winr.annotate("旁瓣!", xy=(F_SINE + 15, -35), xytext=(F_SINE + 50, -45),
                     arrowprops=dict(arrowstyle="->"), fontsize=10, color="red")
    ax_winr.annotate("旁瓣!", xy=(F_SINE - 15, -35), xytext=(F_SINE - 100, -45),
                     arrowprops=dict(arrowstyle="->"), fontsize=10, color="red")

    plt.tight_layout()
    plt.savefig("01_static_overview.png", bbox_inches="tight")
    print("[OK] 静态概览已保存: 01_static_overview.png")
    plt.close()


# ╔══════════════════════════════════════════════════════════╗
# ║  第 2 部分: 时域卷积动画 — 滑动求积分                      ║
# ╚══════════════════════════════════════════════════════════╝

def time_convolution_animation():
    """
    演示时域卷积的逐步过程:

    卷积定义: (f * g)(t) = ∫ f(τ) g(t - τ) dτ

    视觉化: 将窗函数从左边滑到右边，每一帧:
      - 上方: f(τ) 和反转的 g(t - τ)（即窗的翻转滑动版）
      - 下方: 当前计算出的卷积值

    但我这里改成演示"加窗"过程更直观:
    将窗函数从左向右移动，每一步截取一段正弦波，展示"窗滑过去"的效果。
    每个位置计算的是窗与正弦波重叠部分的乘积积分。
    """
    # 使用较短信号以便看清滑动过程
    dur = 0.3
    n_pts = int(FS * dur)
    t_short = np.arange(n_pts) / FS
    sine = np.sin(2 * np.pi * F_SINE * t_short)

    # 窗函数 (宽度 = 信号的 1/5)
    win_width = n_pts // 5
    window = np.hanning(win_width)

    # 卷积结果长度
    conv_len = n_pts + win_width - 1
    conv_result = np.convolve(sine, window, mode="full")

    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(12, 7))
    fig.suptitle("时域卷积: 窗函数滑过正弦波", fontsize=15, fontweight="bold")

    # 固定显示范围
    ax_top.set_xlim(-0.01, dur + 0.05)
    ax_top.set_ylim(-1.5, 1.5)
    ax_top.set_ylabel("幅度")
    ax_top.grid(True, alpha=0.3)

    ax_bottom.set_xlim(-0.01, dur + 0.05)
    ax_bottom.set_ylim(-3, 3)
    ax_bottom.set_xlabel("时间 (秒)")
    ax_bottom.set_ylabel("卷积值")
    ax_bottom.grid(True, alpha=0.3)

    # 静态元素
    sine_line, = ax_top.plot(t_short, sine, lw=1.5, color="#1f77b4", label="正弦波")
    win_patch = ax_top.fill_between([], [], alpha=0.4, color="#ff7f0e", label="窗(当前位置)")
    ax_top.legend(loc="upper right")

    conv_line, = ax_bottom.plot([], [], lw=1.5, color="#d62728")
    dot, = ax_bottom.plot([], [], "ro", ms=8)
    t_conv_axis = np.arange(conv_len) / FS

    def init():
        win_patch.remove()
        # Will be re-created in animate since fill_between objects are harder to update
        return sine_line, conv_line, dot

    # 预计算窗的每个滑动位置
    step = max(1, n_pts // 80)  # 约80帧

    # 用面向对象方式每帧重建 fill_between
    def animate(frame):
        print(f"\r  渲染时域动画: {frame + 1}/{n_pts // step + 1}", end="", flush=True)
        shift = frame * step

        # 窗的当前位置
        win_start = shift / FS
        win_end = (shift + win_width) / FS
        win_t = np.linspace(win_start, win_end, win_width)
        win_vals = window

        ax_top.clear()
        ax_top.set_xlim(-0.01, dur + 0.05)
        ax_top.set_ylim(-1.5, 1.5)
        ax_top.set_ylabel("幅度")
        ax_top.grid(True, alpha=0.3)
        ax_top.plot(t_short, sine, lw=1.5, color="#1f77b4", label="正弦波")
        ax_top.fill_between(win_t, win_vals, alpha=0.4, color="#ff7f0e", label="窗(滑动中)")
        ax_top.set_title(f"时域卷积: 窗从左侧滑过信号", fontweight="bold")
        ax_top.legend(loc="upper right", fontsize=9)

        # 卷积结果
        end_idx = min(shift + win_width, conv_len)
        ax_bottom.clear()
        ax_bottom.set_xlim(-0.01, dur + 0.05)
        ax_bottom.set_ylim(-3, 3)
        ax_bottom.set_xlabel("时间 (秒)")
        ax_bottom.set_ylabel("卷积值")
        ax_bottom.grid(True, alpha=0.3)
        ax_bottom.plot(t_conv_axis[:end_idx], conv_result[:end_idx],
                       lw=1.5, color="#d62728")
        ax_bottom.set_title(f"累计卷积结果 (当前点: t={win_start:.3f}s)",
                            fontweight="bold")
        # 标记当前计算点
        cur_t = (shift) / FS  # 卷积输出的对应时间
        cur_val = conv_result[shift] if shift < conv_len else conv_result[-1]
        ax_bottom.plot(cur_t, cur_val, "ro", ms=8)

        return []

    n_frames = n_pts // step + 1
    anim = FuncAnimation(fig, animate, frames=range(n_frames),
                         init_func=init, blit=False, interval=30)

    writer = PillowWriter(fps=15)
    anim.save("02_time_convolution.gif", writer=writer)
    print()
    print("[OK] 时域卷积动画已保存: 02_time_convolution.gif")
    plt.close()


# ╔══════════════════════════════════════════════════════════╗
# ║  第 3 部分: 频域卷积动画 — 旁瓣如何产生                    ║
# ╚══════════════════════════════════════════════════════════╝

def freq_convolution_animation():
    """
    核心演示: 频域卷积如何产生旁瓣。

    思路:
      - 正弦波的频谱 ≈ δ(F - F_sine) + δ(F + F_sine)  (两根谱线)
      - 窗函数的频谱 = 中心在 0 Hz 的主瓣 + 一系列旁瓣
      - 卷积: 把窗频谱中心"搬"到每个 δ 的位置，叠加

    动画: 让窗频谱从左侧滑向右侧，滑过正弦波的两根谱线。
    当窗的主瓣与正弦谱线对齐时 → 形成加窗信号的谱峰（主瓣）
    窗的旁瓣也随之一同搬移 → 形成加窗信号的旁瓣
    """
    sine = np.sin(2 * np.pi * F_SINE * T)
    window = np.hanning(N)

    # 频谱 (线性幅度，便于显示卷积原理)
    spec_sine = fftshift(np.abs(fft(sine)))
    spec_sine = spec_sine / spec_sine.max()  # 归一化
    spec_win = fftshift(np.abs(fft(window)))
    spec_win = spec_win / spec_win.max()

    # 加窗信号的频谱 (目标)
    spec_windowed = fftshift(np.abs(fft(sine * window)))
    spec_windowed = spec_windowed / spec_windowed.max()

    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(12, 7))
    fig.suptitle("频域卷积: 窗频谱滑过正弦谱线 → 旁瓣诞生", fontsize=15, fontweight="bold")

    # 上方: 正弦频谱 (静态) + 窗频谱 (滑动)
    ax_top.set_xlim(-200, 200)
    ax_top.set_ylim(-0.1, 1.2)
    ax_top.set_ylabel("幅度")
    ax_top.grid(True, alpha=0.3)

    # 下方: 累计卷积结果
    ax_bottom.set_xlim(-200, 200)
    ax_bottom.set_ylim(-0.1, 1.2)
    ax_bottom.set_xlabel("频率 (Hz)")
    ax_bottom.set_ylabel("幅度")
    ax_bottom.grid(True, alpha=0.3)

    # 正弦的谱线位置 (正频率)
    sine_peak_idx = np.argmax(spec_sine)  # 在 fftshift 后的索引
    sine_peak_freq = FREQ[sine_peak_idx]

    def animate(frame):
        print(f"\r  渲染频域动画: {frame + 1}/200", end="", flush=True)

        # 窗频谱的偏移量: 从 -150 Hz 滑到 +150 Hz
        shift = (frame / 199) * 300 - 150  # -150 to 150

        # 将窗频谱搬移到 shift 位置
        shift_idx = int(shift / DF)
        spec_win_shifted = np.roll(spec_win, shift_idx)
        # 幅度缩放 (模拟卷积)
        scale = np.exp(-(shift - sine_peak_freq) ** 2 / (2 * 15 ** 2))  # 高斯加权

        # 上方画布
        ax_top.clear()
        ax_top.set_xlim(-200, 200)
        ax_top.set_ylim(-0.1, 1.2)
        ax_top.set_ylabel("幅度")
        ax_top.grid(True, alpha=0.3)

        # 正弦谱线
        markerline, stemlines, baseline = ax_top.stem(
            FREQ, spec_sine, linefmt="#1f77b4", markerfmt="^",
            basefmt=" ", label="正弦波频谱 (δ-like)"
        )
        # 加大 marker
        markerline.set_markersize(6)

        # 滑动的窗频谱
        ax_top.plot(FREQ, spec_win_shifted, lw=1.5, color="#ff7f0e",
                    label=f"窗频谱 (偏移={shift:.0f} Hz)")
        ax_top.set_title(
            f"窗频谱中心在 {shift:.0f} Hz — 当主瓣碰到正弦谱线时,"
            f" 旁瓣也随之「印」在谱线上!",
            fontweight="bold"
        )
        ax_top.legend(loc="upper right", fontsize=9)

        # 动画辅助线
        ax_top.axvline(x=shift, color="orange", ls="--", alpha=0.5)

        # 下方: 累积卷积效果 — 用实际的加窗信号谱来展示"目标"
        # 随着窗接近正弦频率, 逐步揭示加窗后的频谱
        reveal = np.exp(-(shift - sine_peak_freq) ** 2 / (2 * 10 ** 2))
        ax_bottom.clear()
        ax_bottom.set_xlim(-200, 200)
        ax_bottom.set_ylim(-0.1, 1.2)
        ax_bottom.set_xlabel("频率 (Hz)")
        ax_bottom.set_ylabel("幅度")
        ax_bottom.grid(True, alpha=0.3)

        ax_bottom.plot(FREQ, spec_windowed * reveal, lw=1.5, color="#2ca02c",
                       label="卷积结果 (逐步显现)")
        ax_bottom.plot(FREQ, spec_windowed, lw=0.8, color="#2ca02c",
                       alpha=0.15, label="最终目标")
        ax_bottom.set_title("频域卷积的结果: 主瓣 + 旁瓣 (整体呈现)", fontweight="bold")
        ax_bottom.legend(loc="upper right", fontsize=9)

        # 标注主瓣和旁瓣位置
        if reveal > 0.3:
            ax_bottom.annotate("主瓣", xy=(F_SINE, 1.0), xytext=(F_SINE + 30, 1.05),
                               arrowprops=dict(arrowstyle="->", color="green"),
                               color="green", fontweight="bold")
            for side_lobe_freq in [F_SINE - 15, F_SINE + 15]:
                ax_bottom.annotate("旁瓣", xy=(side_lobe_freq, 0.1),
                                   xytext=(side_lobe_freq + 25, 0.2),
                                   arrowprops=dict(arrowstyle="->", color="red"),
                                   color="red", fontsize=9)

        return []

    anim = FuncAnimation(fig, animate, frames=200, blit=False, interval=25)
    writer = PillowWriter(fps=20)
    anim.save("03_freq_convolution.gif", writer=writer)
    print()
    print("[OK] 频域卷积动画已保存: 03_freq_convolution.gif")
    plt.close()


# ╔══════════════════════════════════════════════════════════╗
# ║  第 4 部分: 旁瓣生成详解 — 动画拼接                        ║
# ╚══════════════════════════════════════════════════════════╝

def sidelobe_explanation():
    """
    多帧动画展示"旁瓣就是窗频谱被卷积到正弦频率处"的直观解释。

    每一帧:
      [左边]               [右边]
      窗频谱(线性幅度)      正弦频谱(δ-like)
         ↓ 卷积              ↓
      结果频谱 = 把窗频谱"贴"到每个 δ 位置后相加
    """
    window = np.hanning(N)
    spec_win_linear = fftshift(np.abs(fft(window)))
    spec_win_linear = spec_win_linear / spec_win_linear.max()

    # 将窗频谱中心对齐到 0 Hz
    # 正弦谱线在 +F_SINE 和 -F_SINE

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("旁瓣是如何产生的? — 逐步演示", fontsize=16, fontweight="bold")

    def animate(frame):
        for ax in axes:
            ax.clear()

        step = frame  # 0..99

        # ── 左: 窗频谱 ──
        axes[0].plot(FREQ, spec_win_linear, lw=1.5, color="#ff7f0e")
        axes[0].set_xlim(-150, 150)
        axes[0].set_ylim(-0.05, 1.1)
        axes[0].set_xlabel("频率 (Hz)")
        axes[0].set_ylabel("幅度")
        axes[0].set_title("① 窗函数频谱\n(主瓣 + 旁瓣)", fontweight="bold")
        axes[0].grid(True, alpha=0.3)

        # 高亮主瓣和旁瓣
        axes[0].axvline(x=0, color="green", ls="--", alpha=0.6, label="主瓣中心")
        axes[0].legend(fontsize=8, loc="upper right")

        # ── 中: 正弦频谱 (δ) ──
        # 用 stem 显示
        sine_spec_vis = np.zeros_like(FREQ)
        pos_idx = np.argmin(np.abs(FREQ - F_SINE))
        neg_idx = np.argmin(np.abs(FREQ + F_SINE))
        sine_spec_vis[pos_idx] = 1.0
        sine_spec_vis[neg_idx] = 1.0

        markerline, stemlines, baseline = axes[1].stem(
            FREQ, sine_spec_vis,
            linefmt="#1f77b4", markerfmt="^", basefmt=" "
        )
        markerline.set_markersize(8)
        axes[1].set_xlim(-150, 150)
        axes[1].set_ylim(-0.05, 1.1)
        axes[1].set_xlabel("频率 (Hz)")
        axes[1].set_title("② 正弦波频谱\n(两根 δ 谱线)", fontweight="bold")
        axes[1].grid(True, alpha=0.3)

        # ── 右: 卷积过程 ──
        # 显示两个"窗频谱副本"叠加: 一个在 +50Hz, 一个在 -50Hz
        # 随动画推进, 逐步展示旁瓣的形成

        # 将窗谱搬移到 ±F_SINE
        shift_idx = int(F_SINE / DF)
        win_at_positive = np.roll(spec_win_linear, shift_idx)
        win_at_negative = np.roll(spec_win_linear, -shift_idx)

        # 逐步显现
        reveal = min(1.0, step / 60)  # 0→1 over 60 frames

        combined = (win_at_positive + win_at_negative) * reveal
        combined = combined / max(combined.max(), 1e-12)

        axes[2].plot(FREQ, combined, lw=1.5, color="#2ca02c",
                     label="窗谱的叠加(=卷积)")
        axes[2].set_xlim(-150, 150)
        axes[2].set_ylim(-0.05, 1.1)
        axes[2].set_xlabel("频率 (Hz)")
        axes[2].set_title(
            f"③ 卷积 = 把①搬到②的位置后叠加\n"
            f"主瓣(绿虚线)旁瓣(红虚线)→ 这就是'旁瓣'的来源!",
            fontweight="bold", fontsize=10
        )
        axes[2].grid(True, alpha=0.3)

        # 标注
        if reveal > 0.3:
            for f0, color in [(F_SINE, "green"), (-F_SINE, "green")]:
                axes[2].axvline(x=f0, color=color, ls="--", alpha=0.5)
            for offset in [12, 18, 25]:
                for sign in [1, -1]:
                    axes[2].axvline(x=F_SINE + sign * offset, color="red",
                                    ls=":", alpha=0.3)
                    axes[2].axvline(x=-F_SINE + sign * offset, color="red",
                                    ls=":", alpha=0.3)
        axes[2].legend(fontsize=8, loc="upper right")

        return []

    anim = FuncAnimation(fig, animate, frames=100, blit=False, interval=40)
    writer = PillowWriter(fps=12)
    anim.save("04_sidelobe_explanation.gif", writer=writer)
    print("[OK] 旁瓣解释动画已保存: 04_sidelobe_explanation.gif")
    plt.close()


# ╔══════════════════════════════════════════════════════════╗
# ║  第 5 部分: 验证 — 时域卷积 vs 频域相乘, 时域相乘 vs 频域卷积 ║
# ╚══════════════════════════════════════════════════════════╝

def verification_plot():
    """
    验证两个对偶关系:

    (A) 时域卷积 ⇔ 频域相乘
        - 对信号和窗做时域卷积
        - 验证其频谱 = 信号频谱 × 窗频谱

    (B) 时域相乘 ⇔ 频域卷积  (本教程的重点)
        - 信号 × 窗 = 加窗信号
        - 验证加窗信号的频谱 = 信号频谱 *窗频谱 (卷积)
    """
    sine = np.sin(2 * np.pi * F_SINE * T)
    window = np.hanning(N)

    # 直接加窗
    windowed_direct = sine * window

    # 用频域卷积实现: spec(sine) *spec(window)
    spec_sine = fft(sine)
    spec_win = fft(window)
    # FFT 卷积: 时域相乘 = 频域循环卷积 / N
    spec_conv = np.convolve(spec_sine, spec_win, mode="same") / N
    windowed_via_freq_conv = np.fft.ifft(spec_conv).real

    # 反过来: 时域卷积 → DFT → 应该等于频域相乘
    time_conved = np.convolve(sine, window, mode="same")
    spec_time_conved = fft(time_conved)
    spec_product = (spec_sine * spec_win) / N

    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    fig.suptitle("验证对偶性: 时域 <-> 频域的卷积/相乘关系", fontsize=15, fontweight="bold")

    # 上左: 验证 (A) 时域卷积 → 频域相乘
    axes[0, 0].plot(T[:200], time_conved[:200], lw=1.2, color="purple",
                    label="时域卷积: sine *window")
    axes[0, 0].set_title("时域卷积 = sine *window", fontweight="bold")
    axes[0, 0].set_xlabel("时间 (秒)")
    axes[0, 0].legend(fontsize=9)
    axes[0, 0].grid(True, alpha=0.3)

    # 上右: 频域相乘
    axes[0, 1].plot(FREQ, 20 * np.log10(np.clip(
        np.abs(fftshift(spec_time_conved)), 1e-12, None)),
        lw=1.2, color="purple", label="DFT(时域卷积)")
    axes[0, 1].plot(FREQ, 20 * np.log10(np.clip(
        np.abs(fftshift(spec_product)), 1e-12, None)),
        lw=1.2, color="orange", ls="--",
        label="spec(sine) × spec(window)")
    axes[0, 1].set_title("频域: DFT(卷积) ≈ 频谱相乘", fontweight="bold")
    axes[0, 1].set_xlabel("频率 (Hz)")
    axes[0, 1].set_ylabel("幅度 (dB)")
    axes[0, 1].set_xlim(-200, 200)
    axes[0, 1].legend(fontsize=9)
    axes[0, 1].grid(True, alpha=0.3)

    # 下左: 时域相乘 (加窗)
    axes[1, 0].plot(T[:200], windowed_direct[:200], lw=1.2, color="#2ca02c",
                    label="sine × window (加窗)")
    axes[1, 0].set_title("时域相乘 = sine × window", fontweight="bold")
    axes[1, 0].set_xlabel("时间 (秒)")
    axes[1, 0].legend(fontsize=9)
    axes[1, 0].grid(True, alpha=0.3)

    # 下右: 频域卷积
    axes[1, 1].plot(FREQ, 20 * np.log10(np.clip(
        np.abs(fftshift(fft(windowed_direct))), 1e-12, None)),
        lw=1.2, color="#2ca02c", label="DFT(sine × window)")
    axes[1, 1].plot(FREQ, 20 * np.log10(np.clip(
        np.abs(fftshift(spec_conv)), 1e-12, None)),
        lw=1.2, color="red", ls="--",
        label="spec(sine) *spec(window)")
    axes[1, 1].set_title("频域: DFT(相乘) ≈ 频谱卷积", fontweight="bold")
    axes[1, 1].set_xlabel("频率 (Hz)")
    axes[1, 1].set_ylabel("幅度 (dB)")
    axes[1, 1].set_xlim(-200, 200)
    axes[1, 1].legend(fontsize=9)
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("05_verification.png", bbox_inches="tight")
    print("[OK] 验证图已保存: 05_verification.png")
    plt.close()


# ╔══════════════════════════════════════════════════════════╗
# ║  第 6 部分: 不同窗函数的旁瓣对比                          ║
# ╚══════════════════════════════════════════════════════════╝

def window_comparison():
    """
    比较三种常见窗函数的频谱特性:
      - 矩形窗 (不加窗 = 突然截断)
      - Hann 窗 (升余弦)
      - Hamming 窗
      - Blackman 窗

    展示:
      - "不加窗" (矩形窗) 的旁瓣最高 → 频谱泄漏最严重
      - Hann 窗的旁瓣衰减快
      - 各种窗在主瓣宽度 vs 旁瓣抑制之间的权衡

    这就是窗函数设计的核心思想!
    """
    window_funcs = {
        "矩形窗 (不加窗)": np.ones(N),
        "Hann 窗": np.hanning(N),
        "Hamming 窗": np.hamming(N),
        "Blackman 窗": np.blackman(N),
    }

    sine = np.sin(2 * np.pi * F_SINE * T)

    fig, (ax_time, ax_freq) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle("窗函数对比: 旁瓣高度 vs 主瓣宽度", fontsize=15, fontweight="bold")

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    zoom_range = (T < 0.1)

    for (name, win), color in zip(window_funcs.items(), colors):
        # 时域
        ax_time.plot(T[zoom_range], win[zoom_range], lw=1.5, color=color, label=name)

        # 频域
        spec = fftshift(np.abs(fft(sine * win)))
        spec_db = 20 * np.log10(np.clip(spec / spec.max(), 1e-12, None))
        ax_freq.plot(FREQ, spec_db, lw=1.2, color=color, label=name, alpha=0.8)

    ax_time.set_title("时域: 各类窗函数形状", fontweight="bold")
    ax_time.set_xlabel("时间 (秒)")
    ax_time.set_ylabel("幅度")
    ax_time.legend(fontsize=9)
    ax_time.grid(True, alpha=0.3)

    ax_freq.set_title("频域: 加窗后频谱 = 旁瓣高度和主瓣宽度的权衡", fontweight="bold")
    ax_freq.set_xlabel("频率 (Hz)")
    ax_freq.set_ylabel("幅度 (dB)")
    ax_freq.set_xlim(-100, 100)
    ax_freq.set_ylim(-100, 5)
    ax_freq.legend(fontsize=9)
    ax_freq.grid(True, alpha=0.3)

    # 标注: 主瓣宽度 vs 旁瓣高度
    ax_freq.annotate(
        "矩形窗: 主瓣最窄, 但旁瓣最高 (-13 dB)\n"
        "Hann 窗: 主瓣稍宽, 旁瓣低 (-31 dB)\n"
        "Blackman 窗: 主瓣最宽, 旁瓣最低 (-58 dB)\n\n"
        "→ 这就是窗函数设计的权衡!",
        xy=(40, -20), fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffffcc", alpha=0.9)
    )

    plt.tight_layout()
    plt.savefig("06_window_comparison.png", bbox_inches="tight")
    print("[OK] 窗函数对比图已保存: 06_window_comparison.png")
    plt.close()


# ╔══════════════════════════════════════════════════════════╗
# ║  第 7 部分: 交互式逐步旁瓣演示                           ║
# ╚══════════════════════════════════════════════════════════╝

def step_by_step_convolution_visual():
    """
    生成一系列静态图, 逐步展示:
    1. 纯正弦波 → 单根谱线
    2. 加上窗函数 → 频谱中出现旁瓣
    3. 把窗谱叠在正弦谱上的分解图

    这种"漫画格"式展示非常适合初学者建立直觉。
    """
    sine = np.sin(2 * np.pi * F_SINE * T)
    window = np.hanning(N)

    spec_sine = fftshift(np.abs(fft(sine)))
    spec_sine = spec_sine / spec_sine.max()
    spec_win = fftshift(np.abs(fft(window)))
    spec_win = spec_win / spec_win.max()
    spec_result = fftshift(np.abs(fft(sine * window)))
    spec_result = spec_result / spec_result.max()

    fig, axes = plt.subplots(2, 4, figsize=(20, 9))
    fig.suptitle("旁瓣诞生图解: 一步步理解「时域相乘 = 频域卷积」",
                 fontsize=16, fontweight="bold")

    # ── Step 1: 原始正弦波 ──
    ax = axes[0, 0]
    ax.plot(T[:300], sine[:300], lw=1, color="#1f77b4")
    ax.set_title("Step 1: 纯正弦波", fontweight="bold")
    ax.set_xlabel("时间")
    ax.set_ylabel("幅度")
    ax.text(0.5, -0.25, "无限长正弦波 × 无限长\n→ 频谱是单根谱线",
            transform=ax.transAxes, ha="center", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="#e8f4fd"))

    ax = axes[1, 0]
    ax.plot(FREQ, 20 * np.log10(np.clip(spec_sine, 1e-12, None)),
            lw=1.2, color="#1f77b4")
    ax.set_xlim(-150, 150)
    ax.set_ylim(-120, 5)
    ax.set_xlabel("频率 (Hz)")
    ax.set_ylabel("幅度 (dB)")
    ax.set_title("频谱: 理想 δ", fontweight="bold")
    ax.grid(True, alpha=0.3)

    # ── Step 2: 实际中我们只能截取一段 ──
    ax = axes[0, 1]
    ax.plot(T[:300], sine[:300], lw=1, color="#1f77b4")
    ax.axvspan(0.05, 0.25, alpha=0.15, color="red")
    ax.set_title("Step 2: 实际: 只能观察一段", fontweight="bold")
    ax.set_xlabel("时间")
    ax.set_ylabel("幅度")
    ax.text(0.5, -0.25, "我们只能取有限长\n→ 相当于乘了一个矩形窗!",
            transform=ax.transAxes, ha="center", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="#ffe8e8"))

    ax = axes[1, 1]
    ax.plot(FREQ, 20 * np.log10(np.clip(spec_sine, 1e-12, None)),
            lw=1.2, color="#1f77b4")
    ax.set_xlim(-150, 150)
    ax.set_ylim(-120, 5)
    ax.set_xlabel("频率 (Hz)")
    ax.set_ylabel("幅度 (dB)")
    ax.set_title("仍是 δ (还未加窗)", fontweight="bold")
    ax.grid(True, alpha=0.3)

    # ── Step 3: 加上窗函数 ──
    ax = axes[0, 2]
    ax.plot(T[:300], sine[:300], lw=0.8, color="#1f77b4", alpha=0.5, label="正弦")
    ax.plot(T[:300], window[:300], lw=1.5, color="#ff7f0e", label="Hann窗")
    ax.set_title("Step 3: 乘以窗函数", fontweight="bold")
    ax.set_xlabel("时间")
    ax.set_ylabel("幅度")
    ax.legend(fontsize=8)
    ax.text(0.5, -0.25, "信号 × 窗 = 加窗信号\n→ 频域: 频谱 *窗谱",
            transform=ax.transAxes, ha="center", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="#fff8e0"))

    ax = axes[1, 2]
    ax.plot(FREQ, 20 * np.log10(np.clip(spec_win, 1e-12, None)),
            lw=1.2, color="#ff7f0e")
    ax.set_xlim(-150, 150)
    ax.set_ylim(-120, 5)
    ax.set_xlabel("频率 (Hz)")
    ax.set_ylabel("幅度 (dB)")
    ax.set_title("窗频谱: 主瓣+旁瓣", fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.axvline(x=0, color="green", ls="--", alpha=0.5)

    # ── Step 4: 最终结果 ──
    ax = axes[0, 3]
    windowed = sine * window
    ax.plot(T[:300], windowed[:300], lw=1, color="#2ca02c")
    ax.set_title("Step 4: 加窗信号", fontweight="bold")
    ax.set_xlabel("时间")
    ax.set_ylabel("幅度")
    ax.text(0.5, -0.25, "两端平滑趋零\n→ 避免截断效应",
            transform=ax.transAxes, ha="center", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="#e8ffe8"))

    ax = axes[1, 3]
    ax.plot(FREQ, 20 * np.log10(np.clip(spec_result, 1e-12, None)),
            lw=1.2, color="#2ca02c")
    ax.set_xlim(-150, 150)
    ax.set_ylim(-120, 5)
    ax.set_xlabel("频率 (Hz)")
    ax.set_ylabel("幅度 (dB)")
    ax.set_title("最终频谱: 主瓣+旁瓣", fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.axvline(x=F_SINE, color="green", ls="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig("07_step_by_step.png", bbox_inches="tight")
    print("[OK] 步骤图解已保存: 07_step_by_step.png")
    plt.close()


# ╔══════════════════════════════════════════════════════════╗
# ║  第 8 部分: 频域卷积的滑窗演示 (核心动画)                  ║
# ╚══════════════════════════════════════════════════════════╝

def freq_convolution_sliding_detailed():
    """
    最核心的动画: 展示窗频谱如何"滑过"正弦谱线, 产生旁瓣。

    三列布局:
      [左] 正弦波频谱 (两根 δ)
      [中] 窗频谱 (当前滑到的位置)
      [右] 卷积结果 = 把窗频谱"贴"到每根 δ 上并叠加
    """
    window = np.hanning(N)
    spec_win_linear = fftshift(np.abs(fft(window)))
    spec_win_linear = spec_win_linear / spec_win_linear.max()

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("频域卷积详解: 窗频谱滑过正弦谱线",
                 fontsize=16, fontweight="bold")

    # 正弦谱线索引
    pos_idx = np.argmin(np.abs(FREQ - F_SINE))
    neg_idx = np.argmin(np.abs(FREQ + F_SINE))

    def animate(frame):
        for ax in axes:
            ax.clear()

        # 窗频谱偏移: 从 -120 Hz 滑到 +120 Hz
        shift = (frame / 149) * 240 - 120
        shift_idx = int(shift / DF)

        win_shifted = np.roll(spec_win_linear, shift_idx)

        # ── 左列: 正弦频谱 ──
        sine_display = np.zeros_like(FREQ)
        sine_display[pos_idx] = 1.0
        sine_display[neg_idx] = 1.0

        markerline, _, _ = axes[0].stem(
            FREQ, sine_display, linefmt="#1f77b4", markerfmt="^", basefmt=" "
        )
        markerline.set_markersize(10)
        axes[0].set_xlim(-150, 150)
        axes[0].set_ylim(-0.05, 1.2)
        axes[0].set_xlabel("频率 (Hz)")
        axes[0].set_title("正弦频谱 = δ(F±50)")
        axes[0].grid(True, alpha=0.3)

        # ── 中列: 滑动的窗频谱 ──
        axes[1].plot(FREQ, win_shifted, lw=1.5, color="#ff7f0e")
        axes[1].axvline(x=shift, color="orange", ls="--", alpha=0.5)
        # 标记主瓣和旁瓣
        main_lobe_freq = shift
        axes[1].plot(main_lobe_freq, 1.0, "gv", ms=8, label="主瓣")
        axes[1].legend(fontsize=8, loc="upper right")
        axes[1].set_xlim(-150, 150)
        axes[1].set_ylim(-0.05, 1.2)
        axes[1].set_xlabel("频率 (Hz)")
        axes[1].set_title(f"窗频谱 (当前中心={shift:.0f} Hz)")
        axes[1].grid(True, alpha=0.3)

        # ── 右列: 卷积结果 ──
        # 窗谱在 +F_SINE 和 -F_SINE 处的叠加
        shift_pos = int(F_SINE / DF)
        shift_neg = int(-F_SINE / DF)

        win_at_pos = np.roll(spec_win_linear, shift_pos)
        win_at_neg = np.roll(spec_win_linear, shift_neg)

        combined = win_at_pos + win_at_neg
        combined = combined / combined.max()

        axes[2].plot(FREQ, combined, lw=1.5, color="#2ca02c",
                     label="最终卷积结果")
        axes[2].set_xlim(-150, 150)
        axes[2].set_ylim(-0.05, 1.2)
        axes[2].set_xlabel("频率 (Hz)")
        axes[2].set_title("卷积结果: 窗谱「印」在 ±50 Hz 处")
        axes[2].grid(True, alpha=0.3)

        # 标注
        for f0, color in [(50, "green"), (-50, "green")]:
            axes[1].axvline(x=f0, color=color, ls="--", alpha=0.3)
            axes[2].axvline(x=f0, color="green", ls="--", alpha=0.6,
                            label="正弦频率" if f0 == 50 else "")
        for side_offset in [15, 25, 35]:
            for sign in [1, -1]:
                for center in [F_SINE, -F_SINE]:
                    axes[2].axvline(x=center + sign * side_offset,
                                    color="red", ls=":", alpha=0.2)
        axes[2].legend(fontsize=8, loc="upper right")

        return []

    anim = FuncAnimation(fig, animate, frames=150, blit=False, interval=40)
    writer = PillowWriter(fps=15)
    anim.save("08_freq_conv_detailed.gif", writer=writer)
    print("[OK] 频域卷积详解动画已保存: 08_freq_conv_detailed.gif")
    plt.close()


# ╔══════════════════════════════════════════════════════════╗
# ║  main                                                       ║
# ╚══════════════════════════════════════════════════════════╝

def main():
    print("=" * 60)
    print("  信号卷积原理演示 -- 时域相乘 <--> 频域卷积")
    print("  面向初学者的可视化教程")
    print("=" * 60)
    print()
    print("本脚本将生成以下文件:")
    print("  1. 01_static_overview.png      -- 静态概览 (四象限图)")
    print("  2. 02_time_convolution.gif     -- 时域卷积滑动动画")
    print("  3. 03_freq_convolution.gif     -- 频域卷积动画")
    print("  4. 04_sidelobe_explanation.gif -- 旁瓣诞生图解动画")
    print("  5. 05_verification.png         -- 对偶关系数值验证")
    print("  6. 06_window_comparison.png    -- 不同窗函数旁瓣对比")
    print("  7. 07_step_by_step.png         -- 逐步图解(漫画格)")
    print("  8. 08_freq_conv_detailed.gif   -- 频域卷积详解")
    print()
    print("正在生成, 请稍候...")
    print()

    static_overview()
    time_convolution_animation()
    freq_convolution_animation()
    sidelobe_explanation()
    verification_plot()
    window_comparison()
    step_by_step_convolution_visual()
    freq_convolution_sliding_detailed()

    print()
    print("=" * 60)
    print("  全部完成! 请查看生成的图片和动画文件。")
    print("=" * 60)
    print()
    print("--- 学习建议 ---")
    print("  1. 先看 07_step_by_step.png 建立整体概念")
    print("  2. 再看 01_static_overview.png 理解四象限关系")
    print("  3. 播放 04_sidelobe_explanation.gif 理解旁瓣来源")
    print("  4. 播放 02_time_convolution.gif 理解时域卷积过程")
    print("  5. 播放 08_freq_conv_detailed.gif 理解频域卷积")
    print("  6. 看 06_window_comparison.png 理解窗函数的权衡")
    print("  7. 看 05_verification.png 验证数学关系")


if __name__ == "__main__":
    main()
