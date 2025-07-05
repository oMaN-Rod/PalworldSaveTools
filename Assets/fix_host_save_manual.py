import os, shutil, sys
import tkinter as tk
from tkinter import messagebox, filedialog
from scan_save import *
from datetime import datetime
def backup_whole_directory(source_folder, subfolder_name):
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    backup_folder = os.path.join(tools_dir, "Backups", subfolder_name)
    os.makedirs(backup_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_folder, f"PalworldSave_backup_{timestamp}")
    shutil.copytree(source_folder, backup_path)
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
    if not os.path.exists(save_path) or not os.path.exists(old_sav_path):
        messagebox.showerror("Error", f'Missing save folder or player file.')
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
                    for j in range(len(group_data['individual_character_handle_ids'])):
                        if group_data['individual_character_handle_ids'][j]['instance_id'] == old_instance_id:
                            group_data['individual_character_handle_ids'][j]['guid'] = new_guid_formatted
                if 'admin_player_uid' in group_data and old_guid_formatted == group_data['admin_player_uid']:
                    group_data['admin_player_uid'] = new_guid_formatted
                if 'players' in group_data:
                    for j in range(len(group_data['players'])):
                        if old_guid_formatted == group_data['players'][j]['player_uid']:
                            group_data['players'][j]['player_uid'] = new_guid_formatted
    backup_whole_directory(os.path.dirname(level_sav_path), "Fix Host Save")
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
window = tk.Tk()
window.title("Fix Host Save - GUID Migrator (Manual IDs)")
window.geometry("820x200")
window.config(bg="#2f2f2f")
try:
    icon_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "resources", "pal.ico")
    window.iconbitmap(icon_path)
except Exception as e:
    print(f"Could not set icon: {e}")
font_style = ("Arial", 12)
frame = tk.Frame(window, bg="#2f2f2f")
frame.pack(padx=20, pady=20, fill='x')
tk.Label(frame, text="Level.sav File Path:", bg="#2f2f2f", fg="white", font=font_style).grid(row=0, column=0, sticky='w')
level_file_entry = tk.Entry(frame, width=60, font=font_style, bg="#444444", fg="white", insertbackground="white")
level_file_entry.grid(row=0, column=1, padx=5)
def browse_file():
    path = filedialog.askopenfilename(title="Select Level.sav", filetypes=[("SAV Files", "*.sav")])
    if path:
        level_file_entry.delete(0, 'end')
        level_file_entry.insert(0, path)
tk.Button(frame, text="Browse", command=browse_file, bg="#555555", fg="white", font=font_style, activebackground="#666666").grid(row=0, column=2, padx=5)
tk.Label(frame, text="Old GUID:", bg="#2f2f2f", fg="white", font=font_style).grid(row=1, column=0, sticky='w', pady=10)
old_guid_entry = tk.Entry(frame, width=40, font=font_style, bg="#444444", fg="white", insertbackground="white")
old_guid_entry.grid(row=1, column=1, padx=5, sticky='w')
tk.Label(frame, text="New GUID:", bg="#2f2f2f", fg="white", font=font_style).grid(row=2, column=0, sticky='w')
new_guid_entry = tk.Entry(frame, width=40, font=font_style, bg="#444444", fg="white", insertbackground="white")
new_guid_entry.grid(row=2, column=1, padx=5, sticky='w')
def manual_fix():
    level_sav_path = level_file_entry.get().strip()
    old_guid = old_guid_entry.get().strip()
    new_guid = new_guid_entry.get().strip()
    if not level_sav_path or not old_guid or not new_guid:
        messagebox.showerror("Error", "Please fill all fields.")
        return
    if not os.path.exists(level_sav_path):
        messagebox.showerror("Error", f"File does not exist: {level_sav_path}")
        return
    if old_guid == new_guid:
        messagebox.showerror("Error", "Old GUID and New GUID cannot be the same.")
        return
    try:
        folder_path = os.path.dirname(level_sav_path)
        fix_save(folder_path, new_guid, old_guid)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fix save:\n{e}")
tk.Button(frame, text="Apply Manual GUID Swap", command=manual_fix, bg="#555555", fg="white", font=font_style, activebackground="#666666").grid(row=3, column=1, pady=20)
window.mainloop()