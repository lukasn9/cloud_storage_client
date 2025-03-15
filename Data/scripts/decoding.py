import os
import cv2
import sys
import yt_dlp
import re
import numpy as np
import concurrent.futures
from tabulate import tabulate
from time import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from .clear_terminal import clear_terminal

cur_frame = 1

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

def authenticate_youtube():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.dirname(script_dir)
    client_secret_path = os.path.join(data_dir, "client_secret.json")
    
    if not os.path.exists(client_secret_path):
        sys.exit(1)
        
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)

def get_unlisted_videos(youtube):
    video_list = []
    
    channels_response = youtube.channels().list(part="contentDetails", mine=True).execute()
    if "items" not in channels_response:
        print("No YouTube channel found.")
        return []

    uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    next_page_token = None
    while True:
        playlist_response = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        video_ids = [item["snippet"]["resourceId"]["videoId"] for item in playlist_response["items"]]

        video_response = youtube.videos().list(
            part="status,snippet",
            id=",".join(video_ids)
        ).execute()

        for video in video_response["items"]:
            if video["status"]["privacyStatus"] == "unlisted":
                title = video["snippet"]["title"]
                video_id = video["id"]
                url = f"https://www.youtube.com/watch?v={video_id}"
                description = video["snippet"].get("description", "No description")
                
                display_info = [title, description]
                complete_info = [title, url, description]
                
                if len(description) <= 6:
                    video_list.append(complete_info)

        next_page_token = playlist_response.get("nextPageToken")
        if not next_page_token:
            break

    return video_list

def process_frame_group(frames, grid_height, grid_width, block_size):
    global cur_frame
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
    
    inp = str(input("Decode from YouTube/path (1/2): "))
    
    video_path = None
    downloaded_file = None

    clear_terminal()
    if inp == "1":
        try:
            youtube = authenticate_youtube()
            video_list = get_unlisted_videos(youtube)

            if not video_list:
                print("No unlisted videos found.")
                return
            
            display_list = [[item[0], item[2]] for item in video_list]
            
            print(tabulate(display_list, headers=["Title", "Description"], tablefmt="fancy_grid"))
        
            index = int(input(f"Enter the index of the video (1-{len(video_list)}): ")) - 1
            clear_terminal()
            if index < 0 or index >= len(video_list):
                print("Invalid selection.")
                return
            
            video_url = video_list[index][1]
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
        
        except ValueError:
            print("Invalid input. Exiting.")
            return

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
        sys.exit(1)
    
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
    extension = f".{extension}" if extension else ".bin"
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
        output_path = f"Data/outputs/files/{output_name}.bin"
        with open(output_path, "wb") as file:
            file.write(decoded_bytes)
        print(f"Error saving with detected extension. File saved as {output_path}")
    
    if downloaded_file and os.path.exists(downloaded_file):
        os.remove(downloaded_file)
    
    print()
    inp = input("Press Enter to continue: ")