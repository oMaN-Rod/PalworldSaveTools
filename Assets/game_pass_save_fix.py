from import_libs import *
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
    python_exe = os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
        base_path = os.path.normpath(base_path)
        if os.path.basename(base_path) == "Assets":
            script_path = os.path.join(base_path, "xgp_save_extract.py")
        else:
            script_path = os.path.join(base_path, "Assets", "xgp_save_extract.py")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(base_path) == "Assets":
            script_path = os.path.join(base_path, "xgp_save_extract.py")
        else:
            script_path = os.path.join(base_path, "Assets", "xgp_save_extract.py")
    print(f"Running script at: {script_path}")
    command = [python_exe, script_path]
    try:
        subprocess.run(command, check=True)
        print("Command executed successfully")
        process_zip_files()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
def list_folders_in_directory(directory):
    try:
        if not os.path.exists(directory): os.makedirs(directory)
        return [item for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item))]
    except: return []
def is_folder_empty(directory):
    try:
        if not os.path.exists(directory): os.makedirs(directory)
        return len(os.listdir(directory)) == 0
    except: return False
def find_zip_files(directory):
    return [f for f in os.listdir(directory) if f.endswith(".zip") and f.startswith("palworld_") and is_valid_zip(os.path.join(directory, f))] if os.path.exists(directory) else []
def is_valid_zip(zip_file_path):
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref: zip_ref.testzip()
        return True
    except: return False
def unzip_file(zip_file_path, extract_to_folder):
    os.makedirs(extract_to_folder, exist_ok=True)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref: zip_ref.extractall(extract_to_folder)
def convert_sav_JSON(saveName):
    save_path = os.path.abspath(f"./saves/{saveName}/Level/01.sav")
    if not os.path.exists(save_path): return None
    python_exe = os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")
    subprocess.run([python_exe, "-m", "palworld_save_tools.commands.convert", save_path], check=True)
    return saveName
def convert_JSON_sav(saveName):
    python_exe = os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")
    json_path = os.path.abspath(f"./saves/{saveName}/Level/01.sav.json")
    output_path = os.path.abspath(f"./saves/{saveName}/Level.sav")
    try:
        subprocess.run([python_exe, "-m", "palworld_save_tools.commands.convert", json_path, "--output", output_path], check=True)
        os.remove(json_path)
        move_save_steam(saveName)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
def generate_random_name(length=32):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
def move_save_steam(saveName):
    local_app_data_path = os.path.expandvars(r"%localappdata%\Pal\Saved\SaveGames")
    try:
        if not os.path.exists(local_app_data_path): raise FileNotFoundError()
        subdirs = [d for d in os.listdir(local_app_data_path) if os.path.isdir(os.path.join(local_app_data_path, d))]
        if not subdirs: raise FileNotFoundError()
        target_folder = os.path.join(local_app_data_path, subdirs[0])
        source_folder = os.path.join("./saves", saveName)
        def ignore_folders(_, names): return {n for n in names if n in {"Level", "Slot1", "Slot2", "Slot3"}}
        new_name = generate_random_name()
        new_target_folder = os.path.join(target_folder, new_name if os.path.exists(os.path.join(target_folder, saveName)) else saveName)
        shutil.copytree(source_folder, new_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
        game_pass_save_path = os.path.join(os.getcwd(), "GamePassSave")
        os.makedirs(game_pass_save_path, exist_ok=True)
        new_gamepass_target_folder = os.path.join(game_pass_save_path, new_name)
        shutil.copytree(source_folder, new_gamepass_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
        messagebox.showinfo("Success", "Your save is migrated to Steam. You may go ahead and open Steam Palworld.")
        shutil.rmtree("./saves")
        window.quit()
    except Exception as e:
        print(f"Error copying save folder: {e}")
        messagebox.showerror("Error", f"Failed to copy the save folder: {e}")
def transfer_steam_to_gamepass(source_folder):
    python_exe = os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")
    main_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "palworld_xpg_import", "main.py")
    try:
        subprocess.run([python_exe, main_py_path, source_folder], check=True)
        messagebox.showinfo("Success", "Steam save exported to GamePass format!")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        messagebox.showerror("Error", f"Conversion failed: {e}")
window = customtkinter.CTk()
window.title("Palworld Save Converter")
window.geometry(f"400x130+{(window.winfo_screenwidth() // 2 - 200)}+{(window.winfo_screenheight() // 2 - 65)}")
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "pal.ico")
window.iconbitmap(icon_path)
xgp_button = customtkinter.CTkButton(window, text="GamePass", command=get_save_game_pass, width=150)
xgp_button.place(x=110, y=20)
steam_button = customtkinter.CTkButton(window, text="Steam", command=get_save_steam, width=150)
steam_button.place(x=110, y=70)
progressbar = customtkinter.CTkProgressBar(window, orientation="horizontal", mode="determinate", width=350)
progressbar.set(0)
def on_exit():
    try:
        window.destroy()
    except Exception:
        pass
    sys.exit()
window.protocol("WM_DELETE_WINDOW", on_exit)
window.mainloop()