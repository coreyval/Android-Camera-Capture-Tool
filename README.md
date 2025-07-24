# Android-Camera-Capture-Tool

A desktop GUI utility built in Python that enables users to control Android phone cameras via `scrcpy`. It is designed for scanning and image capture workflows where timing, automation, and proper photo saving are crucial.

---

## 🚀 Features

- 📸 **Photo Capture**: Take timed snapshots directly from your Android camera.
- 🔍 **Zoom Preview Support**: Use zoom modes via your device’s native camera app.
- ⚠️ **Workflow Warning**: Warns user not to take pictures in zoom preview — use the application’s capture button instead.
- 📂 **Custom Save Location**: Choose where your images are stored.
- ⏱️ **Auto-Capture Timer**: Automatically takes photos at set intervals.
- 📤 **Executable Build**: Can be compiled to `.exe` with PyInstaller for use on other machines.

---

## 🖥️ Requirements

- Python 3.7+
- Android device with USB debugging enabled
- `scrcpy` installed and added to your system PATH

### Python Libraries

Install required libraries with:

```bash
pip install pillow
```

---

## 🔧 Setup

1. Clone the repo or download the `.py` file.
2. Ensure `scrcpy` is installed and functional.
3. Run the script:

```bash
python camera_capture_tool.py
```

4. Alternatively, build an `.exe` with:

```bash
pyinstaller --noconsole --onefile camera_capture_tool.py
```

---

## 📚 How to Use

1. Plug in your Android device via USB and make sure it’s authorized for debugging.
2. Launch the app — it will open a control window and preview the camera.
3. Use the app’s capture button to take photos (⚠️ not from the zoom preview itself).
4. Select a save location to store all captured images.

---

## ⚠️ Notes

- **Do not** take pictures from the zoom preview UI — always use the application's capture button.
- The zoom preview is only meant for positioning and focus.
- Closing the app will automatically terminate any `scrcpy` processes.

---

## 📦 License

MIT License — use freely, modify, and distribute with credit.

---

## 🙌 Credits

Created by Corey Valentine Jr.  
Uses:  
- [scrcpy](https://github.com/Genymobile/scrcpy)  
- [Pillow](https://python-pillow.org)
