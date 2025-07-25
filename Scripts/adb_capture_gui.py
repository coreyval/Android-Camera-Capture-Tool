import os
import time
import subprocess
from datetime import datetime
from PIL import Image, ExifTags, ImageTk
import cv2
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import numpy as np
import threading
import sys

SAVE_DIR = os.path.abspath("./captures")
os.makedirs(SAVE_DIR, exist_ok=True)
TEMP_VIEW_DIR = os.path.join(SAVE_DIR, "temp_view")
os.makedirs(TEMP_VIEW_DIR, exist_ok=True)

# ---------- GUI Root ----------
root = tk.Tk()
root.title("Samsung Camera Tool")
root.geometry("300x500")
root.attributes('-topmost', True)



# ---------- Quit ----------
def quit_app():
    if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
        try:
            subprocess.run(["taskkill", "/f", "/im", "scrcpy.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"⚠️ Could not kill scrcpy: {e}")
        root.destroy()
        sys.exit(0)
root.protocol("WM_DELETE_WINDOW", quit_app)

# ---------- SCRCPY ----------
def tool_path(filename):
    base = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base, "tools", filename)

def start_standard_view():
    try:
        subprocess.Popen([tool_path("scrcpy.exe"), "--stay-awake"])
    except FileNotFoundError:
        messagebox.showerror(
            title="scrcpy Not Found",
            message="Please install scrcpy and ensure it's on your PATH."
        )

# ---------- ADB ----------
def run_adb(cmd):
    result = subprocess.run([tool_path("adb.exe"), "shell"] + cmd, capture_output=True, text=True)
    return result.stdout.strip()

def list_photos():
    output = run_adb(["ls", "-t", "/sdcard/DCIM/Camera"])
    return output.splitlines()

def pull_photo(file_name, local_dir):
    local_path = os.path.join(local_dir, file_name)
    subprocess.run([tool_path("adb.exe"), "pull", f"/sdcard/DCIM/Camera/{file_name}", local_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return local_path

def launch_camera_app():
    try:
        subprocess.run([tool_path("adb.exe"), "shell", "am", "start", "-n", "com.sec.android.app.camera/.Camera"])
    except Exception as e:
        messagebox.showerror("Camera Error", f"Failed to open camera: {e}")

def trigger_camera():
    try:
        subprocess.run([tool_path("adb.exe"), "shell", "input", "keyevent", "27"])
    except Exception as e:
        messagebox.showerror("Capture Error", f"Failed to capture photo: {e}")

def pull_all_photos():
    photos = list_photos()
    if not photos:
        messagebox.showinfo("No Photos", "No photos found on the device.")
        return []

    os.makedirs(TEMP_VIEW_DIR, exist_ok=True)
    for file in photos:
        pull_photo(file, TEMP_VIEW_DIR)
    return [os.path.join(TEMP_VIEW_DIR, f) for f in photos if os.path.exists(os.path.join(TEMP_VIEW_DIR, f))]

# ---------- Image Viewer ----------
def preview_carousel(images):
    if not images:
        return

    idx = [0]
    selected_photos = []

    def update_image():
        img_bgr = cv2.imread(images[idx[0]])
        if img_bgr is None:
            return
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb).resize((600, 600))
        img_tk = ImageTk.PhotoImage(img_pil)
        panel.config(image=img_tk)
        panel.image = img_tk
        label.config(text=f"{idx[0]+1}/{len(images)}\n{os.path.basename(images[idx[0]])}")

    def next_img():
        if idx[0] < len(images) - 1:
            idx[0] += 1
            update_image()

    def prev_img():
        if idx[0] > 0:
            idx[0] -= 1
            update_image()

    def delete_photo():
        path = images.pop(idx[0])
        if os.path.exists(path):
            os.remove(path)
        if not images:
            win.destroy()
            return
        if idx[0] >= len(images):
            idx[0] = len(images) - 1
        update_image()

    def select_photo():
        if images[idx[0]] not in selected_photos:
            selected_photos.append(images[idx[0]])
        messagebox.showinfo("Selected", "Photo added to export list.")

    def go_to_index():
        try:
            value = int(simpledialog.askstring("Go to Photo", f"Enter photo number (1-{len(images)}):"))
            if 1 <= value <= len(images):
                idx[0] = value - 1
                update_image()
        except:
            pass

    def export_photos(photos):
        folder = filedialog.askdirectory(title="Select Export Folder")
        if not folder:
            return
        exported = 0
        for path in photos:
            name = os.path.basename(path)
            dest_path = os.path.join(folder, name)
            if os.path.exists(dest_path):
                continue
            try:
                img = Image.open(path)
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                exif = img._getexif()
                if exif is not None:
                    orientation_value = exif.get(orientation, None)
                    if orientation_value == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation_value == 8:
                        img = img.rotate(90, expand=True)
                img = img.convert("RGB")
                img.save(dest_path)
                exported += 1
            except:
                continue
        messagebox.showinfo("Export Complete", f"Saved {exported} photo(s).")

    def export_selected():
        export_photos(selected_photos)

    def export_all():
        export_photos(images)

    win = tk.Toplevel()
    win.title("View Photos")
    panel = tk.Label(win)
    panel.pack()

    label = tk.Label(win, text="", pady=5)
    label.pack()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="⏪ Prev", command=prev_img).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="⏩ Next", command=next_img).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="🗑 Delete", command=delete_photo).grid(row=1, column=0, columnspan=2, pady=5)
    tk.Button(btn_frame, text="✅ Select", command=select_photo).grid(row=2, column=0, columnspan=2, pady=5)
    tk.Button(btn_frame, text="🔢 Go to #", command=go_to_index).grid(row=3, column=0, columnspan=2, pady=5)
    tk.Button(btn_frame, text="💾 Export Selected", command=export_selected).grid(row=4, column=0, columnspan=2, pady=5)
    tk.Button(btn_frame, text="📤 Export All", command=export_all).grid(row=5, column=0, columnspan=2, pady=10)

    update_image()
    win.mainloop()

# ---------- Handlers ----------
def take_photo():
    trigger_camera()
    time.sleep(0.5)
    photos = list_photos()
    if photos:
        path = pull_photo(photos[0], SAVE_DIR)
        messagebox.showinfo("Saved", f"Photo saved to: {path}")

def set_save_dir():
    global SAVE_DIR
    folder = filedialog.askdirectory(title="Select Save Folder")
    if folder:
        SAVE_DIR = folder
        messagebox.showinfo("Set", f"Save folder set to: {SAVE_DIR}")

def view_all_photos():
    imgs = pull_all_photos()
    preview_carousel(imgs)

def connect_wirelessly():
    confirm = messagebox.askyesno(
        "USB Connection Required",
        "⚠️ Your phone must be plugged in via USB first to enable wireless ADB and connected to the same network.\n\nContinue?"
    )
    if not confirm:
        return

    try:
        ip_output = subprocess.check_output([tool_path("adb.exe"), "shell", "ip", "route"], text=True)
        ip_address = ip_output.split("src")[-1].strip().split()[0]

        subprocess.run([tool_path("adb.exe"), "tcpip", "5555"], check=True)
        time.sleep(1)

        subprocess.run([tool_path("adb.exe"), "connect", ip_address], check=True)
        messagebox.showinfo("Connected", f"📡 Connected wirelessly to {ip_address}")
    except Exception as e:
        messagebox.showerror("Wireless Error", f"❌ Failed to connect wirelessly:\n{e}")


# ---------- GUI Setup ----------
button_frame = tk.Frame(root)
button_frame.pack(expand=True)

buttons = [
    ("📶 Connect Wirelessly", connect_wirelessly),
    ("📱 Open Camera App", launch_camera_app),
    ("📸 Take Photo", take_photo),
    ("👁️ Live View", start_standard_view),
    ("🖼 View All Phone Photos", view_all_photos),
    ("📂 Set Save Folder", set_save_dir),
    ("❎ Quit App", quit_app),
]


for i, (label, func) in enumerate(buttons):
    row = i // 2
    col = i % 2
    btn = tk.Button(button_frame, text=label, command=func, height=2, width=16)
    btn.grid(row=row, column=col, padx=5, pady=5)

root.mainloop()
