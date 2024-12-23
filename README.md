# 视频转PDF幻灯片工具

这是一个用于从视频中提取独特帧并将其转换为PDF幻灯片的工具。该工具通过背景减除算法检测视频中的独特帧，并将这些帧保存为图片，最终将这些图片合并为一个PDF文件。

## 功能概述

- **提取独特帧**：通过背景减除算法检测视频中的独特帧。
- **保存为图片**：将检测到的独特帧保存为PNG格式的图片。
- **生成PDF**：将保存的图片合并为一个PDF文件。
- **进度跟踪**：在处理过程中实时显示进度。
- **错误处理**：提供详细的错误处理和日志记录。

## 依赖库

- `opencv-python`
- `imutils`
- `img2pdf`
- `shutil`
- `glob`
- `argparse`

## 安装依赖

在使用本工具之前，请确保已安装所有依赖库。可以通过以下命令安装：

```bash
pip install opencv-python imutils img2pdf
```

## 使用方法

### 命令行参数

- `video_path`：要处理的视频文件路径。
- `--savepdf`：是否将输出保存为PDF文件（可选）。

### 示例

```bash
python script.py /path/to/video.mp4 --savepdf
```

### 输出

- 图片：保存到 `./output/<视频文件名>/` 目录下。
- PDF：保存到 `./output/<视频文件名>.pdf`。

## 代码结构

- `get_frames`：从视频中提取帧，并根据帧率限制帧数。
- `detect_unique_screenshots`：检测并保存独特的帧。
- `initialize_output_folder`：初始化输出文件夹。
- `convert_screenshots_to_pdf`：将截图转换为PDF。
- `process_video`：主处理函数，调用上述函数完成视频处理。

## 常量说明

- `FRAME_RATE`：帧率，控制每秒处理的帧数。
- `WARMUP`：初始跳过的帧数，避免背景模型未稳定时的误检测。
- `FGBG_HISTORY`：背景减除模型的历史帧数。
- `VAR_THRESHOLD`：马氏距离阈值，用于背景减除。
- `DETECT_SHADOWS`：是否检测阴影。
- `MIN_PERCENT`：最小差异百分比，用于判断是否为独特帧。
- `MAX_PERCENT`：最大差异百分比，用于判断帧是否结束。

## 注意事项

- 视频文件路径必须正确，且视频格式需为OpenCV支持的格式。
- 如果视频中没有独特帧，将不会生成PDF文件。
- 处理过程中会显示进度，用户可以通过进度信息了解处理状态。

## 错误处理

- 提供详细的错误日志，帮助用户快速定位问题。
- 在处理过程中捕获并处理常见错误，如文件不存在、视频无法打开等。

## 贡献

欢迎提交问题和改进建议！请通过GitHub的Issue或Pull Request功能参与贡献。

## 许可证

本项目采用MIT许可证，详情请参阅[LICENSE](LICENSE)文件。
