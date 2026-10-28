#!/usr/bin/env python3
"""Fetch images from Pexels API for Under the Hood section visuals"""
import json
import os
import subprocess
import sys

API_KEY = "V4YU7sSIYfFbBrGJ70fvE0vQppXITHKScJZ8XVDHqSbOWf7opaTcNqMt"
OUTPUT_DIR = r"C:\Users\user\agent-ready-under-the-hood\assets\images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Search queries mapped to filenames - each scene needs visual concepts
IMAGES = {
    # Scene 1: Intro - "Under the Hood" concept
    "engine-hood.jpg": "car engine hood open mechanical",
    "gear-mechanism.jpg": "gear mechanism machinery closeup",
    
    # Scene 2: 40 Rules - Rule concept
    "rule-book.jpg": "rule book guidelines documentation",
    "checklist.jpg": "checklist items completed",
    
    # Scene 3: Four Goals - Architecture concept
    "architecture Blueprint.jpg": "architecture blueprint technical drawing",
    "building-foundation.jpg": "building foundation construction",
    
    # Scene 4: Predictable - Consistency concept
    "consistent-output.jpg": "consistent production line factory",
    "same-result.jpg": "identical products整齐排列",
    
    # Scene 5: Modular - Components concept
    "modular-components.jpg": "modular components拼装",
    "lego-blocks.jpg": "lego blocks connected",
    "doorway-passageway.jpg": "doorway passage connection",
    
    # Scene 6: Scalable - Growth concept
    "database-logging.jpg": "database server logging",
    "growth-chart.jpg": "growth chart upward trend",
    "scalable-system.jpg": "scalable cloud system",
    
    # Scene 7: Consistent - Standard concept
    "file-header.jpg": "document header template",
    "standard-format.jpg": "standardized format template",
    "organized-files.jpg": "organized files folders",
    
    # Scene 8: Same Pattern - Pattern concept
    "repeating-pattern.jpg": "repeating pattern design",
    "fractal-pattern.jpg": "fractal pattern mathematical",
    "template-reuse.jpg": "template reuse copy",
    
    # Scene 9: Worth It - ROI concept
    "roi-return.jpg": "return on investment growth",
    "hundred-x.jpg": "hundred times multiplier",
    "success-celebration.jpg": "success celebration achievement",
    
    # Background images for visual richness
    "dark-tech-bg.jpg": "dark technology background abstract",
    "code-screen.jpg": "code screen programming dark",
    "server-room.jpg": "server room data center",
}

def fetch_image(query, filename):
    """Fetch image from Pexels using PowerShell"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
        print(f"  [SKIP] {filename} already exists")
        return True
    
    # Search Pexels
    search_url = f"https://api.pexels.com/v1/search?query={query.replace(' ', '+')}&per_page=1"
    ps_cmd = f'''
    $headers = @{{ "Authorization" = "{API_KEY}" }}
    $response = Invoke-RestMethod -Uri "{search_url}" -Headers $headers
    $response.photos[0].src.large
    '''
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15
        )
        image_url = result.stdout.strip()
        if not image_url:
            print(f"  [ERROR] No URL for {filename}")
            return False
        
        # Download image
        dl_cmd = f'Invoke-WebRequest -Uri "{image_url}" -OutFile "{filepath}"'
        subprocess.run(["powershell", "-Command", dl_cmd], timeout=30)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            print(f"  [OK] {filename} ({os.path.getsize(filepath)} bytes)")
            return True
        else:
            print(f"  [ERROR] Download failed for {filename}")
            return False
    except Exception as e:
        print(f"  [ERROR] {filename}: {e}")
        return False

if __name__ == "__main__":
    print("Fetching images from Pexels for Under the Hood section...")
    success = 0
    for filename, query in IMAGES.items():
        if fetch_image(query, filename):
            success += 1
    print(f"\nDone: {success}/{len(IMAGES)} images fetched")
