from scan_save import *
from datetime import datetime, timedelta
import customtkinter as ctk
def backup_whole_directory(source_folder, backup_folder):
    if not os.path.exists(backup_folder): os.makedirs(backup_folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_folder, f"PalworldSave_backup_{timestamp}")
    shutil.copytree(source_folder, backup_path)
    print(f"Backup of {source_folder} created at: {backup_path}")
def fix_save(save_path, new_guid, old_guid, guild_fix=True):
    if new_guid[-4:] == '.sav' or old_guid[-4:] == '.sav':
        messagebox.showerror("Error", "Use only the GUID, not the entire filename.")
        return
    if len(new_guid) != 32 or len(old_guid) != 32:
        messagebox.showerror("Error", "GUIDs must be 32 characters long.")
        return
    if new_guid == old_guid:
        messagebox.showerror("Error", "New GUID and Old GUID cannot be the same.")
        return
    new_guid_formatted = '{}-{}-{}-{}-{}'.format(new_guid[:8], new_guid[8:12], new_guid[12:16], new_guid[16:20], new_guid[20:]).lower()
    old_guid_formatted = '{}-{}-{}-{}-{}'.format(old_guid[:8], old_guid[8:12], old_guid[12:16], old_guid[16:20], old_guid[20:]).lower()
    level_sav_path = os.path.join(save_path, 'Level.sav')
    old_sav_path = os.path.join(save_path, 'Players', old_guid + '.sav')
    new_sav_path = os.path.join(save_path, 'Players', new_guid + '.sav')
    if not os.path.exists(save_path):
        messagebox.showerror("Error", f'Save path "{save_path}" does not exist.')
        return
    if not os.path.exists(old_sav_path):
        messagebox.showerror("Error", f'Player save "{old_sav_path}" does not exist.')
        return
    level_json = sav_to_json(level_sav_path)
    old_json = sav_to_json(old_sav_path)
    old_json['properties']['SaveData']['value']['PlayerUId']['value'] = new_guid_formatted
    old_instance_id = old_json['properties']['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    if guild_fix:
        group_ids = level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
        for group_id in group_ids:
            if group_id['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
                group_data = group_id['value']['RawData']['value']
                if 'individual_character_handle_ids' in group_data:
                    handle_ids = group_data['individual_character_handle_ids']
                    for j in range(len(handle_ids)):
                        if handle_ids[j]['instance_id'] == old_instance_id:
                            handle_ids[j]['guid'] = new_guid_formatted
                if 'admin_player_uid' in group_data and old_guid_formatted == group_data['admin_player_uid']:
                    group_data['admin_player_uid'] = new_guid_formatted
                if 'players' in group_data:
                    for j in range(len(group_data['players'])):
                        if old_guid_formatted == group_data['players'][j]['player_uid']:
                            group_data['players'][j]['player_uid'] = new_guid_formatted
    json_to_sav(level_json, level_sav_path)
    json_to_sav(old_json, old_sav_path)
    if os.path.exists(new_sav_path): os.remove(new_sav_path)
    os.rename(old_sav_path, new_sav_path)
    messagebox.showinfo("Success", "Fix has been applied! Have fun!")
def sav_to_json(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data, oodle_path=oodle_path)
    gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return gvas_file.dump()
def json_to_sav(json_data, output_filepath):
    gvas_file = GvasFile.load(json_data)
    save_type = 0x32 if "Pal.PalworldSaveGame" in gvas_file.header.save_game_class_name or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name else 0x31
    sav_file = compress_gvas_to_sav(gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES), save_type)
    with open(output_filepath, "wb") as f:
        f.write(sav_file)
def populate_player_lists(folder_path):
    players_folder = os.path.join(folder_path, "Players")
    if not os.path.exists(players_folder):
        messagebox.showerror("Error", "Players folder not found next to selected Level.sav")
        return []
    player_files = [f[:-4] for f in os.listdir(players_folder) if f.endswith(".sav")]
    return player_files
def choose_level_file():
    path = filedialog.askopenfilename(title="Select Level.sav file", filetypes=[("SAV Files", "*.sav")])
    if not path: return
    folder_path = os.path.dirname(path)
    players_folder = os.path.join(folder_path, "Players")
    if not os.path.exists(players_folder):
        messagebox.showerror("Error", "Players folder not found next to selected Level.sav")
        return
    level_sav_entry.delete(0, "end")
    level_sav_entry.insert(0, path)
    player_values = populate_player_lists(folder_path)
    old_guid_combobox.configure(values=player_values)
    old_guid_combobox.set("")
    new_guid_combobox.configure(values=player_values)
    new_guid_combobox.set("")
def fix_save_wrapper():
    old_guid = old_guid_combobox.get()
    new_guid = new_guid_combobox.get()
    file_path = level_sav_entry.get()
    if not (old_guid and new_guid and file_path):
        messagebox.showerror("Error", "Please fill in all fields!")
        return
    folder_path = os.path.dirname(file_path)
    backup_whole_directory(folder_path, "Backups/Fix Host Save")
    fix_save(folder_path, new_guid, old_guid)
ctk.set_appearance_mode("dark")
window = ctk.CTk()
window.title("Fix Host Save - GUID Migrator")
window.geometry("520x350")
icon_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "resources", "pal.ico")
try: window.iconbitmap(icon_path)
except Exception as e: print(f"Could not set icon: {e}")
ctk.CTkLabel(window, text='Select Level.sav file:').pack(pady=(15, 5))
file_frame = ctk.CTkFrame(window)
file_frame.pack(pady=0, padx=10, fill="x")
level_sav_entry = ctk.CTkEntry(file_frame, width=400)
level_sav_entry.pack(side="left", padx=(5, 5), pady=5)
browse_button = ctk.CTkButton(file_frame, text="Browse", command=choose_level_file)
browse_button.pack(side="left", padx=5, pady=5)
ctk.CTkLabel(window, text='Old GUID:').pack(pady=(15, 5))
old_guid_combobox = ctk.CTkComboBox(window, width=480, values=[])
old_guid_combobox.pack()
old_guid_combobox.set("")
ctk.CTkLabel(window, text='New GUID:').pack(pady=(15, 5))
new_guid_combobox = ctk.CTkComboBox(window, width=480, values=[])
new_guid_combobox.pack()
new_guid_combobox.set("")
migrate_button = ctk.CTkButton(window, text="Migrate", command=fix_save_wrapper)
migrate_button.pack(pady=20)
window.mainloop()