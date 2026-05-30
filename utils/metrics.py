import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr

def calculate_metrics(img1_path, img2_path):
    """
    Calculates SSIM and PSNR between two images.
    Greyscale conversion is used to match medical imaging standards.
    """
    try:
        # Load images and convert to grayscale numpy arrays
        img1 = Image.open(img1_path).convert("L")
        img2 = Image.open(img2_path).convert("L")

        # Resize img1 to match img2 exactly (should be 256x256)
        if img1.size != img2.size:
            img1 = img1.resize(img2.size)

        img1_arr = np.array(img1)
        img2_arr = np.array(img2)

        # Calculate SSIM
        s_score = ssim(img1_arr, img2_arr)
        
        # Calculate PSNR (data_range is 255 for 8-bit images)
        p_score = psnr(img1_arr, img2_arr, data_range=255)

        return {
            "ssim": round(float(s_score), 4),
            "psnr": round(float(p_score), 2)
        }
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return {"ssim": 0.0, "psnr": 0.0}
