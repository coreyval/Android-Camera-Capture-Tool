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
import signal
import sys

SAVE_DIR = os.path.abspath("./captures")
os.makedirs(SAVE_DIR, exist_ok=True)
captured_photos = []
initial_files = []

# Gracefully quit application
def quit_app():
    if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
        try:
            # Kill all scrcpy instances
            subprocess.run(["taskkill", "/f", "/im", "scrcpy.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"⚠️ Could not kill scrcpy: {e}")
        root.destroy()
        sys.exit(0)


# ---------- SCRCPY ----------
def start_standard_view():
    try:
        subprocess.Popen([
            "scrcpy",
            "--stay-awake",
            "--max-size", "800",
            "--max-fps", "30",
            "--crop", "1080:1080:0:885",
            "--window-width", "600",
            "--window-height", "600",
        ])
    except FileNotFoundError:
        messagebox.showerror("scrcpy Not Found",
            "Please install scrcpy and ensure it's on your PATH.")

def start_advanced_view():
    try:
        subprocess.Popen([
            "scrcpy",
            "--stay-awake",
            "--max-size", "800",
            "--max-fps", "60",
            "--crop", "1080:1800:0:500",
            "--window-width", "1200",
            "--window-height", "600",
        ])
    except FileNotFoundError:
        messagebox.showerror("scrcpy Not Found",
            "Please install scrcpy and ensure it's on your PATH.")

# ---------- ADB Utilities ----------
def run_adb(cmd):
    result = subprocess.run(["adb", "shell"] + cmd, capture_output=True, text=True)
    return result.stdout.strip()

def list_photos():
    output = run_adb(["ls", "-t", "/sdcard/DCIM/Camera"])
    return output.splitlines()

def launch_camera_and_snap():
    try:
        subprocess.run(["adb", "shell", "am", "start", "-n", "com.sec.android.app.camera/.Camera"])
        time.sleep(0.002)
        subprocess.run(["adb", "shell", "input", "keyevent", "27"])
        time.sleep(0.002)
    except Exception as e:
        messagebox.showerror("Camera Error", f"Failed to trigger camera: {e}")

def pull_latest_photo():
    try:
        current_files = list_photos()
        new_files = [f for f in current_files if f not in initial_files]
        if not new_files:
            print("❌ No new photo found.")
            return None
        latest_photo = new_files[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = os.path.join(SAVE_DIR, f"{timestamp}_{latest_photo}")
        subprocess.run(["adb", "pull", f"/sdcard/DCIM/Camera/{latest_photo}", local_path])
        return local_path
    except Exception as e:
        print(f"⚠️ Failed to pull photo: {e}")
        return None

def pull_photos_from_phone():
    if not SAVE_DIR:
        messagebox.showerror("Error", "Please select a save location first.")
        return

    timestamp = time.strftime("PhoneDump_%Y-%m-%d_%H-%M-%S")
    full_path = os.path.join(SAVE_DIR, timestamp)
    os.makedirs(full_path, exist_ok=True)

    src = "/sdcard/Pictures"
    dst = os.path.join(full_path, "Pictures")
    os.makedirs(dst, exist_ok=True)

    result = subprocess.run(["adb", "pull", src, dst], capture_output=True, text=True)
    if result.returncode != 0:
        messagebox.showerror("Error", f"Failed to pull photos:\n{result.stderr}")
        return

    messagebox.showinfo("Success", f"Photos pulled to:\n{dst}")


# ---------- Image Processing ----------
def auto_rotate_image(path):
    try:
        image = Image.open(path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            orientation = exif.get(orientation)
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
        image.save(path)
        print("🎠 Auto-rotated and overwritten.")
    except Exception as e:
        print(f"⚠️ Auto-rotation failed: {e}")

def process_image(path):
    auto_rotate_image(path)
    try:
        img = cv2.imread(path)
        if img is not None:
            cv2.imwrite(path, img)
    except Exception as e:
        print(f"⚠️ Processing failed: {e}")

# ---------- Carousel Preview ----------
def preview_carousel(images):
    if not images:
        return

    idx = [0]

    def update_image():
        img_bgr = cv2.imread(images[idx[0]])
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

    def save_all():
        tag = simpledialog.askstring("Name Photos", "Enter prefix/tag for photos (e.g. item123):")
        if tag:
            for i, path in enumerate(images):
                ext = os.path.splitext(path)[1]
                new_name = f"{tag}_{i+1:02d}{ext}"
                new_path = os.path.join(SAVE_DIR, new_name)
                os.rename(path, new_path)
                process_image(new_path)
        win.destroy()
        messagebox.showinfo("Saved", "✅ Photos saved and renamed.")

    def discard_all():
        for path in images:
            os.remove(path)
        win.destroy()
        messagebox.showinfo("Discarded", "🗑️ Photos discarded.")

    win = tk.Toplevel()
    win.title("Photo Carousel")
    panel = tk.Label(win)
    panel.pack()

    label = tk.Label(win, text="", pady=5)
    label.pack()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="⏪ Prev", command=prev_img).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="⏩ Next", command=next_img).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="📀 Save All", command=save_all).grid(row=1, column=0, pady=10)
    tk.Button(btn_frame, text="❌ Discard All", command=discard_all).grid(row=1, column=1, pady=10)

    update_image()
    win.mainloop()

# ---------- Event Handlers ----------
def take_photo():
    launch_camera_and_snap()
    path = pull_latest_photo()
    if path:
        captured_photos.append(path)
        print(f"✅ Photo captured: {path}")
    else:
        print("⚠️ No new photo captured.")

def finish_session():
    if not captured_photos:
        messagebox.showinfo("Info", "No photos captured.")
        return
    preview_carousel(captured_photos)
    root.destroy()

# ---------- System Preferences ---------
def choose_save_directory():
    global SAVE_DIR
    selected_dir = filedialog.askdirectory(title="Select Save Folder")
    if selected_dir:
        SAVE_DIR = selected_dir
        messagebox.showinfo("Folder Set", f"📂 Photos will now be saved to:\n{SAVE_DIR}")


# ---------- GUI Setup ----------
initial_files = list_photos()
root = tk.Tk()
root.title("Samsung Camera Capture Tool")
root.geometry("300x400")
root.attributes('-topmost', True)  # Always on top
root.protocol("WM_DELETE_WINDOW", quit_app)

btn_quit = tk.Button(root, text="❎ Quit App", command=quit_app, height=1, width=20)
btn_quit.pack(pady=5)

take_btn = tk.Button(root, text="📸 Take Photo", command=take_photo, height=2, width=20)
take_btn.pack(pady=10)

done_btn = tk.Button(root, text="✅ Finish & Preview", command=finish_session, height=2, width=20)
done_btn.pack(pady=10)

std_view_btn = tk.Button(root, text="👁️ Standard View", command=start_standard_view, height=2, width=20)
std_view_btn.pack(pady=10)

adv_view_btn = tk.Button(root, text="🔎 Advanced View", command=start_advanced_view, height=2, width=20)
adv_view_btn.pack(pady=10)

folder_btn = tk.Button(root, text="📂 Set Save Folder", command=choose_save_directory, height=2, width=20)
folder_btn.pack(pady=10)

pull_photos_button = tk.Button(root, text="📷 Pull All Photos", command=pull_photos_from_phone)
pull_photos_button.pack(pady=10)

root.mainloop()
