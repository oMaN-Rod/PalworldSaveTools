import os, subprocess, sys, shutil
from pathlib import Path
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
        import resource
        resource.setrlimit(resource.RLIMIT_NOFILE, (65535, 65535))
    os.system('cls' if os.name == 'nt' else 'clear')
    os.makedirs("PalworldSave/Players", exist_ok=True)
    if not os.path.exists("venv"):
        print(f"{YELLOW_FONT}Setting up your environment...{RESET_FONT}")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        bin_dir = "Scripts" if os.path.exists(os.path.join("venv", "Scripts", "python.exe")) else "bin"
        venv_python = os.path.join("venv", bin_dir, "python.exe" if os.name == "nt" else "python")
        pip_executable = os.path.join("venv", bin_dir, "pip.exe" if os.name == "nt" else "pip")
        sys.executable = venv_python
        subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print(f"{YELLOW_FONT}Installing packages into venv...{RESET_FONT}")
        result = subprocess.run([pip_executable, "install", "--no-cache-dir", "-r", "requirements.txt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0 or b"ERROR:" in result.stderr or b"Failed" in result.stderr or b"fatal:" in result.stderr:
            print(f"{RED_FONT}Dependency install failed. Deleting corrupted venv...{RESET_FONT}")
            shutil.rmtree("venv", ignore_errors=True)
            print(f"{YELLOW_FONT}venv has been deleted.{RESET_FONT}")
            print(f"{RED_FONT}PLEASE follow the prerequisites on GitHub to be able to use this tool.{RESET_FONT}")
            sys.exit(1)
    bin_dir = "Scripts" if os.path.exists(os.path.join("venv", "Scripts", "python.exe")) else "bin"
    venv_python = os.path.join("venv", bin_dir, "python.exe" if os.name == "nt" else "python")
    sys.executable = venv_python
def get_versions():
    tools_version = "1.0.67"
    game_version = "0.6.2"
    return tools_version, game_version
columns = os.get_terminal_size().columns
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
    assets_folder = os.path.join(os.path.dirname(__file__), "Assets")
    disabled_tools = {}
    if choice in disabled_tools:
        print("Sorry, this option is currently disabled.")
        return
    tool_mapping = {
        1: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "convert_level_location_finder.py"), "json"]),
        2: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "convert_level_location_finder.py"), "sav"]),
        3: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "convert_players_location_finder.py"), "json"]),
        4: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "convert_players_location_finder.py"), "sav"]),
        5: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "game_pass_save_fix.py")]),
        6: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "convertids.py")]),
        7: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "coords.py")]),
        8: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "slot_injector.py")]),
        9: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "palworld_save_pal.py")]),
        10: scan_save,
        11: lambda: subprocess.run([sys.executable, "-m", "Assets.bases"]),
        12: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "character_transfer.py")]),
        13: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "fix_host_save.py")]),
        14: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "fix_host_save_manual.py")]),
        15: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "restore_map.py")]),
        16: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "delete_bases.py")]),
        17: lambda: subprocess.run([sys.executable, os.path.join(assets_folder, "paldefender_bases.py")]),
        18: reset_update_tools,
        19: about_tools,
        20: usage_tools,
        21: readme_tools,
        22: sys.exit
    }
    tool_mapping.get(choice, lambda: print("Invalid choice!"))()
def scan_save():
    for file in ["scan_save.log", "players.log", "sort_players.log"]: Path(file).unlink(missing_ok=True)
    if Path("Pal Logger").exists(): subprocess.run(["rmdir", "/s", "/q", "Pal Logger"], shell=True)
    if Path("PalworldSave/Level.sav").exists(): subprocess.run([sys.executable, os.path.join("Assets", "scan_save.py"), "PalworldSave/Level.sav"])
    else: print(f"{RED_FONT}Error: PalworldSave/Level.sav not found!{RESET_FONT}")
def reset_update_tools():
    repo_url = "https://github.com/deafdudecomputers/PalworldSaveTools.git"
    print(f"{GREEN_FONT}Resetting/Updating PalworldSaveTools...{RESET_FONT}")
    subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "remote", "remove", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "remote", "add", "origin", repo_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "fetch", "--all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "clean", "-fdx"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    os.system('pause' if os.name == 'nt' else 'read -n 1 -s -r -p "Press any key to continue..."')
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
    if len(sys.argv) > 1:
        try:
            choice = int(sys.argv[1])
            run_tool(choice)
            tools_version, game_version = get_versions()
            set_console_title(f"PalworldSaveTools v{tools_version}")
        except ValueError:
            print(center_text(f"{RED_FONT}Invalid argument. Please pass a valid number.{RESET_FONT}"))
    else:
        while True:
            tools_version, game_version = get_versions()
            set_console_title(f"PalworldSaveTools v{tools_version}")
            display_menu(tools_version, game_version)
            try:
                choice = int(input(f"{GREEN_FONT}Select what you want to do:{RESET_FONT}"))
                os.system('cls' if os.name == 'nt' else 'clear')
                run_tool(choice)
                os.system('pause' if os.name == 'nt' else 'read -n 1 -s -r -p "Press any key to continue..."')
            except ValueError: pass