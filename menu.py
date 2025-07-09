import os, subprocess, sys, shutil
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import importlib.util
RED_FONT = "\033[91m"
YELLOW_FONT= "\033[93m"
GREEN_FONT = "\033[92m"
RESET_FONT = "\033[0m"
def is_frozen():
    return getattr(sys, 'frozen', False)
def get_python_executable():
    if is_frozen():
        return sys.executable
    else:
        return sys.executable
def run_python_script(script_path, *args, change_cwd=True):
    if not os.path.exists(script_path):
        print(f"Error: Script not found: {script_path}")
        return
    try:
        original_argv = sys.argv.copy()
        original_path = sys.path.copy()
        original_cwd = os.getcwd()
        original_builtins = None
        assets_folder = os.path.dirname(script_path)
        if assets_folder not in sys.path:
            sys.path.insert(0, assets_folder)
        sys.argv = [script_path] + list(args)
        if change_cwd:
            os.chdir(assets_folder)
        spec = importlib.util.spec_from_file_location("__main__", script_path)
        module = importlib.util.module_from_spec(spec)
        import builtins
        original_builtins = builtins.__dict__.copy()
        builtins.exit = sys.exit
        builtins.quit = sys.exit
        sys.modules["__main__"] = module
        spec.loader.exec_module(module)
    except SystemExit:
        pass
    except Exception as e:
        print(f"Error running {script_path}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sys.argv = original_argv
        sys.path = original_path
        os.chdir(original_cwd)
        if original_builtins is not None:
            import builtins
            builtins.__dict__.clear()
            builtins.__dict__.update(original_builtins)
def set_console_title(title):
    if sys.platform == "win32":
        os.system(f'title {title}')
    else:
        print(f'\033]0;{title}\a', end='', flush=True)
def get_versions():
    tools_version = "1.0.54"
    game_version = "0.6.1"
    return tools_version, game_version
def run_tool(choice):
    if is_frozen():
        assets_folder = os.path.join(os.path.dirname(sys.executable), "Assets")
    else:
        assets_folder = os.path.join(os.path.dirname(__file__), "Assets")
    def run_script(script_name, *args):
        script_path = os.path.join(assets_folder, script_name)
        print(f"Running {script_name}...")
        if is_frozen():
            run_python_script(script_path, *args)
        else:
            venv_python = os.path.join("venv", "Scripts" if os.name == "nt" else "bin", "python")
            try:
                subprocess.run([venv_python, script_path] + list(args), check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running {script_name}: {e}")
    tool_mapping = {
        1: lambda: run_script("convert_level_location_finder.py", "json"),
        2: lambda: run_script("convert_level_location_finder.py", "sav"),
        3: lambda: run_script("convert_players_location_finder.py", "json"),
        4: lambda: run_script("convert_players_location_finder.py", "sav"),
        5: lambda: run_script("game_pass_save_fix.py"),
        6: lambda: run_script("convertids.py"),
        7: lambda: run_script("coords.py"),
        8: lambda: run_script("slot_injector.py"),
        9: lambda: run_script("palworld_save_pal.py"),
        10: scan_save,
        11: generate_map,
        12: lambda: run_script("character_transfer.py"),
        13: lambda: run_script("fix_host_save.py"),
        14: lambda: run_script("fix_host_save_manual.py"),
        15: lambda: run_script("restore_map.py"),
        16: lambda: run_script("delete_bases.py"),
        17: lambda: run_script("paldefender_bases.py"),
        18: reset_update_tools,
        19: sys.exit
    }
    tool_mapping.get(choice, lambda: print("Invalid choice!"))()
def scan_save():
    for file in ["scan_save.log", "players.log", "sort_players.log"]:
        Path(file).unlink(missing_ok=True)
    if Path("Pal Logger").exists():
        subprocess.run(["rmdir", "/s", "/q", "Pal Logger"], shell=True)
    level_sav_path = Path("PalworldSave/Level.sav")
    if level_sav_path.exists():
        if is_frozen():
            assets_folder = os.path.join(os.path.dirname(sys.executable), "Assets")
            script_path = os.path.join(assets_folder, "scan_save.py")
            run_python_script(script_path, str(level_sav_path), change_cwd=False)
        else:
            venv_python = os.path.join("venv", "Scripts" if os.name == "nt" else "bin", "python")
            subprocess.run([venv_python, os.path.join("Assets", "scan_save.py"), str(level_sav_path)])
    else:
        print(f"{RED_FONT}Error: PalworldSave/Level.sav not found!{RESET_FONT}")
def generate_map():
    if is_frozen():
        assets_folder = os.path.join(os.path.dirname(sys.executable), "Assets")
        run_python_script(os.path.join(assets_folder, "bases.py"))
    else:
        venv_python = os.path.join("venv", "Scripts" if os.name == "nt" else "bin", "python")
        subprocess.run([venv_python, "-m", "Assets.bases"])
    if Path("updated_worldmap.png").exists():
        print(f"{GREEN_FONT}Opening updated_worldmap.png...{RESET_FONT}")
        subprocess.run(["start", "updated_worldmap.png"], shell=True)
    else:
        print(f"{RED_FONT}updated_worldmap.png not found.{RESET_FONT}")
def reset_update_tools():
    repo_url = "https://github.com/deafdudecomputers/PalworldSaveTools.git"
    print(f"{GREEN_FONT}Resetting/Updating PalworldSaveTools...{RESET_FONT}")
    subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "remote", "remove", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "remote", "add", "origin", repo_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "fetch", "--all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    choice = input(f"{GREEN_FONT}Do you want a FULL reset? This will delete ALL untracked files. (y/n): {RESET_FONT}").strip().lower()
    if choice == "y":
        subprocess.run(["git", "clean", "-fdx"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{GREEN_FONT}PalworldSaveTools reset completed successfully.{RESET_FONT}")
    subprocess.run(["git", "reset", "--hard", "origin/main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists("venv"):
        if os.name == 'nt':
            subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", "venv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["rm", "-rf", "venv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.name == 'nt':
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", ".git"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["rm", "-rf", ".git"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for root, dirs, _ in os.walk(".", topdown=False):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
    print(f"{GREEN_FONT}Update complete. All files have been replaced.{RESET_FONT}")
    input(f"{GREEN_FONT}Press Enter to continue...{RESET_FONT}")
converting_tools = [
    "Convert Level.sav file to Level.json",
    "Convert Level.json file back to Level.sav",
    "Convert Player files to json format",
    "Convert Player files back to sav format",
    "Convert GamePass ←→ Steam",
    "Convert SteamID",
    "Convert Coordinates"
]
management_tools = [
    "Slot Injector",
    "Modify Save",
    "Scan Save",
    "Generate Map",
    "Character Transfer",
    "Fix Host Save",
    "Fix Host Save Manual",
    "Restore Map"
]
cleaning_tools = [
    "All in One Deletion Tool",
    "Generate PalDefender Commands"
]
pws_tools = [
    "Reset/Update",
    "Exit"
]
class MenuGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Assets", "resources", "pal.ico")
            if os.name == 'nt' and os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set icon: {e}")
        tools_version, game_version = get_versions()
        self.title(f"PalworldSaveTools v{tools_version}")
        self.configure(bg="#1e1e1e")
        self.geometry("800x730")
        self.resizable(False, True)
        self.setup_ui()
    def setup_ui(self):
        container = tk.Frame(self, bg="#1e1e1e")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        ascii_font = ("Consolas", 11)
        version_font = ("Consolas", 13, "bold")
        logo = [
            "  ___      _                _    _ ___              _____         _    ",
            " | _ \\__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___",
            " |  _/ _` | \\ V  V / _ \\ '_| / _` \\__ \\/ _` \\ V / -_)| |/ _ \\/ _ \\ (_-<",
            " |_| \\__,_|_|\\_/\\_/\\___/_| |_\\__,_|___/\\__,_|\\_/\\___||_|\\___/\\___/_/__/ "
        ]
        for line in logo:
            tk.Label(container, text=line, fg="#ccc", bg="#1e1e1e", font=ascii_font).pack(anchor="center")
        tk.Label(container, text="PalworldSaveTools", fg="#9cf", bg="#1e1e1e", font=version_font).pack(pady=(10,0))
        tools_version, game_version = get_versions()
        tk.Label(container, text=f"v{tools_version} (Game v{game_version})", fg="#6f9", bg="#1e1e1e", font=("Consolas", 10)).pack(pady=(0,15))
        tools_frame = tk.Frame(container, bg="#1e1e1e")
        tools_frame.pack(fill="both", expand=True)
        self.left_frame = tk.Frame(tools_frame, bg="#1e1e1e")
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0,5))
        self.right_frame = tk.Frame(tools_frame, bg="#1e1e1e")
        self.right_frame.pack(side="left", fill="both", expand=True, padx=(5,0))
        left_categories = [
            ("Converting Tools", converting_tools, "#2196F3"),
            ("Management Tools", management_tools, "#4CAF50")
        ]
        right_categories = [
            ("Cleaning Tools", cleaning_tools, "#FFC107"),
            ("PalworldSaveTools", pws_tools, "#9C27B0")
        ]
        start_index = 1
        for title, tools, color in left_categories:
            frame = tk.LabelFrame(self.left_frame, text=title, fg=color, bg="#2a2a2a",
                                  font=("Consolas", 12, "bold"), bd=2, relief="groove", labelanchor="n")
            frame.pack(fill="x", pady=5)
            self.populate_tools(frame, tools, start_index, color)
            start_index += len(tools)
        for title, tools, color in right_categories:
            frame = tk.LabelFrame(self.right_frame, text=title, fg=color, bg="#2a2a2a",
                                  font=("Consolas", 12, "bold"), bd=2, relief="groove", labelanchor="n")
            frame.pack(fill="x", pady=5)
            self.populate_tools(frame, tools, start_index, color)
            start_index += len(tools)
    def populate_tools(self, parent, tools, start_index, color):
        for i, tool in enumerate(tools):
            btn = tk.Button(parent, text=f"{start_index+i}. {tool}", font=("Consolas", 9), bg="#333", fg=color,
                            activebackground="#444", relief="flat", anchor="w",
                            command=lambda idx=start_index+i: self.run_tool(idx))
            btn.pack(fill="x", pady=3, padx=5)
    def run_tool(self, choice):
        self.withdraw()
        try:
            run_tool(choice)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run tool {choice}.\n{e}")
        self.deiconify()
if __name__ == "__main__":
    tools_version, game_version = get_versions()
    set_console_title(f"PalworldSaveTools v{tools_version}")
    app = MenuGUI()
    app.mainloop()