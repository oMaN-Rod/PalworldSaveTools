from import_libs import *
from convert import *
def search_file(pattern, directory):
    return glob.glob(f"{directory}/PalworldSave/**/{pattern}", recursive=True)
def main():
    args = sys.argv[1:] if hasattr(sys, 'frozen') else sys.argv[1:]
    if len(args) != 1 or args[0] not in ["sav", "json"]:
        print("Usage: script.py <sav|json>")
        exit(1)
    ext = args[0]
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
    level_files = search_file("Level.json", base_dir) if ext == "sav" else search_file("Level.sav", base_dir)
    if not level_files:
        print("File not found.")
        exit(1)
    for level_file in level_files:
        if ext == "sav":
            output_path = level_file.replace(".json", ".sav")
            convert_json_to_sav(level_file, output_path)
        else:
            output_path = level_file.replace(".sav", ".json")
            convert_sav_to_json(level_file, output_path)
        print(f"Converted {level_file} to {output_path}")
if __name__ == "__main__": main()