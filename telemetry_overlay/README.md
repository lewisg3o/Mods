 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/telemetry_overlay/README.md b/telemetry_overlay/README.md
new file mode 100644
index 0000000000000000000000000000000000000000..c1945e43c35855f259e33bc327a261e54782edb2
--- /dev/null
+++ b/telemetry_overlay/README.md
@@ -0,0 +1,122 @@
+# Telemetry Overlay OCR (Windows Setup)
+
+This tool reads your in-game dashboard from the screen in real time (OCR), then shows:
+
+- Speed
+- RPM
+- Gear
+- Transmission mode
+
+in a **separate always-on-top window**.
+
+---
+
+## 1) Install prerequisites on your PC
+
+### A. Install Python
+
+- Download Python 3.10+ from https://www.python.org/downloads/
+- During install, check **"Add Python to PATH"**
+
+### B. Install Tesseract OCR
+
+- Download from: https://github.com/UB-Mannheim/tesseract/wiki
+- Default path is usually:
+  - `C:\Program Files\Tesseract-OCR\tesseract.exe`
+
+You can either:
+- Add this folder to PATH, or
+- Put the full path in `config.json` (`tesseract_cmd` field)
+
+---
+
+## 2) Download this folder to your PC
+
+Copy the `telemetry_overlay` folder to any location, for example:
+
+`C:\Games\telemetry_overlay`
+
+---
+
+## 3) One-time setup (easy mode)
+
+Open **PowerShell** inside the folder and run:
+
+```powershell
+powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
+```
+
+This creates `.venv` and installs dependencies.
+
+---
+
+## 4) Configure capture regions
+
+Edit `config.json` and set the pixel regions for your HUD.
+
+> The sample coordinates are based on your screenshot and may still require tuning.
+
+```json
+{
+  "capture_interval_ms": 120,
+  "tesseract_cmd": "C:/Program Files/Tesseract-OCR/tesseract.exe",
+  "regions": {
+    "speed": { "x": 1380, "y": 861, "w": 140, "h": 50 },
+    "rpm": { "x": 1240, "y": 850, "w": 120, "h": 60 },
+    "gear": { "x": 1265, "y": 930, "w": 60, "h": 60 },
+    "transmission": { "x": 1260, "y": 980, "w": 110, "h": 40 }
+  }
+}
+```
+
+### Tips for better OCR
+
+- Run game in **borderless windowed** at fixed resolution
+- Keep HUD scale unchanged
+- Use bright/high-contrast dashboard theme if possible
+
+---
+
+## 5) Run the overlay
+
+### Option A: double-click
+
+- Double-click `run_overlay.bat`
+
+### Option B: terminal
+
+```powershell
+.\.venv\Scripts\python.exe .\main.py --config .\config.json
+```
+
+You should see a small always-on-top telemetry window.
+
+---
+
+## Troubleshooting
+
+### "tesseract is not installed or it's not in your PATH"
+
+Set `tesseract_cmd` in `config.json` to your full `tesseract.exe` path.
+
+### Values show `--`
+
+- Your regions are off by a few pixels
+- Game resolution changed
+- HUD moved/scaled
+
+Adjust `x/y/w/h` until OCR locks onto each text area.
+
+### OCR is unstable/flickering
+
+- Increase `capture_interval_ms` to `150` or `200`
+- Use consistent lighting/HUD contrast
+
+---
+
+## Files
+
+- `main.py` - capture + OCR + overlay window
+- `config.json` - capture regions and settings
+- `setup_windows.ps1` - creates venv + installs dependencies
+- `run_overlay.bat` - quick launcher on Windows
 
EOF
)
