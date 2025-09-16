from pathlib import Path
import subprocess

def test_cli_help():
    r = subprocess.run(["python", "-m", "pdfsmith.cli", "--help"], capture_output=True, text=True)
    assert r.returncode == 0
