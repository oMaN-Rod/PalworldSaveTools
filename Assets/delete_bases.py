import os, sys, shutil, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from uuid import UUID
from datetime import datetime
from scan_save import decompress_sav_to_gvas, GvasFile, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, compress_gvas_to_sav
from tkinter import simpledialog
current_save_path = None
loaded_level_json = None
def as_uuid(val): return str(val).replace('-', '').lower() if val else ''
def are_equal_uuids(a,b): return as_uuid(a)==as_uuid(b)
def backup_whole_directory(source_folder, backup_folder):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_backup_folder = os.path.join(base_dir, backup_folder)
    if not os.path.exists(full_backup_folder): os.makedirs(full_backup_folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(full_backup_folder, f"PalworldSave_backup_{timestamp}")
    shutil.copytree(source_folder, backup_path)
    print(f"Backup created at: {backup_path}")
def sav_to_json(path):
    with open(path,"rb") as f:
        data = f.read()
    raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return g.dump()
def json_to_sav(j,path):
    g = GvasFile.load(j)
    t = 0x32 if "Pal.PalworldSaveGame" in g.header.save_game_class_name else 0x31
    data = compress_gvas_to_sav(g.write(SKP_PALWORLD_CUSTOM_PROPERTIES),t)
    with open(path,"wb") as f: f.write(data)
def load_save():
    global current_save_path, loaded_level_json, backup_save_path
    p = filedialog.askopenfilename(title="Select Level.sav", filetypes=[("SAV","*.sav")])
    if not p: return
    d = os.path.dirname(p); playerdir=os.path.join(d,"Players")
    if not os.path.isdir(playerdir):
        messagebox.showerror("Error","Players folder missing"); return    
    current_save_path = d
    backup_save_path = current_save_path
    loaded_level_json = sav_to_json(p)
    refresh_all()
def format_duration(s):
    d,h = divmod(int(s),86400); hr, m = divmod(h,3600); mm, ss=divmod(m,60)
    return f"{d}d:{hr}h:{mm}m"
def get_players():
    out=[]; wsd=loaded_level_json['properties']['worldSaveData']['value']
    tick=wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value']!='EPalGroupType::Guild': continue
        gid=as_uuid(g['key'])
        players=g['value']['RawData']['value'].get('players',[])
        for p in players:
            uid=as_uuid(p.get('player_uid')); name=p.get('player_info',{}).get('player_name',"Unknown")
            last=p.get('player_info',{}).get('last_online_real_time')
            lastseen="Unknown" if last is None else format_duration((tick-last)/1e7)
            out.append((uid,name,gid,lastseen))
    return out
def refresh_all():
    guild_tree.delete(*guild_tree.get_children())
    base_tree.delete(*base_tree.get_children())
    player_tree.delete(*player_tree.get_children())
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value']=='EPalGroupType::Guild':
            name=g['value']['RawData']['value'].get('guild_name',"Unknown"); gid=as_uuid(g['key'])
            guild_tree.insert("","end",values=(name,gid))
    for uid,name,gid,seen in get_players():
        player_tree.insert("","end",values=(uid,name,gid,seen))
def on_guild_search(evt):
    q=guild_search_var.get().lower()
    for iid in guild_tree.get_children():
        v=guild_tree.item(iid)['values']; guild_tree.item(iid, tags=() if q in str(v[0]).lower() or q in v[1] else ("hid",))
    guild_tree.tag_configure("hid", foreground="#555")
def on_base_search(evt):
    q=base_search_var.get().lower()
    for iid in base_tree.get_children():
        v=base_tree.item(iid)['values']; base_tree.item(iid,tags=() if q in v[0].lower() else("h",))
    base_tree.tag_configure("h",foreground="#555")
def on_player_search(evt):
    q=player_search_var.get().lower()
    for iid in player_tree.get_children():
        v=player_tree.item(iid)['values']
        show=any(q in str(c).lower() for c in v)
        player_tree.item(iid, tags=() if show else("h",))
    player_tree.tag_configure("h",foreground="#555")
def on_guild_select(evt):
    sel=guild_tree.selection()
    if not sel: return
    name,gid=guild_tree.item(sel[0])['values']
    guild_result.config(text=f"Selected Guild: {name}")
    base_tree.delete(*base_tree.get_children())
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']:
        if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'),gid):
            base_tree.insert("","end",values=(str(b['key']),))
def on_base_select(evt):
    sel=base_tree.selection()
    if not sel: return
    base_result.config(text=f"Selected Base: {base_tree.item(sel[0])['values'][0]}")
def delete_map_object(instance_id, base_camp_id, loaded_json):
    mod_list = loaded_json['properties']['worldSaveData']['value']['MapObjectSaveData']['value']['values']
    before_count = len(mod_list)
    mod_list[:] = [m for m in mod_list if not (
        m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id') == instance_id and
        m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('base_camp_id_belong_to') == base_camp_id
    )]
    after_count = len(mod_list)
    if before_count != after_count:
        print(f"Deleted MapObject instance {instance_id} belonging to base camp {base_camp_id}")
def delete_base_camp(base, guild_id, loaded_json):
    base_val = base['value']
    raw_data = base_val.get('RawData', {}).get('value', {})
    base_id = base['key']
    base_group_id = raw_data.get('group_id_belong_to')
    if not are_equal_uuids(base_group_id, guild_id): return False
    group_data_map = loaded_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    group_data = next((g for g in group_data_map if are_equal_uuids(g['key'], guild_id)), None)
    if not group_data: return False
    group_raw = group_data['value']['RawData']['value']
    base_ids = group_raw.get('base_ids', [])
    mp_points = group_raw.get('map_object_instance_ids_base_camp_points', [])
    if base_id in base_ids:
        idx = base_ids.index(base_id)
        base_ids.pop(idx)
        if mp_points and idx < len(mp_points): mp_points.pop(idx)
    map_objs = loaded_json['properties']['worldSaveData']['value']['MapObjectSaveData']['value']['values']
    map_obj_ids_to_delete = []
    for m in map_objs:
        raw = m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
        inst_id = raw.get('instance_id')
        base_camp = raw.get('base_camp_id_belong_to')
        if base_camp == base_id:
            map_obj_ids_to_delete.append(inst_id)
    for mo_id in map_obj_ids_to_delete:
        delete_map_object(mo_id, base_id, loaded_json)
    base_list = loaded_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']
    base_list[:] = [b for b in base_list if b['key'] != base_id]
    print(f"Deleted base camp {base_id} for guild {guild_id}")
    print("Remaining base IDs:", len(base_list))
    for b in base_list: print("-", b['key'])
    return True
def delete_selected_guild():
    sel=guild_tree.selection()
    if not sel: messagebox.showerror("Error","Select guild"); return
    gid=guild_tree.item(sel[0])['values'][1]
    backup_whole_directory(backup_save_path,"Backups/DeleteGuild")
    wsd=loaded_level_json['properties']['worldSaveData']['value']
    for b in wsd['BaseCampSaveData']['value'][:]:
        if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
            delete_base_camp(b, gid, loaded_level_json)
    wsd['GroupSaveDataMap']['value'] = [g for g in wsd['GroupSaveDataMap']['value'] if as_uuid(g['key']) != gid]
    json_to_sav(loaded_level_json,os.path.join(current_save_path,"Level.sav"))
    messagebox.showinfo("Deleted","Guild and bases deleted")
    refresh_all()
def delete_selected_base():
    sel=base_tree.selection()
    if not sel: messagebox.showerror("Error","Select base"); return
    bid=base_tree.item(sel[0])['values'][0]
    backup_whole_directory(backup_save_path,"Backups/DeleteBase")
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value'][:]:
        if str(b['key']) == bid:
            delete_base_camp(b, b['value']['RawData']['value'].get('group_id_belong_to'), loaded_level_json)
            break
    json_to_sav(loaded_level_json,os.path.join(current_save_path,"Level.sav"))
    messagebox.showinfo("Deleted","Base deleted"); refresh_all()
def delete_selected_player():
    sel=player_tree.selection()
    if not sel: messagebox.showerror("Error","Select player"); return
    uid=player_tree.item(sel[0])['values'][0]
    backup_whole_directory(backup_save_path,"Backups/DeletePlayer")
    pfile=os.path.join(current_save_path,"Players",uid+".sav")
    if os.path.exists(pfile): os.remove(pfile)
    messagebox.showinfo("Deleted","Player file deleted"); refresh_all()
def delete_inactive():
    d = simpledialog.askinteger("Days", "Delete bases where ALL players inactive for days?")
    if d is None: return
    backup_whole_directory(backup_save_path, "Backups/DeleteInactive")
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    to_clear = []
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        allold = True
        for p in g['value']['RawData']['value'].get('players', []):
            last_online = p.get('player_info', {}).get('last_online_real_time')
            if last_online is None:
                allold = False
                break
            days_offline = ((tick - last_online) / 1e7) / 86400
            if days_offline < d:
                allold = False
                break
        if allold: to_clear.append(as_uuid(g['key']))
    cnt = 0
    for b in wsd['BaseCampSaveData']['value'][:]:
        gid = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
        if gid in to_clear:
            if delete_base_camp(b, gid, loaded_level_json):
                cnt += 1
    json_to_sav(loaded_level_json, os.path.join(current_save_path, "Level.sav"))
    messagebox.showinfo("Done", f"Deleted {cnt} bases")
    refresh_all() 
def on_player_select(evt):
    sel = player_tree.selection()
    if not sel: return
    uid, name, *_ = player_tree.item(sel[0])['values']
    player_result.config(text=f"Selected Player: {name} ({uid})")
def delete_inactive_players_button():
    d = simpledialog.askinteger("Days", "Delete players inactive for days?")
    if d is None: return
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    backup_whole_directory(folder, "Backups/DeleteInactivePlayers")
    delete_inactive_players(folder, inactive_days=d)
    refresh_all()
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
            if last_online is None:
                keep_players.append(player)
                continue
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
            admin_uid = str(raw.get('admin_player_uid', '')).replace('-', '')
            keep_uids = [str(p.get('player_uid', '')).replace('-', '') for p in keep_players]
            if admin_uid not in keep_uids:
                raw['admin_player_uid'] = ""
    if deleted_info:
        json_to_sav(level_json, level_sav_path)
        messagebox.showinfo("Success", f"Deleted {len(deleted_info)} inactive player(s)!")
    else:
        messagebox.showinfo("Info", "No inactive players found for deletion.")
window = tk.Tk()
window.title("All in One Deletion Tool")
window.geometry("1200x700")
window.config(bg="#2f2f2f")
font=("Arial",10)
s=ttk.Style(window)
s.theme_use('clam')
try: window.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "resources", "pal.ico"))
except Exception: pass
for opt in [
    ("Treeview.Heading",{"font":("Arial",12,"bold"),"background":"#444","foreground":"white"}),
    ("Treeview",{"background":"#333","foreground":"white","fieldbackground":"#333"}),
    ("TFrame",{"background":"#2f2f2f"}),
    ("TLabel",{"background":"#2f2f2f","foreground":"white"}),
    ("TEntry",{"fieldbackground":"#444","foreground":"white"}),
    ("Dark.TButton",{"background":"#555555","foreground":"white","font":font,"padding":6}),
]:
    s.configure(opt[0],**opt[1])
s.map("Dark.TButton",
      background=[("active", "#666666"), ("!disabled", "#555555")],
      foreground=[("disabled", "#888888"), ("!disabled", "white")])
def create_search_panel(parent, label_text, search_var, search_callback, tree_columns, tree_headings, tree_col_widths, width, height, tree_height=24):
    panel = ttk.Frame(parent, style="TFrame")
    panel.place(width=width, height=height)
    topbar = ttk.Frame(panel, style="TFrame")
    topbar.pack(fill='x', padx=5, pady=5)
    lbl = ttk.Label(topbar, text=label_text, font=("Arial",10), style="TLabel")
    lbl.pack(side='left')
    entry = ttk.Entry(topbar, textvariable=search_var)
    entry.pack(side='left', fill='x', expand=True, padx=(5,0))
    search_var.trace_add('write', lambda *a: search_callback(None))
    tree = ttk.Treeview(panel, columns=tree_columns, show='headings', height=tree_height)
    tree.pack(fill='both', expand=True, padx=5, pady=(0,5))
    for col, head, width_col in zip(tree_columns, tree_headings, tree_col_widths):
        tree.heading(col, text=head)
        tree.column(col, width=width_col, anchor='w')
    return panel, tree, entry
guild_search_var = tk.StringVar()
gframe, guild_tree, guild_search_entry = create_search_panel(window, "Search Guilds:", guild_search_var, on_guild_search,
    ("Name","ID"), ("Guild Name","Guild ID"), (130,130), 310, 600)
gframe.place(x=10,y=40)
guild_tree.bind("<<TreeviewSelect>>", on_guild_select)
base_search_var = tk.StringVar()
bframe, base_tree, base_search_entry = create_search_panel(window, "Search Bases:", base_search_var, on_base_search,
    ("ID",), ("Base ID",), (280,), 310, 600)
bframe.place(x=330,y=40)
base_tree.bind("<<TreeviewSelect>>", on_base_select)
player_search_var = tk.StringVar()
pframe, player_tree, player_search_entry = create_search_panel(window, "Search Players:", player_search_var, on_player_search,
    ("UID","Name","GID","Last"), ("Player UID","Player Name","Guild ID","Last Seen"), (100,120,120,90), 540, 600)
pframe.place(x=650,y=40)
player_tree.bind("<<TreeviewSelect>>", on_player_select)
guild_result=tk.Label(window,text="Selected Guild: N/A",bg="#2f2f2f",fg="white",font=font)
guild_result.place(x=10,y=10)
base_result=tk.Label(window,text="Selected Base: N/A",bg="#2f2f2f",fg="white",font=font)
base_result.place(x=330,y=10)
player_result=tk.Label(window,text="Selected Player: N/A",bg="#2f2f2f",fg="white",font=font)
player_result.place(x=650,y=10)
btn_load_save=ttk.Button(window,text="Load Level.sav",command=load_save, style="Dark.TButton")
btn_load_save.place(x=650 + 540 - 5 - btn_load_save.winfo_reqwidth(), y=10)
btn_delete_guild=ttk.Button(window,text="Delete Selected Guild",command=delete_selected_guild, style="Dark.TButton")
btn_delete_guild.place(x=10 + (310 // 2) - (btn_delete_guild.winfo_reqwidth() // 2), y=40 + 600 + 10)
btn_delete_base=ttk.Button(window,text="Delete Selected Base",command=delete_selected_base, style="Dark.TButton")
btn_delete_base.place(x=330 + 5, y=40 + 600 + 10)
btn_delete_inactive=ttk.Button(window,text="Delete Inactive Bases",command=delete_inactive, style="Dark.TButton")
btn_delete_inactive.place(x=330 + 310 - 5 - btn_delete_inactive.winfo_reqwidth(), y=40 + 600 + 10)
btn_delete_player=ttk.Button(window,text="Delete Selected Player",command=delete_selected_player, style="Dark.TButton")
btn_delete_player.place(x=650 + (540 // 4) - (btn_delete_player.winfo_reqwidth() // 2), y=40 + 600 + 10)
btn_delete_inactive_players=ttk.Button(window,text="Delete Inactive Players",command=delete_inactive_players_button, style="Dark.TButton")
btn_delete_inactive_players.place(x=650 + (540 * 3 // 4) - (btn_delete_inactive_players.winfo_reqwidth() // 2), y=40 + 600 + 10)
window.update_idletasks()
window.mainloop()