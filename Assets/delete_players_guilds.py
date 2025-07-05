from scan_save import *
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import filedialog, messagebox
from uuid import UUID
import os
import shutil
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
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
    tick_now = level_json['properties']['worldSaveData']['value']['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    for i, group in enumerate(group_data_list):
        if group['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            raw = group['value']['RawData']['value']
            guild_id = group['value'].get('GroupId', {}).get('value') or group.get('key') or f"guild_{i}"
            guild_name = raw.get('guild_name', 'Unknown Guild')
            players = raw.get('players', [])
            if players:
                admin_uid = str(players[0].get('player_uid', '')).replace('-', '')
                admin_name = players[0].get('player_info', {}).get('player_name', 'Unknown Leader')
            else:
                admin_uid = ""
                admin_name = "Unknown Leader"
            guild_files.append((guild_id, guild_name, admin_name))
            for player in players:
                uid = str(player.get('player_uid', '')).replace('-', '')
                name = player.get('player_info', {}).get('player_name', 'Unknown')
                last_online = player.get('player_info', {}).get('last_online_real_time')
                if last_online is None:
                    last_online_str = "N/A"
                else:
                    seconds_offline = (tick_now - last_online) / 1e7
                    last_online_str = format_duration(seconds_offline)
                player_files.append((uid, name, last_online_str))
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
    old_tree.delete(*old_tree.get_children())
    guild_tree.delete(*guild_tree.get_children())
    for guid, name, last_online_str in player_values:
        old_tree.insert("", "end", values=(name, guid, last_online_str))
    old_tree.original_rows = old_tree.get_children()
    for guid, name, leader in guild_values:
        guild_tree.insert("", "end", values=(name, leader, guid))
    guild_tree.original_rows = guild_tree.get_children()
    player_result_label.config(text="Selected Player: N/A")
    guild_result_label.config(text="Selected Guild: N/A")
    global current_save_path
    current_save_path = folder_path
def delete_selected_player():
    sel = old_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select a player first")
        return
    guid_str = old_tree.item(sel[0])['values'][1]
    try:
        guid = UUID(guid_str.replace('-', '').strip())
    except ValueError:
        messagebox.showerror("Error", "Invalid Player UID format")
        return
    backup_whole_directory(current_save_path, "Backups/Delete Player")
    delete_player(current_save_path, guid)
    choose_level_file()
def delete_selected_guild():
    sel = guild_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select a guild first")
        return
    guid_str = guild_tree.item(sel[0])['values'][2]
    try:
        guid = UUID(guid_str.replace('-', '').strip())
    except ValueError:
        messagebox.showerror("Error", "Invalid Guild ID format")
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
def filter_treeview(tree, query):
    query = query.lower()
    for row in tree.original_rows:
        tree.reattach(row, '', 'end')
    for row in tree.original_rows:
        values = tree.item(row, "values")
        if not any(query in str(value).lower() for value in values):
            tree.detach(row)
def on_old_search(*args):
    filter_treeview(old_tree, old_search_var.get())
def on_guild_search(*args):
    filter_treeview(guild_tree, guild_search_var.get())
def on_player_select(event):
    selected = old_tree.selection()
    if selected:
        values = old_tree.item(selected[0], 'values')
        player_result_label.config(text=f"Selected Player: {values[1]} ({values[0]})")
    else:
        player_result_label.config(text="Selected Player: N/A")
def on_guild_select(event):
    selected = guild_tree.selection()
    if selected:
        values = guild_tree.item(selected[0], 'values')
        guild_result_label.config(text=f"Selected Guild: {values[1]} ({values[0]})")
    else:
        guild_result_label.config(text="Selected Guild: N/A")        
def sort_treeview_column(tree, col, reverse):
    data = [(tree.set(k, col), k) for k in tree.get_children('')]
    try:
        data.sort(key=lambda t: int(t[0]), reverse=reverse)
    except ValueError:
        data.sort(key=lambda t: t[0].lower(), reverse=reverse)
    for index, (_, k) in enumerate(data):
        tree.move(k, '', index)
    tree.heading(col, command=lambda: sort_treeview_column(tree, col, not reverse))
window = tk.Tk()
window.title("Player & Guild Deletion Tool")
window.geometry("1200x550")
window.config(bg="#2f2f2f")
try:
    icon_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "resources", "pal.ico")
    window.iconbitmap(icon_path)
except Exception:
    pass
font_style = ("Arial", 10)
style = ttk.Style()
style.theme_use('clam')
style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#444444", foreground="white")
style.configure("Treeview", background="#333333", foreground="white", rowheight=25, fieldbackground="#333333", borderwidth=0)
file_frame = tk.Frame(window, bg="#2f2f2f")
file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
file_frame.grid_columnconfigure(1, weight=1)
tk.Label(file_frame, text='Select Level.sav file:', bg="#2f2f2f", fg="white", font=font_style).grid(row=0, column=0)
level_sav_entry = tk.Entry(file_frame, font=font_style, bg="#444444", fg="white", insertbackground="white")
level_sav_entry.grid(row=0, column=1, sticky="ew", padx=5)
browse_button = tk.Button(file_frame, text="Browse", command=choose_level_file, bg="#555555", fg="white", font=font_style, activebackground="#666666")
browse_button.grid(row=0, column=2, padx=(0, 15))
tk.Label(file_frame, text="Delete players inactive for days:", bg="#2f2f2f", fg="white", font=font_style).grid(row=0, column=3)
inactive_days_entry = tk.Entry(file_frame, width=5, font=font_style, bg="#444444", fg="white", insertbackground="white")
inactive_days_entry.insert(0, "30")
inactive_days_entry.grid(row=0, column=4, padx=(2, 5))
delete_inactive_btn = tk.Button(file_frame, text="Delete", command=batch_delete_inactive, bg="#555555", fg="white", font=font_style, activebackground="#666666")
delete_inactive_btn.grid(row=0, column=5, padx=(0, 15))
tk.Label(file_frame, text="Delete players with less than pals caught:", bg="#2f2f2f", fg="white", font=font_style).grid(row=0, column=6)
caught_pals_entry = tk.Entry(file_frame, width=5, font=font_style, bg="#444444", fg="white", insertbackground="white")
caught_pals_entry.insert(0, "1")
caught_pals_entry.grid(row=0, column=7, padx=(2, 5))
delete_by_caught_btn = tk.Button(file_frame, text="Delete", command=batch_delete_by_caught, bg="#555555", fg="white", font=font_style, activebackground="#666666")
delete_by_caught_btn.grid(row=0, column=8)
old_frame = tk.Frame(window, bg="#2f2f2f")
old_frame.grid(row=1, column=0, sticky="nsew", padx=(10,5), pady=10)
old_frame.grid_rowconfigure(1, weight=1)
old_frame.grid_columnconfigure(0, weight=1)
search_frame_old = tk.Frame(old_frame, bg="#2f2f2f")
search_frame_old.grid(row=0, column=0, sticky="ew", pady=5)
old_search_var = tk.StringVar()
tk.Label(search_frame_old, text="Search Players:", bg="#2f2f2f", fg="white", font=font_style).pack(side='left', padx=(0,5))
old_search_entry = tk.Entry(search_frame_old, textvariable=old_search_var, font=font_style, bg="#444444", fg="white", insertbackground="white")
old_search_entry.pack(side='left', fill='x', expand=True)
old_tree = ttk.Treeview(old_frame, columns=("Name", "GUID", "LastOnline"), show='headings', selectmode='browse', style="Treeview")
old_tree.grid(row=1, column=0, sticky="nsew")
old_tree.heading("Name", text="Player Name", command=lambda: sort_treeview_column(old_tree, "Name", False))
old_tree.heading("GUID", text="Player UID", command=lambda: sort_treeview_column(old_tree, "GUID", False))
old_tree.heading("LastOnline", text="Last Online", command=lambda: sort_treeview_column(old_tree, "LastOnline", False))
old_tree.column("Name", width=200, anchor='center', stretch=True)
old_tree.column("GUID", width=200, anchor='center', stretch=True)
old_tree.column("LastOnline", width=150, anchor='center', stretch=True)
old_tree.tag_configure("even", background="#333333")
old_tree.tag_configure("odd", background="#444444")
old_tree.tag_configure("selected", background="#555555")
player_result_label = tk.Label(old_frame, text="Selected Player: N/A", bg="#2f2f2f", fg="white", font=font_style)
player_result_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
delete_player_btn = tk.Button(old_frame, text="Delete Selected Player", command=delete_selected_player, bg="#555555", fg="white", font=font_style, activebackground="#666666")
delete_player_btn.grid(row=3, column=0, sticky="ew", pady=5)
guild_frame = tk.Frame(window, bg="#2f2f2f")
guild_frame.grid(row=1, column=1, sticky="nsew", padx=(5,10), pady=10)
guild_frame.grid_rowconfigure(1, weight=1)
guild_frame.grid_columnconfigure(0, weight=1)
search_frame_guild = tk.Frame(guild_frame, bg="#2f2f2f")
search_frame_guild.grid(row=0, column=0, sticky="ew", pady=5)
guild_search_var = tk.StringVar()
tk.Label(search_frame_guild, text="Search Guilds:", bg="#2f2f2f", fg="white", font=font_style).pack(side='left', padx=(0,5))
guild_search_entry = tk.Entry(search_frame_guild, textvariable=guild_search_var, font=font_style, bg="#444444", fg="white", insertbackground="white")
guild_search_entry.pack(side='left', fill='x', expand=True)
guild_tree = ttk.Treeview(guild_frame, columns=("Name", "Leader", "GUID"), show='headings', selectmode='browse', style="Treeview")
guild_tree.grid(row=1, column=0, sticky="nsew")
guild_tree.heading("Name", text="Guild Name", command=lambda: sort_treeview_column(guild_tree, "Name", False))
guild_tree.heading("Leader", text="Guild Leader", command=lambda: sort_treeview_column(guild_tree, "Leader", False))
guild_tree.heading("GUID", text="Guild ID", command=lambda: sort_treeview_column(guild_tree, "GUID", False))
guild_tree.column("Name", width=200, anchor='center', stretch=True)
guild_tree.column("Leader", width=150, anchor='center', stretch=True)
guild_tree.column("GUID", width=200, anchor='center', stretch=True)
guild_tree.tag_configure("even", background="#333333")
guild_tree.tag_configure("odd", background="#444444")
guild_tree.tag_configure("selected", background="#555555")
guild_result_label = tk.Label(guild_frame, text="Selected Guild: N/A", bg="#2f2f2f", fg="white", font=font_style)
guild_result_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
delete_guild_btn = tk.Button(guild_frame, text="Delete Selected Guild", command=delete_selected_guild, bg="#555555", fg="white", font=font_style, activebackground="#666666")
delete_guild_btn.grid(row=3, column=0, sticky="ew", pady=5)
window.grid_rowconfigure(1, weight=1)
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
old_tree.original_rows = []
guild_tree.original_rows = []
old_search_var.trace_add('write', lambda *args: filter_treeview(old_tree, old_search_var.get()))
guild_search_var.trace_add('write', lambda *args: filter_treeview(guild_tree, guild_search_var.get()))
old_tree.bind("<<TreeviewSelect>>", on_player_select)
guild_tree.bind("<<TreeviewSelect>>", on_guild_select)
window.mainloop()