from import_libs import *
from convert import *
def search_for_players_folders(search_name, root_path):
    return [
        os.path.join(root, dir_name)
        for root, dirs, _ in os.walk(os.path.join(root_path, "PalworldSave"))
        for dir_name in dirs
        if dir_name == search_name
    ]
def main():
    args = sys.argv[1:] if hasattr(sys, 'frozen') else sys.argv[1:]
    if len(args) != 1 or args[0] not in ["sav", "json"]:
        print("Usage: script.py <sav|json>")
        exit(1)
    ext = args[0]
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
    players_folders = search_for_players_folders("Players", base_dir)
    if not players_folders:
        print("Players folder not found.")
        exit(1)
    for folder in players_folders:
        empty = True
        for root, _, files in os.walk(folder):
            if not files:
                print("Players folder empty.")
                continue
            empty = False
            for file in files:
                path = os.path.join(root, file)
                if ext == "sav" and file.endswith(".json"):
                    output_path = path.replace(".json", ".sav")
                    convert_json_to_sav(path, output_path)
                    print(f"Converted {path} to {output_path}")
                elif ext == "json" and file.endswith(".sav"):
                    output_path = path.replace(".sav", ".json")
                    convert_sav_to_json(path, output_path)
                    print(f"Converted {path} to {output_path}")
        if empty:
            print("Players folder empty.")
if __name__ == "__main__": main()