import os
import time
import cv2
import imutils
import shutil
import img2pdf
import glob
import argparse
from typing import Generator, Tuple, Optional

# 定义常量
OUTPUT_SLIDES_DIR = "./output"  # 输出目录
FRAME_RATE = 5  # 帧率
WARMUP = FRAME_RATE * 3  # 初始跳过的帧数
FGBG_HISTORY = FRAME_RATE * 15  # 背景对象中的帧数
VAR_THRESHOLD = 16  # 马氏距离阈值
DETECT_SHADOWS = True  # 是否检测阴影
MIN_PERCENT = 0.1  # 最小差异百分比
MAX_PERCENT = 3  # 最大差异百分比

def get_frames(video_path: str) -> Generator[Tuple[int, float, Optional[cv2.Mat]], None, None]:
    """
    从视频中返回帧，改进帧数限制计算。
    参数:
        video_path: 视频文件路径
    返回:
        包含 (帧计数, 帧时间, 帧) 的元组
    """
    vs = None
    try:
        vs = cv2.VideoCapture(video_path)
        if not vs.isOpened():
            raise Exception(f'无法打开文件 {video_path}')

        # 获取视频属性
        fps = vs.get(cv2.CAP_PROP_FPS)
        total_frames = int(vs.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # 根据时长和帧率计算预期处理的帧数
        expected_processed_frames = int(duration * FRAME_RATE)
        
        print(f"视频属性:")
        print(f"FPS: {fps}")
        print(f"总帧数: {total_frames}")
        print(f"时长: {duration:.2f} 秒")
        print(f"预期处理的帧数: {expected_processed_frames}")

        frame_time = 0
        processed_frames = 0
        
        # 使用 expected_processed_frames 作为限制
        while processed_frames < expected_processed_frames:
            vs.set(cv2.CAP_PROP_POS_MSEC, frame_time * 1000)
            frame_time += 1/FRAME_RATE
            
            ret, frame = vs.read()
            
            if not ret or frame is None:
                print(f"视频结束，帧数 {processed_frames}")
                break

            processed_frames += 1
            
            # 进度报告
            # if processed_frames % 100 == 0:
#                 progress = (processed_frames / expected_processed_frames) * 100
#                 print(f"已处理 {processed_frames}/{expected_processed_frames} 帧 ({progress:.1f}%)")
                
            yield processed_frames, frame_time, frame

        print(f"视频处理完成")
        print(f"总处理帧数: {processed_frames}/{expected_processed_frames}")

    except Exception as e:
        print(f"get_frames 错误: {str(e)}")
        raise
    finally:
        if vs is not None:
            vs.release()

def detect_unique_screenshots(video_path: str, output_folder_screenshot_path: str) -> int:
    """
    检测并保存独特的帧，改进进度跟踪和错误处理。
    返回捕获的截图数量。
    """
    fgbg = cv2.createBackgroundSubtractorMOG2(
        history=FGBG_HISTORY,
        varThreshold=VAR_THRESHOLD,
        detectShadows=DETECT_SHADOWS
    )
    
    captured = False
    start_time = time.time()
    W, H = None, None
    screenshots_count = 0
    last_progress_time = time.time()

    try:
        for frame_count, frame_time, frame in get_frames(video_path):
            orig = frame.copy()
            frame = imutils.resize(frame, width=600)
            mask = fgbg.apply(frame)

            if W is None or H is None:
                H, W = mask.shape[:2]

            p_diff = (cv2.countNonZero(mask) / float(W * H)) * 100

            # 每10秒打印一次进度
            current_time = time.time()
            if current_time - last_progress_time >= 20:
                print(f"处理中... 当前帧: {frame_count}, 捕获截图: {screenshots_count}")
                last_progress_time = current_time

            if p_diff < MIN_PERCENT and not captured and frame_count > WARMUP:
                captured = True
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                time_str = time.strftime('%H_%M_%S', time.gmtime(frame_time))
                filename = f"{video_name}_{time_str}_{screenshots_count:03d}.png"

                path = os.path.join(output_folder_screenshot_path, filename)
                print(f"保存截图 {screenshots_count + 1}: {path}")
                cv2.imwrite(path, orig)
                screenshots_count += 1

            elif captured and p_diff >= MAX_PERCENT:
                captured = False

        processing_time = time.time() - start_time
        print(f'处理完成，耗时 {processing_time:.2f} 秒')
        print(f'总共捕获截图: {screenshots_count}')
        return screenshots_count

    except Exception as e:
        print(f"截图检测错误: {str(e)}")
        raise

def initialize_output_folder(video_path: str) -> str:
    """
    初始化输出文件夹，改进错误处理。
    """
    try:
        output_folder_screenshot_path = os.path.join(
            OUTPUT_SLIDES_DIR,
            os.path.splitext(os.path.basename(video_path))[0]
        )

        if os.path.exists(output_folder_screenshot_path):
            shutil.rmtree(output_folder_screenshot_path)

        os.makedirs(output_folder_screenshot_path, exist_ok=True)
        print(f'初始化输出文件夹: {output_folder_screenshot_path}')
        return output_folder_screenshot_path

    except Exception as e:
        print(f"初始化输出文件夹错误: {str(e)}")
        raise

def convert_screenshots_to_pdf(video_path: str, output_folder_screenshot_path: str) -> None:
    """
    将截图转换为PDF，改进错误处理。
    """
    try:
        output_pdf_path = os.path.join(
            OUTPUT_SLIDES_DIR,
            f"{os.path.splitext(os.path.basename(video_path))[0]}.pdf"
        )
        
        image_files = sorted(glob.glob(os.path.join(output_folder_screenshot_path, "*.png")))
        if not image_files:
            raise Exception("没有找到要转换为PDF的图片")

        print(f'将 {len(image_files)} 张图片转换为PDF...')
        with open(output_pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_files))

        print(f'PDF创建成功，路径: {output_pdf_path}')

    except Exception as e:
        print(f"转换为PDF错误: {str(e)}")
        raise

def process_video(video_path: str, savepdf: bool) -> None:
    """
    主处理函数，改进错误处理和状态报告。
    """
    try:
        print(f'处理视频: {video_path}')
        output_folder_screenshot_path = initialize_output_folder(video_path)
        
        screenshots_count = detect_unique_screenshots(video_path, output_folder_screenshot_path)
        
        if screenshots_count == 0:
            print("警告: 视频中没有捕获到截图。")
        
        if savepdf and screenshots_count > 0:
            convert_screenshots_to_pdf(video_path, output_folder_screenshot_path)
        elif savepdf:
            print("PDF转换跳过 - 没有截图可转换。")
        else:
            print("PDF转换跳过 - 配置要求。")

        print("视频处理完成。")
        
    except Exception as e:
        print(f"视频处理错误: {str(e)}")
        raise
    finally:
        print("清理完成。")

if __name__ == "__main__":
    try:
        print("启动视频处理脚本...")
        parser = argparse.ArgumentParser()
        parser.add_argument("video_path", help="要转换为PDF幻灯片的视频路径", type=str)
        parser.add_argument("--savepdf", help="是否将输出保存为PDF", action="store_true")
        
        args = parser.parse_args()
        process_video(args.video_path, args.savepdf)
        
    except KeyboardInterrupt:
        print("\n用户中断进程。")
    except Exception as e:
        print(f"致命错误: {str(e)}")
    finally:
        print("脚本执行完成。")
