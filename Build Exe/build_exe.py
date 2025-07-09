import os, sys, shutil, subprocess
def clean_build():
    build_dirs = ["build", "dist"]
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name)
def install_cx_freeze():
    try:
        import cx_Freeze
        print("cx_Freeze is already installed")
    except ImportError:
        print("Installing cx_Freeze...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cx_Freeze"])
def build_executable():
    print("Building executable with cx_Freeze...")
    try:
        subprocess.check_call([sys.executable, "setup.py", "build"], cwd=".")
        print("Build completed successfully!")
        print("Executable can be found in the 'dist' directory")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)
def main():
    print("PalworldSaveTools Build Script")
    print("=" * 40)
    clean_build()
    install_cx_freeze()
    build_executable()
if __name__ == "__main__":
    main()