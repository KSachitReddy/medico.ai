#!/usr/bin/env python3
"""
setup.py — One-shot setup: creates venv, installs deps, checks Tesseract.
Usage:  python setup.py
"""
import subprocess
import sys
import os
import platform

ROOT = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(ROOT, "venv")


def run(cmd, **kwargs):
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"  ❌ Command failed (exit {result.returncode})")
    return result.returncode == 0


def venv_python():
    if platform.system() == "Windows":
        return os.path.join(VENV, "Scripts", "python.exe")
    return os.path.join(VENV, "bin", "python")


def venv_pip():
    if platform.system() == "Windows":
        return os.path.join(VENV, "Scripts", "pip.exe")
    return os.path.join(VENV, "bin", "pip")


def main():
    print("=" * 60)
    print("  Medico.AI — Setup")
    print("=" * 60)

    # 1. Create venv
    if not os.path.exists(VENV):
        print("\n[1/4] Creating virtual environment…")
        run([sys.executable, "-m", "venv", "venv"], cwd=ROOT)
    else:
        print("\n[1/4] Virtual environment already exists — skipping.")

    # 2. Upgrade pip
    print("\n[2/4] Upgrading pip…")
    run([venv_pip(), "install", "--upgrade", "pip"], cwd=ROOT)

    # 3. Install requirements
    print("\n[3/4] Installing Python dependencies…")
    req_path = os.path.join(ROOT, "requirements.txt")
    ok = run([venv_pip(), "install", "-r", req_path], cwd=ROOT)
    if not ok:
        print("  ⚠️  Some packages failed — you may need to install them manually.")

    # 4. Tesseract check
    print("\n[4/4] Checking Tesseract OCR…")
    try:
        import shutil
        tess = shutil.which("tesseract")
        if tess:
            print(f"  ✅ Tesseract found at: {tess}")
        else:
            sys_name = platform.system()
            print("  ⚠️  Tesseract not found on PATH.")
            if sys_name == "Darwin":
                print("  Install with:  brew install tesseract")
            elif sys_name == "Linux":
                print("  Install with:  sudo apt install tesseract-ocr")
            elif sys_name == "Windows":
                print("  Download from: https://github.com/tesseract-ocr/tesseract")
                print("  Then add the install directory to your PATH.")
            print("  Note: EasyOCR will be used as a fallback if Tesseract is missing.")
    except Exception as e:
        print(f"  Could not check Tesseract: {e}")

    print("\n" + "=" * 60)
    print("  ✅  Setup complete!")
    print()
    print("  To start Medico.AI:")
    if platform.system() == "Windows":
        print("    venv\\Scripts\\activate")
    else:
        print("    source venv/bin/activate")
    print("    python start.py")
    print()
    print("  Or run backend and frontend separately:")
    print("    python backend/app.py          # API on :8000")
    print("    streamlit run frontend/app.py  # UI  on :8501")
    print("=" * 60)


if __name__ == "__main__":
    main()
