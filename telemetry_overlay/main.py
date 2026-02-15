import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import mss
import numpy as np
import pytesseract
import tkinter as tk


@dataclass
class Region:
    x: int
    y: int
    w: int
    h: int


@dataclass
class Config:
    capture_interval_ms: int
    tesseract_cmd: str
    regions: dict


def load_config(path: Path) -> Config:
    payload = json.loads(path.read_text())
    regions = {
        name: Region(**values)
        for name, values in payload.get("regions", {}).items()
    }
    return Config(
        capture_interval_ms=int(payload.get("capture_interval_ms", 120)),
        tesseract_cmd=str(payload.get("tesseract_cmd", "")),
        regions=regions,
    )


def preprocess_image(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def ocr_text(image: np.ndarray, allowlist: str) -> str:
    config = f"--psm 7 -c tessedit_char_whitelist={allowlist}"
    return pytesseract.image_to_string(image, config=config).strip()


def extract_speed(text: str) -> str:
    match = re.search(r"\d+", text)
    return match.group(0) if match else "--"


def extract_rpm(text: str) -> str:
    match = re.search(r"\d+", text)
    return match.group(0) if match else "--"


def extract_gear(text: str) -> str:
    match = re.search(r"[0-9NRPD]", text.upper())
    return match.group(0) if match else "--"


def extract_transmission(text: str) -> str:
    cleaned = re.sub(r"[^A-Z]", "", text.upper())
    return cleaned if cleaned else "--"


def capture_region(sct: mss.mss, region: Region) -> np.ndarray:
    monitor = {
        "left": region.x,
        "top": region.y,
        "width": region.w,
        "height": region.h,
    }
    screenshot = np.array(sct.grab(monitor))
    return cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)


def build_window() -> tuple[tk.Tk, tk.Label]:
    root = tk.Tk()
    root.title("Telemetry Overlay")
    root.attributes("-topmost", True)
    root.configure(bg="#111111")
    root.geometry("240x140")
    root.resizable(False, False)
    label = tk.Label(
        root,
        text="Initializing...",
        font=("Segoe UI", 14),
        fg="#00FFAA",
        bg="#111111",
        justify="left",
    )
    label.pack(expand=True, fill="both", padx=10, pady=10)
    return root, label


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR telemetry overlay")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    args = parser.parse_args()

    config = load_config(args.config)
    if config.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd

    root, label = build_window()
    sct = mss.mss()

    def update() -> None:
        start = time.time()
        speed = rpm = gear = transmission = "--"

        if "speed" in config.regions:
            speed_img = preprocess_image(capture_region(sct, config.regions["speed"]))
            speed = extract_speed(ocr_text(speed_img, "0123456789"))

        if "rpm" in config.regions:
            rpm_img = preprocess_image(capture_region(sct, config.regions["rpm"]))
            rpm = extract_rpm(ocr_text(rpm_img, "0123456789"))

        if "gear" in config.regions:
            gear_img = preprocess_image(capture_region(sct, config.regions["gear"]))
            gear = extract_gear(ocr_text(gear_img, "0123456789NRPD"))

        if "transmission" in config.regions:
            trans_img = preprocess_image(
                capture_region(sct, config.regions["transmission"])
            )
            transmission = extract_transmission(ocr_text(trans_img, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

        label.configure(
            text=(
                "Speed: {speed} MPH\n"
                "RPM: {rpm}\n"
                "Gear: {gear}\n"
                "Mode: {transmission}"
            ).format(
                speed=speed,
                rpm=rpm,
                gear=gear,
                transmission=transmission,
            )
        )

        elapsed_ms = int((time.time() - start) * 1000)
        delay = max(20, config.capture_interval_ms - elapsed_ms)
        root.after(delay, update)

    root.after(0, update)
    root.mainloop()


if __name__ == "__main__":
    main()
