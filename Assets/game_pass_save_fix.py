from import_libs import *
saves = []
save_extractor_done = threading.Event()
save_converter_done = threading.Event()
base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
root_dir = os.path.abspath(os.path.join(base_dir, ".."))
def get_save_game_pass():
    saves_path = os.path.join(root_dir, "saves")
    if os.path.exists(saves_path): shutil.rmtree(saves_path)
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
    if not find_zip_files(root_dir):
        print("Fetching zip files from local directory...")
        threading.Thread(target=run_save_extractor, daemon=True).start()
    else:
        process_zip_files()
def process_zip_files():
    saves_path = os.path.join(root_dir, "saves")
    if is_folder_empty(saves_path):
        zip_files = find_zip_files(root_dir)
        print(zip_files)
        if zip_files:
            full_zip_path = os.path.join(root_dir, zip_files[0])
            unzip_file(full_zip_path, saves_path)
            save_extractor_done.set()
        else:
            print("No save files found on XGP please reinstall the game on XGP and try again")
            window.quit()
def convert_save_files(progressbar):
    saves_path = os.path.join(root_dir, "saves")
    saveFolders = list_folders_in_directory(saves_path)
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
def run_save_extractor():
    python_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")
    base = base_dir
    if not os.path.exists(os.path.join(base, "xgp_save_extract.py")):
        base = os.path.join(base, "Assets")
    script_path = os.path.join(base, "xgp_save_extract.py")
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
    save_path = os.path.join(root_dir, "saves", saveName, "Level", "01.sav")
    if not os.path.exists(save_path): return None
    if getattr(sys, 'frozen', False):
        import sys as sys_module
        from palworld_save_tools.commands import convert
        old_argv = sys_module.argv
        try:
            sys_module.argv = ["convert", save_path]
            convert.main()
        except Exception as e:
            print(f"Error converting save (frozen): {e}")
            return None
        finally:
            sys_module.argv = old_argv
    else:
        python_exe = os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")
        env = os.environ.copy()
        env["PYTHONPATH"] = base_dir + os.pathsep + env.get("PYTHONPATH", "")
        try:
            subprocess.run([python_exe, "-m", "palworld_save_tools.commands.convert", save_path], check=True, env=env, cwd=base_dir)
        except subprocess.CalledProcessError as e:
            print(f"Error converting save (unfrozen): {e}")
            return None
    return saveName
def convert_JSON_sav(saveName):
    json_path = os.path.join(root_dir, "saves", saveName, "Level", "01.sav.json")
    output_path = os.path.join(root_dir, "saves", saveName, "Level.sav")
    if not os.path.exists(json_path): return
    if getattr(sys, 'frozen', False):
        import sys as sys_module
        from palworld_save_tools.commands import convert
        old_argv = sys_module.argv
        try:
            sys_module.argv = ["convert", json_path, "--output", output_path]
            convert.main()
            os.remove(json_path)
            move_save_steam(saveName)
        except Exception as e:
            print(f"Error converting JSON save (frozen): {e}")
        finally:
            sys_module.argv = old_argv
    else:
        python_exe = os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")
        env = os.environ.copy()
        env["PYTHONPATH"] = base_dir + os.pathsep + env.get("PYTHONPATH", "")
        try:
            subprocess.run([python_exe, "-m", "palworld_save_tools.commands.convert", json_path, "--output", output_path], check=True, env=env, cwd=base_dir)
            os.remove(json_path)
            move_save_steam(saveName)
        except subprocess.CalledProcessError as e:
            print(f"Error converting JSON save (unfrozen): {e}")
def generate_random_name(length=32):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
def move_save_steam(saveName):
    local_app_data_path = os.path.expandvars(r"%localappdata%\Pal\Saved\SaveGames")
    try:
        if not os.path.exists(local_app_data_path): raise FileNotFoundError()
        subdirs = [d for d in os.listdir(local_app_data_path) if os.path.isdir(os.path.join(local_app_data_path, d))]
        if not subdirs: raise FileNotFoundError()
        target_folder = os.path.join(local_app_data_path, subdirs[0])
        source_folder = os.path.join(root_dir, "saves", saveName)
        def ignore_folders(_, names): return {n for n in names if n in {"Level", "Slot1", "Slot2", "Slot3"}}
        new_name = generate_random_name()
        new_target_folder = os.path.join(target_folder, new_name if os.path.exists(os.path.join(target_folder, saveName)) else saveName)
        shutil.copytree(source_folder, new_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
        game_pass_save_path = os.path.join(root_dir, "GamePassSave")
        os.makedirs(game_pass_save_path, exist_ok=True)
        new_gamepass_target_folder = os.path.join(game_pass_save_path, new_name)
        shutil.copytree(source_folder, new_gamepass_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
        messagebox.showinfo("Success", "Your save is migrated to Steam. You may go ahead and open Steam Palworld.")
        shutil.rmtree(os.path.join(root_dir, "saves"))
        window.quit()
    except Exception as e:
        print(f"Error copying save folder: {e}")
        messagebox.showerror("Error", f"Failed to copy the save folder: {e}")
def transfer_steam_to_gamepass(source_folder):
    python_exe = os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")
    main_py_path = os.path.join(base_dir, "palworld_xpg_import", "main.py")
    try:
        subprocess.run([python_exe, main_py_path, source_folder], check=True)
        messagebox.showinfo("Success", "Steam save exported to GamePass format!")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        messagebox.showerror("Error", f"Conversion failed: {e}")
window = customtkinter.CTk()
window.title("Palworld Save Converter")
window.geometry("400x200")
icon_path = os.path.join(base_dir, "resources", "pal.ico")
window.iconbitmap(icon_path)
main_frame = customtkinter.CTkFrame(window, fg_color="transparent")
main_frame.pack(expand=True, fill="both")
xgp_button = customtkinter.CTkButton(main_frame, text="GamePass", command=get_save_game_pass, width=150)
xgp_button.pack(pady=(20, 10))
steam_button = customtkinter.CTkButton(main_frame, text="Steam", command=get_save_steam, width=150)
steam_button.pack(pady=(0, 10))
progressbar = customtkinter.CTkProgressBar(main_frame, orientation="horizontal", mode="determinate", width=350)
progressbar.set(0)
progressbar.pack(pady=(0, 10))
save_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
save_frame.pack(pady=(10, 10))
def update_combobox(saveList):
    global saves
    saves = saveList
    for widget in save_frame.winfo_children():
        widget.destroy()
    if saves:
        combobox = customtkinter.CTkComboBox(save_frame, values=saves, width=320, font=("Arial", 14))
        combobox.pack(pady=(10, 10))
        combobox.set("Choose a save to convert:")
        button = customtkinter.CTkButton(save_frame, width=150, text="Convert Save", command=lambda: convert_JSON_sav(combobox.get()))
        button.pack(pady=(0, 10))
def on_exit():
    try:
        window.destroy()
    except Exception:
        pass
    sys.exit()
window.protocol("WM_DELETE_WINDOW", on_exit)
window.mainloop()