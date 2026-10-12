import os
from PIL import Image, ImageDraw

def create_test_images():
    base_dir = "test_input"
    chapters = {
        "Chapter 01": [
            ("001.jpg", (800, 1000), (255, 100, 100)),  # Reddish
            ("002.jpg", (800, 1000), (100, 255, 100)),  # Greenish
            ("003.jpg", (600, 800), (100, 100, 255)),   # Blueish, different width!
        ],
        "Chapter 02": [
            ("001.jpg", (800, 1200), (255, 255, 100)),  # Yellowish
            ("002.jpg", (800, 1200), (100, 255, 255)),  # Cyanish
        ]
    }
    
    for ch_name, imgs in chapters.items():
        ch_dir = os.path.join(base_dir, ch_name)
        os.makedirs(ch_dir, exist_ok=True)
        for name, size, color in imgs:
            img = Image.new("RGB", size, color)
            # Draw simple text
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), f"{ch_name} - {name}", fill=(0, 0, 0))
            img.save(os.path.join(ch_dir, name))
            print(f"Created {os.path.join(ch_dir, name)} size={size}")

if __name__ == "__main__":
    create_test_images()
