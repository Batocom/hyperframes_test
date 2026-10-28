#!/usr/bin/env python3
"""Remove backgrounds from fetched images using rembg"""
import os
import sys
from pathlib import Path

# Add image_editor to path for bg_service
sys.path.insert(0, r"C:\Users\user\image_editor")
from bg_service import remove_bg, available
from PIL import Image

IMAGE_DIR = r"C:\Users\user\agent-ready-under-the-hood\assets\images"
OUTPUT_DIR = r"C:\Users\user\agent-ready-under-the-hood\assets\images-nobg"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Images that need background removal (foreground elements)
IMAGES_TO_PROCESS = [
    "gear-mechanism.jpg",
    "checklist.jpg",
    "lego-blocks.jpg",
    "doorway-passageway.jpg",
    "growth-chart.jpg",
    "organized-files.jpg",
    "fractal-pattern.jpg",
    "hundred-x.jpg",
    "success-celebration.jpg",
]

def remove_background(filename):
    """Remove background from a single image"""
    input_path = os.path.join(IMAGE_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename.replace('.jpg', '.png'))
    
    if os.path.exists(output_path):
        print(f"  [SKIP] {filename} already processed")
        return True
    
    if not os.path.exists(input_path):
        print(f"  [ERROR] {filename} not found")
        return False
    
    try:
        img = Image.open(input_path)
        result = remove_bg(img)
        result.save(output_path, 'PNG')
        print(f"  [OK] {filename} -> {filename.replace('.jpg', '.png')}")
        return True
    except Exception as e:
        print(f"  [ERROR] {filename}: {e}")
        return False

if __name__ == "__main__":
    if not available():
        print("ERROR: rembg not installed. Run: pip install rembg onnxruntime")
        sys.exit(1)
    
    print("Removing backgrounds from images...")
    success = 0
    for filename in IMAGES_TO_PROCESS:
        if remove_background(filename):
            success += 1
    print(f"\nDone: {success}/{len(IMAGES_TO_PROCESS)} backgrounds removed")
