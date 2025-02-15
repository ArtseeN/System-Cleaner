from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": ["os", "sys", "PyQt6", "ctypes", "winreg", "psutil"],
    "includes": ["PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets"],
    "include_files": [],
    "excludes": ["tkinter", "unittest", "email", "http", "xml"],
    "include_msvcr": True
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Sistem Temizleyici",
    version="1.0",
    description="Windows Sistem Temizleme Uygulaması",
    options={"build_exe": build_exe_options},
    executables=[Executable("cleaner_app.py", base=base)]
) 