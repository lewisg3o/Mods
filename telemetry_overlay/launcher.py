import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

CONFIG_PATH = Path(__file__).with_name("config.json")
MAIN_PATH = Path(__file__).with_name("main.py")

DEFAULT_CONFIG = {
    "capture_interval_ms": 120,
    "tesseract_cmd": "",
    "regions": {
        "speed": {"x": 1380, "y": 861, "w": 140, "h": 50},
        "rpm": {"x": 1240, "y": 850, "w": 120, "h": 60},
        "gear": {"x": 1265, "y": 930, "w": 60, "h": 60},
        "transmission": {"x": 1260, "y": 980, "w": 110, "h": 40},
    },
}

REQUIRED_REGION_KEYS = ("speed", "rpm", "gear", "transmission")
REQUIRED_BOX_KEYS = ("x", "y", "w", "h")


@dataclass
class FieldRef:
    key: str
    entry: tk.Entry


def load_existing_config() -> dict:
    if not CONFIG_PATH.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(DEFAULT_CONFIG))

    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    if isinstance(payload, dict):
        merged["capture_interval_ms"] = payload.get(
            "capture_interval_ms", merged["capture_interval_ms"]
        )
        merged["tesseract_cmd"] = payload.get("tesseract_cmd", merged["tesseract_cmd"])
        regions = payload.get("regions", {})
        if isinstance(regions, dict):
            for region_name in REQUIRED_REGION_KEYS:
                if isinstance(regions.get(region_name), dict):
                    for box_key in REQUIRED_BOX_KEYS:
                        if box_key in regions[region_name]:
                            merged["regions"][region_name][box_key] = regions[region_name][box_key]
    return merged


def missing_config_values(config: dict) -> list[str]:
    missing = []
    if not str(config.get("tesseract_cmd", "")).strip():
        missing.append("tesseract_cmd")

    for region_name in REQUIRED_REGION_KEYS:
        region = config.get("regions", {}).get(region_name)
        if not isinstance(region, dict):
            missing.append(f"regions.{region_name}")
            continue
        for box_key in REQUIRED_BOX_KEYS:
            value = region.get(box_key)
            if not isinstance(value, int):
                missing.append(f"regions.{region_name}.{box_key}")
    return missing


def run_overlay() -> int:
    process = subprocess.run([sys.executable, str(MAIN_PATH), "--config", str(CONFIG_PATH)])
    return process.returncode


def open_setup_wizard(config: dict) -> dict | None:
    root = tk.Tk()
    root.title("Telemetry Overlay - First Run Setup")
    root.geometry("560x560")
    root.resizable(False, False)

    container = tk.Frame(root, padx=16, pady=12)
    container.pack(fill="both", expand=True)

    tk.Label(
        container,
        text="Enter values required to run the overlay",
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    ).pack(fill="x", pady=(0, 10))

    tk.Label(
        container,
        text="Tip: keep your game resolution/HUD scale fixed and adjust regions if OCR is wrong.",
        anchor="w",
        justify="left",
        fg="#333333",
    ).pack(fill="x", pady=(0, 10))

    tesseract_frame = tk.Frame(container)
    tesseract_frame.pack(fill="x", pady=(0, 12))
    tk.Label(tesseract_frame, text="Tesseract path:", width=20, anchor="w").pack(side="left")
    tesseract_entry = tk.Entry(tesseract_frame)
    tesseract_entry.pack(side="left", fill="x", expand=True)
    tesseract_entry.insert(0, str(config.get("tesseract_cmd", "")))

    interval_frame = tk.Frame(container)
    interval_frame.pack(fill="x", pady=(0, 12))
    tk.Label(interval_frame, text="Capture interval (ms):", width=20, anchor="w").pack(side="left")
    interval_entry = tk.Entry(interval_frame, width=10)
    interval_entry.pack(side="left", anchor="w")
    interval_entry.insert(0, str(config.get("capture_interval_ms", 120)))

    region_field_refs: dict[str, list[FieldRef]] = {}

    for region_name in REQUIRED_REGION_KEYS:
        region = config["regions"][region_name]
        section = tk.LabelFrame(container, text=f"{region_name.capitalize()} region")
        section.pack(fill="x", pady=4)
        refs: list[FieldRef] = []

        for box_key in REQUIRED_BOX_KEYS:
            row = tk.Frame(section, padx=8, pady=4)
            row.pack(fill="x")
            tk.Label(row, text=box_key.upper(), width=4, anchor="w").pack(side="left")
            entry = tk.Entry(row, width=10)
            entry.pack(side="left")
            entry.insert(0, str(region.get(box_key, "")))
            refs.append(FieldRef(box_key, entry))

        region_field_refs[region_name] = refs

    result: dict | None = None

    def save_and_close() -> None:
        nonlocal result
        try:
            capture_interval_ms = int(interval_entry.get().strip())
            if capture_interval_ms < 20:
                raise ValueError("Capture interval must be >= 20")

            tesseract_cmd = tesseract_entry.get().strip()
            if not tesseract_cmd:
                raise ValueError("Tesseract path is required")

            updated = {
                "capture_interval_ms": capture_interval_ms,
                "tesseract_cmd": tesseract_cmd,
                "regions": {},
            }
            for region_name, refs in region_field_refs.items():
                updated["regions"][region_name] = {}
                for ref in refs:
                    value = int(ref.entry.get().strip())
                    if ref.key in ("w", "h") and value <= 0:
                        raise ValueError(f"{region_name}.{ref.key} must be > 0")
                    updated["regions"][region_name][ref.key] = value

            CONFIG_PATH.write_text(json.dumps(updated, indent=2), encoding="utf-8")
            result = updated
            root.destroy()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))

    button_row = tk.Frame(container, pady=12)
    button_row.pack(fill="x")
    tk.Button(button_row, text="Save and Run", command=save_and_close).pack(side="right")
    tk.Button(button_row, text="Cancel", command=root.destroy).pack(side="right", padx=(0, 8))

    root.mainloop()
    return result


def main() -> int:
    config = load_existing_config()
    missing = missing_config_values(config)

    if missing:
        updated = open_setup_wizard(config)
        if updated is None:
            return 1

    return run_overlay()


if __name__ == "__main__":
    raise SystemExit(main())
