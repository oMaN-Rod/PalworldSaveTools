from import_libs import *

def get_python_executable():
    """Get the correct Python executable, handling frozen state"""
    return sys.executable
saves = []
save_extractor_done = threading.Event()
save_converter_done = threading.Event()
def get_save_game_pass():
    if os.path.exists("./saves"): shutil.rmtree("./saves")
    print("Fetching save from GamePass...")
    progressbar.set(0.0)
    threading.Thread(target=check_for_zip_files, daemon=True).start()
    threading.Thread(target=check_progress, args=(progressbar,), daemon=True).start()
def get_save_steam():
    folder = filedialog.askdirectory(title="Select Steam Save Folder to Transfer")
    if not folder:
        print("No folder selected.")
        return
    threading.Thread(target=transfer_steam_to_gamepass, args=(folder,), daemon=True).start()
def check_progress(progressbar):
    if save_extractor_done.is_set():
        progressbar.set(0.5)
        print("Attempting to convert the save files...")
        threading.Thread(target=convert_save_files, args=(progressbar,), daemon=True).start()
    else:
        window.after(1000, check_progress, progressbar)
def check_for_zip_files():
    if not find_zip_files("./"):
        print("Fetching zip files from local directory...")
        threading.Thread(target=run_save_extractor, daemon=True).start()
    else:
        process_zip_files()
def process_zip_files():
    if is_folder_empty("./saves"):
        zip_files = find_zip_files("./")
        print(zip_files)
        if zip_files:
            unzip_file(zip_files[0], "./saves")
            save_extractor_done.set()
        else:
            print("No save files found on XGP please reinstall the game on XGP and try again")
            window.quit()
def convert_save_files(progressbar):
    saveFolders = list_folders_in_directory("./saves")
    if not saveFolders:
        print("No save files found")        
        return
    saveList = []
    for saveName in saveFolders:        
        name = convert_sav_JSON(saveName)        
        if name: saveList.append(name)        
    update_combobox(saveList)
    progressbar.destroy()
    print("Choose a save to convert:")
def update_combobox(saveList):
    global saves
    saves = saveList
    if saves:
        combobox = customtkinter.CTkComboBox(master=window, values=saves, width=320, font=("Arial", 14))
        combobox.place(relx=0.5, rely=0.5, anchor="center")
        combobox.set("Choose a save to convert:")
        button = customtkinter.CTkButton(window, width=200, text="Convert Save", command=lambda: convert_JSON_sav(combobox.get()))
        button.place(relx=0.5, rely=0.8, anchor="center")
def run_save_extractor():
    python_exe = get_python_executable()
    if getattr(sys, 'frozen', False):
        # When frozen, find Assets folder relative to executable
        assets_folder = os.path.join(os.path.dirname(sys.executable), "Assets")
        command = [python_exe, os.path.join(assets_folder, "xgp_save_extract.py")]
    else:
        command = [python_exe, "Assets/xgp_save_extract.py"]
    try:
        subprocess.run(command, check=True)
        print("Command executed successfully")
        process_zip_files()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
def list_folders_in_directory(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Directory {directory} created.")
        all_items = os.listdir(directory)
        return [item for item in all_items if os.path.isdir(os.path.join(directory, item))]
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error accessing {directory}: {e}")
        return []
def is_folder_empty(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Directory {directory} created.")
        return len(os.listdir(directory)) == 0
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error accessing {directory}: {e}")
        return False
def find_zip_files(directory):
    zip_files = []
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith(".zip") and filename.startswith("palworld_"):
                zip_file_path = os.path.join(directory, filename)
                if is_valid_zip(zip_file_path):
                    zip_files.append(filename)
    else:
        print(f"Directory {directory} does not exist.")
    return zip_files
def is_valid_zip(zip_file_path):
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref: zip_ref.testzip()
        return True
    except zipfile.BadZipFile: return False
def unzip_file(zip_file_path, extract_to_folder):
    print(f"Unzipping {zip_file_path} to {extract_to_folder}...")
    os.makedirs(extract_to_folder, exist_ok=True)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to_folder)
    print(f"Extracted all files to {extract_to_folder}")
def convert_sav_JSON(saveName):
    save_path = os.path.abspath(f"./saves/{saveName}/Level/01.sav")
    if not os.path.exists(save_path): return None
    python_exe = get_python_executable()
    command = [python_exe, "-m", "palworld_save_tools.commands.convert", save_path]
    if getattr(sys, 'frozen', False):
        # When frozen, run from the Assets folder location
        assets_folder = os.path.join(os.path.dirname(sys.executable), "Assets")
        subprocess.run(command, check=True, cwd=assets_folder)
    else:
        subprocess.run(command, check=True, cwd="Assets")
    return saveName
def convert_JSON_sav(saveName):
    print(saveName)
    print(f"Converting JSON file to .sav: {saveName}")
    python_exe = get_python_executable()
    json_path = os.path.abspath(f"./saves/{saveName}/Level/01.sav.json")
    output_path = os.path.abspath(f"./saves/{saveName}/Level.sav")
    command = [python_exe, "-m", "palworld_save_tools.commands.convert", json_path, "--output", output_path]
    try:
        if getattr(sys, 'frozen', False):
            # When frozen, run from the Assets folder location
            assets_folder = os.path.join(os.path.dirname(sys.executable), "Assets")
            subprocess.run(command, check=True, cwd=assets_folder)
        else:
            subprocess.run(command, check=True, cwd="Assets")
        print("Command executed successfully")
        os.remove(json_path)
        print(f"Deleted JSON file: {json_path}")
        move_save_steam(saveName)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
def generate_random_name(length=32):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
def get_unique_folder_name(base_path):
    if not os.path.exists(base_path):
        return base_path
    i = 1
    while True:
        new_path = f"{base_path}_{i}"
        if not os.path.exists(new_path):
            return new_path
        i += 1
def move_save_steam(saveName):
    print("Moving save file to Steam and GamePassSave...")
    local_app_data_path = os.path.expandvars(r"%localappdata%\Pal\Saved\SaveGames")
    try:
        if not os.path.exists(local_app_data_path): raise FileNotFoundError(f"SaveGames directory does not exist at {local_app_data_path}")
        subdirs = [d for d in os.listdir(local_app_data_path) if os.path.isdir(os.path.join(local_app_data_path, d))]
        if not subdirs: raise FileNotFoundError(f"No subdirectories found in {local_app_data_path}")
        target_folder = os.path.join(local_app_data_path, subdirs[0])
        print(f"Detected Steam target folder: {target_folder}")
        source_folder = os.path.join("./saves", saveName)
        def ignore_folders(_, names): return {name for name in names if name in {"Level", "Slot1", "Slot2", "Slot3"}}
        new_name = generate_random_name()
        new_target_folder = target_folder + "/" + saveName
        if os.path.exists(new_target_folder):
            print(f"Original folder: {new_target_folder}")
            new_target_folder = target_folder + "/" + new_name
            print(f"Folder already exists in Steam. Renaming to: {new_target_folder}")
        shutil.copytree(source_folder, new_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
        print(f"Save folder copied to Steam at {new_target_folder}")
        game_pass_save_path = os.path.join(os.getcwd(), "GamePassSave")
        if not os.path.exists(game_pass_save_path): os.makedirs(game_pass_save_path)        
        new_gamepass_target_folder = os.path.join(game_pass_save_path, new_name)
        shutil.copytree(source_folder, new_gamepass_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
        print(f"Save folder copied to GamePassSave at {new_gamepass_target_folder}")
        messagebox.showinfo("Success", "Your save is migrated to Steam. You may go ahead and open Steam Palworld.")
        shutil.rmtree("./saves")
        window.quit()
    except Exception as e:
        print(f"Error copying save folder: {e}")
        messagebox.showerror("Error", f"Failed to copy the save folder: {e}")
def transfer_steam_to_gamepass(source_folder):
    print(f"Transferring Steam save from {source_folder} to GamePassSave folder using main.py...")
    main_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "palworld_xpg_import", "main.py")
    try:
        save_files = os.listdir(source_folder)
        required_suffixes = ["LevelMeta", "LocalData", "WorldOption", "UserOption"]
        missing = [suffix for suffix in required_suffixes if not any(f.endswith(suffix) for f in save_files)]
        if missing:
            print(f"Warning: Missing files with suffixes: {', '.join(missing)}. Continuing conversion anyway.")
        python_exe = get_python_executable()
        subprocess.run([python_exe, main_py_path, source_folder], check=True)
        print("Steam to GamePass conversion completed successfully!")
        messagebox.showinfo("Success", "Steam save exported to GamePass format!")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        messagebox.showerror("Error", f"Conversion failed: {e}")
window = customtkinter.CTk()
window.title("Palworld Save Converter")
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "pal.ico")
window.iconbitmap(icon_path)
app_width = 400
app_height = 130
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width // 2) - (app_width // 2)
y = (screen_height // 2) - (app_height // 2)
window.geometry(f"{app_width}x{app_height}+{x}+{y}")
xgp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "xgp.png")
steam_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "steam.png")
xgp_img = customtkinter.CTkImage(dark_image=Image.open(xgp_path).resize((60, 30)), size=(60, 30))
steam_img = customtkinter.CTkImage(dark_image=Image.open(steam_path))
label_xgp = customtkinter.CTkLabel(window, image=xgp_img, text="")
label_steam = customtkinter.CTkLabel(window, image=steam_img, text="")
label_xgp.place(relx=0.3, rely=0.15, anchor="center")
label_steam.place(relx=0.7, rely=0.15, anchor="center")
button_gamepass = customtkinter.CTkButton(window, width=140, text="GamePass → Steam", command=get_save_game_pass)
button_gamepass.place(relx=0.3, rely=0.55, anchor="center")
button_steam = customtkinter.CTkButton(window, width=140, text="Steam → GamePass", command=get_save_steam)
button_steam.place(relx=0.7, rely=0.55, anchor="center")
progressbar = customtkinter.CTkProgressBar(master=window)
progressbar.set(0)
progressbar.place(relx=0.5, rely=0.85, anchor="center")
window.mainloop()