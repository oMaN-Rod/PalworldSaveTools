import os, subprocess, sys, shutil
from pathlib import Path
import importlib.util

# Check if running as frozen executable
def is_frozen():
    return getattr(sys, 'frozen', False)

def get_python_executable():
    if is_frozen():
        # When frozen, use the bundled Python executable
        return sys.executable
    else:
        return sys.executable

def run_python_script(script_path, *args, change_cwd=True):
    """Run a Python script by importing it as a module"""
    if not os.path.exists(script_path):
        print(f"Error: Script not found: {script_path}")
        return
    
    try:
        # Save original sys.argv and sys.path
        original_argv = sys.argv.copy()
        original_path = sys.path.copy()
        original_cwd = os.getcwd()
        original_builtins = None
        
        # Add Assets folder to Python path so imports work
        assets_folder = os.path.dirname(script_path)
        if assets_folder not in sys.path:
            sys.path.insert(0, assets_folder)
        
        # Set sys.argv for the script
        sys.argv = [script_path] + list(args)
        
        # Change to Assets folder so relative imports work, but only if requested
        if change_cwd:
            os.chdir(assets_folder)
        
        # Import and run the script
        spec = importlib.util.spec_from_file_location("__main__", script_path)
        module = importlib.util.module_from_spec(spec)
        
        # Add built-in functions that scripts might expect
        import builtins
        original_builtins = builtins.__dict__.copy()
        builtins.exit = sys.exit
        builtins.quit = sys.exit
        
        sys.modules["__main__"] = module
        spec.loader.exec_module(module)
        
    except SystemExit:
        # Handle sys.exit() calls gracefully
        pass
    except Exception as e:
        print(f"Error running {script_path}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original sys.argv, sys.path, working directory, and builtins
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
            pass  # resource module not available on Windows
    os.system('cls' if os.name == 'nt' else 'clear')
    os.makedirs("PalworldSave/Players", exist_ok=True)
def get_versions():
    tools_version = "1.0.53"
    game_version = "0.6.1"
    return tools_version, game_version
try:
    columns = os.get_terminal_size().columns
except OSError:
    columns = 80  # Default width for non-interactive environments
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
def display_menu(tools_version, game_version):
    display_logo()
    text = f"{BLUE_FONT}Converting Tools{RESET_FONT}"
    print(center_text(text))
    print(center_text("=" * 85))
    for i, tool in enumerate(converting_tools, 1): print(center_text(f"{BLUE_FONT}{i}{RESET_FONT}. {tool}"))
    print(center_text("=" * 85))
    text = f"{GREEN_FONT}Management Tools{RESET_FONT}"
    print(center_text(text))
    print(center_text("=" * 85))
    for i, tool in enumerate(management_tools, len(converting_tools) + 1): print(center_text(f"{GREEN_FONT}{i}{RESET_FONT}. {tool}"))
    print(center_text("=" * 85))
    text = f"{YELLOW_FONT}Cleaning Tools{RESET_FONT}"
    print(center_text(text))
    print(center_text("=" * 85))
    for i, tool in enumerate(cleaning_tools, len(converting_tools) + len(management_tools) + 1): print(center_text(f"{YELLOW_FONT}{i}{RESET_FONT}. {tool}"))
    print(center_text("=" * 85))
    text = f"{PURPLE_FONT}PalworldSaveTools{RESET_FONT}"
    print(center_text(text))
    print(center_text("=" * 85))
    for i, tool in enumerate(pws_tools, len(converting_tools) + len(management_tools) + len(cleaning_tools) + 1): print(center_text(f"{PURPLE_FONT}{i}{RESET_FONT}. {tool}"))
    print(center_text("=" * 85))
def run_tool(choice):
    if is_frozen():
        # When frozen, Assets folder is in the same directory as the executable
        assets_folder = os.path.join(os.path.dirname(sys.executable), "Assets")
    else:
        assets_folder = os.path.join(os.path.dirname(__file__), "Assets")
    
    def run_script(script_name, *args):
        script_path = os.path.join(assets_folder, script_name)
        print(f"Running {script_name}...")
        if is_frozen():
            # When frozen, import and run the script directly
            run_python_script(script_path, *args)
        else:
            # When not frozen, use subprocess
            python_exe = get_python_executable()
            try:
                subprocess.run([python_exe, script_path] + list(args), check=True)
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
        19: about_tools,
        20: usage_tools,
        21: readme_tools,
        22: sys.exit
    }
    tool_mapping.get(choice, lambda: print("Invalid choice!"))()
def scan_save():
    if is_frozen():
        assets_folder = os.path.join(os.path.dirname(sys.executable), "Assets")
    else:
        assets_folder = "Assets"
    for file in ["scan_save.log", "players.log", "sort_players.log"]: Path(file).unlink(missing_ok=True)
    if Path("Pal Logger").exists(): subprocess.run(["rmdir", "/s", "/q", "Pal Logger"], shell=True)
    
    # Check for Level.sav file
    level_sav_path = Path("PalworldSave/Level.sav")
    if level_sav_path.exists(): 
        script_path = os.path.join(assets_folder, "scan_save.py")
        print(f"Found Level.sav at: {level_sav_path.absolute()}")
        if is_frozen():
            # Don't change working directory for scan_save - it needs to run from main directory
            run_python_script(script_path, str(level_sav_path), change_cwd=False)
        else:
            subprocess.run([get_python_executable(), script_path, str(level_sav_path)])
    else: 
        print(f"{RED_FONT}Error: PalworldSave/Level.sav not found!{RESET_FONT}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Looking for file at: {level_sav_path.absolute()}")
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
def reset_update_tools():
    repo_url = "https://github.com/deafdudecomputers/PalworldSaveTools.git"
    print(f"{GREEN_FONT}Resetting/Updating PalworldSaveTools...{RESET_FONT}")
    subprocess.run(["git", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "remote", "remove", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "remote", "add", "origin", repo_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "fetch", "--all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    choice = input(f"{GREEN_FONT}Do you want a FULL reset? This will delete ALL untracked files. (y/n): {RESET_FONT}").strip().lower()
    if choice == "y":
        subprocess.run(["git", "clean", "-fdx"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{GREEN_FONT}PalworldSaveTools reset completed successfully.{RESET_FONT}")
    subprocess.run(["git", "reset", "--hard", "origin/main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    os.execv(original_executable, [original_executable] + sys.argv)
def about_tools():
    display_logo()
    print("PalworldSaveTools, all in one tool for fixing/transferring/editing/etc Palworld saves.")
    print("Author: MagicBear and cheahjs")
    print("License: MIT License")
    print("Updated by: Pylar and Techdude")
    print("Map Pictures Provided by: Kozejin")
    print("Testers/Helpers: Lethe, rcioletti, oMaN-Rod, KrisCris, Zvendson and xKillerMaverick")
    print("The UI was made by xKillerMaverick")
    print("Contact me on Discord: Pylar1991")
def usage_tools():
    display_logo()
    print("Some options may require you to use PalworldSave folder, so place your saves in that folder.")
    print("If you encounter some errors, make sure to run Scan Save first.")
    print("Then repeat the previous option to see if it fixes the previous error.")
    print("If everything else fails, you may contact me on Discord: Pylar1991")
    print("Or raise an issue on my github: https://github.com/deafdudecomputers/PalworldSaveTools")
def readme_tools():
    display_logo()
    readme_path = Path("readme.md")
    if readme_path.exists(): subprocess.run(["start", str(readme_path)], shell=True)
    else: print(f"{RED_FONT}readme.md not found.{RESET_FONT}")
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
pws_tools = [
    "Reset/Update PalworldSaveTools",
    "About PalworldSaveTools",
    "PalworldSaveTools Usage",
    "PalworldSaveTools Readme",
    "Exit"
]
if __name__ == "__main__":
    tools_version, game_version = get_versions()
    set_console_title(f"PalworldSaveTools v{tools_version}")
    setup_environment()
    os.system('cls' if os.name == 'nt' else 'clear')
    # Check if running with menu choice argument (skip cx_Freeze internal args)
    user_choice = None
    if len(sys.argv) > 1:
        # Filter out cx_Freeze internal arguments
        for arg in sys.argv[1:]:
            if not arg.startswith('--') and not arg.startswith('-'):
                try:
                    user_choice = int(arg)
                    break
                except ValueError:
                    continue
    
    if user_choice is not None:
        try:
            run_tool(user_choice)
            tools_version, game_version = get_versions()
            set_console_title(f"PalworldSaveTools v{tools_version}")
        except Exception as e:
            print(center_text(f"{RED_FONT}Error running tool: {e}{RESET_FONT}"))
    else:
        while True:
            tools_version, game_version = get_versions()
            set_console_title(f"PalworldSaveTools v{tools_version}")
            display_menu(tools_version, game_version)
            try:
                choice = int(input(f"{GREEN_FONT}Select what you want to do:{RESET_FONT}"))
                os.system('cls' if os.name == 'nt' else 'clear')
                run_tool(choice)
                input(f"{GREEN_FONT}Press Enter to continue...{RESET_FONT}")
            except ValueError: pass