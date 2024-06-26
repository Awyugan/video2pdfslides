import os
import time
import cv2
import imutils
import shutil
import img2pdf
import glob
import argparse
from concurrent.futures import ThreadPoolExecutor
from Foundation import NSURL
from AVFoundation import AVAsset
from tqdm import tqdm

############# Define constants

OUTPUT_SLIDES_DIR = f"./output"

FRAME_RATE = 30                   # 每秒需要处理的帧数，计数越少速度越快
WARMUP = FRAME_RATE              # 初始要跳过的帧数
FGBG_HISTORY = FRAME_RATE * 15   # 背景对象中的帧数
VAR_THRESHOLD = 16               # 像素与模型之间的马哈拉诺比斯距离平方的阈值，用于确定背景模型是否很好地描述了像素。
DETECT_SHADOWS = False            # 如果为真，算法将检测阴影并标记它们。
MIN_PERCENT = 0.1                # 前景和背景之间的差异的最小百分比，以检测运动是否停止
MAX_PERCENT = 3                  # 前景和背景之间的最大百分比，以检测帧是否仍在移动
SAVEPDF = False                   # 设置为True时自动保存PDF，设置为False时不保存PDF

def get_video_size(video_path):
    try:
        url = NSURL.fileURLWithPath_(video_path)
        asset = AVAsset.assetWithURL_(url)
        video_tracks = asset.tracksWithMediaType_('video')

        if len(video_tracks) == 0:
            raise Exception("Error: No video tracks found in the video file.")

        video_track = video_tracks[0]
        natural_size = video_track.naturalSize()
        width = natural_size.width
        height = natural_size.height
        return width, height
    except Exception as e:
        print(f"AVFoundation error: {e}, falling back to OpenCV.")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f'unable to open file {video_path}')
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        cap.release()
        return int(width), int(height)

def get_frames(video_path):
    '''A function to return the frames from a video located at video_path
    this function skips frames as defined in FRAME_RATE'''
    
    # open a pointer to the video file initialize the width and height of the frame
    vs = cv2.VideoCapture(video_path)
    if not vs.isOpened():
        raise Exception(f'unable to open file {video_path}')

    total_frames = vs.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_time = 0
    frame_count = 1  # 将初始帧计数器从1开始

    # 获取视频的原始尺寸
    width, height = get_video_size(video_path)
    
    # 循环播放视频帧
    while True:
        # 从视频中抓取一帧
        vs.set(cv2.CAP_PROP_POS_MSEC, frame_time * 1000)    # 将帧移动到时间戳
        frame_time += 1/FRAME_RATE

        (_, frame) = vs.read()
        # 如果帧为 None，那么我们已经到达视频文件的末尾
        if frame is None:
            break

        # 确保帧的尺寸与视频的原始尺寸一致
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (int(width), int(height)))
        yield frame_count, frame_time, frame

        frame_count += 1  # 在循环的末尾增加帧计数器

    vs.release()

def detect_unique_screenshots(video_path, output_folder_screenshot_path):
    ''''''
    # 使用参数初始化fgbg背景对象
    fgbg = cv2.createBackgroundSubtractorMOG2(history=FGBG_HISTORY, varThreshold=VAR_THRESHOLD, detectShadows=DETECT_SHADOWS)

    captured = False
    start_time = time.time()
    (W, H) = (None, None)

    screenshoots_count = 0
    for frame_count, frame_time, frame in get_frames(video_path):
        orig = frame.copy() # clone the original frame (so we can save it later), 
        mask = fgbg.apply(frame) # apply the background subtractor

        # if the width and height are empty, grab the spatial dimensions
        (H, W) = mask.shape[:2]

        # compute the percentage of the mask that is "foreground"
        p_diff = (cv2.countNonZero(mask) / float(W * H)) * 100

        # if p_diff less than N% then motion has stopped, thus capture the frame
        if p_diff < MIN_PERCENT and not captured and frame_count > WARMUP:
            captured = True
            video_name = video_path.rsplit('/', 1)[-1].split('.')[0]
            time_str = time.strftime('%H_%M_%S', time.gmtime(frame_time))
            filename = f"{video_name}_{screenshoots_count:03d}_{time_str}.png"

            path = os.path.join(output_folder_screenshot_path, filename)
            cv2.imwrite(path, orig)
            screenshoots_count += 1

        # otherwise, either the scene is changing or we're still in warmup
        # mode so let's wait until the scene has settled or we're finished
        # building the background model
        elif captured and p_diff >= MAX_PERCENT:
            captured = False
    print(f'{screenshoots_count} screenshots Captured!')
    print(f'Time taken {time.time()-start_time}s')
    return 

def initialize_output_folder(video_path):
    '''Clean the output folder if already exists'''
    output_folder_screenshot_path = f"{OUTPUT_SLIDES_DIR}/{video_path.rsplit('/')[-1].split('.')[0]}"

    if os.path.exists(output_folder_screenshot_path):
        shutil.rmtree(output_folder_screenshot_path)

    os.makedirs(output_folder_screenshot_path, exist_ok=True)
    print('initialized output folder', output_folder_screenshot_path)
    return output_folder_screenshot_path

def convert_screenshots_to_pdf(output_folder_screenshot_path):
    output_pdf_path = f"{OUTPUT_SLIDES_DIR}/{output_folder_screenshot_path.rsplit('/')[-1]}" + '.pdf'
    print('converting images to pdf..')
    with open(output_pdf_path, "wb") as f:
        f.write(img2pdf.convert(sorted(glob.glob(f"{output_folder_screenshot_path}/*.png"))))
    print('Pdf Created!')
    print('pdf saved at', output_pdf_path)

def process_video(video_path):
    print('Processing video:', video_path)
    output_folder_screenshot_path = initialize_output_folder(video_path)
    detect_unique_screenshots(video_path, output_folder_screenshot_path)

    if SAVEPDF:
        convert_screenshots_to_pdf(output_folder_screenshot_path)
    else:
        print("PDF saving skipped as per configuration.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("video_path")
    parser.add_argument("video_path", help="path of video or folder containing videos to be converted to pdf slides", type=str)
    parser.add_argument("--savepdf", help="Set to True to save PDF, False to skip saving PDF", type=bool, default=False)
    args = parser.parse_args()
    video_path = args.video_path
    SAVEPDF = args.savepdf

    if os.path.isdir(video_path):
        video_files = [os.path.join(video_path, f) for f in os.listdir(video_path) if f.endswith(('.mp4', '.avi', '.mkv'))]
    else:
        video_files = [video_path]

    for video_file in tqdm(video_files, desc="Processing videos"):
        process_video(video_file)
