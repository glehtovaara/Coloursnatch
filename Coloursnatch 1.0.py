import tkinter as tk
from PIL import ImageGrab, ImageTk, Image
import colorsys
import os
import ctypes

VERSION = "Ver : 2.0"

class MultiMonitorSpectrometer:
    def __init__(self, root):
        self.root = root
        self.root.title(f"ColourSnatcher")
        self.root.geometry("420x800")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#f0f0f0")

        # --- WINDOWS SETTINGS ---
        try:
            # Tell Windows this app is DPI aware (Fixes blurry capture on 4K/scaled monitors)
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            myappid = f'syntax.spectrometer.{VERSION}'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except: pass

	# --- ICON ---
        try:
            import sys
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, "icon.ico")
            else:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(icon_path): 
                self.root.iconbitmap(icon_path)
        except: pass

        self.is_held = False
        self.current_hex = "#FFFFFF"
        self.saved_hexes = ["#FFFFFF"] * 16

        self.setup_menu()

        self.setup_ui()
        self.update_loop()


    def setup_ui(self):
        # Top Header
        self.create_title_header("ColourSnatcher | Ver 2.00")
        # Chips
        self.create_header("Chips (Space to Freeze)")
        self.chips_frame = tk.Frame(self.root, bg="white", relief="sunken", bd=7)
        self.chips_frame.pack(fill="x", padx=10, pady=5)
        self.chip_buttons = []
        for i in range(16):
            row, col = divmod(i, 8)
            btn = tk.Button(self.chips_frame, width=4, height=2, bg="white", relief="flat",
                            command=lambda idx=i: self.recall_chip(idx))
            btn.grid(row=row, column=col, padx=1, pady=1)
            self.chip_buttons.append(btn)

        # Active Info
        self.create_header("Active Color Info")
        self.color_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.color_frame.pack(fill="x", padx=10, pady=5)
        self.swatch = tk.Label(self.color_frame, width=12, height=6, bg="white", relief="ridge")
        self.swatch.pack(side="right", padx=5)
        
        data_fields = tk.Frame(self.color_frame, bg="#f0f0f0")
        data_fields.pack(side="left", fill="both", expand=True)
        self.quick_readout = tk.Label(data_fields, text="HEX: #FFFFFF\nRGB: 255, 255, 255", font=("Consolas", 10, "bold"), bg="#f0f0f0", justify="left")
        self.quick_readout.pack(pady=2, anchor="w")
        tk.Button(data_fields, text="Copy HEX", command=self.copy_hex).pack(fill="x")
        tk.Button(data_fields, text="Copy RGB", command=self.copy_hex).pack(fill="x")

        # Shades
        self.create_header("Shades")
        self.shade_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.shade_frame.pack(fill="x", padx=10, pady=5)
        self.shade_boxes = []
        for _ in range(7):
            s = tk.Label(self.shade_frame, width=5, height=2, relief="flat")
            s.pack(side="left", expand=True, fill="x", padx=1)
            self.shade_boxes.append(s)


        # Mixer
        self.create_header("Mixer Data")
        self.mixer_label = tk.Label(self.root, bg="white", font=("Arial", 13, "bold"), relief="sunken", bd=5, pady=10)
        self.mixer_label.pack(fill="x", padx=10, pady=5)

        # Magnifier
        self.create_header("Magnifier")
        self.canvas = tk.Canvas(self.root, width=380, height=140, bg="grey", bd=3, highlightthickness=2)
        self.canvas.pack(padx=10, pady=5)
              

        # Footer
        footer = tk.Frame(self.root, bg="#e0e0e0", pady=5)
        footer.pack(side="bottom", fill="x")
        tk.Label(footer, text="[SPACE] Freeze / Unfreeze | [CTRL+C] Copy Hex Code", bg="#e0e0e0", font=("Arial", 8, "bold")).pack()

        # Footer
        footer = tk.Frame(self.root, bg="#e0e0e0", pady=5)
        footer.pack(side="bottom", fill="x")
        tk.Label(footer, text=f"{VERSION}", bg="#e0e0e0", font=("Arial", 8, "bold")).pack()

        self.root.bind("<space>", lambda e: self.toggle_and_save())
        self.root.bind("<Control-c>", lambda e: self.copy_hex())


    def create_title_header(self, text):
        tk.Label(self.root, text=text.upper(), bg="#d8d8d8", fg="#444", anchor="w", padx=13,font=("Arial", 13, "bold")).pack(fill="x", padx=13, pady=(8, 0))

    def create_header(self, text):
        tk.Label(self.root, text=text.upper(), bg="#d8d8d8", fg="#444", anchor="w", padx=13, font=("Arial", 8, "bold")).pack(fill="x", padx=5, pady=(8, 0))

    def rgb_to_cmyk(self, r, g, b):
        if (r, g, b) == (0, 0, 0): return 0, 0, 0, 100
        c, m, y = 1 - r/255, 1 - g/255, 1 - b/255
        k = min(c, m, y)
        if k == 1: return 0, 0, 0, 100
        return int((c-k)/(1-k)*100), int((m-k)/(1-k)*100), int((y-k)/(1-k)*100), int(k*100)

    def setup_menu(self):
        menubar = tk.Menu(self.root)

        #file menu

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        #About menu

        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="About", menu=about_menu)

        self.root.config(menu=menubar)


    def show_about(self):
        from tkinter import messagebox 
        messagebox.showinfo("About", f"ColourSnatcher {VERSION}Created by GaroBam in 2026. Made with AI assistance")

    def toggle_and_save(self):
        self.is_held = not self.is_held
        self.canvas.config(highlightbackground="red" if self.is_held else "black")
        if self.is_held:
            self.saved_hexes.insert(0, self.current_hex.upper())
            self.saved_hexes.pop()
            for i, h in enumerate(self.saved_hexes): self.chip_buttons[i].config(bg=h)

    def recall_chip(self, idx):
        self.is_held = True
        self.canvas.config(highlightbackground="red")
        self.current_hex = self.saved_hexes[idx]
        rgb = tuple(int(self.current_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        self.update_ui_elements(rgb)

    def update_ui_elements(self, rgb):
        r, g, b = rgb
        self.current_hex = '#%02x%02x%02x' % rgb
        self.current_rgb = f"{r},{g},{b}"
        self.swatch.config(bg=self.current_hex)
        self.quick_readout.config(text=f"HEX: {self.current_hex.upper()}\nRGB: {r}, {g}, {b}")
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        c, m, y, k = self.rgb_to_cmyk(r, g, b)
        self.mixer_label.config(text=f"CMYK: {c}%, {m}%, {y}%, {k}%\nHSV:  {int(h*360)}°, {int(s*100)}%, {int(v*100)}%")
        for i, f in enumerate([0.3, 0.6, 0.8, 1.0, 1.2, 1.5, 1.8]):
            sh = tuple(max(0, min(255, int(val * f))) for val in rgb)
            self.shade_boxes[i].config(bg='#%02x%02x%02x' % sh)

    def update_loop(self):
        if not self.is_held:
            try:
                # Use winfo_pointerxy for absolute desktop coordinates
                x = self.root.winfo_pointerx()
                y = self.root.winfo_pointery()
                
                # all_screens=True is the key for multi-monitor support
                # It captures the entire virtual desktop area
                bbox = (x-10, y-4, x+10, y+4)
                patch = ImageGrab.grab(bbox=bbox, all_screens=True)
                rgb = patch.getpixel((10, 4))
                self.update_ui_elements(rgb)

                zoom = patch.resize((380, 140), Image.Resampling.NEAREST)
                self.tk_img = ImageTk.PhotoImage(zoom)
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
                self.canvas.create_rectangle(188, 68, 192, 72, outline="red")
            except Exception as e:
                pass # Silently handle if mouse moves out of total bounds
        self.root.after(50, self.update_loop)

    def copy_hex(self):
        self.root.clipboard_clear(); self.root.clipboard_append(self.current_hex.upper())

    def copy_hex(self):
        self.root.clipboard_clear(); self.root.clipboard_append(self.current_rgb.upper())

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiMonitorSpectrometer(root)
    root.mainloop()
