import os, subprocess, sys, shutil
from pathlib import Path
import importlib.util
import tkinter as tk
from tkinter import messagebox
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
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
RED_FONT = "\033[91m"
BLUE_FONT = "\033[94m"
GREEN_FONT = "\033[92m"
YELLOW_FONT= "\033[93m"
PURPLE_FONT = "\033[95m"
RESET_FONT = "\033[0m"
original_executable = sys.executable
def set_console_title(title): os.system(f'title {title}') if sys.platform == "win32" else print(f'\033]0;{title}\a', end='', flush=True)
def setup_environment():
    if sys.platform != "win32":
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_NOFILE, (65535, 65535))
        except ImportError:
            pass
    os.system('cls' if os.name == 'nt' else 'clear')
    os.makedirs("PalworldSave/Players", exist_ok=True)
def get_versions():
    tools_version = "1.0.68"
    game_version = "0.6.2"
    return tools_version, game_version
try:
    columns = os.get_terminal_size().columns
except OSError:
    columns = 80
def center_text(text):
    return "\n".join(line.center(columns) for line in text.splitlines())
def display_logo():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(center_text("=" * 85))
    text = r"""     
  ___      _                _    _ ___              _____         _    
 | _ \__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___
 |  _/ _` | \ V  V / _ \ '_| / _` \__ \/ _` \ V / -_)| |/ _ \/ _ \ (_-<
 |_| \__,_|_|\_/\_/\___/_| |_\__,_|___/\__,_|\_/\___||_|\___/\___/_/__/
    """
    print(center_text(text))
    print(f"{center_text(f'{GREEN_FONT}v{tools_version} - Working as of v{game_version} Patch{RESET_FONT}')}")
    print(f"{center_text(f'{RED_FONT}WARNING: ALWAYS BACKUP YOUR SAVES BEFORE USING THIS TOOL!{RESET_FONT}')}")
    print(f"{center_text(f'{RED_FONT}MAKE SURE TO UPDATE YOUR SAVES ON/AFTER THE v{game_version} PATCH!{RESET_FONT}')}")
    print(f"{center_text(f'{RED_FONT}IF YOU DO NOT UPDATE YOUR SAVES, YOU WILL GET ERRORS!{RESET_FONT}')}")
    print(center_text("=" * 85))
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
            python_exe = get_python_executable()
            try:
                subprocess.run([python_exe, script_path] + list(args), check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running {script_name}: {e}")
    tool_lists = [
        [
            lambda: run_script("convert_level_location_finder.py", "json"),
            lambda: run_script("convert_level_location_finder.py", "sav"),
            lambda: run_script("convert_players_location_finder.py", "json"),
            lambda: run_script("convert_players_location_finder.py", "sav"),
            lambda: run_script("game_pass_save_fix.py"),
            lambda: run_script("convertids.py"),
            lambda: run_script("coords.py"),
        ],
        [
            lambda: run_script("all_in_one_deletion.py"),
            lambda: run_script("paldefender_bases.py"),
        ],
        [
            lambda: run_script("slot_injector.py"),
            lambda: run_script("modify_save.py"),
            scan_save,
            generate_map,
            lambda: run_script("character_transfer.py"),
            lambda: run_script("fix_host_save.py"),
            lambda: run_script("fix_host_save_manual.py"),
            lambda: run_script("restore_map.py"),
        ]
    ]
    try:
        category_index, tool_index = choice
        tool_lists[category_index][tool_index]()
    except Exception as e:
        print(f"Invalid choice or error running tool: {e}")
def scan_save():
    if is_frozen():
        base_path = os.path.dirname(sys.executable)
        assets_folder = os.path.join(base_path, "Assets")
    else:
        base_path = os.path.abspath(".")
        assets_folder = "Assets"
    for file in ["scan_save.log", "players.log", "sort_players.log"]:
        Path(file).unlink(missing_ok=True)
    level_sav_path = os.path.join(base_path, "PalworldSave", "Level.sav")
    if os.path.exists(level_sav_path):
        script_path = os.path.join(assets_folder, "scan_save.py")
        print(f"Found Level.sav at: {level_sav_path}")
        print("Now starting the tool...")
        if is_frozen():
            run_python_script(script_path, str(level_sav_path), change_cwd=True)
        else:
            subprocess.run([get_python_executable(), script_path, str(level_sav_path)], cwd=base_path)
    else:
        print(f"{RED_FONT}Error: PalworldSave/Level.sav not found!{RESET_FONT}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Looking for file at: {level_sav_path}")
        print("Make sure to place your Level.sav file in the PalworldSave folder.")
def generate_map():
    if is_frozen():
        assets_folder = os.path.join(os.path.dirname(sys.executable), "Assets")
        run_python_script(os.path.join(assets_folder, "bases.py"))
    else:
        subprocess.run([get_python_executable(), "-m", "Assets.bases"])
    if Path("updated_worldmap.png").exists():
        print(f"{GREEN_FONT}Opening updated_worldmap.png...{RESET_FONT}")
        subprocess.run(["start", "updated_worldmap.png"], shell=True)
    else: print(f"{RED_FONT}updated_worldmap.png not found.{RESET_FONT}")
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
    "Generate PalDefender killnearestbase commands"
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
        self.title(f"PalworldSaveTools v{tools_version}")
        self.configure(bg="#1e1e1e")
        self.geometry("800x650")
        self.resizable(False, True)
        self.setup_ui()
    def setup_ui(self):
        container = tk.Frame(self, bg="#1e1e1e")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        ascii_font = ("Consolas", 12)
        version_font = ("Consolas", 13, "bold")
        logo_text = r"""
  ___      _                _    _ ___              _____         _    
 | _ \__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___
 |  _/ _` | \ V  V / _ \ '_| / _` \__ \/ _` \ V / -_)| |/ _ \/ _ \ (_-<
 |_| \__,_|_|\_/\_/\___/_| |_\__,_|___/\__,_|\_/\___||_|\___/\___/_/__/
        """
        logo_lines = logo_text.strip('\n').split('\n')
        for line in logo_lines:
            tk.Label(container, text=line, fg="#ccc", bg="#1e1e1e", font=ascii_font).pack(anchor="center")
        #tk.Label(container, text="PalworldSaveTools", fg="#9cf", bg="#1e1e1e", font=version_font).pack(pady=(10,0))
        tools_version, game_version = get_versions()
        info_lines = [
            f"v{tools_version} - Working as of v{game_version}",
            "WARNING: ALWAYS BACKUP YOUR SAVES BEFORE USING THIS TOOL!",
            f"MAKE SURE TO UPDATE YOUR SAVES ON/AFTER THE v{game_version} PATCH!",
            "IF YOU DO NOT UPDATE YOUR SAVES, YOU WILL GET ERRORS!"
        ]
        colors = ["#6f9", "#f44", "#f44", "#f44"]
        fonts = [("Consolas", 10)] + [("Consolas", 9, "bold")] * 3
        for text, color, font in zip(info_lines, colors, fonts):
            tk.Label(container, text=text, fg=color, bg="#1e1e1e", font=font).pack(pady=(0,2))
        tk.Label(container, text="="*85, fg="#ccc", bg="#1e1e1e", font=ascii_font).pack(pady=(5,10))
        tools_frame = tk.Frame(container, bg="#1e1e1e")
        tools_frame.pack(fill="both", expand=True)
        left_frame = tk.Frame(tools_frame, bg="#1e1e1e")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0,5))
        right_frame = tk.Frame(tools_frame, bg="#1e1e1e")
        right_frame.pack(side="left", fill="both", expand=True, padx=(5,0))
        left_categories = [
            ("Converting Tools", converting_tools, "#2196F3"),
            ("Cleaning Tools", cleaning_tools, "#FFC107")
        ]
        right_categories = [
            ("Management Tools", management_tools, "#4CAF50")
        ]
        for idx, (title, tools, color) in enumerate(left_categories):
            frame = tk.LabelFrame(left_frame, text=title, fg=color, bg="#2a2a2a", font=("Consolas", 12, "bold"),
                                  bd=2, relief="groove", labelanchor="n")
            frame.pack(fill="x", pady=5)
            self.populate_tools(frame, tools, idx, color)
        for idx, (title, tools, color) in enumerate(right_categories, start=len(left_categories)):
            frame = tk.LabelFrame(right_frame, text=title, fg=color, bg="#2a2a2a", font=("Consolas", 12, "bold"),
                                  bd=2, relief="groove", labelanchor="n")
            frame.pack(fill="x", pady=5)
            self.populate_tools(frame, tools, idx, color)
    def populate_tools(self, parent, tools, category_offset, color):
        for i, tool in enumerate(tools):
            idx = (category_offset, i)
            btn = tk.Button(parent, text=tool, font=("Consolas", 9), bg="#333", fg=color,
                            activebackground="#444", relief="flat", anchor="w",
                            command=lambda idx=idx: self.run_tool(idx))
            btn.pack(fill="x", pady=3, padx=5)
    def run_tool(self, choice):
        self.withdraw()
        try:
            run_tool(choice)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run tool {choice}.\n{e}")
        self.deiconify()
def on_exit():
    app.destroy()
    sys.exit(0)
if __name__ == "__main__":
    tools_version, game_version = get_versions()
    set_console_title(f"PalworldSaveTools v{tools_version}")
    clear_console() 
    app = MenuGUI()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.destroy(), sys.exit(0)))
    app.mainloop()