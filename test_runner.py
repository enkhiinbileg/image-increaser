import os
import sys
import tkinter as tk
from main import WebtoonProcessorApp

# Create Tkinter root but don't call mainloop
root = tk.Tk()
app = WebtoonProcessorApp(root)

# Set directories
app.input_dir.set(os.path.abspath("test_input"))
app.output_dir.set(os.path.abspath("test_output"))
app.slice_mode.set("height")
app.slice_height.set("1500")

# Run scanning
app.scan_input_directory()
print(f"Detected chapters: {len(app.detected_chapters)}")

# Execute processing directly on the main thread (synchronously)
for chapter in app.detected_chapters:
    name = chapter["name"]
    path = chapter["path"]
    images = chapter["images"]
    out_dir = os.path.join("test_output", name)
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Processing chapter {name}...")
    success = app.process_single_chapter(name, path, images, out_dir)
    print(f"Chapter {name} success: {success}")

print("\n--- Output Files Check ---")
if os.path.exists("test_output"):
    for ch in os.listdir("test_output"):
        ch_path = os.path.join("test_output", ch)
        if os.path.isdir(ch_path):
            print(f"Folder: {ch}")
            for f in os.listdir(ch_path):
                f_path = os.path.join(ch_path, f)
                print(f"  {f} - Size: {os.path.getsize(f_path)} bytes")
else:
    print("test_output does not exist!")
