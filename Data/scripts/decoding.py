import os
import cv2
import sys
import yt_dlp
import re
import numpy as np
from .clear_terminal import clear_terminal

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
        video_path = input("Enter the path of the video: ")
        video_path = video_path.strip('"')
    else:
        sys.exit(0)
    
    if not video_path or not os.path.exists(video_path):
        print(f"Error: Video file not found at path: {video_path}")
        return
    
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print(f"Error: OpenCV could not open video file: {video_path}")
        return
    
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    block_size = 5
    grid_width, grid_height = width // block_size, height // block_size
    ppf = grid_width * grid_height
    frames_per_data_frame = 5

    print("Decoding...")
    print(f"Video dimensions: {width}x{height}")
    print(f"Total video frames: {frame_count}")
    
    total_data_frames = frame_count // frames_per_data_frame
    
    print(f"Expected data frames: {total_data_frames}")

    data = []
    
    for data_frame_idx in range(total_data_frames):
        accumulated_frame = np.zeros((grid_height, grid_width), dtype=np.float32)
        
        frames_read = 0
        for _ in range(frames_per_data_frame):
            success, frame = video.read()
            if not success:
                print(f"Warning: Could not read frame, reached end of video.")
                break
                
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            for row in range(grid_height):
                for col in range(grid_width):
                    y, x = row * block_size, col * block_size
                    block = gray_frame[y:y+block_size, x:x+block_size]
                    accumulated_frame[row, col] += np.mean(block)
            
            frames_read += 1
            
        if frames_read < frames_per_data_frame:
            print(f"Warning: Incomplete frame group, expected {frames_per_data_frame} frames but got {frames_read}")
            continue
        
        averaged_frame = accumulated_frame / frames_per_data_frame
        _, binary_frame = cv2.threshold(averaged_frame, 127.5, 1, cv2.THRESH_BINARY_INV)
        
        binary_frame = binary_frame.astype(np.uint8)
        
        data.extend(binary_frame.flatten().astype(str))
        
        print(f"Progress: {data_frame_idx + 1}/{total_data_frames} data frames ({(data_frame_idx + 1) * 100 // total_data_frames}%)")
    
    video.release()
    print("Frame processing complete.")

    data_string = ''.join(data)
    print(f"Total bits collected: {len(data_string)}")
    
    last_one_index = data_string.rfind('1')
    if last_one_index == -1:
        print("Error: No valid data found in the video.")
        return

    data_string = data_string[:last_one_index + 1]
    
    extension = ""
    if len(data_string) >= 48:
        extension_bits = data_string[-48:]
        data_string = data_string[:-48]
        
        for i in range(0, 48, 8):
            char_bits = extension_bits[i:i+8]
            try:
                char_value = int(char_bits, 2)
                if 32 <= char_value <= 126:
                    extension += chr(char_value)
            except ValueError:
                continue
        
        extension = extension.rstrip('#')
    
    extension = re.sub(r'[^a-zA-Z0-9.]', '', extension)
    if not extension or len(extension) > 10:
        extension = "bin"
        extension = "." + extension
        print(f"File extension couldn't be detected, defaulting to .bin")
    else:
        extension = "." + extension
        print(f"Detected file extension: {extension}")
    
    byte_chunks = [data_string[i:i+8] for i in range(0, len(data_string), 8)]
    if len(byte_chunks) > 0 and len(byte_chunks[-1]) < 8:
        byte_chunks.pop()
    
    decoded_bytes = bytearray()
    for chunk in byte_chunks:
        try:
            decoded_bytes.append(int(chunk, 2))
        except ValueError:
            continue
    
    os.makedirs("Data/outputs/files", exist_ok=True)
    output_name = input("Enter the name for the output file (without extension): ")
    output_path = f"Data/outputs/files/{output_name}{extension}"
    
    try:
        with open(output_path, "wb") as file:
            file.write(decoded_bytes)
        print(f"Decoding complete. File saved as {output_path}")
    except OSError as e:
        safe_path = f"Data/outputs/files/{output_name}.bin"
        print(f"Error saving with detected extension: {str(e)}")
        with open(safe_path, "wb") as file:
            file.write(decoded_bytes)
        print(f"Decoding complete. File saved as {safe_path}")
    
    if downloaded_file and os.path.exists(downloaded_file):
        os.remove(downloaded_file)
    
    input("Press Enter to continue: ")