from scan_save import *
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
from uuid import UUID
import os
import shutil
import sys
import tkinter as tk
from tkinter import ttk

current_save_path = None
loaded_level_json = None

def backup_whole_directory(source_folder, backup_folder):
    if not os.path.exists(backup_folder): os.makedirs(backup_folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_folder, f"PalworldSave_backup_{timestamp}")
    shutil.copytree(source_folder, backup_path)
    print(f"Backup of {source_folder} created at: {backup_path}")

def sav_to_json(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data)
    gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return gvas_file.dump()

def get_nested(d, *keys):
    for k in keys:
        if isinstance(d, dict): d = d.get(k, None)
        else: return None
    return d

def as_uuid(value):
    try: return UUID(str(value).replace('-', '').strip())
    except: return None

def are_equal_uuids(uuid1, uuid2):
    return str(uuid1).replace('-', '').lower() == str(uuid2).replace('-', '').lower()

def delete_guild(folder_path, guid):
    global loaded_level_json
    if loaded_level_json is None:
        messagebox.showerror("Error", "No save loaded.")
        return
    level_sav_path = os.path.join(folder_path, 'Level.sav')
    players_folder = os.path.join(folder_path, 'Players')
    group_data_list = loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    base_data_list = loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']
    guild_to_delete = None
    for group in group_data_list:
        if group["value"]["GroupType"]["value"]["value"] == "EPalGroupType::Guild" and guid == group["key"]:
            guild_to_delete = group
            break
    if not guild_to_delete:
        messagebox.showinfo("Info", "Guild not found.")
        return
    guild_name = guild_to_delete['value']['RawData']['value'].get('guild_name', 'Unknown Guild')
    print(f"Deleting Guild: {guild_name} ({guid})")
    group_players = guild_to_delete['value']['RawData']['value'].get('players', [])
    for player in group_players:
        player_guid = str(player.get('player_uid','')).replace('-', '')
        player_save_file = os.path.join(players_folder, player_guid + '.sav')
        if os.path.exists(player_save_file):
            os.remove(player_save_file)
            print(f"Deleted Player UID: {player_guid}")
    group_data_list.remove(guild_to_delete)
    bases_to_delete = [b for b in base_data_list if are_equal_uuids(as_uuid(b["value"]["RawData"]["value"].get("group_id_belong_to")), guid)]
    for base in bases_to_delete:
        base_id = base["value"]["RawData"]["value"].get("id", "Unknown")
        print(f"Deleted Base ID: {base_id}")
        base_data_list.remove(base)
    json_to_sav(loaded_level_json, level_sav_path)
    messagebox.showinfo("Success", f"Deleted guild, its players, and its bases!")
    print("Success! Deleted guild, its players, and its bases!")
    sys.exit()

def json_to_sav(json_data, output_filepath):
    gvas_file = GvasFile.load(json_data)
    save_type = 0x32 if "Pal.PalworldSaveGame" in gvas_file.header.save_game_class_name or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name else 0x31
    sav_file = compress_gvas_to_sav(gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES), save_type)
    with open(output_filepath, "wb") as f:
        f.write(sav_file)

def populate_guilds(folder_path):
    global loaded_level_json
    if loaded_level_json is None:
        return []
    group_data_list = loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    guilds = []
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            guild_name = group['value']['RawData']['value'].get('guild_name', 'Unknown Guild')
            guild_id = str(group['key'])
            guilds.append((guild_name, guild_id))
    return guilds

def populate_bases_for_guild(guild_guid_str):
    guild_guid = UUID(guild_guid_str.replace('-', '').strip())
    bases_tree.delete(*bases_tree.get_children())
    if loaded_level_json is None:
        return
    base_data_list = loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']
    for base in base_data_list:
        raw = base["value"]["RawData"]["value"]
        group_id_belong_to = as_uuid(raw.get("group_id_belong_to"))
        if are_equal_uuids(group_id_belong_to, guild_guid):
            base_id = str(raw.get("id", "Unknown"))
            bases_tree.insert("", "end", values=(base_id,))

def delete_selected_guild():
    sel = guild_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select a guild first")
        return
    guid_str = guild_tree.item(sel[0])['values'][1]
    try:
        guid = UUID(guid_str.strip())
    except ValueError:
        messagebox.showerror("Error", "Invalid Guild ID format")
        return
    backup_whole_directory(current_save_path, "Backups/Delete Guild")
    delete_guild(current_save_path, guid)

def delete_selected_base():
    sel = bases_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select a base first")
        return
    base_id = bases_tree.item(sel[0])['values'][0].strip()
    global loaded_level_json
    if loaded_level_json is None:
        messagebox.showerror("Error", "No save loaded.")
        return
    base_data_list = loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']
    group_data_list = loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    found = False
    for i, base in enumerate(base_data_list):
        base_raw = base['value']['RawData']['value']
        current_base_id = str(base_raw.get('id', ''))
        if current_base_id == base_id:
            group_id = as_uuid(base_raw.get('group_id_belong_to'))
            guild_name = "Unknown Guild"
            for group in group_data_list:
                if are_equal_uuids(as_uuid(group['key']), group_id):
                    guild_name = group['value']['RawData']['value'].get('guild_name', 'Unknown Guild')
                    break
            print(f"Deleted Base ID: {base_id} (Guild: {guild_name})")
            del base_data_list[i]
            found = True
            break
    if not found:
        messagebox.showerror("Error", "Base not found in save.")
        return
    level_sav_path = os.path.join(current_save_path, 'Level.sav')
    json_to_sav(loaded_level_json, level_sav_path)
    messagebox.showinfo("Success", f"Deleted base {base_id}!")
    print(f"Success! Deleted base {base_id}!")
    sys.exit()

def choose_level_file():
    path = filedialog.askopenfilename(title="Select Level.sav file", filetypes=[("SAV Files", "*.sav")])
    if not path: return
    folder_path = os.path.dirname(path)
    players_folder = os.path.join(folder_path, "Players")
    if not os.path.exists(players_folder):
        messagebox.showerror("Error", "Players folder not found next to selected Level.sav")
        return
    global current_save_path, loaded_level_json
    current_save_path = folder_path
    loaded_level_json = sav_to_json(os.path.join(folder_path, 'Level.sav'))
    guilds = populate_guilds(folder_path)
    guild_tree.delete(*guild_tree.get_children())
    bases_tree.delete(*bases_tree.get_children())
    for name, gid in guilds:
        guild_tree.insert("", "end", values=(name, gid))
    guild_result_label.config(text="Selected Guild: N/A")
    base_result_label.config(text="Selected Base: N/A")

def on_guild_select(event):
    selected = guild_tree.selection()
    if not selected:
        guild_result_label.config(text="Selected Guild: N/A")
        bases_tree.delete(*bases_tree.get_children())
        base_result_label.config(text="Selected Base: N/A")
        return
    values = guild_tree.item(selected[0], 'values')
    guild_result_label.config(text=f"Selected Guild: {values[0]} ({values[1]})")
    populate_bases_for_guild(values[1])

def on_base_select(event):
    selected = bases_tree.selection()
    if not selected:
        base_result_label.config(text="Selected Base: N/A")
        return
    values = bases_tree.item(selected[0], 'values')
    base_result_label.config(text=f"Selected Base: {values[0]}")

window = tk.Tk()
window.title("Guild & Bases Deletion Tool")
window.geometry("1000x600")
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

main_frame = tk.Frame(window, bg="#2f2f2f")
main_frame.pack(fill='both', expand=True, padx=10, pady=10)

guild_frame = tk.Frame(main_frame, bg="#2f2f2f")
guild_frame.pack(side='left', fill='both', expand=True, padx=(0,5))

guild_label = tk.Label(guild_frame, text="Guilds", bg="#2f2f2f", fg="white", font=("Arial", 14, "bold"))
guild_label.pack()

guild_tree = ttk.Treeview(guild_frame, columns=("GuildName", "GuildID"), show='headings', selectmode='browse', style="Treeview")
guild_tree.pack(fill='both', expand=True)
guild_tree.heading("GuildName", text="Guild Name")
guild_tree.heading("GuildID", text="Guild ID")
guild_tree.column("GuildName", anchor='center')
guild_tree.column("GuildID", anchor='center')

guild_result_label = tk.Label(guild_frame, text="Selected Guild: N/A", bg="#2f2f2f", fg="white", font=font_style)
guild_result_label.pack(pady=5)

delete_guild_btn = tk.Button(guild_frame, text="Delete Selected Guild", command=delete_selected_guild, bg="#555555", fg="white", font=font_style, activebackground="#666666")
delete_guild_btn.pack(fill='x', pady=5)

bases_frame = tk.Frame(main_frame, bg="#2f2f2f")
bases_frame.pack(side='right', fill='both', expand=True, padx=(5,0))

bases_label = tk.Label(bases_frame, text="Bases", bg="#2f2f2f", fg="white", font=("Arial", 14, "bold"))
bases_label.pack()

bases_tree = ttk.Treeview(bases_frame, columns=("BaseID",), show='headings', selectmode='browse', style="Treeview")
bases_tree.pack(fill='both', expand=True)
bases_tree.heading("BaseID", text="Base ID")
bases_tree.column("BaseID", anchor='center')

base_result_label = tk.Label(bases_frame, text="Selected Base: N/A", bg="#2f2f2f", fg="white", font=font_style)
base_result_label.pack(pady=5)

delete_base_btn = tk.Button(bases_frame, text="Delete Selected Base", command=delete_selected_base, bg="#555555", fg="white", font=font_style, activebackground="#666666")
delete_base_btn.pack(fill='x', pady=5)

choose_button = tk.Button(window, text="Load Level.sav", command=choose_level_file, bg="#555555", fg="white", font=font_style, activebackground="#666666")
choose_button.pack(pady=10)

guild_tree.bind("<<TreeviewSelect>>", on_guild_select)
bases_tree.bind("<<TreeviewSelect>>", on_base_select)

window.mainloop()
