import sys
import os
from cx_Freeze import setup, Executable

# Find CustomTkinter assets
def find_customtkinter_assets():
    try:
        import customtkinter
        customtkinter_path = os.path.dirname(customtkinter.__file__)
        assets_path = os.path.join(customtkinter_path, "assets")
        if os.path.exists(assets_path):
            return (assets_path, "lib/customtkinter/assets")
    except ImportError:
        pass
    return None

# Find pyooz/ooz library files
def find_ooz_library():
    try:
        import ooz
        ooz_path = os.path.dirname(ooz.__file__)
        return (ooz_path, "Assets/palworld_save_tools/lib/windows")
    except ImportError:
        pass
    return None

# Dependencies are automatically detected, but it might need fine-tuning
build_exe_options = {
    "packages": [
        "os", "sys", "subprocess", "pathlib", "shutil",
        "msgpack", "psutil", "matplotlib", "pandas", "requests", 
        "customtkinter", "cityhash", "tkinter", "json", "uuid", "time",
        "datetime", "struct", "enum", "collections", "itertools", "math",
        "zlib", "gzip", "zipfile", "threading", "multiprocessing", "io",
        "base64", "binascii", "hashlib", "hmac", "secrets", "ssl", "socket",
        "urllib", "http", "email", "mimetypes", "tempfile", "glob", "fnmatch",
        "argparse", "configparser", "logging", "traceback", "warnings", "weakref",
        "string", "random", "re", "copy", "ctypes", "functools", "gc",
        "importlib", "importlib.metadata", "importlib.util", "PIL", "PIL.Image", "PIL.ImageDraw", "PIL.ImageOps", "PIL.ImageFont", 
        "numpy", "ooz", "pickle", "tarfile", "csv", "pprint", "code", "platform",
        "matplotlib.patches", "matplotlib.font_manager", "matplotlib.patheffects",
        "tkinter.font", "tkinter.simpledialog", "urllib.request", "multiprocessing.shared_memory"
    ],
    "excludes": [
        "test", "unittest", "pdb", "tkinter.test", "lib2to3", "distutils",
        "setuptools", "pip", "wheel", "venv", "ensurepip"
    ],
    "include_files": [
        ("Assets/", "Assets/"),
        ("PalworldSave/", "PalworldSave/"),
        ("readme.md", "readme.md"),
        ("license", "license")
    ],
    "zip_include_packages": [],
    "zip_exclude_packages": ["customtkinter"],
    "build_exe": "dist",
    "bin_includes": ["python311.dll"] if sys.platform == "win32" else []
}

# Add CustomTkinter assets if found
customtkinter_assets = find_customtkinter_assets()
if customtkinter_assets:
    build_exe_options["include_files"].append(customtkinter_assets)

# Add ooz library if found
ooz_library = find_ooz_library()
if ooz_library:
    build_exe_options["include_files"].append(ooz_library)

# GUI applications require a different base on Windows
base = None
if sys.platform == "win32":
    base = "Console"  # Use "Win32GUI" for windowed apps, "Console" for console apps

setup(
    name="PalworldSaveTools",
    version="1.0.53",
    description="All-in-one tool for fixing/transferring/editing Palworld saves",
    options={"build_exe": build_exe_options},
    executables=[Executable("menu.py", base=base, target_name="PalworldSaveTools.exe")]
)