import os
import subprocess
import sys

def open_pdf(path):
    if os.path.exists(path):
        if os.name == "nt":  # Windows
            os.startfile(path)
        elif os.name == "posix":  # macOS/Linux
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])
