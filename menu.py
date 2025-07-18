import os, sys, shutil
from pathlib import Path
import importlib.util
import tkinter as tk
from tkinter import messagebox

# Import the refactored modules from Assets only when needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Assets"))

# Explicit imports for cx_Freeze compatibility
try:
    # Import all modules that are used in import_and_call
    import convert_level_location_finder
    import convert_players_location_finder
    import game_pass_save_fix
    import convertids
    import coords
    import all_in_one_deletion
    import paldefender_bases
    import slot_injector
    import modify_save
    import character_transfer
    import fix_host_save
    import fix_host_save_manual
    import restore_map
    from common import ICON_PATH, get_versions, open_file_with_default_app
except ImportError:
    # Handle frozen executable case
    from Assets.common import ICON_PATH, get_versions, open_file_with_default_app
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
def is_frozen():
    return getattr(sys, 'frozen', False)
def get_python_executable():
    if is_frozen():
        return sys.executable
    else:
        return sys.executable
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
    # Module mapping for cx_Freeze compatibility
    MODULE_MAP = {
        'convert_level_location_finder': convert_level_location_finder,
        'convert_players_location_finder': convert_players_location_finder,
        'game_pass_save_fix': game_pass_save_fix,
        'convertids': convertids,
        'coords': coords,
        'all_in_one_deletion': all_in_one_deletion,
        'paldefender_bases': paldefender_bases,
        'slot_injector': slot_injector,
        'modify_save': modify_save,
        'character_transfer': character_transfer,
        'fix_host_save': fix_host_save,
        'fix_host_save_manual': fix_host_save_manual,
        'restore_map': restore_map,
    }
    
    def import_and_call(module_name, function_name, *args):
        module = MODULE_MAP.get(module_name)
        if module is None:
            raise ImportError(f"Module not found: {module_name}")
        
        func = getattr(module, function_name)
        return func(*args) if args else func()
    
    tool_lists = [
        [
            lambda: import_and_call("convert_level_location_finder", "convert_level_location_finder", "json"),
            lambda: import_and_call("convert_level_location_finder", "convert_level_location_finder", "sav"),
            lambda: import_and_call("convert_players_location_finder", "convert_players_location_finder", "json"),
            lambda: import_and_call("convert_players_location_finder", "convert_players_location_finder", "sav"),
            lambda: import_and_call("game_pass_save_fix", "game_pass_save_fix"),
            lambda: import_and_call("convertids", "convert_steam_id"),
            lambda: import_and_call("coords", "convert_coordinates"),
        ],
        [
            lambda: import_and_call("all_in_one_deletion", "all_in_one_deletion"),
            lambda: import_and_call("paldefender_bases", "paldefender_bases"),
        ],
        [
            lambda: import_and_call("slot_injector", "slot_injector"),
            lambda: import_and_call("modify_save", "modify_save"),
            scan_save,
            generate_map,
            lambda: import_and_call("character_transfer", "character_transfer"),
            lambda: import_and_call("fix_host_save", "fix_host_save"),
            lambda: import_and_call("fix_host_save_manual", "fix_host_save_manual"),
            lambda: import_and_call("restore_map", "restore_map"),
        ]
    ]
    try:
        category_index, tool_index = choice
        tool_lists[category_index][tool_index]()
    except Exception as e:
        print(f"Invalid choice or error running tool: {e}")
def scan_save():
    # Import scan_save function dynamically to avoid import issues
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Assets"))
    from scan_save import scan_save as scan_save_func
    
    if is_frozen():
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    
    for file in ["scan_save.log", "players.log", "sort_players.log"]:
        Path(file).unlink(missing_ok=True)
    
    level_sav_path = os.path.join(base_path, "PalworldSave", "Level.sav")
    if os.path.exists(level_sav_path):
        print(f"Found Level.sav at: {level_sav_path}")
        print("Now starting the tool...")
        success = scan_save_func(str(level_sav_path))
        if not success:
            print(f"{RED_FONT}Error scanning save file!{RESET_FONT}")
    else:
        print(f"{RED_FONT}Error: PalworldSave/Level.sav not found!{RESET_FONT}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Looking for file at: {level_sav_path}")
        print("Make sure to place your Level.sav file in the PalworldSave folder.")
def generate_map():
    # Import generate_map function dynamically to avoid import issues
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Assets"))
    from bases import generate_map as generate_map_func
    
    success = generate_map_func()
    if success:
        if Path("updated_worldmap.png").exists():
            print(f"{GREEN_FONT}Opening updated_worldmap.png...{RESET_FONT}")
            open_file_with_default_app("updated_worldmap.png")
        else: 
            print(f"{RED_FONT}updated_worldmap.png not found.{RESET_FONT}")
    else:
        print(f"{RED_FONT}Error generating map!{RESET_FONT}")
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
            if os.name == 'nt' and os.path.exists(ICON_PATH):
                self.iconbitmap(ICON_PATH)
        except Exception as e:
            print(f"Could not set icon: {e}")
        tools_version, _ = get_versions()
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