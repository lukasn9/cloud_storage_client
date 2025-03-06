import os
import cv2
import numpy as np
from .clear_terminal import clear_terminal

from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_service():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    client_secret_path = os.path.join(script_dir, "..", "client_secret.json")

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)

class YouTubeAPI:
    def __init__(self, youtube):
        self.youtube = youtube
        
    def upload_video(self, file_path, title, description, category_id, privacy_status='private'):
        print(f"Attempting to upload file at: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }

        media = MediaFileUpload(file_path, resumable=True)

        request = self.youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )

        response = request.execute()
        return response

def encode():
    clear_terminal()
    file_path = input("Enter the path of the file: ")
    youtube = get_youtube_service()
    
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    clear_terminal()

    if not os.path.exists(file_path):
        print("Error: File not found.")
        return
    
    file_extension = os.path.splitext(file_path)[1].lower()[1:]
    
    extension_binary = ''.join(format(ord(char), '08b') for char in file_extension)
    
    remaining_bits = 32 - len(extension_binary)
    if remaining_bits > 0:
        extra_chars_needed = (remaining_bits + 7) // 8
        padding = '#' * extra_chars_needed
        padding_binary = ''.join(format(ord(char), '08b') for char in padding)
        padding_binary = padding_binary[:remaining_bits]
        extension_binary += padding_binary
    else:
        extension_binary = extension_binary[:32]
    
    with open(file_path, "rb") as file:
        data = file.read()

    data_string = ''.join(format(byte, '08b') for byte in data)
    
    data_string += extension_binary

    width, height = 2560, 1440
    ppf = width * height

    total_frames = (len(data_string) + ppf - 1) // ppf

    clear_terminal()
    print("Encoding...")
    print(f"File extension: {file_extension}")
    print(f"Extension binary: {extension_binary} ({len(extension_binary)} bits)")
    print(f"Binary length: {len(data_string)} bits (including 32 bits for extension)")
    print(f"Total frames: {total_frames}")
    
    output_filename = f"{name_without_ext}.mp4"
    output_path = os.path.join("Data/outputs", output_filename)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 60
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame_idx in range(total_frames):
        frame = np.ones((height, width), dtype=np.uint8) * 255

        start_idx = frame_idx * ppf
        end_idx = min(start_idx + ppf, len(data_string))
        frame_data = data_string[start_idx:end_idx]

        for i, bit in enumerate(frame_data):
            row = i // width
            col = i % width

            if bit == "1":
                frame[row, col] = 0

        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        video_writer.write(bgr_frame)

        print(f"Progress: {frame_idx + 1}/{total_frames} frames ({(frame_idx + 1) * 100 // total_frames}%)")

    video_writer.release()
    print("Encoding complete.")

    absolute_output_path = os.path.abspath(output_path)
    print(f"Video saved to: {absolute_output_path}")

    try:
        yt_api = YouTubeAPI(youtube)
        upload = yt_api.upload_video(
            absolute_output_path, 
            name_without_ext, 
            file_extension,
            28  
        )
        print("Video upload complete.")
    except Exception as e:
        print(f"Error during upload: {str(e)}")

    print()
    inp = input("Press Enter to continue: ")