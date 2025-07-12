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
def clean_character_save_parameter_map(data_source, valid_uids):
    if "CharacterSaveParameterMap" not in data_source: return
    entries = data_source["CharacterSaveParameterMap"].get("value", [])
    keep = []
    for entry in entries:
        key = entry.get("key", {})
        value = entry.get("value", {}).get("RawData", {}).get("value", {})
        saveparam = value.get("object", {}).get("SaveParameter", {}).get("value", {})
        inst_id = key.get("InstanceId", {}).get("value", "")
        owner_uid_obj = saveparam.get("OwnerPlayerUId")
        if owner_uid_obj is None:
            keep.append(entry)
            continue
        owner_uid = owner_uid_obj.get("value", "")
        no_owner = owner_uid in ("", "00000000-0000-0000-0000-000000000000")
        player_uid = key.get("PlayerUId", {}).get("value", "")
        if (player_uid and str(player_uid).replace("-", "") in valid_uids) or \
           (str(owner_uid).replace("-", "") in valid_uids) or \
           no_owner:
            keep.append(entry)
    entries[:] = keep
def load_save():
    global current_save_path, loaded_level_json, backup_save_path
    p = filedialog.askopenfilename(title="Select Level.sav", filetypes=[("SAV","*.sav")])
    if not p: return
    if not p.endswith("Level.sav"):
        messagebox.showerror("Error!", "This is NOT Level.sav. Please select Level.sav file.")
        return
    d = os.path.dirname(p); playerdir=os.path.join(d,"Players")
    if not os.path.isdir(playerdir):
        messagebox.showerror("Error","Players folder missing"); return    
    current_save_path = d
    backup_save_path = current_save_path
    loaded_level_json = sav_to_json(p)
    build_player_levels()
    refresh_all()
    print(f"Done loading the save!")
def save_changes():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    if not current_save_path or not loaded_level_json: return
    backup_whole_directory(backup_save_path, "Backups/AllinOneDeletionTool")
    level_sav_path = os.path.join(current_save_path, "Level.sav")
    json_to_sav(loaded_level_json, level_sav_path)
    messagebox.showinfo("Saved", "Changes saved to Level.sav")
def format_duration(s):
    d,h = divmod(int(s),86400); hr, m = divmod(h,3600); mm, ss=divmod(m,60)
    return f"{d}d:{hr}h:{mm}m"
def get_players():
    out = []
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        gid = str(g['key'])
        players = g['value']['RawData']['value'].get('players', [])
        for p in players:
            uid_raw = p.get('player_uid')
            uid = str(uid_raw) if uid_raw is not None else ''
            name = p.get('player_info', {}).get('player_name', "Unknown")
            last = p.get('player_info', {}).get('last_online_real_time')
            lastseen = "Unknown" if last is None else format_duration((tick - last) / 1e7)
            level = player_levels.get(uid.replace('-', ''), '?') if uid else '?'
            out.append((uid, name, gid, lastseen, level))
    return out
def refresh_all():
    guild_tree.delete(*guild_tree.get_children())
    base_tree.delete(*base_tree.get_children())
    player_tree.delete(*player_tree.get_children())
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value']=='EPalGroupType::Guild':
            name=g['value']['RawData']['value'].get('guild_name',"Unknown"); gid=as_uuid(g['key'])
            guild_tree.insert("","end",values=(name,gid))
    for uid,name,gid,seen,level in get_players():
        player_tree.insert("", "end", iid=uid, values=(uid, name, gid, seen, level))
def on_guild_search(evt=None):
    q = guild_search_var.get().lower()
    guild_tree.delete(*guild_tree.get_children())
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        name = g['value']['RawData']['value'].get('guild_name', 'Unknown')
        gid = as_uuid(g['key'])
        if q in name.lower() or q in gid.lower():
            guild_tree.insert("", "end", values=(name, gid))
def on_base_search(evt=None):
    q = base_search_var.get().lower()
    base_tree.delete(*base_tree.get_children())
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']:
        bid = str(b['key'])
        if q in bid.lower():
            base_tree.insert("", "end", values=(bid,))
def on_player_search(evt=None):
    q = player_search_var.get().lower()
    player_tree.delete(*player_tree.get_children())
    for uid, name, gid, seen, level in get_players():
        if any(q in str(c).lower() for c in (uid, name, gid, seen, level)):
            player_tree.insert("", "end", values=(uid, name, gid, seen, level))
def extract_level(data):
    while isinstance(data, dict) and 'value' in data:
        data = data['value']
    return data
from collections import defaultdict
player_levels = {}
def build_player_levels():
    global player_levels
    char_map = loaded_level_json['properties']['worldSaveData']['value'].get('CharacterSaveParameterMap', {}).get('value', [])
    uid_level_map = defaultdict(lambda: '?')
    for entry in char_map:
        key = entry.get('key', {})
        val = entry.get('value', {}).get('RawData', {}).get('value', {})
        uid_obj = key.get('PlayerUId', {})
        uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
        level = extract_level(val.get('object', {}).get('SaveParameter', {}).get('value', {}).get('Level', '?'))
        if uid: uid_level_map[uid.replace('-', '')] = level
    player_levels = dict(uid_level_map)
def on_guild_select(evt):
    sel = guild_tree.selection()
    if not sel:
        guild_members_tree.delete(*guild_members_tree.get_children())
        base_tree.delete(*base_tree.get_children())
        guild_result.config(text="Selected Guild: N/A")
        return
    name, gid = guild_tree.item(sel[0])['values']
    guild_result.config(text=f"Selected Guild: {name}")
    base_tree.delete(*base_tree.get_children())
    guild_members_tree.delete(*guild_members_tree.get_children())
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']:
        if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
            base_tree.insert("", "end", values=(str(b['key']),))
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], gid):
            raw = g['value'].get('RawData', {}).get('value', {})
            players = raw.get('players', [])
            for p in players:
                p_name = p.get('player_info', {}).get('player_name', 'Unknown')
                p_uid_raw = p.get('player_uid', '')
                p_uid = str(p_uid_raw).replace('-', '')
                p_level = player_levels.get(p_uid, '?')
                guild_members_tree.insert("", "end", values=(p_name, p_level, p_uid))
            break
def on_base_select(evt):
    sel=base_tree.selection()
    if not sel: return
    base_result.config(text=f"Selected Base: {base_tree.item(sel[0])['values'][0]}")
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
    map_obj_ids_to_delete = {m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id')
                             for m in map_objs
                             if m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('base_camp_id_belong_to') == base_id}
    if map_obj_ids_to_delete:
        mod_list = loaded_json['properties']['worldSaveData']['value']['MapObjectSaveData']['value']['values']
        mod_list[:] = [m for m in mod_list if m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id') not in map_obj_ids_to_delete]
    base_list = loaded_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']
    base_list[:] = [b for b in base_list if b['key'] != base_id]
    print(f"Deleted base camp {base_id} for guild {guild_id}")
    return True
def delete_selected_guild():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    sel = guild_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select guild")
        return
    gid = guild_tree.item(sel[0])['values'][1]
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    players_folder = os.path.join(current_save_path, 'Players')
    deleted_uids = set()
    for g in wsd.get('GroupSaveDataMap', {}).get('value', []):
        if are_equal_uuids(g['key'], gid):
            for p in g['value']['RawData']['value'].get('players', []):
                deleted_uids.add(str(p.get('player_uid', '')).replace('-', ''))
            break
    for uid in deleted_uids:
        f = os.path.join(players_folder, uid + '.sav')
        if os.path.exists(f): os.remove(f)
    for b in wsd.get('BaseCampSaveData', {}).get('value', [])[:]:
        if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
            delete_base_camp(b, gid, loaded_level_json)
    guilds = wsd.get('GroupSaveDataMap', {}).get('value', [])
    wsd['GroupSaveDataMap']['value'] = [g for g in guilds if not are_equal_uuids(g['key'], gid)]
    valid_uids = {
        str(p.get('player_uid', '')).replace('-', '')
        for g in wsd['GroupSaveDataMap']['value']
        if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
        for p in g['value']['RawData']['value'].get('players', [])
    }
    char_save_map = wsd.get("CharacterSaveParameterMap", {}).get("value", [])
    char_save_map[:] = [
        entry for entry in char_save_map
        if not (
            entry['value']['RawData']['value']['object']['SaveParameter']['struct_type'] == 'PalIndividualCharacterSaveParameter'
            and entry['value']['RawData']['value']['object']['SaveParameter']['value'].get('IsPlayer', {}).get('value', False)
            and str(entry['key']['PlayerUId']['value']).replace("-", "") not in valid_uids
        )
    ]
    clean_character_save_parameter_map(wsd, valid_uids)
    refresh_all()
    messagebox.showinfo("Deleted", "Guild, players, and all their pals successfully deleted")
def delete_selected_base():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    sel = base_tree.selection()
    if not sel: messagebox.showerror("Error", "Select base"); return
    bid = base_tree.item(sel[0])['values'][0]
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value'][:]:
        if str(b['key']) == bid:
            delete_base_camp(b, b['value']['RawData']['value'].get('group_id_belong_to'), loaded_level_json)
            break
    refresh_all()
    messagebox.showinfo("Deleted", "Base deleted")
def get_owner_uid(entry):
    try:
        return entry["value"]["object"]["SaveParameter"]["value"]["OwnerPlayerUId"].get("value", "")
    except Exception:
        return ""
def delete_selected_player():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    sel = player_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select player")
        return
    uid = player_tree.item(sel[0])['values'][0].replace('-', '')
    players_folder = os.path.join(current_save_path, 'Players')
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    deleted = False
    for group in wsd['GroupSaveDataMap']['value']:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        raw = group['value']['RawData']['value']
        original_players = raw.get('players', [])
        keep_players = []
        for player in original_players:
            player_uid = str(player.get('player_uid', '')).replace('-', '')
            if player_uid == uid:
                player_path = os.path.join(players_folder, player_uid + '.sav')
                if os.path.exists(player_path):
                    os.remove(player_path)
                deleted = True
            else:
                keep_players.append(player)
        if len(keep_players) != len(original_players):
            raw['players'] = keep_players
            admin_uid = str(raw.get('admin_player_uid', '')).replace('-', '')
            keep_uids = [str(p.get('player_uid', '')).replace('-', '') for p in keep_players]
            if admin_uid not in keep_uids:
                raw['admin_player_uid'] = "00000000-0000-0000-0000-000000000000"
    if deleted:
        char_save_map = wsd.get("CharacterSaveParameterMap", {}).get("value", [])
        char_save_map[:] = [
            entry for entry in char_save_map
            if not (
                entry['value']['RawData']['value']['object']['SaveParameter']['struct_type'] == 'PalIndividualCharacterSaveParameter'
                and entry['value']['RawData']['value']['object']['SaveParameter']['value'].get('IsPlayer', {}).get('value', False)
                and str(entry['key']['PlayerUId']['value']).replace("-", "") == uid
            )
        ]
        valid_uids = {
            str(p.get('player_uid', '')).replace('-', '')
            for g in wsd['GroupSaveDataMap']['value']
            if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
            for p in g['value']['RawData']['value'].get('players', [])
        }
        clean_character_save_parameter_map(wsd, valid_uids)
        refresh_all()
        messagebox.showinfo("Deleted", "Player deleted successfully!")
    else:
        messagebox.showinfo("Info", "Player not found or already deleted.")
def delete_inactive_bases():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    d = simpledialog.askinteger("Delete Inactive Bases", "Delete bases where ALL players inactive for how many days?")
    if d is None: return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    to_clear = []
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        allold = True
        for p in g['value']['RawData']['value'].get('players', []):
            last_online = p.get('player_info', {}).get('last_online_real_time')
            if last_online is None or ((tick - last_online) / 1e7) / 86400 < d:
                allold = False; break
        if allold: to_clear.append(as_uuid(g['key']))
    cnt = 0
    for b in wsd['BaseCampSaveData']['value'][:]:
        gid = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
        if gid in to_clear:
            if delete_base_camp(b, gid, loaded_level_json): cnt += 1
    refresh_all()
    messagebox.showinfo("Done", f"Deleted {cnt} bases")
def is_valid_level(level):
    try:
        return int(level) > 0
    except:
        return False
def delete_empty_guilds():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    build_player_levels()
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data = wsd['GroupSaveDataMap']['value']
    to_delete = []
    for g in group_data:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        players = g['value']['RawData']['value'].get('players', [])
        if not players:
            to_delete.append(g)
            continue
        all_invalid = True
        for p in players:
            if isinstance(p, dict) and 'player_uid' in p:
                uid_obj = p['player_uid']
                if hasattr(uid_obj, 'hex'):
                    uid = uid_obj.hex
                else:
                    uid = str(uid_obj)
            else:
                uid = str(p)
            uid = uid.replace('-', '')
            level = player_levels.get(uid, None)
            if is_valid_level(level):
                all_invalid = False
                break
        if all_invalid:
            to_delete.append(g)
    for g in to_delete:
        gid = as_uuid(g['key'])
        bases = wsd.get('BaseCampSaveData', {}).get('value', [])[:]
        for b in bases:
            if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                delete_base_camp(b, gid, loaded_level_json)
        group_data.remove(g)
    refresh_all()
    messagebox.showinfo("Done", f"Deleted {len(to_delete)} guild(s)")
def on_player_select(evt):
    sel = player_tree.selection()
    if not sel: return
    uid, name, *_ = player_tree.item(sel[0])['values']
    player_result.config(text=f"Selected Player: {name} ({uid})")
def delete_inactive_players_button():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    d = simpledialog.askinteger("Days", "Delete players inactive for days?")
    if d is None: return
    delete_inactive_players(folder, inactive_days=d)
def delete_inactive_players(folder_path, inactive_days=30):
    players_folder = os.path.join(folder_path, 'Players')
    if not os.path.exists(players_folder): return
    build_player_levels()
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick_now = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    deleted_info = []
    group_data_list = wsd['GroupSaveDataMap']['value']
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        original_players = raw.get('players', [])
        keep_players = []
        for player in original_players:
            uid_obj = player.get('player_uid', '')
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj).replace('-', '')
            player_name = player.get('player_info', {}).get('player_name', 'Unknown')
            last_online = player.get('player_info', {}).get('last_online_real_time')
            level = player_levels.get(uid)
            inactive = last_online is not None and ((tick_now - last_online) / 864000000000) >= inactive_days
            if inactive or not is_valid_level(level):
                player_path = os.path.join(players_folder, uid + '.sav')
                if os.path.exists(player_path): os.remove(player_path)
                reason = "Inactive" if inactive else "Invalid level"
                extra = f" - Inactive for {format_duration((tick_now - last_online)/1e7)}" if inactive and last_online else ""
                deleted_info.append(f"{player_name} ({uid}) - {reason}{extra}")
                char_map = wsd.get("CharacterSaveParameterMap", {}).get("value", [])
                char_map[:] = [entry for entry in char_map
                               if str(entry.get("key", {}).get("PlayerUId", {}).get("value", "")).replace("-", "") != uid]
            else:
                keep_players.append(player)
        if len(keep_players) != len(original_players):
            raw['players'] = keep_players
            admin_uid = str(raw.get('admin_player_uid', '')).replace('-', '')
            keep_uids = [str(p.get('player_uid', '')).replace('-', '') for p in keep_players]
            if admin_uid not in keep_uids: raw['admin_player_uid'] = "00000000-0000-0000-0000-000000000000"
    if deleted_info:
        valid_uids = {
            str(p.get('player_uid', '')).replace('-', '')
            for g in wsd['GroupSaveDataMap']['value']
            if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
            for p in g['value']['RawData']['value'].get('players', [])
        }
        clean_character_save_parameter_map(wsd, valid_uids)
        refresh_all()
        messagebox.showinfo("Success", f"Deleted {len(deleted_info)} player(s)!")
    else:
        messagebox.showinfo("Info", "No players found for deletion.")
def delete_duplicated_players():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick_now = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    group_data_list = wsd['GroupSaveDataMap']['value']
    uid_to_player = {}
    uid_to_group = {}
    deleted_players = []
    def format_duration(ticks):
        total_seconds = int(ticks / 1e7)
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        return f"{days}d:{hours}h:{minutes}m ago"
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        for player in players[:]:
            uid_obj = player.get('player_uid', '')
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj).replace('-', '')
            player_name = player.get('player_info', {}).get('player_name', 'Unknown')
            guild_id = group['key']
            last_online = player.get('player_info', {}).get('last_online_real_time') or 0
            days_inactive = (tick_now - last_online) / 864000000000 if last_online else float('inf')
            if uid in uid_to_player:
                existing_player = uid_to_player[uid]
                existing_group = uid_to_group[uid]
                existing_raw = existing_group['value']['RawData']['value']
                existing_lo = existing_player.get('player_info', {}).get('last_online_real_time') or 0
                existing_days_inactive = (tick_now - existing_lo) / 864000000000 if existing_lo else float('inf')
                existing_name = existing_player.get('player_info', {}).get('player_name', 'Unknown')
                existing_gid = existing_group['key']
                if days_inactive > existing_days_inactive:
                    raw['players'] = [p for p in players if str(p.get('player_uid', '')).replace('-', '') != uid]
                    deleted_players.append({
                        'deleted_uid': uid,
                        'deleted_name': player_name,
                        'deleted_gid': guild_id,
                        'deleted_last_online': last_online,
                        'kept_uid': uid,
                        'kept_name': existing_name,
                        'kept_gid': existing_gid,
                        'kept_last_online': existing_lo
                    })
                else:
                    existing_raw['players'] = [p for p in existing_raw.get('players', []) if str(p.get('player_uid', '')).replace('-', '') != uid]
                    deleted_players.append({
                        'deleted_uid': uid,
                        'deleted_name': existing_name,
                        'deleted_gid': existing_gid,
                        'deleted_last_online': existing_lo,
                        'kept_uid': uid,
                        'kept_name': player_name,
                        'kept_gid': guild_id,
                        'kept_last_online': last_online
                    })
                    uid_to_player[uid] = player
                    uid_to_group[uid] = group
            else:
                uid_to_player[uid] = player
                uid_to_group[uid] = group
    refresh_all()
    for d in deleted_players:
        print(f"KEPT    -> UID: {d['kept_uid']}, Name: {d['kept_name']}, Guild ID: {d['kept_gid']}, Last Online: {format_duration(tick_now - d['kept_last_online'])}")
        print(f"DELETED -> UID: {d['deleted_uid']}, Name: {d['deleted_name']}, Guild ID: {d['deleted_gid']}, Last Online: {format_duration(tick_now - d['deleted_last_online'])}\n")
    print(f"Deleted {len(deleted_players)} duplicate player(s)...")
def on_guild_members_search(event=None):
    q = guild_members_search_var.get().lower()
    guild_members_tree.delete(*guild_members_tree.get_children())
    sel = guild_tree.selection()
    if not sel: return
    gid = guild_tree.item(sel[0])['values'][1]
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], gid):
            raw = g['value'].get('RawData', {}).get('value', {})
            players = raw.get('players', [])
            for p in players:
                p_name = p.get('player_info', {}).get('player_name', 'Unknown')
                p_uid_raw = p.get('player_uid', '')
                p_uid = str(p_uid_raw).replace('-', '')
                p_level = player_levels.get(p_uid, '?')
                if q in p_name.lower() or q in str(p_level).lower() or q in p_uid.lower():
                    guild_members_tree.insert("", "end", values=(p_name, p_level, p_uid))
            break
def on_guild_member_select(event=None):
    pass    
window = tk.Tk()
window.title("All in One Deletion Tool")
window.geometry("1200x700")
window.config(bg="#2f2f2f")
font = ("Arial", 10)
s = ttk.Style(window)
s.theme_use('clam')
try: window.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "resources", "pal.ico"))
except Exception: pass
for opt in [
    ("Treeview.Heading", {"font": ("Arial", 12, "bold"), "background": "#444", "foreground": "white"}),
    ("Treeview", {"background": "#333", "foreground": "white", "fieldbackground": "#333"}),
    ("TFrame", {"background": "#2f2f2f"}),
    ("TLabel", {"background": "#2f2f2f", "foreground": "white"}),
    ("TEntry", {"fieldbackground": "#444", "foreground": "white"}),
    ("Dark.TButton", {"background": "#555555", "foreground": "white", "font": font, "padding": 6}),
]:
    s.configure(opt[0], **opt[1])
s.map("Dark.TButton",
      background=[("active", "#666666"), ("!disabled", "#555555")],
      foreground=[("disabled", "#888888"), ("!disabled", "white")])
def create_search_panel(parent, label_text, search_var, search_callback, tree_columns, tree_headings, tree_col_widths, width, height, tree_height=24):
    panel = ttk.Frame(parent, style="TFrame")
    panel.place(width=width, height=height)
    topbar = ttk.Frame(panel, style="TFrame")
    topbar.pack(fill='x', padx=5, pady=5)
    lbl = ttk.Label(topbar, text=label_text, font=("Arial", 10), style="TLabel")
    lbl.pack(side='left')
    entry = ttk.Entry(topbar, textvariable=search_var)
    entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
    search_var.trace_add('write', lambda *a: search_callback(None))
    tree = ttk.Treeview(panel, columns=tree_columns, show='headings', height=tree_height)
    tree.pack(fill='both', expand=True, padx=5, pady=(0, 5))
    for col, head, width_col in zip(tree_columns, tree_headings, tree_col_widths):
        tree.heading(col, text=head)
        tree.column(col, width=width_col, anchor='w')
    return panel, tree, entry
guild_search_var = tk.StringVar()
gframe, guild_tree, guild_search_entry = create_search_panel(window, "Search Guilds:", guild_search_var, on_guild_search,
    ("Name", "ID"), ("Guild Name", "Guild ID"), (130, 130), 310, 600)
gframe.place(x=10, y=40)
guild_tree.bind("<<TreeviewSelect>>", on_guild_select)
base_search_var = tk.StringVar()
bframe, base_tree, base_search_entry = create_search_panel(window, "Search Bases:", base_search_var, on_base_search,
    ("ID",), ("Base ID",), (280,), 310, 280)
bframe.place(x=330, y=40)
base_tree.bind("<<TreeviewSelect>>", on_base_select)
guild_members_search_var = tk.StringVar()
gm_frame, guild_members_tree, guild_members_search_entry = create_search_panel(
    window, "Guild Members:", guild_members_search_var, on_guild_members_search,
    ("Name", "Level", "UID"), ("Member", "Level", "UID"), (100, 50, 140), 310, 320)
gm_frame.place(x=330, y=320)
guild_members_tree.bind("<<TreeviewSelect>>", on_guild_member_select)
player_search_var = tk.StringVar()
pframe, player_tree, player_search_entry = create_search_panel(
    window, "Search Players:", player_search_var, on_player_search,
    ("UID", "Name", "GID", "Last", "Level"),
    ("Player UID", "Player Name", "Guild ID", "Last Seen", "Level"),
    (100, 120, 120, 90, 50),
    540, 600)
pframe.place(x=650, y=40)
player_tree.bind("<<TreeviewSelect>>", on_player_select)
guild_result = tk.Label(window, text="Selected Guild: N/A", bg="#2f2f2f", fg="white", font=font)
guild_result.place(x=10, y=10)
base_result = tk.Label(window, text="Selected Base: N/A", bg="#2f2f2f", fg="white", font=font)
base_result.place(x=330, y=10)
player_result = tk.Label(window, text="Selected Player: N/A", bg="#2f2f2f", fg="white", font=font)
player_result.place(x=650, y=10)
btn_save_changes = ttk.Button(window, text="Save Changes", command=save_changes, style="Dark.TButton")
btn_save_changes.place(x=650 + 540 - 5 - btn_save_changes.winfo_reqwidth(), y=10)
window.update_idletasks()
btn_load_save = ttk.Button(window, text="Load Level.sav", command=load_save, style="Dark.TButton")
btn_load_save.place(x=btn_save_changes.winfo_x() - 10 - btn_load_save.winfo_reqwidth(), y=10)
window.update_idletasks()
btn_delete_guild = ttk.Button(window, text="Delete Selected Guild", command=delete_selected_guild, style="Dark.TButton")
btn_delete_guild.place(x=20, y=40 + 600 + 10)
btn_delete_empty_guilds = ttk.Button(window, text="Delete Empty Guilds", command=delete_empty_guilds, style="Dark.TButton")
btn_delete_empty_guilds.place(x=20 + btn_delete_guild.winfo_reqwidth() + 10, y=40 + 600 + 10)
btn_delete_base = ttk.Button(window, text="Delete Selected Base", command=delete_selected_base, style="Dark.TButton")
btn_delete_base.place(x=330 + 5, y=40 + 600 + 10)
btn_delete_inactive_bases = ttk.Button(window, text="Delete Inactive Bases", command=delete_inactive_bases, style="Dark.TButton")
btn_delete_inactive_bases.place(x=330 + 310 - 5 - btn_delete_inactive_bases.winfo_reqwidth(), y=40 + 600 + 10)
y_pos = 40 + 600 + 10
base_x = 650
panel_width = 540
btn_delete_player = ttk.Button(window, text="Delete Selected Player", command=delete_selected_player, style="Dark.TButton")
btn_fix_duplicate_players = ttk.Button(window, text="Delete Duplicate Players", command=delete_duplicated_players, style="Dark.TButton")
btn_delete_inactive_players = ttk.Button(window, text="Delete Inactive Players", command=delete_inactive_players_button, style="Dark.TButton")
btn_delete_player.place(x=base_x + panel_width * 0.18 - (btn_delete_player.winfo_reqwidth() // 2), y=y_pos)
btn_fix_duplicate_players.place(x=base_x + panel_width * 0.50 - (btn_fix_duplicate_players.winfo_reqwidth() // 2), y=y_pos)
btn_delete_inactive_players.place(x=base_x + panel_width * 0.82 - (btn_delete_inactive_players.winfo_reqwidth() // 2), y=y_pos)
window.mainloop()