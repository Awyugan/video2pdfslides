# video2pdfslides

## Description
This project converts a video presentation into a deck of PDF slides by capturing screenshots of unique frames. It uses background subtraction to detect changes in the video frames and captures screenshots when significant changes are detected.

### YouTube Demo
Watch the demo on YouTube: [video2pdfslides Demo](https://www.youtube.com/watch?v=Q0BIPYLoSBs)

## Setup
To set up the project, install the required packages using pip:
```bash
pip install -r requirements.txt
```

## Steps to Run the Code
1. Run the script with the path to the video file:
   ```bash
   python video2pdfslides.py <video_path>
   ```
2. The script will capture screenshots of unique frames and save them in the output folder.
3. Once the screenshots are captured, the program will pause, and the user is asked to manually verify the screenshots and delete any duplicate images.
4. After verifying and cleaning up the screenshots, the program will continue and create a PDF out of the remaining screenshots.

## Example
There are two sample videos available in the `./input` directory. You can test the code using these inputs:
- For a video with 4 unique slides:
  ```bash
  python video2pdfslides.py "./input/Test Video 1.mp4"
  ```
- For a video with 19 unique slides:
  ```bash
  python video2pdfslides.py "./input/Test Video 2.mp4"
  ```

## Fine-Tuning Parameters
The default parameters work well for typical video presentations. However, if the video presentation has lots of animations, the default parameters might result in duplicate or missing slides. To improve results for any video presentation, including those with animations, you can fine-tune the following parameters:
- `MIN_PERCENT`: The minimum percentage of the mask that is "foreground" to detect motion has stopped.
- `MAX_PERCENT`: The maximum percentage of the mask that is "foreground" to detect the frame is still moving.
- `FGBG_HISTORY`: The number of frames in the background object.

Descriptions of these variables can be found in the code comments.

## Developer Contact Info
For any questions or feedback, please contact:
- Awyugan: awyugan@gmail.com