$ErrorActionPreference = "Stop"

Write-Host "[1/3] Creating virtual environment..."
python -m venv .venv

Write-Host "[2/3] Upgrading pip..."
.\.venv\Scripts\python.exe -m pip install --upgrade pip

Write-Host "[3/3] Installing dependencies..."
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt

Write-Host ""
Write-Host "Setup complete."
Write-Host "Run the overlay with:"
Write-Host ".\.venv\Scripts\python.exe .\launcher.py"
Write-Host ""
Write-Host "If OCR fails, verify Tesseract is installed and set tesseract_cmd in config.json"
