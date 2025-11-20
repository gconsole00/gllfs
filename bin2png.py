import io
import math
from PIL import Image

def choose_file_dimensions(raw_data):
    """
    Calculates the minimum necessary (width, height) dimensions for the image.
    """
    num_bytes = len(raw_data)
    # Each pixel stores 3 bytes (R, G, B)
    # num_pixels is calculated using float division and ceiling
    num_pixels = int(math.ceil(float(num_bytes) / 3.0)) 
    sqrt = math.sqrt(num_pixels)
    sqrt_max = int(math.ceil(sqrt))
    return sqrt_max, sqrt_max


def data_to_png_data(raw_data):
    """
    Encodes a binary file into a PNG image.
    Optimized: Uses Image.frombytes() for vectorized pixel creation.
    """
    dimensions = choose_file_dimensions(raw_data)
    
    width, height = dimensions
    target_len = width * height * 3

    # 3. Padding (Prepare the image buffer)
    num_bytes = len(raw_data)
    padding_needed = target_len - num_bytes
    
    # Pad with zero bytes ('\x00') to match the required size for the RGB image
    padded_data = raw_data + b'\x00' * padding_needed
    img = Image.frombytes('RGB', (width, height), padded_data)
    # 5. Save Image to In-Memory Buffer
    png_buffer = io.BytesIO()
    img.save(png_buffer, format="PNG")
    return png_buffer.getvalue()

def png_data_to_data(data, og_length):
    """
    Decodes a PNG image back into a binary file.
    Optimized: Uses Image.tobytes() for vectorized pixel retrieval.
    """
    img = Image.open(io.BytesIO(data))
    rgb_im = img.convert('RGB')
    raw_data = rgb_im.tobytes()
    data_to_write = raw_data[:og_length]
    return data_to_write
