from scan_save import *
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import filedialog, messagebox
from uuid import UUID
import os
import shutil
import time
current_save_path = None
def backup_whole_directory(source_folder, backup_folder):
    if not os.path.exists(backup_folder): os.makedirs(backup_folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_folder, f"PalworldSave_backup_{timestamp}")
    shutil.copytree(source_folder, backup_path)
    print(f"Backup of {source_folder} created at: {backup_path}")
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
        return [], []
    player_files = []
    guild_files = []
    level_json = sav_to_json(os.path.join(folder_path, 'Level.sav'))
    group_data_list = level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    for i, group in enumerate(group_data_list):
        if group['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            guild_id = group['value'].get('GroupId', {}).get('value') or group.get('key') or f"guild_{i}"
            guild_name = group['value']['RawData']['value'].get('guild_name', 'Unknown Guild')
            guild_files.append(f"{guild_id} - {guild_name}")
            players = group['value']['RawData']['value'].get('players', [])
            for player in players:
                uid = str(player.get('player_uid', '')).replace('-', '')
                name = player.get('player_info', {}).get('player_name', 'Unknown')
                player_files.append(f"{uid} - {name}")
    return player_files, guild_files
def extract_guid(display_text):
    return display_text.split(' - ')[0]
def delete_player(folder_path, guid):
    guid_str = guid.hex
    level_sav_path = os.path.join(folder_path, 'Level.sav')
    players_folder = os.path.join(folder_path, 'Players')
    player_file_path = os.path.join(players_folder, guid_str + '.sav')
    if not os.path.exists(player_file_path):
        messagebox.showerror("Error", f"Player save file not found: {player_file_path}")
        return
    level_json = sav_to_json(level_sav_path)
    group_data_list = level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            group_data = group['value']['RawData']['value']
            players = group_data.get('players', [])
            group_data['players'] = [p for p in players if str(p.get('player_uid','')).replace('-', '') != guid_str]
            if str(group_data.get('admin_player_uid','')).replace('-', '') == guid_str:
                group_data['admin_player_uid'] = ""
    json_to_sav(level_json, level_sav_path)
    os.remove(player_file_path)
    messagebox.showinfo("Success", f"Deleted player {guid_str}")
def format_duration(seconds):
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(days)}d:{int(hours)}h:{int(minutes)}m:{int(seconds)}s"
def delete_inactive_players(folder_path, inactive_days=30):
    level_sav_path = os.path.join(folder_path, 'Level.sav')
    players_folder = os.path.join(folder_path, 'Players')
    if not os.path.exists(level_sav_path) or not os.path.exists(players_folder): return
    level_json = sav_to_json(level_sav_path)
    wsd = level_json['properties']['worldSaveData']['value']
    tick_now = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    deleted_info = []
    group_data_list = wsd['GroupSaveDataMap']['value']
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        original_players = raw.get('players', [])
        keep_players = []
        for player in original_players:
            player_uid = str(player.get('player_uid','')).replace('-', '')
            player_name = player.get('player_info', {}).get('player_name', 'Unknown')
            last_online = player.get('player_info', {}).get('last_online_real_time')
            if last_online is None: keep_players.append(player); continue
            seconds_offline = (tick_now - last_online) / 1e7
            days_offline = seconds_offline / 86400
            if days_offline >= inactive_days:
                player_path = os.path.join(players_folder, player_uid + '.sav')
                if os.path.exists(player_path):
                    os.remove(player_path)
                    deleted_info.append(f"{player_name} ({player_uid}) - Inactive for {format_duration(seconds_offline)}")
            else:
                keep_players.append(player)
        if len(keep_players) != len(original_players):
            raw['players'] = keep_players
            if str(raw.get('admin_player_uid','')).replace('-', '') not in [str(p.get('player_uid','')).replace('-', '') for p in keep_players]:
                raw['admin_player_uid'] = ""
    if deleted_info:
        json_to_sav(level_json, level_sav_path)
        print(f"\n[Inactive Deletion Report] {len(deleted_info)} player(s) deleted:")
        for info in deleted_info:
            print(" -", info)
        messagebox.showinfo("Success", f"Deleted {len(deleted_info)} inactive player(s).")
    else:
        print("\n[Inactive Deletion Report] No inactive players found.")
        messagebox.showinfo("Info", "No inactive players found for deletion.")
def delete_guild(folder_path, guid):
    guid_str = guid.hex
    level_sav_path = os.path.join(folder_path, 'Level.sav')
    players_folder = os.path.join(folder_path, 'Players')
    level_json = sav_to_json(level_sav_path)
    group_data_list = level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    guild_to_delete = None
    for group in group_data_list:
        if (
            group["value"]["GroupType"]["value"]["value"] == "EPalGroupType::Guild"
            and guid == group["key"]
        ):
            guild_to_delete = group
            break
    if not guild_to_delete:
        messagebox.showinfo("Info", "Player's guild not found.")
        return
    group_players = guild_to_delete['value']['RawData']['value'].get('players', [])
    for player in group_players:
        player_guid = str(player.get('player_uid','')).replace('-', '')
        player_save_file = os.path.join(players_folder, player_guid + '.sav')
        if os.path.exists(player_save_file):
            os.remove(player_save_file)
    group_data_list.remove(guild_to_delete)
    json_to_sav(level_json, level_sav_path)
    messagebox.showinfo("Success", f"Deleted guild and all its players")
def build_player_pal_caught_count(level_json):
    player_pal_caught_count = {}
    group_data_list = level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    players_folder = os.path.join(current_save_path, "Players")
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        players = group['value']['RawData']['value'].get('players', [])
        for player in players:
            uid = player.get('player_uid')
            if uid is None:
                continue
            uid_str = str(uid).replace('-', '')
            player_save_file = os.path.join(players_folder, uid_str + '.sav')
            count = 0
            if os.path.exists(player_save_file):
                try:
                    with open(player_save_file, "rb") as f:
                        data = f.read()
                        raw_gvas, _ = decompress_sav_to_gvas(data, oodle_path=oodle_path)
                    gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
                    json_data = gvas_file.dump()
                    pal_capture_count_list = json_data.get('properties', {}).get('SaveData', {}).get('value', {}).get('RecordData', {}).get('value', {}).get('PalCaptureCount', {}).get('value', [])
                    if pal_capture_count_list:
                        count = sum(entry.get('value', 0) for entry in pal_capture_count_list)
                except Exception:
                    count = 0
            player_pal_caught_count[uid] = count
    return player_pal_caught_count
def delete_players_by_caught_count(folder_path, min_caught):
    level_sav_path = os.path.join(folder_path, 'Level.sav')
    players_folder = os.path.join(folder_path, 'Players')
    level_json = sav_to_json(level_sav_path)
    player_pal_caught_count = build_player_pal_caught_count(level_json)
    group_data_list = level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    deleted_info = []
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        original_players = raw.get('players', [])
        keep_players = []
        for player in original_players:
            player_uid = player.get('player_uid')
            if not player_uid:
                keep_players.append(player)
                continue
            uid_str = str(player_uid).replace('-', '')
            caught_count = player_pal_caught_count.get(player_uid, 0)
            if caught_count < min_caught:
                player_path = os.path.join(players_folder, uid_str + '.sav')
                if os.path.exists(player_path):
                    os.remove(player_path)
                    deleted_info.append(f"{player.get('player_info', {}).get('player_name', 'Unknown')} ({uid_str}) - Caught {caught_count} pals")
            else:
                keep_players.append(player)
        if len(keep_players) != len(original_players):
            raw['players'] = keep_players
            if str(raw.get('admin_player_uid','')).replace('-', '') not in [str(p.get('player_uid','')).replace('-', '') for p in keep_players]:
                raw['admin_player_uid'] = ""
    if deleted_info:
        json_to_sav(level_json, level_sav_path)
        print(f"\n[Pal Caught Deletion Report] {len(deleted_info)} player(s) deleted:")
        for info in deleted_info:
            print(" -", info)
        messagebox.showinfo("Success", f"Deleted {len(deleted_info)} player(s) with less than {min_caught} pals caught.")
    else:
        print("\n[Pal Caught Deletion Report] No players found below the threshold.")
        messagebox.showinfo("Info", "No players deleted based on caught pals count.")
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
    player_values, guild_values = populate_player_lists(folder_path)
    old_guid_combobox.configure(values=player_values)
    guild_guid_combobox.configure(values=guild_values)
    old_guid_combobox.set("")
    guild_guid_combobox.set("")
    global current_save_path
    current_save_path = folder_path
def delete_selected_player():
    display = old_guid_combobox.get()
    if not display:
        messagebox.showerror("Error", "Select a player first")
        return
    guid = UUID(extract_guid(display))
    backup_whole_directory(current_save_path, "Backups/Delete Player")
    delete_player(current_save_path, guid)
    choose_level_file()
def delete_selected_guild():
    display = guild_guid_combobox.get()
    if not display:
        messagebox.showerror("Error", "Select a guild first")
        return
    guid_str = extract_guid(display)
    try:
        guid = UUID(guid_str)
    except:
        messagebox.showerror("Error", "Invalid guild ID format")
        return
    backup_whole_directory(current_save_path, "Backups/Delete Guild")
    delete_guild(current_save_path, guid)
    choose_level_file()
def batch_delete_inactive():
    if not current_save_path:
        messagebox.showerror("Error", "Load a save first")
        return
    try:
        days = int(inactive_days_entry.get())
    except:
        messagebox.showerror("Error", "Enter valid number of days")
        return
    backup_whole_directory(current_save_path, "Backups/Delete Inactive")
    delete_inactive_players(current_save_path, days)
    choose_level_file()
def batch_delete_by_caught():
    if not current_save_path:
        messagebox.showerror("Error", "Load a save first")
        return
    try:
        min_caught = int(caught_pals_entry.get())
    except:
        messagebox.showerror("Error", "Enter a valid number")
        return
    backup_whole_directory(current_save_path, "Backups/Delete By Caught")
    delete_players_by_caught_count(current_save_path, min_caught)
    choose_level_file()
ctk.set_appearance_mode("dark")
window = ctk.CTk()
window.title("Player & Guild Deletion Tool")
window.geometry("520x600")
import sys
icon_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "resources", "pal.ico")
try: window.iconbitmap(icon_path)
except: pass
ctk.CTkLabel(window, text='Select Level.sav file:').pack(pady=(15, 5))
file_frame = ctk.CTkFrame(window)
file_frame.pack(pady=0, padx=10, fill="x")
level_sav_entry = ctk.CTkEntry(file_frame, width=400)
level_sav_entry.pack(side="left", padx=(5, 5), pady=5)
ctk.CTkButton(file_frame, text="Browse", command=choose_level_file).pack(side="left", padx=5, pady=5)
ctk.CTkLabel(window, text='Player GUID:').pack(pady=(15, 5))
old_guid_combobox = ctk.CTkComboBox(window, width=480, values=[])
old_guid_combobox.pack()
old_guid_combobox.set("")
ctk.CTkButton(window, text="Delete Selected Player", command=delete_selected_player).pack(pady=10)
ctk.CTkLabel(window, text='Guild GUID:').pack(pady=(15, 5))
guild_guid_combobox = ctk.CTkComboBox(window, width=480, values=[])
guild_guid_combobox.pack()
guild_guid_combobox.set("")
ctk.CTkButton(window, text="Delete Selected Guild and Players", command=delete_selected_guild).pack(pady=10)
ctk.CTkLabel(window, text='Delete Inactive Players (days):').pack(pady=(15,5))
inactive_days_entry = ctk.CTkEntry(window, width=100)
inactive_days_entry.pack()
inactive_days_entry.insert(0, "30")
ctk.CTkButton(window, text="Batch Delete Inactive Players", command=batch_delete_inactive).pack(pady=10)
ctk.CTkLabel(window, text='Delete Players with less than X Caught Pals:').pack(pady=(15,5))
caught_pals_entry = ctk.CTkEntry(window, width=100)
caught_pals_entry.pack()
caught_pals_entry.insert(0, "5")
ctk.CTkButton(window, text="Batch Delete by Caught Pals", command=batch_delete_by_caught).pack(pady=10)
window.mainloop()