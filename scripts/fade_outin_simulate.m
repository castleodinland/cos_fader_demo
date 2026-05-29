function fade_outin_dummy()
% 创建主窗口 (Figure)
% 关闭之前可能存在的同名窗口
close(findobj('Type', 'figure', 'Name', 'Sine Wave Fade Generator'));

fig = figure('Name', 'Sine Wave Fade Generator', ...
             'Position', [50, 30, 1450, 960], ...
             'MenuBar', 'none', ...
             'ToolBar', 'figure', ...
             'NumberTitle', 'off');

% 定义全局参数
fs = 44100;
f = 100;
num_points = 2000;
fade_length = 128;
t = (0:num_points-1) / fs;
original_signal = sin(2 * pi * f * t);

% 状态变量
max_start_idx = num_points - (2 * fade_length);
fade_out_start = 350; % 初始默认位置
is_dragging = false;

% ==================== 1. 创建多绘图区域 (Layout) ====================
% 上方时域图 (横跨整个宽度)
ax1 = axes('Parent', fig, 'Position', [0.1, 0.55, 0.85, 0.38]);
hold(ax1, 'on');
grid(ax1, 'on');

% 下左图：线性 Fade 语谱图 (Spectrogram)
ax2 = axes('Parent', fig, 'Position', [0.1, 0.12, 0.38, 0.33]);
hold(ax2, 'on');

% 下右图：优化 Cosine Fade 语谱图 (Spectrogram)
ax3 = axes('Parent', fig, 'Position', [0.57, 0.12, 0.38, 0.33]);
hold(ax3, 'on');

% ==================== 2. 自定义高兼容性时频分析 (STFT) 参数 ====================
% 为了不依赖 signal 工具箱的 specgram，我们手工计算滑动窗口的参数
win_len = 64;
noverlap = 60;
step = win_len - noverlap; % 步长 = 4
nfft = 256; % FFT 点数

% 预计算时间轴和频率轴
% 滑动窗口的中心点对应的采样点 index
t_samples = win_len/2 : step : (num_points - win_len/2);
num_frames = length(t_samples);

% 频率轴 (0 到 Nyquist)
f_stft = (0 : nfft/2) * (fs / nfft);
num_freq_bins = length(f_stft);

% 创建汉宁窗用于抑制 STFT 的频谱泄露
win = hanning_local(win_len);

% ==================== 3. 一次性绘制静态背景元素 ====================

% 3.1 时域：原始未处理信号 (极浅灰色参考虚线)
plot(ax1, 1:num_points, original_signal, 'Color', [0.85 0.85 0.85], 'LineStyle', ':', 'LineWidth', 1);

% 3.2 时域：底部滑块轨道 (在 y = -1.2 处的灰色水平线)
plot(ax1, [1, max_start_idx], [-1.2, -1.2], 'Color', [0.7 0.7 0.7], 'LineStyle', '-', 'LineWidth', 3);

% ==================== 4. 创建动态对象句柄 (时域) ====================

% 4.1 优化后的 Cosine Fade 信号 (深灰色实线，默认加粗)
h_opt = plot(ax1, 1:num_points, original_signal, 'Color', [0.4 0.4 0.4], 'LineStyle', '-', 'LineWidth', 2.5);

% 4.2 线性 Fade 信号 (加粗深蓝色实线，重点观察的主信号)
h_linear = plot(ax1, 1:num_points, original_signal, 'Color', [0.0 0.4 0.8], 'LineStyle', '-', 'LineWidth', 2.5);

% 4.3 垂直分界线与特征点
h_line_red = plot(ax1, [fade_out_start, fade_out_start], [-1.25, 1.2], 'r--', 'LineWidth', 1.5);
h_point_red = plot(ax1, fade_out_start, 0, 'ro', 'MarkerSize', 8, 'MarkerFaceColor', 'r');

h_line_green = plot(ax1, [fade_out_start, fade_out_start], [-1.25, 1.2], 'g--', 'LineWidth', 1.5);
h_point_green = plot(ax1, fade_out_start, 0, 'go', 'MarkerSize', 8, 'MarkerFaceColor', 'g');

h_line_mag = plot(ax1, [fade_out_start, fade_out_start], [-1.25, 1.2], 'm--', 'LineWidth', 1.5);
h_point_mag = plot(ax1, fade_out_start, 0, 'mo', 'MarkerSize', 8, 'MarkerFaceColor', 'm');

% 4.4 横坐标上的滑动交互手柄 (红色向上三角形 ▲，放在轨道上 y = -1.2 处)
h_handle = plot(ax1, fade_out_start, -1.2, 'r^', 'MarkerSize', 14, 'MarkerFaceColor', 'r', 'LineWidth', 1.5);

% ==================== 5. 创建动态对象句柄 (2D 语谱图) ====================
% 初始空白热力图数据
init_spec = -120 * ones(num_freq_bins, num_frames);

% 5.1 线性 Fade 语谱图句柄
h_img_linear = imagesc(t_samples, f_stft / 1000, init_spec, 'Parent', ax2);
% 5.2 优化 Cosine Fade 语谱图句柄
h_img_opt = imagesc(t_samples, f_stft / 1000, init_spec, 'Parent', ax3);

% --- 辅助指示线：在语谱图上同步绘制当前手柄对应的红绿蓝垂直指示线 ---
h_spec_red2 = plot(ax2, [fade_out_start, fade_out_start], [0, fs/2000], 'r--', 'LineWidth', 1.2);
h_spec_green2 = plot(ax2, [fade_out_start, fade_out_start], [0, fs/2000], 'g--', 'LineWidth', 1.2);
h_spec_mag2 = plot(ax2, [fade_out_start, fade_out_start], [0, fs/2000], 'm--', 'LineWidth', 1.2);

h_spec_red3 = plot(ax3, [fade_out_start, fade_out_start], [0, fs/2000], 'r--', 'LineWidth', 1.2);
h_spec_green3 = plot(ax3, [fade_out_start, fade_out_start], [0, fs/2000], 'g--', 'LineWidth', 1.2);
h_spec_mag3 = plot(ax3, [fade_out_start, fade_out_start], [0, fs/2000], 'm--', 'LineWidth', 1.2);

% ==================== 6. 坐标轴与主题设置 ====================

% 时域轴设置
axis(ax1, [1 num_points -1.35 1.25]);
ylabel(ax1, 'Amplitude', 'FontSize', 11);
title(ax1, 'Time Domain: Drag Red Triangle (\bf\color{red}\Delta\rm) on Slider to Adjust Fade Point', 'FontSize', 11);

% 线性 Fade 语谱图轴设置 (左下)
axis(ax2, [1 num_points 0 fs/2000]);
ylabel(ax2, 'Frequency (kHz)', 'FontSize', 11);
xlabel(ax2, 'Sample Index (n)', 'FontSize', 11);
title(ax2, 'Audition-style Spectrogram: Linear Fade (Sharp Corners)', 'FontSize', 10, 'Color', [0.0 0.4 0.8]);

% 优化 Cosine Fade 语谱图轴设置 (右下)
axis(ax3, [1 num_points 0 fs/2000]);
ylabel(ax3, 'Frequency (kHz)', 'FontSize', 11);
xlabel(ax3, 'Sample Index (n)', 'FontSize', 11);
title(ax3, 'Audition-style Spectrogram: Cosine Fade (Smooth)', 'FontSize', 10, 'Color', [0.3 0.3 0.3]);

% 为两个语谱图应用统一的热力图配色
colormap(ax2, 'jet');
colormap(ax3, 'jet');
caxis(ax2, [-100 0]); % 设定 -100dB 到 0dB 的色彩映射范围
caxis(ax3, [-100 0]);

% 时域图例
% ==================== 8. 线型控制选框（右上角，归一化坐标） ====================
% 使用 checkbox，选中 → 加粗实线，取消 → 虚线
% 归一化 Units 确保缩放时始终黏着在右上角
cb_linear = uicontrol('Style', 'checkbox', 'Parent', fig, ...
    'Units', 'normalized', ...
    'String', 'Linear Bold', ...
    'Position', [0.82, 0.94, 0.14, 0.03], ...
    'Value', 1, ...
    'Callback', @toggle_linear_cb);

cb_cos = uicontrol('Style', 'checkbox', 'Parent', fig, ...
    'Units', 'normalized', ...
    'String', 'Cosine Bold', ...
    'Position', [0.82, 0.90, 0.14, 0.03], ...
    'Value', 1, ...
    'Callback', @toggle_cos_cb);

legend(ax1, [h_linear, h_opt, h_handle], ...
       {'Linear Fade', ...
        'Cosine Fade (Smooth)', ...
        'X-Axis Handle (Drag Left/Right)'}, ...
       'Location', 'northoutside', 'Orientation', 'horizontal');

% 初始化渲染（第一次需要完全绘制时域和频域图）
update_time_domain();
update_spectrograms();

% ==================== 7. 绑定鼠标交互事件 ====================
set(fig, 'WindowButtonDownFcn', @on_mousedown);
set(fig, 'WindowButtonMotionFcn', @on_mousemove);
set(fig, 'WindowButtonUpFcn', @on_mouseup);

    % --- 鼠标按下事件 ---
    function on_mousedown(~, ~)
        cp = get(ax1, 'CurrentPoint');
        x_click = cp(1,1);
        y_click = cp(1,2);

        xlims = xlim(ax1);
        ylims = ylim(ax1);

        % 确保点击在时域坐标轴内
        if x_click >= xlims(1) && x_click <= xlims(2) && y_click >= ylims(1) && y_click <= ylims(2)
            % 交互判定：点击位置靠近手柄 X 坐标，且位于 y 轴的最下方 (-1.35 到 -0.9)
            x_range = xlims(2) - xlims(1);
            if abs(x_click - fade_out_start) < 0.04 * x_range && y_click <= -0.9
                is_dragging = true;
                set(fig, 'Pointer', 'hand'); % 改变鼠标为手形
            end
        end
    end

    % --- 鼠标移动事件 ---
    % 核心性能优化：拖动过程中【只更新时域】，完全不计算FFT！
    function on_mousemove(~, ~)
        if is_dragging
            cp = get(ax1, 'CurrentPoint');
            x_curr = cp(1,1);

            % 限制拖动范围在合法轨道区间内
            fade_out_start = round(max(1, min(max_start_idx, x_curr)));

            % 极速重绘时域波形（极度顺滑）
            update_time_domain();
        end
    end

    % --- 鼠标松开事件 ---
    % 鼠标一旦释放，瞬间触发高计算量的 STFT 并刷新语谱图！
    function on_mouseup(~, ~)
        if is_dragging
            is_dragging = false;
            set(fig, 'Pointer', 'arrow');

            % 释放瞬间更新频域（一气呵成）
            update_spectrograms();
        end
    end

    % --- 时域极速刷新函数 (耗时约 0.5ms) ---
    function update_time_domain()
        % 计算淡入淡出区间
        fade_out_end = fade_out_start + fade_length - 1;
        fade_in_start = fade_out_end + 1;
        fade_in_end = fade_in_start + fade_length - 1;

        % 从原始正弦信号重新计算包络效果
        p_linear = original_signal;
        p_opt = original_signal;

        t_norm = linspace(0, 1, fade_length);

        % 线性包络
        fade_out_env_linear = 1 - t_norm;
        fade_in_env_linear = t_norm;

        % 优化包络
        fade_out_env_opt = 0.5 * (1 + cos(pi * t_norm));
        fade_in_env_opt = 0.5 * (1 - cos(pi * t_norm));

        % 应用包络
        p_linear(fade_out_start:fade_out_end) = p_linear(fade_out_start:fade_out_end) .* fade_out_env_linear;
        p_linear(fade_in_start:fade_in_end) = p_linear(fade_in_start:fade_in_end) .* fade_in_env_linear;

        p_opt(fade_out_start:fade_out_end) = p_opt(fade_out_start:fade_out_end) .* fade_out_env_opt;
        p_opt(fade_in_start:fade_in_end) = p_opt(fade_in_start:fade_in_end) .* fade_in_env_opt;

        % --- 极速属性更新 ---
        set(h_linear, 'YData', p_linear);
        set(h_opt, 'YData', p_opt);

        % 更新时域辅助线
        set(h_line_red, 'XData', [fade_out_start, fade_out_start]);
        set(h_point_red, 'XData', fade_out_start, 'YData', p_linear(fade_out_start));

        boundary_idx = fade_out_end + 0.5;
        set(h_line_green, 'XData', [boundary_idx, boundary_idx]);
        set(h_point_green, 'XData', boundary_idx, 'YData', 0);

        set(h_line_mag, 'XData', [fade_in_end, fade_in_end]);
        set(h_point_mag, 'XData', fade_in_end, 'YData', p_linear(fade_in_end));

        % 更新滑动三角手柄位置
        set(h_handle, 'XData', fade_out_start);

        % 更新动态总标题 (提示用户释放在计算频谱)
        title(ax1, {sprintf('100Hz Sine Wave: Drag Handle (\\bf\\color{red}\\Delta\\rm) to Align and Compare Noise'), ...
                   sprintf('Fade Out: [%d -> %d] | Fade In: [%d -> %d]  \\color{red}(Release mouse to update Spectrogram)', ...
                   fade_out_start, fade_out_end, fade_in_start, fade_in_end)}, 'FontSize', 12);

        drawnow();
    end

    % --- 频域/语谱图刷新函数 (在释放鼠标时单次调用，避免拖动卡顿) ---
    function update_spectrograms()
        % 重新计算对应位置的信号用于 STFT 计算
        fade_out_end = fade_out_start + fade_length - 1;
        fade_in_start = fade_out_end + 1;
        fade_in_end = fade_in_start + fade_length - 1;

        p_linear = original_signal;
        p_opt = original_signal;

        t_norm = linspace(0, 1, fade_length);
        fade_out_env_linear = 1 - t_norm;
        fade_in_env_linear = t_norm;
        fade_out_env_opt = 0.5 * (1 + cos(pi * t_norm));
        fade_in_env_opt = 0.5 * (1 - cos(pi * t_norm));

        p_linear(fade_out_start:fade_out_end) = p_linear(fade_out_start:fade_out_end) .* fade_out_env_linear;
        p_linear(fade_in_start:fade_in_end) = p_linear(fade_in_start:fade_in_end) .* fade_in_env_linear;

        p_opt(fade_out_start:fade_out_end) = p_opt(fade_out_start:fade_out_end) .* fade_out_env_opt;
        p_opt(fade_in_start:fade_in_end) = p_opt(fade_in_start:fade_in_end) .* fade_in_env_opt;

        % 自定义高兼容性时频计算 (STFT)
        dB_s_linear = calculate_stft(p_linear);
        dB_s_opt = calculate_stft(p_opt);

        % 更新下方的 2D 语谱图颜色矩阵 (CData)
        set(h_img_linear, 'CData', dB_s_linear);
        set(h_img_opt, 'CData', dB_s_opt);

        % 同步更新两张语谱图上的红、绿、粉垂直辅助指示线
        boundary_idx = fade_out_end + 0.5;
        set(h_spec_red2, 'XData', [fade_out_start, fade_out_start]);
        set(h_spec_green2, 'XData', [boundary_idx, boundary_idx]);
        set(h_spec_mag2, 'XData', [fade_in_end, fade_in_end]);

        set(h_spec_red3, 'XData', [fade_out_start, fade_out_start]);
        set(h_spec_green3, 'XData', [boundary_idx, boundary_idx]);
        set(h_spec_mag3, 'XData', [fade_in_end, fade_in_end]);

        % 移除红色“等待释放”提示，替换为“已更新”状态
        title(ax1, {sprintf('100Hz Sine Wave: Drag Handle (\\bf\\color{red}\\Delta\\rm) to Align and Compare Noise'), ...
                   sprintf('Fade Out: [%d -> %d] | Fade In: [%d -> %d]  \\color[rgb]{0,0.5,0}(Spectrogram Updated!)', ...
                   fade_out_start, fade_out_end, fade_in_start, fade_in_end)}, 'FontSize', 12);

        drawnow();
    end

    % --- STFT 算法核心实现 (独立于任何外部工具箱) ---
    function dB_matrix = calculate_stft(signal_in)
        dB_matrix = zeros(num_freq_bins, num_frames);
        for col = 1:num_frames
            center_idx = t_samples(col);
            start_idx = center_idx - win_len/2 + 1;
            end_idx = center_idx + win_len/2;

            sig_segment = signal_in(start_idx:end_idx);

            % 加窗平滑 (去基线并乘以汉宁窗)
            sig_windowed = (sig_segment(:) - mean(sig_segment)) .* win;

            % 快速傅里叶变换 (FFT)
            fft_res = fft(sig_windowed, nfft);

            % 提取单边带幅度谱
            mag_spectrum = abs(fft_res(1:num_freq_bins));
            dB_matrix(:, col) = mag_spectrum;
        end
        % 整体矩阵归一化，最大值设为 0dB
        max_val = max(dB_matrix(:));
        if max_val == 0, max_val = 1; end
        dB_matrix = 20 * log10(dB_matrix / max_val + 1e-6);
    end

    % --- 汉宁窗本地实现函数 ---
    function w = hanning_local(L)
        w = 0.5 * (1 - cos(2 * pi * (0:L-1)' / (L - 1)));
    end

    % --- 线型控制：Linear 曲线切换加粗/虚线 ---
    function toggle_linear_cb(src, ~)
        cur = get(h_linear, 'LineStyle');
        if strcmp(cur, '-')
            set(h_linear, 'LineWidth', 1.5, 'LineStyle', '--');
            set(src, 'Value', 0);
        else
            set(h_linear, 'LineWidth', 2.5, 'LineStyle', '-');
            set(src, 'Value', 1);
        end
    end

    % --- 线型控制：Cosine 曲线切换加粗/虚线 ---
    function toggle_cos_cb(src, ~)
        cur = get(h_opt, 'LineStyle');
        if strcmp(cur, '-')
            set(h_opt, 'LineWidth', 1.5, 'LineStyle', '--');
            set(src, 'Value', 0);
        else
            set(h_opt, 'LineWidth', 2.5, 'LineStyle', '-');
            set(src, 'Value', 1);
        end
    end
end
