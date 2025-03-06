import os
import cv2
from .clear_terminal import clear_terminal

def decode():
    clear_terminal()

    video_path = input("Enter the path of the video: ")
    
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print("Error: Video not found.")
        return
    
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ppf = width * height

    clear_terminal()
    print("Decoding...")
    print(f"Total frames: {frame_count}")

    data = []

    for frame_idx in range(frame_count):
        success, frame = video.read()
        if not success:
            print("Error: Frame not found.")
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        _, binary_frame = cv2.threshold(gray_frame, 127, 1, cv2.THRESH_BINARY_INV)

        for row in range(height):
            for col in range(width):
                if row * width + col < width * height:
                    data.append(str(binary_frame[row, col]))

        print(f"Progress: {frame_idx + 1}/{frame_count} frames ({(frame_idx + 1) * 100 // frame_count}%)")
    video.release()

    data_string = ''.join(data)
    
    total_bits_needed = frame_count * ppf
    
    if len(data_string) > total_bits_needed:
        data_string = data_string[:total_bits_needed]
    
    last_one_index = data_string.rfind('1')
    if last_one_index == -1:
        print("Error: No valid data found in the video.")
        return
    
    data_string = data_string[:last_one_index + 1]
    
    if len(data_string) >= 32:
        extension_bits = data_string[-32:]
        data_string = data_string[:-32]
        
        extension = ""
        for i in range(0, 32, 8):
            if i + 8 <= len(extension_bits):
                char_bits = extension_bits[i:i+8]
                try:
                    char_value = int(char_bits, 2)
                    if char_value > 0:
                        extension += chr(char_value)
                except ValueError:
                    pass
        
        hash_padding_count = 0
        while extension.endswith('#') and hash_padding_count < 3:
            extension = extension[:-1]
            hash_padding_count += 1
            
    else:
        extension = ""
    
    if extension:
        extension = "." + extension
    
    print(f"Detected file extension: {extension}")
    
    byte_chunks = [data_string[i:i+8] for i in range(0, len(data_string), 8)]

    if len(byte_chunks[-1]) < 8:
        byte_chunks.pop()

    decoded_bytes = bytearray()
    for chunk in byte_chunks:
        try:
            decoded_bytes.append(int(chunk, 2))
        except ValueError:
            continue

    output_name = input("Enter the name for the output file (without extension): ")
    output_path = f"outputs/{output_name}{extension}"
    
    os.makedirs("outputs", exist_ok=True)
    
    with open(output_path, "wb") as file:
        file.write(decoded_bytes)

    print(f"Decoding complete. File saved as {output_path}")

    print()
    inp = input("Press Enter to continue: ")