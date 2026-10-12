import os
import re
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
from PIL import Image

# Disable Pillow decompression bomb warning for large webtoon images
Image.MAX_IMAGE_PIXELS = None

# Supported image extensions
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff')

def natural_sort_key(s):
    """Sort strings containing numbers in human order (e.g. 2.jpg before 10.jpg)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

class WebtoonProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Webtoon Image Merger & Slicer")
        self.root.geometry("900x640")
        self.root.minsize(800, 600)
        
        # Colors & Theme (Modern Dark Theme)
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.success_color = "#a6e3a1"
        self.warning_color = "#f9e2af"
        self.card_bg = "#252538"
        self.button_bg = "#303046"
        self.button_hover = "#45475a"
        self.text_bg = "#11111b"

        self.root.configure(bg=self.bg_color)
        
        # State variables
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.slice_mode = tk.StringVar(value="height")  # "height" or "count"
        self.slice_height = tk.StringVar(value="2000")
        self.slice_count = tk.StringVar(value="5")
        self.scale_mode = tk.StringVar(value="first")  # "first", "max", "none"
        self.output_format = tk.StringVar(value="JPEG")  # "JPEG", "PNG", "WEBP"
        self.jpeg_quality = tk.IntVar(value=90)
        
        self.detected_chapters = []  # List of dicts: {"name": str, "path": str, "images": list}
        self.is_processing = False
        self.stop_requested = False

        self.setup_styles()
        self.build_ui()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure Ttk widgets global styles
        style.configure(".", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
        style.configure("TEntry", fieldbackground=self.card_bg, foreground=self.fg_color, insertcolor=self.fg_color, borderwidth=1)
        style.configure("TProgressbar", thickness=18)
        
        # LabelFrames
        style.configure("TLabelframe", background=self.bg_color, foreground=self.accent_color, bordercolor=self.button_bg)
        style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.accent_color, font=("Segoe UI", 10, "bold"))
        
        # Custom styles
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground=self.accent_color)
        style.configure("Title.TLabel", font=("Segoe UI", 11, "bold"))
        
    def build_ui(self):
        # Top Header
        header_frame = tk.Frame(self.root, bg=self.bg_color, pady=10)
        header_frame.pack(fill="x", padx=20)
        
        title_label = ttk.Label(header_frame, text="Webtoon Image Merger & Slicer", style="Header.TLabel")
        title_label.pack(side="left")
        
        subtitle = ttk.Label(header_frame, text="Batch Chapter Processor", foreground="#a6adc8")
        subtitle.pack(side="left", padx=15, ipady=5)

        # Main Layout: Two columns (Left: config and settings, Right: Chapter list & logs)
        main_paned = tk.PanedWindow(self.root, orient="horizontal", bg=self.bg_color, bd=0, sashwidth=4)
        main_paned.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left Panel (Settings)
        left_panel = tk.Frame(main_paned, bg=self.bg_color)
        main_paned.add(left_panel, width=380)
        
        # Right Panel (List and Logs)
        right_panel = tk.Frame(main_paned, bg=self.bg_color)
        main_paned.add(right_panel)

        # --- LEFT PANEL: Folders & Settings ---
        
        # 1. Folders Section
        folder_lf = ttk.LabelFrame(left_panel, text=" Хавтасны Тохиргоо (Folders) ")
        folder_lf.pack(fill="x", pady=(0, 5), ipady=3)
        
        # Input Path
        ttk.Label(folder_lf, text="Оруулах хавтас (Input Folder):").pack(anchor="w", padx=10, pady=(3, 1))
        input_frame = tk.Frame(folder_lf, bg=self.bg_color)
        input_frame.pack(fill="x", padx=10, pady=2)
        
        self.input_entry = tk.Entry(input_frame, textvariable=self.input_dir, bg=self.card_bg, fg=self.fg_color, 
                                    insertbackground=self.fg_color, bd=1, relief="solid")
        self.input_entry.pack(side="left", fill="x", expand=True, ipady=3)
        input_btn = tk.Button(input_frame, text="Сонгох", command=self.browse_input, bg=self.button_bg, fg=self.fg_color, 
                              activebackground=self.button_hover, activeforeground=self.fg_color, bd=0, padx=10, relief="flat")
        input_btn.pack(side="right", padx=(5, 0))
        
        # Output Path
        ttk.Label(folder_lf, text="Гарах хавтас (Output Folder):").pack(anchor="w", padx=10, pady=(6, 1))
        output_frame = tk.Frame(folder_lf, bg=self.bg_color)
        output_frame.pack(fill="x", padx=10, pady=2)
        
        self.output_entry = tk.Entry(output_frame, textvariable=self.output_dir, bg=self.card_bg, fg=self.fg_color, 
                                     insertbackground=self.fg_color, bd=1, relief="solid")
        self.output_entry.pack(side="left", fill="x", expand=True, ipady=3)
        output_btn = tk.Button(output_frame, text="Сонгох", command=self.browse_output, bg=self.button_bg, fg=self.fg_color, 
                               activebackground=self.button_hover, activeforeground=self.fg_color, bd=0, padx=10, relief="flat")
        output_btn.pack(side="right", padx=(5, 0))

        # 4. Action Buttons (Moved up for better visibility)
        btn_frame = tk.Frame(left_panel, bg=self.bg_color)
        btn_frame.pack(fill="x", pady=8)
        
        self.start_btn = tk.Button(btn_frame, text="Эхлүүлэх (Start)", command=self.start_processing, bg=self.accent_color, fg=self.bg_color,
                                   activebackground="#74c7ec", font=("Segoe UI", 11, "bold"), bd=0, height=2, cursor="hand2")
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.stop_btn = tk.Button(btn_frame, text="Зогсоох (Stop)", command=self.stop_processing, bg="#f38ba8", fg=self.bg_color,
                                  activebackground="#f5e0dc", font=("Segoe UI", 11, "bold"), bd=0, height=2, cursor="hand2")
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
        self.stop_btn.config(state="disabled")

        # 2. Slicing Settings Section
        slice_lf = ttk.LabelFrame(left_panel, text=" Хуваах Тохиргоо (Slicing) ")
        slice_lf.pack(fill="x", pady=5, ipady=4)
        
        # Slicing Mode Radios
        mode_frame = tk.Frame(slice_lf, bg=self.bg_color)
        mode_frame.pack(fill="x", padx=10, pady=5)
        
        self.height_radio = tk.Radiobutton(mode_frame, text="Өндрөөр хэрчих (Height)", variable=self.slice_mode, value="height",
                                           bg=self.bg_color, fg=self.fg_color, selectcolor=self.bg_color,
                                           activebackground=self.bg_color, activeforeground=self.fg_color,
                                           command=self.toggle_slice_inputs)
        self.height_radio.pack(side="left", expand=True, anchor="w")
        
        self.count_radio = tk.Radiobutton(mode_frame, text="Тэнцүү тоонд хуваах (Count)", variable=self.slice_mode, value="count",
                                          bg=self.bg_color, fg=self.fg_color, selectcolor=self.bg_color,
                                          activebackground=self.bg_color, activeforeground=self.fg_color,
                                          command=self.toggle_slice_inputs)
        self.count_radio.pack(side="left", expand=True, anchor="w")
        
        # Slicing inputs
        self.inputs_frame = tk.Frame(slice_lf, bg=self.bg_color)
        self.inputs_frame.pack(fill="x", padx=10, pady=5)
        
        # Height input
        self.height_label = ttk.Label(self.inputs_frame, text="Заах өндөр (pixels):")
        self.height_label.grid(row=0, column=0, sticky="w", pady=5)
        self.height_spin = tk.Spinbox(self.inputs_frame, from_=500, to=50000, increment=500, textvariable=self.slice_height,
                                      bg=self.card_bg, fg=self.fg_color, buttonbackground=self.button_bg, bd=1, width=15)
        self.height_spin.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Count input
        self.count_label = ttk.Label(self.inputs_frame, text="Хэсгийн тоо (parts):")
        self.count_label.grid(row=1, column=0, sticky="w", pady=5)
        self.count_spin = tk.Spinbox(self.inputs_frame, from_=2, to=100, increment=1, textvariable=self.slice_count,
                                     bg=self.card_bg, fg=self.fg_color, buttonbackground=self.button_bg, bd=1, width=15)
        self.count_spin.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        self.toggle_slice_inputs()

        # 3. Image Operations Settings
        img_lf = ttk.LabelFrame(left_panel, text=" Зургийн Тохиргоо (Image Settings) ")
        img_lf.pack(fill="x", pady=5, ipady=4)
        
        # Scaling Mode
        ttk.Label(img_lf, text="Өргөнийг тааруулах (Scaling Mode):").pack(anchor="w", padx=10, pady=(5, 2))
        scale_cb = ttk.Combobox(img_lf, textvariable=self.scale_mode, state="readonly", values=["first", "max", "none"])
        scale_cb.pack(fill="x", padx=10, pady=2)
        scale_cb.set("first")  # Default to resize to first image width
        
        # Tooltip explanation
        scale_desc = ttk.Label(img_lf, font=("Segoe UI", 8), foreground="#a6adc8",
                               text="first: Эхний зургийн өргөнд бусдыг тааруулна (Зөвлөмж болгох)\nmax: Хамгийн өргөн зургийн өргөнд тааруулна\nnone: Хэмжээг өөрчлөхгүй (Зарим зураг зөрж магадгүй)")
        scale_desc.pack(anchor="w", padx=10, pady=(2, 10))

        # Format and Quality
        format_frame = tk.Frame(img_lf, bg=self.bg_color)
        format_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(format_frame, text="Формат (Format):").grid(row=0, column=0, sticky="w", pady=5)
        format_cb = ttk.Combobox(format_frame, textvariable=self.output_format, state="readonly", values=["JPEG", "PNG", "WEBP"], width=10)
        format_cb.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        format_cb.bind("<<ComboboxSelected>>", self.toggle_quality_slider)
        
        self.quality_label = ttk.Label(format_frame, text="Чанар (Quality):")
        self.quality_label.grid(row=1, column=0, sticky="w", pady=5)
        
        self.quality_slider = tk.Scale(format_frame, from_=10, to=100, orient="horizontal", variable=self.jpeg_quality,
                                       bg=self.bg_color, fg=self.fg_color, highlightbackground=self.bg_color,
                                       activebackground=self.accent_color, troughcolor=self.card_bg, bd=0)
        self.quality_slider.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

        # --- RIGHT PANEL: Chapter List & Console Logs ---
        
        # 1. Chapter List LabelFrame
        chapter_lf = ttk.LabelFrame(right_panel, text=" Дэд бүлгүүд (Detected Chapters) ")
        chapter_lf.pack(fill="both", expand=True, pady=(0, 5))
        
        # Listbox with Scrollbar
        list_frame = tk.Frame(chapter_lf, bg=self.bg_color)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical")
        list_scroll.pack(side="right", fill="y")
        
        self.chapter_listbox = tk.Listbox(list_frame, bg=self.text_bg, fg=self.fg_color, selectbackground=self.button_hover,
                                          selectforeground=self.accent_color, bd=0, yscrollcommand=list_scroll.set,
                                          font=("Segoe UI", 10), highlightthickness=0)
        self.chapter_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.config(command=self.chapter_listbox.yview)

        # Progress bars (Moved to the middle of the right panel for better visibility)
        prog_frame = tk.Frame(right_panel, bg=self.bg_color)
        prog_frame.pack(fill="x", pady=5)
        
        # Chapter Progress
        self.chap_progress_lbl = ttk.Label(prog_frame, text="Нийт явц: 0/0")
        self.chap_progress_lbl.pack(anchor="w")
        self.chap_progress = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar")
        self.chap_progress.pack(fill="x", pady=(2, 6))
        
        # Slice/Image Progress
        self.img_progress_lbl = ttk.Label(prog_frame, text="Одоогийн бүлэг: Бэлэн")
        self.img_progress_lbl.pack(anchor="w")
        self.img_progress = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar")
        self.img_progress.pack(fill="x", pady=(2, 4))

        # 2. Logs / Terminal Section
        log_lf = ttk.LabelFrame(right_panel, text=" Ажиллагааны явц (Console Logs) ")
        log_lf.pack(fill="both", expand=True, pady=(5, 0))
        
        self.log_text = ScrolledText(log_lf, bg=self.text_bg, fg=self.fg_color, bd=0, font=("Consolas", 9), insertbackground=self.fg_color)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.config(state="disabled")

    def browse_input(self):
        folder = filedialog.askdirectory(title="Оруулах зургуудын хавтасыг сонгоно уу")
        if folder:
            # Normalize path delimiters
            folder = os.path.normpath(folder)
            self.input_dir.set(folder)
            
            # Default output folder to [input_folder]_processed if output is empty
            if not self.output_dir.get():
                self.output_dir.set(folder + "_processed")
                
            self.scan_input_directory()

    def browse_output(self):
        folder = filedialog.askdirectory(title="Үр дүнг хадгалах хавтасыг сонгоно уу")
        if folder:
            self.output_dir.set(os.path.normpath(folder))

    def toggle_slice_inputs(self):
        mode = self.slice_mode.get()
        if mode == "height":
            self.height_spin.config(state="normal")
            self.count_spin.config(state="disabled")
        else:
            self.height_spin.config(state="disabled")
            self.count_spin.config(state="normal")

    def toggle_quality_slider(self, event=None):
        fmt = self.output_format.get()
        if fmt == "PNG":
            self.quality_slider.config(state="disabled")
        else:
            self.quality_slider.config(state="normal")

    def log(self, message):
        """Append log message in the console log section thread-safely."""
        def append():
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        self.root.after(0, append)

    def scan_input_directory(self):
        path = self.input_dir.get()
        if not path or not os.path.exists(path):
            return
        
        self.chapter_listbox.delete(0, tk.END)
        self.detected_chapters = []
        self.log(f"Хавтас уншиж байна: {path}")

        # Scan for subdirectories (chapters)
        subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        subdirs.sort(key=natural_sort_key)

        if subdirs:
            # Multi-chapter structure
            self.log(f"Дэд хавтаснууд (Бүлгүүд) олдлоо: {len(subdirs)}")
            for subdir in subdirs:
                sub_path = os.path.join(path, subdir)
                images = [f for f in os.listdir(sub_path) if f.lower().endswith(IMAGE_EXTENSIONS)]
                images.sort(key=natural_sort_key)
                if images:
                    self.detected_chapters.append({
                        "name": subdir,
                        "path": sub_path,
                        "images": images
                    })
                    self.chapter_listbox.insert(tk.END, f"📁 {subdir} ({len(images)} зураг)")
                else:
                    self.log(f"Анхаар: {subdir} хавтас дотор зураг олдсонгүй.")
        else:
            # Single chapter structure (images directly in root input)
            images = [f for f in os.listdir(path) if f.lower().endswith(IMAGE_EXTENSIONS)]
            images.sort(key=natural_sort_key)
            if images:
                folder_name = os.path.basename(path)
                self.detected_chapters.append({
                    "name": folder_name,
                    "path": path,
                    "images": images
                })
                self.chapter_listbox.insert(tk.END, f"📁 {folder_name} [Үндсэн хавтас] ({len(images)} зураг)")
                self.log(f"Үндсэн хавтаснаас {len(images)} зураг олдлоо.")
            else:
                self.log("Алдаа: Сонгосон хавтас дотор боловсруулах боломжтой зураг олдсонгүй.")
                messagebox.showwarning("Анхааруулга", "Боловсруулах зураг (.png, .jpg, .jpeg, .webp) олдсонгүй!")

    def start_processing(self):
        if self.is_processing:
            return
        
        input_dir = self.input_dir.get().strip()
        output_dir = self.output_dir.get().strip()
        
        if not input_dir or not os.path.exists(input_dir):
            messagebox.showerror("Алдаа", "Оруулах хавтсыг зөв сонгоно уу!")
            return
        
        if not output_dir:
            messagebox.showerror("Алдаа", "Гаралтын хавтсыг зааж өгнө үү!")
            return

        if not self.detected_chapters:
            self.scan_input_directory()
            if not self.detected_chapters:
                messagebox.showerror("Алдаа", "Боловсруулах бүлэг/зураг олдсонгүй!")
                return
            
        # Validate slicing parameters
        if self.slice_mode.get() == "height":
            try:
                h = int(self.slice_height.get())
                if h < 100: raise ValueError
            except ValueError:
                messagebox.showerror("Алдаа", "Хэрчих өндрийг зөв бүхэл тоо оруулна уу (Хамгийн багадаа 100px)!")
                return
        else:
            try:
                c = int(self.slice_count.get())
                if c < 2: raise ValueError
            except ValueError:
                messagebox.showerror("Алдаа", "Хуваах хэсгийн тоог зөв оруулна уу (Хамгийн багадаа 2)!")
                return

        # Start background processing thread
        self.is_processing = True
        self.stop_requested = False
        
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.input_entry.config(state="disabled")
        self.output_entry.config(state="disabled")
        
        threading.Thread(target=self.process_batches, daemon=True).start()

    def stop_processing(self):
        if self.is_processing:
            self.stop_requested = True
            self.log("Хэрэглэгч зогсоох хүсэлт илгээлээ. Түр хүлээнэ үү...")
            self.stop_btn.config(state="disabled")

    def process_batches(self):
        out_root = self.output_dir.get()
        total_chapters = len(self.detected_chapters)
        
        self.log(f"--- БАГЦ АЖИЛЛАГАА ЭХЭЛЛЭЭ (Нийт {total_chapters} бүлэг) ---")
        
        # Reset progress bar
        self.root.after(0, lambda: self.chap_progress.configure(maximum=total_chapters, value=0))
        
        try:
            for idx, chapter in enumerate(self.detected_chapters):
                if self.stop_requested:
                    self.log("Үйл ажиллагааг хэрэглэгчийн хүсэлтээр зогсоолоо.")
                    break
                
                chap_name = chapter["name"]
                chap_path = chapter["path"]
                images_list = chapter["images"]
                
                self.log(f"\n[{idx+1}/{total_chapters}] '{chap_name}' боловсруулж байна...")
                self.root.after(0, lambda label_text=f"Нийт явц: {idx}/{total_chapters}", c=idx: [
                    self.chap_progress_lbl.config(text=label_text),
                    self.chap_progress.configure(value=c)
                ])
                
                # Create chapter output directory
                chap_out_dir = os.path.join(out_root, chap_name)
                os.makedirs(chap_out_dir, exist_ok=True)
                
                success = self.process_single_chapter(chap_name, chap_path, images_list, chap_out_dir)
                if not success:
                    if self.stop_requested:
                        break
                    self.log(f"Алдаа: '{chap_name}' бүлгийг боловсруулах үед алдаа гарлаа. Алгасаж байна.")
            
            if not self.stop_requested:
                self.root.after(0, lambda: [
                    self.chap_progress_lbl.config(text=f"Нийт явц: {total_chapters}/{total_chapters}"),
                    self.chap_progress.configure(value=total_chapters),
                    self.img_progress_lbl.config(text="Бүх ажил амжилттай дууслаа!"),
                    self.img_progress.configure(value=100)
                ])
                self.log(f"\n--- БҮХ АЖИЛЛАГАА АМЖИЛТТАЙ ДУУСЛАА --- \nҮр дүн хадгалагдсан газар: {out_root}")
                messagebox.showinfo("Амжилттай", f"Бүх бүлгүүдийг амжилттай боловсруулж дууслаа!\nХавтас: {out_root}")
                
        except Exception as e:
            self.log(f"\nСистемийн ноцтой алдаа: {str(e)}")
            messagebox.showerror("Алдаа", f"Ажиллагааны явцад ноцтой алдаа гарлаа:\n{str(e)}")
        finally:
            self.is_processing = False
            self.root.after(0, self.reset_ui_state)

    def process_single_chapter(self, chap_name, chap_path, image_names, out_dir):
        total_images = len(image_names)
        self.log(f"'{chap_name}': {total_images} зураг ачаалж байна...")
        
        # Load and collect size information
        loaded_images = []
        target_width = None
        
        self.root.after(0, lambda: [
            self.img_progress_lbl.config(text=f"Уншиж байна: 0/{total_images}"),
            self.img_progress.configure(maximum=total_images, value=0)
        ])

        try:
            # 1. Open and resize images to align widths
            scale_m = self.scale_mode.get()
            
            for i, img_name in enumerate(image_names):
                if self.stop_requested:
                    return False
                
                img_p = os.path.join(chap_path, img_name)
                try:
                    img = Image.open(img_p)
                    # Convert to RGB (to prevent issues with RGBA/GIF palettes in JPEGs)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    loaded_images.append(img)
                except Exception as ex:
                    self.log(f"Зураг нээх алдаа: {img_name}. Алдаа: {str(ex)}")
                    continue
                
                self.root.after(0, lambda val=i+1: [
                    self.img_progress_lbl.config(text=f"Уншиж байна: {val}/{total_images}"),
                    self.img_progress.configure(value=val)
                ])

            if not loaded_images:
                self.log(f"Алдаа: '{chap_name}' дотор унших боломжтой зураг байсангүй.")
                return False

            # Determine target width
            widths = [img.width for img in loaded_images]
            if scale_m == "first":
                target_width = loaded_images[0].width
            elif scale_m == "max":
                target_width = max(widths)
            else:
                # Keep original widths (none), we'll align them centered, but standard is first image's width
                target_width = loaded_images[0].width 

            self.log(f"Нэгтгэх өргөн (Target Width): {target_width}px")

            # 2. Resize and calculate total height
            resized_images = []
            total_height = 0
            
            for i, img in enumerate(loaded_images):
                if self.stop_requested:
                    return False
                
                if img.width != target_width:
                    # Scale keeping aspect ratio
                    scale_factor = target_width / img.width
                    new_height = int(img.height * scale_factor)
                    if new_height == 0: new_height = 1
                    # High quality resampling
                    img_resized = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
                    resized_images.append(img_resized)
                    total_height += new_height
                else:
                    resized_images.append(img)
                    total_height += img.height

            self.log(f"Нийт босоо өндөр (Total Merged Height): {total_height}px")

            # 3. Create canvas and paste images
            self.root.after(0, lambda: self.img_progress_lbl.config(text="Зургуудыг нэгтгэж байна..."))
            merged_image = Image.new('RGB', (target_width, total_height), (255, 255, 255))
            
            current_y = 0
            for img in resized_images:
                if self.stop_requested:
                    return False
                merged_image.paste(img, (0, current_y))
                current_y += img.height
            
            # Free memory of source images
            for img in loaded_images:
                img.close()
            for img in resized_images:
                if img is not merged_image:
                    img.close()

            # 4. Determine Slicing boundaries
            self.root.after(0, lambda: self.img_progress_lbl.config(text="Зургийг хэрчиж байна..."))
            slices = []
            
            mode = self.slice_mode.get()
            if mode == "height":
                s_height = int(self.slice_height.get())
                # Slice by height
                num_slices = (total_height + s_height - 1) // s_height
                for s_idx in range(num_slices):
                    y_start = s_idx * s_height
                    y_end = min((s_idx + 1) * s_height, total_height)
                    slices.append((y_start, y_end))
            else:
                s_count = int(self.slice_count.get())
                # Slice into equal parts
                slice_height_val = total_height // s_count
                for s_idx in range(s_count):
                    y_start = s_idx * slice_height_val
                    y_end = total_height if s_idx == s_count - 1 else (s_idx + 1) * slice_height_val
                    slices.append((y_start, y_end))

            total_slices = len(slices)
            self.log(f"Хуваагдах хэсгийн тоо: {total_slices}")
            
            self.root.after(0, lambda: [
                self.img_progress_lbl.config(text=f"Хадгалж байна: 0/{total_slices}"),
                self.img_progress.configure(maximum=total_slices, value=0)
            ])

            # 5. Crop and Save slices
            fmt = self.output_format.get()
            ext = ".jpg" if fmt == "JPEG" else ".png" if fmt == "PNG" else ".webp"
            save_format = "JPEG" if fmt == "JPEG" else "PNG" if fmt == "PNG" else "WEBP"
            quality = self.jpeg_quality.get()
            
            for s_idx, (y_start, y_end) in enumerate(slices):
                if self.stop_requested:
                    return False
                
                # Crop slice
                slice_img = merged_image.crop((0, y_start, target_width, y_end))
                
                # Save slice
                slice_name = f"{s_idx + 1:03d}{ext}"
                slice_path = os.path.join(out_dir, slice_name)
                
                if save_format == "PNG":
                    slice_img.save(slice_path, format=save_format)
                else:
                    slice_img.save(slice_path, format=save_format, quality=quality)
                
                slice_img.close()
                
                self.root.after(0, lambda val=s_idx+1: [
                    self.img_progress_lbl.config(text=f"Хадгалж байна: {val}/{total_slices}"),
                    self.img_progress.configure(value=val)
                ])

            merged_image.close()
            self.log(f"Амжилттай: '{chap_name}' бүлгийг {total_slices} зураг болгон хувааж хадгаллаа.")
            return True

        except Exception as e:
            self.log(f"Алдаа гарлаа: {str(e)}")
            return False

    def reset_ui_state(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.input_entry.config(state="normal")
        self.output_entry.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = WebtoonProcessorApp(root)
    
    # If folder passed in cmd arguments, load it automatically
    if len(sys.argv) > 1:
        passed_path = sys.argv[1]
        if os.path.exists(passed_path):
            app.input_dir.set(os.path.normpath(passed_path))
            app.output_dir.set(os.path.normpath(passed_path + "_processed"))
            app.scan_input_directory()
            
    root.mainloop()
