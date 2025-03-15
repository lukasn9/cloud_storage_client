import os
import cv2
import sys
import yt_dlp
import re
import numpy as np
import concurrent.futures
from time import time
from .clear_terminal import clear_terminal

cur_frame = 1

def process_frame_group(frames, grid_height, grid_width, block_size):
    accumulated_frame = np.zeros((grid_height, grid_width), dtype=np.float32)
    for frame in frames:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for row in range(grid_height):
            for col in range(grid_width):
                y, x = row * block_size, col * block_size
                block = gray_frame[y:y+block_size, x:x+block_size]
                accumulated_frame[row, col] += np.mean(block)
    averaged_frame = accumulated_frame / len(frames)
    _, binary_frame = cv2.threshold(averaged_frame, 127.5, 1, cv2.THRESH_BINARY_INV)
    print(f"Processing frame {cur_frame}")
    cur_frame += 1
    return binary_frame.astype(np.uint8).flatten().astype(str).tolist()

def decode():
    clear_terminal()
    inp = str(input("Decode from an URL/Path (1/2/Exit): "))
    
    video_path = None
    downloaded_file = None

    clear_terminal()
    if inp == "1":
        video_url = input("Enter the URL of the video: ")
        os.makedirs("Data/temp", exist_ok=True)
        
        ydl_opts = {
            "format": "best",
            "outtmpl": "Data/temp/%(title)s.%(ext)s",
            "quiet": False,
            "no_warnings": False
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', 'video')
            ext = info.get('ext', 'mp4')
            downloaded_file = f"Data/temp/{title}.{ext}"
            video_path = downloaded_file
            print(f"Downloaded video to: {video_path}")
            
    elif inp == "2":
        video_path = input("Enter the path of the video: ").strip('"')
    else:
        sys.exit(0)
    
    if not video_path or not os.path.exists(video_path):
        print(f"Error: Video file not found at path: {video_path}")
        return
    
    start = time()

    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print(f"Error: OpenCV could not open video file: {video_path}")
        return
    
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width, height = int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    block_size, frames_per_data_frame = 5, 5
    grid_width, grid_height = width // block_size, height // block_size
    total_data_frames = frame_count // frames_per_data_frame

    print(f"Decoding {total_data_frames} data frames from {frame_count} video frames.")
    
    data = []
    frame_batches = []
    for _ in range(total_data_frames):
        frames = []
        for _ in range(frames_per_data_frame):
            success, frame = video.read()
            if not success:
                break
            frames.append(frame)
        if frames:
            frame_batches.append(frames)
    
    video.release()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(process_frame_group, frame_batches, 
                               [grid_height] * len(frame_batches), 
                               [grid_width] * len(frame_batches), 
                               [block_size] * len(frame_batches))
        for result in results:
            data.extend(result)
    
    print("Frame processing complete.")
    
    data_string = ''.join(data)
    print(f"Total bits collected: {len(data_string)}")
    
    last_one_index = data_string.rfind('1')
    if last_one_index == -1:
        print("Error: No valid data found in the video.")
        return
    
    data_string = data_string[:last_one_index + 1]
    extension_bits, extension = data_string[-48:], ""
    data_string = data_string[:-48]
    
    for i in range(0, 48, 8):
        try:
            char_value = int(extension_bits[i:i+8], 2)
            if 32 <= char_value <= 126:
                extension += chr(char_value)
        except ValueError:
            continue
    
    extension = re.sub(r'[^a-zA-Z0-9.]', '', extension).rstrip('#')
    extension = f".{extension}" if extension else ".txt"
    print(f"Detected file extension: {extension}")
    
    byte_chunks = [data_string[i:i+8] for i in range(0, len(data_string), 8) if len(data_string[i:i+8]) == 8]
    decoded_bytes = bytearray(int(chunk, 2) for chunk in byte_chunks)
    
    end = time()
    print(f"Decoding took {round(end - start, 2)} seconds.")

    os.makedirs("Data/outputs/files", exist_ok=True)
    output_name = input("Enter the name for the output file (without extension): ")
    output_path = f"Data/outputs/files/{output_name}{extension}"
    
    try:
        with open(output_path, "wb") as file:
            file.write(decoded_bytes)
        print(f"Decoding complete. File saved as {output_path}")
    except OSError:
        output_path = f"Data/outputs/{output_name}.bin"
        with open(output_path, "wb") as file:
            file.write(decoded_bytes)
        print(f"Error saving with detected extension. File saved as {output_path}")
    
    if downloaded_file and os.path.exists(downloaded_file):
        os.remove(downloaded_file)
    
    input("Press Enter to continue: ")