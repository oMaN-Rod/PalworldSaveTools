from import_libs import *
from datetime import datetime, timedelta
from common import ICON_PATH
level_sav_path, host_sav_path, t_level_sav_path, t_host_sav_path = None, None, None, None
level_json, host_json, targ_lvl, targ_json = None, None, None, None
target_section_ranges, target_save_type, target_raw_gvas, targ_json_gvas = None, None, None, None
selected_source_player, selected_target_player = None, None
source_guild_dict, target_guild_dict = dict(), dict()
source_section_load_handle, target_section_load_handle = None, None
STRUCT_START = b'\x0f\x00\x00\x00StructProperty\x00'
MAP_START = b'\x0c\x00\x00\x00MapProperty\x00'
ARRAY_START = b'\x0e\x00\x00\x00ArrayProperty\x00'
def backup_whole_directory(source_folder, backup_folder):
    if not os.path.isabs(backup_folder):
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        backup_folder = os.path.abspath(os.path.join(base_path, backup_folder))
    if not os.path.exists(backup_folder): os.makedirs(backup_folder)
    print("Now backing up the whole directory of the Level.sav's location...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_folder, f"PalworldSave_backup_{timestamp}")
    shutil.copytree(source_folder, backup_path)
    print(f"Backup of {source_folder} created at: {backup_path}")
def _convert_stringval(value):
    if hasattr(value, 'typename'):
        value = str(value)
        try:
            value = int(value)
        except (ValueError, TypeError):
            pass
    return value
ttk._convert_stringval = _convert_stringval
def safe_uuid_str(u):
    if isinstance(u, str):
        return u
    if hasattr(u, 'hex'):
        return str(u)
    from uuid import UUID
    if isinstance(u, bytes) and len(u) == 16:
        return str(UUID(bytes=u))
    return str(u)
class MyReader(FArchiveReader):
    def __init__(self, data, type_hints=None, custom_properties=None, debug=False, allow_nan=True):
        super().__init__(data, type_hints=type_hints or {}, custom_properties=custom_properties or {}, debug=debug, allow_nan=allow_nan)
        self.orig_data = data
        self.data = io.BytesIO(data)
    def curr_property(self, path=""):
        properties = {}
        name = self.fstring()
        type_name = self.fstring()
        size = self.u64()
        properties[name] = self.property(type_name, size, f"{path}.{name}")
        return properties
    def load_section(self, property_name, type_start=STRUCT_START, path='.worldSaveData', reverse=False):
        def encode_property_name(name):
            return struct.pack('i', len(name) + 1) + name.encode('ascii') + b'\x00'
        def find_property_start(data, property_name, type_start, reverse):
            target = encode_property_name(property_name) + type_start
            return data.rfind(target) if reverse else data.find(target)
        start_index = find_property_start(self.orig_data, property_name, type_start, reverse)
        self.data.seek(start_index)
        return self.curr_property(path=path), (start_index, self.data.tell())
    def load_sections(self, prop_types, path='.worldSaveData', reverse=False):
        def encode_property_name(name):
            return struct.pack('i', len(name) + 1) + name.encode('ascii') + b'\x00'
        def find_property_start(data, property_name, type_start, offset=0, reverse=False):
            target = encode_property_name(property_name) + type_start
            return data.rfind(target, offset) if reverse else data.find(target, offset)
        properties = {}
        end_idx = 0
        section_ranges = []
        for prop, type_start in prop_types:
            start_idx = find_property_start(self.orig_data, prop, type_start, offset=end_idx, reverse=reverse)
            if start_idx == -1:
                raise ValueError(f"Property {prop} not found")
            self.data.seek(start_idx)
            properties.update(self.curr_property(path=path))
            end_idx = self.data.tell()
            section_ranges.append((start_idx, end_idx))
        return properties, section_ranges        
class MyWriter(FArchiveWriter):
    def __init__(self, custom_properties=None, debug=False):
        super().__init__(custom_properties=custom_properties or {}, debug=debug)
        self.data = io.BytesIO()
    def curr_properties(self, properties):
        for key in properties:
            if key not in ['custom_type', 'skip_type']:
                self.fstring(key)
                self.property(properties[key])
    def write_sections(self, props, section_ranges, bytes_data, parent_section_size_idx):
        props = [{k: v} for k, v in props.items()]
        prop_bytes = []
        for prop in props:
            self.curr_properties(prop)
            prop_bytes.append(self.bytes())
            self.data = io.BytesIO()
        bytes_concat_array = []
        last_end = 0
        n_bytes_more = 0
        old_size = struct.unpack('Q', bytes_data[parent_section_size_idx:parent_section_size_idx + 8])[0]
        for prop_byte, (section_start, section_end) in zip(prop_bytes, section_ranges):
            bytes_concat_array.append(bytes_data[last_end:section_start])
            bytes_concat_array.append(prop_byte)
            n_bytes_more += len(prop_byte) - (section_end - section_start)
            last_end = section_end
        bytes_concat_array.append(bytes_data[last_end:])
        new_size_bytes = struct.pack('Q', old_size + n_bytes_more)
        bytes_concat_array[0] = bytes_concat_array[0][:parent_section_size_idx] + new_size_bytes + bytes_concat_array[0][parent_section_size_idx + 8:]
        return b''.join(bytes_concat_array)
    def guid(self, u):
        self.data.write(u)
    def optional_guid(self, u):
        if u is None:
            self.bool(False)
        else:
            self.bool(True)
            self.data.write(u)
def fast_deepcopy(json_dict):
    return pickle.loads(pickle.dumps(json_dict, -1))
class SkipGvasFile(GvasFile):
    header: GvasHeader
    properties: dict[str, Any]
    trailer: bytes
    @staticmethod
    def read(
        data: bytes,
        type_hints: dict[str, str] = {},
        custom_properties: dict[str, tuple[Callable, Callable]] = {},
        allow_nan: bool = True,
    ) -> "GvasFile":
        gvas_file = SkipGvasFile()
        with MyReader(
            data,
            type_hints=type_hints,
            custom_properties=custom_properties,
            allow_nan=allow_nan,
        ) as reader:
            gvas_file.header = GvasHeader.read(reader)
            gvas_file.properties = reader.properties_until_end()
            gvas_file.trailer = reader.read_to_end()
            if gvas_file.trailer != b"\x00\x00\x00\x00":
                print(
                    f"{len(gvas_file.trailer)} bytes of trailer data, file may not have fully parsed"
                )
        return gvas_file
    def write(
        self, custom_properties: dict[str, tuple[Callable, Callable]] = {}
    ) -> bytes:
        writer = FArchiveWriter(custom_properties)
        self.header.write(writer)
        writer.properties(self.properties)
        writer.write(self.trailer)
        return writer.bytes()        
def validate_inputs():
    if not all([level_sav_path, t_level_sav_path, selected_source_player, selected_target_player]):
        messagebox.showerror("Error!", "Please have both level files and players selected before starting transfer.")
        return False
    response = messagebox.askyesno(title='WARNING', message='WARNING: Running this script WILL change your target save files and could potentially corrupt your data. It is HIGHLY recommended that you make a backup of your save folder before continuing. Press Yes if you would like to continue.')
    return response
def load_json_files():
    global host_json_gvas, targ_json_gvas, host_json, targ_json
    host_json_gvas = load_player_file(level_sav_path, selected_source_player)
    if not host_json_gvas: return False
    host_json = host_json_gvas.properties
    targ_json_gvas = load_player_file(t_level_sav_path, selected_target_player)
    if not targ_json_gvas: return False
    targ_json = targ_json_gvas.properties
    return True
def update_targ_tech_and_data():
    global host_json, targ_json
    targ_save = targ_json["SaveData"]["value"]
    host_save = host_json["SaveData"]["value"]
    if "TechnologyPoint" in host_save:
        targ_save["TechnologyPoint"] = fast_deepcopy(host_save["TechnologyPoint"])
    elif "TechnologyPoint" in targ_save:
        targ_save["TechnologyPoint"]["value"] = 0
    if "bossTechnologyPoint" in host_save:
        targ_save["bossTechnologyPoint"] = fast_deepcopy(host_save["bossTechnologyPoint"])
    elif "bossTechnologyPoint" in targ_save:
        targ_save["bossTechnologyPoint"]["value"] = 0
    targ_save["UnlockedRecipeTechnologyNames"] = fast_deepcopy(host_save.get("UnlockedRecipeTechnologyNames", {}))
    targ_save["PlayerCharacterMakeData"] = fast_deepcopy(host_save.get("PlayerCharacterMakeData", {}))
    if 'RecordData' in host_save:
        targ_save["RecordData"] = fast_deepcopy(host_save["RecordData"])
    elif 'RecordData' in targ_save:
        del targ_save['RecordData']
def gather_inventory_ids(json_data):
    inv_info = json_data["SaveData"]["value"]["InventoryInfo"]["value"]
    return {
        "main": inv_info["CommonContainerId"]["value"]["ID"]["value"],
        "key": inv_info["EssentialContainerId"]["value"]["ID"]["value"],
        "weps": inv_info["WeaponLoadOutContainerId"]["value"]["ID"]["value"],
        "armor": inv_info["PlayerEquipArmorContainerId"]["value"]["ID"]["value"],
        "foodbag": inv_info["FoodEquipContainerId"]["value"]["ID"]["value"],
        "pals": json_data["SaveData"]["value"]["PalStorageContainerId"]["value"]["ID"]["value"],
        "otomo": json_data["SaveData"]["value"]["OtomoCharacterContainerId"]["value"]["ID"]["value"],
    }
def gather_host_containers(inv_ids):
    global host_main, host_key, host_weps, host_armor, host_foodbag, host_pals, host_otomo
    host_main = host_key = host_weps = host_armor = host_foodbag = None
    host_pals = host_otomo = None
    for c in level_json["ItemContainerSaveData"]["value"]:
        cid = c["key"]["ID"]["value"]
        if cid == inv_ids["main"]: host_main = c
        elif cid == inv_ids["key"]: host_key = c
        elif cid == inv_ids["weps"]: host_weps = c
        elif cid == inv_ids["armor"]: host_armor = c
        elif cid == inv_ids["foodbag"]: host_foodbag = c
    for c in level_json["CharacterContainerSaveData"]["value"]:
        cid = c["key"]["ID"]["value"]
        if cid == inv_ids["pals"]: host_pals = c
        elif cid == inv_ids["otomo"]: host_otomo = c
def gather_and_update_dynamic_containers():
    global level_additional_dynamic_containers, targ_lvl, dynamic_guids
    dynamic_container_level_json = level_json['DynamicItemSaveData']['value']['values']
    level_additional_dynamic_containers = [(dc, dc.get('ID', {}).get('value')) for dc in dynamic_container_level_json]
    dynamic_guid_map = {local_id: i for i, (_, local_id) in enumerate(level_additional_dynamic_containers) if local_id is not None}
    dynamic_guids = set(dynamic_guid_map.keys())
    target_dynamic_containers = targ_lvl['DynamicItemSaveData']['value']['values']
    repeated_indices = set()
    for i, target_dynamic_container in enumerate(target_dynamic_containers):
        target_container_id = target_dynamic_container.get('ID')
        if target_container_id is None: continue
        target_guid = target_container_id.get('value')
        if target_guid in dynamic_guids:
            j = dynamic_guid_map[target_guid]
            target_dynamic_containers[i] = fast_deepcopy(level_additional_dynamic_containers[j][0])
            repeated_indices.add(j)
    target_dynamic_containers += [fast_deepcopy(container) for i, (container, local_id) in enumerate(level_additional_dynamic_containers) if i not in repeated_indices]
    print(f"[DEBUG] Replaced {len(repeated_indices)} dynamic containers")
def collect_param_maps(owner_uid):
    param_maps = []
    palcount = 0
    for character in level_json["CharacterSaveParameterMap"]["value"]:
        try:
            raw = character['value']['RawData']['value']
            if raw["object"]["SaveParameter"]["value"]["OwnerPlayerUId"]["value"] == owner_uid:
                param_maps.append(fast_deepcopy(character))
                palcount += 1
        except: pass
    return param_maps, palcount
def update_param_maps_for_target(param_maps, targ_pals_id, targ_uid):
    for pal in param_maps:
        slot = pal['value']['RawData']['value']["object"]["SaveParameter"]["value"]["SlotId"]["value"]
        slot["ContainerId"]["value"]["ID"]["value"] = targ_pals_id
        pal['value']['RawData']['value']["object"]["SaveParameter"]["value"]["OwnerPlayerUId"]["value"] = targ_uid
def replace_character_save_params(param_maps, targ_uid):
    new_map = []
    removed = 0
    for character in targ_lvl["CharacterSaveParameterMap"]["value"]:
        try:
            uid = character['value']['RawData']['value']['object']['SaveParameter']['value']['OwnerPlayerUId']['value']
            if uid == targ_uid:
                removed += 1
                continue
        except Exception as e: pass
        new_map.append(character)
    new_map += param_maps
    print(f"[DEBUG] Removed {removed} old pals from target.")
    print(f"[DEBUG] Added {len(param_maps)} new pals to target.")
    targ_lvl["CharacterSaveParameterMap"]["value"] = new_map
def replace_containers(inv_ids_targ):
    global host_main, host_key, host_weps, host_armor, host_foodbag, host_pals, host_otomo, targ_lvl
    for c in targ_lvl["CharacterContainerSaveData"]["value"]:
        cid = c["key"]["ID"]["value"]
        if cid == inv_ids_targ["pals"] and host_pals:
            c["value"] = fast_deepcopy(host_pals["value"])
        elif cid == inv_ids_targ["otomo"] and host_otomo:
            c["value"] = fast_deepcopy(host_otomo["value"])
    for c in targ_lvl["ItemContainerSaveData"]["value"]:
        cid = c["key"]["ID"]["value"]
        if cid == inv_ids_targ["main"] and host_main:
            c["value"] = fast_deepcopy(host_main["value"])
        elif cid == inv_ids_targ["key"] and host_key:
            c["value"] = fast_deepcopy(host_key["value"])
        elif cid == inv_ids_targ["weps"] and host_weps:
            c["value"] = fast_deepcopy(host_weps["value"])
        elif cid == inv_ids_targ["armor"] and host_armor:
            c["value"] = fast_deepcopy(host_armor["value"])
        elif cid == inv_ids_targ["foodbag"] and host_foodbag:
            c["value"] = fast_deepcopy(host_foodbag["value"])
def get_exported_map(host_guid):
    host_instance_id = host_json["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
    for character_save_param in level_json["CharacterSaveParameterMap"]["value"]:
        try:
            player_uid = character_save_param["key"]["PlayerUId"]["value"]
            inst_id = character_save_param["key"]["InstanceId"]["value"]
            if player_uid == host_guid and inst_id == host_instance_id:
                return character_save_param
        except Exception:
            continue
    return None
def update_target_character_with_exported_map(targ_uid, exported_map):
    targ_instance_id = targ_json["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
    updated = 0
    for i, character in enumerate(targ_lvl["CharacterSaveParameterMap"]["value"]):
        try:
            key = character.get("key", {})
            player_uid = key.get("PlayerUId", {}).get("value")
            inst_id = key.get("InstanceId", {}).get("value")
            if player_uid == targ_uid and inst_id == targ_instance_id:
                character['value'] = exported_map['value']
                updated += 1
                print(f"[DEBUG] Replaced target character data at index {i} with exported_map for OwnerUID {targ_uid} and InstanceId {targ_instance_id}")
        except Exception as e:
            print(f"[DEBUG] Exception updating character index {i}: {e}")
    if updated == 0:
        print(f"[DEBUG] No matching target characters found with OwnerUID {targ_uid} and InstanceId {targ_instance_id}")
    return updated
def update_guild_data(targ_lvl, targ_json, host_guid, char_instanceid, keep_old_guild_id, source_guild_dict):
    group_id = None
    targ_uid = targ_json["SaveData"]["value"]["IndividualId"]["value"]["PlayerUId"]["value"]
    if not keep_old_guild_id:
        for group_data in targ_lvl["GroupSaveDataMap"]["value"]:
            if group_data["value"]["GroupType"]["value"]["value"] == "EPalGroupType::Guild":
                if targ_uid in [player_item['player_uid'] for player_item in group_data["value"]["RawData"]["value"]["players"]]:
                    group_id = group_data["value"]["RawData"]["value"]['group_id']
                    guild_items_json = group_data["value"]["RawData"]["value"]["individual_character_handle_ids"]
                    break
        if group_id is None:
            messagebox.showerror(message='Guild ID not found, aborting...')
            return False
        guild_item_instances = set(guild_item['instance_id'] for guild_item in guild_items_json)
    else:
        for group_idx, group_data in enumerate(targ_lvl["GroupSaveDataMap"]["value"]):
            if group_data["value"]["GroupType"]["value"]["value"] == "EPalGroupType::Guild" and group_data["key"] not in source_guild_dict:
                new_character_guild_found = False
                for player_idx, player_item in enumerate(group_data["value"]["RawData"]["value"]["players"]):
                    if player_item['player_uid'] == targ_uid:
                        new_character_guild_found = True
                        break
                if new_character_guild_found:
                    group_data["value"]["RawData"]["value"]["players"].pop(player_idx)
                    if group_data["value"]["RawData"]["value"]["players"]:
                        if group_data["value"]["RawData"]["value"]["admin_player_uid"] == targ_uid:
                            group_data["value"]["RawData"]["value"]["admin_player_uid"] = group_data["value"]["RawData"]["value"]["players"][0]['player_uid']
                        for handle_idx, character_handle_id in enumerate(group_data["value"]["RawData"]["value"]["individual_character_handle_ids"]):
                            if character_handle_id['guid'] == targ_uid:
                                group_data["value"]["RawData"]["value"]["individual_character_handle_ids"].pop(handle_idx)
                    else:
                        targ_lvl["GroupSaveDataMap"]["value"].pop(group_idx)
                    break
        for group_data in targ_lvl["GroupSaveDataMap"]["value"]:
            if group_data["key"] in source_guild_dict:
                old_player_found = False
                for player_item in group_data["value"]["RawData"]["value"]["players"]:
                    if player_item['player_uid'] == host_guid:
                        old_player_found = True
                        player_item['player_uid'] = targ_uid
                        break
                if old_player_found:
                    for character_handle_id in group_data["value"]["RawData"]["value"]["individual_character_handle_ids"]:
                        if character_handle_id['guid'] == host_guid:
                            character_handle_id['guid'] = targ_uid
                            character_handle_id['instance_id'] = char_instanceid
                            break
                    if group_data["value"]["RawData"]["value"]["admin_player_uid"] == host_guid:
                        group_data["value"]["RawData"]["value"]["admin_player_uid"] = targ_uid
                    group_id = group_data["key"]
                    break
        if group_id is None:
            print("No old guild containing the source player is found in target, moving guilds from old world now...")
            old_guild = None
            for group_data in source_guild_dict.values():
                for player_item in group_data["value"]["RawData"]["value"]["players"]:
                    if player_item['player_uid'] == host_guid:
                        old_guild = fast_deepcopy(group_data)
                        break
                if old_guild is not None:
                    break
            if old_guild is None:
                messagebox.showerror(message="No guild containing the source player found in the source either, aborting...")
                return False
            group_id = old_guild["key"]
            if old_guild["value"]["RawData"]["value"]["admin_player_uid"] == host_guid:
                old_guild["value"]["RawData"]["value"]["admin_player_uid"] = targ_uid
            for player_item in old_guild["value"]["RawData"]["value"]["players"]:
                if player_item['player_uid'] == host_guid:
                    player_item['player_uid'] = targ_uid
                    break
            for character_handle_id in old_guild["value"]["RawData"]["value"]["individual_character_handle_ids"]:
                if character_handle_id['guid'] == host_guid:
                    character_handle_id['guid'] = targ_uid
                    character_handle_id['instance_id'] = char_instanceid
                    break
            targ_lvl["GroupSaveDataMap"]["value"].append(old_guild)
    return True
def main():
    global host_guid, targ_uid, exported_map
    if not validate_inputs(): return
    host_guid = UUID.from_str(selected_source_player)
    targ_uid = UUID.from_str(selected_target_player)
    if not load_json_files(): return
    host_inv_ids = gather_inventory_ids(host_json)
    targ_inv_ids = gather_inventory_ids(targ_json)
    gather_host_containers(host_inv_ids)
    exported_map = get_exported_map(host_guid)
    if not exported_map:
        messagebox.showerror("Error!", f"Couldn't find exported_map for OwnerUID {host_guid}")
        return
    param_maps, palcount = collect_param_maps(host_guid)
    print(f"[DEBUG] Collected {palcount} pals from source.")
    update_param_maps_for_target(param_maps, targ_inv_ids["pals"], targ_uid)
    replace_character_save_params(param_maps, targ_uid)
    replace_containers(targ_inv_ids)
    gather_and_update_dynamic_containers()
    update_target_character_with_exported_map(targ_uid, exported_map)
    if not update_guild_data(targ_lvl, targ_json, host_guid, targ_uid, keep_old_guild_id, source_guild_dict): return
    update_targ_tech_and_data()
    print("[DEBUG] Writing back modified data.")
    save_and_backup()
    print("Transfer Successful!")
    messagebox.showinfo(title="Transfer Successful!", message='Transfer Successful!')
def save_and_backup():
    global targ_json_gvas
    print("Now saving the data...")
    WORLDSAVESIZEPREFIX = b'\x0e\x00\x00\x00worldSaveData\x00\x0f\x00\x00\x00StructProperty\x00'
    size_idx = target_raw_gvas.find(WORLDSAVESIZEPREFIX) + len(WORLDSAVESIZEPREFIX)
    output_data = MyWriter(custom_properties=PALWORLD_CUSTOM_PROPERTIES).write_sections(targ_lvl, target_section_ranges, target_raw_gvas, size_idx)
    from scan_save import GvasFile
    if targ_json_gvas is None or not hasattr(targ_json_gvas, 'header'):
        targ_json_gvas = load_player_file(t_level_sav_path, selected_target_player)
        if targ_json_gvas is None:
            raise RuntimeError("Failed to load target player's GvasFile for saving.")
    targ_json_gvas.properties = targ_json
    t_host_sav_path = os.path.join(os.path.dirname(t_level_sav_path), 'Players', selected_target_player + '.sav')
    if not os.path.exists(t_host_sav_path):
        t_host_sav_path = os.path.join(os.path.dirname(t_level_sav_path), '../Players', selected_target_player + '.sav')
    backup_folder = "Backups/Character Transfer"
    backup_whole_directory(os.path.dirname(t_level_sav_path), backup_folder)
    gvas_to_sav(t_level_sav_path, output_data)
    gvas_to_sav(t_host_sav_path, targ_json_gvas.write())
    print("Done saving the data!")
def sav_to_gvas(file):
    with open(file, 'rb') as f:
        data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data)
    return raw_gvas, save_type
def gvas_to_sav(file, gvas_data):
    sav_file_data = compress_gvas_to_sav(gvas_data, target_save_type)
    with open(file, 'wb') as out:
        out.write(sav_file_data)
def select_file():
    return filedialog.askopenfilename(filetypes=[("Palworld Saves", "*.sav *.json")])
def load_file(path):
    global status_label, root
    loaded_file, save_type = None, None
    if path.endswith(".sav"):
        loaded_file, save_type = sav_to_gvas(path)
    return loaded_file, save_type
def load_player_file(level_sav_path, player_uid):
    player_file_path = os.path.join(os.path.dirname(level_sav_path), 'Players', player_uid + '.sav')
    if not os.path.exists(player_file_path):
        player_file_path = os.path.join(os.path.dirname(level_sav_path), '../Players', player_uid + '.sav')
        if not os.path.exists(player_file_path):
            messagebox.showerror("Error!", f"Player file {player_file_path} not present")
            return None
    raw_gvas, save_type = load_file(player_file_path)
    if not raw_gvas:
        messagebox.showerror("Error!", f"Invalid file {player_file_path}")
        return
    return SkipGvasFile.read(raw_gvas)
def load_players(save_json, is_source):
    guild_dict = source_guild_dict if is_source else target_guild_dict
    if guild_dict:
        guild_dict.clear()
    players = {}
    for group_data in save_json["GroupSaveDataMap"]["value"]:
        if group_data["value"]["GroupType"]["value"]["value"] == "EPalGroupType::Guild":
            group_id = group_data["value"]["RawData"]["value"]['group_id']
            players[group_id] = group_data["value"]["RawData"]["value"]["players"]
            guild_dict[group_id] = group_data
    list_box = source_player_list if is_source else target_player_list
    list_box.configure(displaycolumns=())
    list_box.delete(*list_box.get_children())
    if is_source:
        filter_treeview.source_original_rows = []
    else:
        filter_treeview.target_original_rows = []
    rows_to_insert = []
    for guild_id, player_items in players.items():
        for player_item in player_items:
            playerUId = ''.join(safe_uuid_str(player_item['player_uid']).split('-')).upper()
            rows_to_insert.append((safe_uuid_str(guild_id), playerUId, player_item['player_info']['player_name']))
    for values in rows_to_insert:
        row_id = list_box.insert('', tk.END, values=values)
        if is_source:
            filter_treeview.source_original_rows.append(row_id)
        else:
            filter_treeview.target_original_rows.append(row_id)
    list_box.configure(displaycolumns='#all')
def load_all_source_sections_async(group_save_section, reader):
    global level_json
    level_json, _ = reader.load_sections([
        ('CharacterSaveParameterMap', MAP_START),
        ('ItemContainerSaveData', MAP_START),
        ('DynamicItemSaveData', ARRAY_START),
        ('CharacterContainerSaveData', MAP_START)],
        path='.worldSaveData')
    level_json.update(group_save_section)
def source_level_file():
    global level_sav_path, source_level_path_label, level_json, selected_source_player, source_section_load_handle
    tmp = select_file()
    if tmp:
        if not tmp.endswith("Level.sav"):
            messagebox.showerror("Error!", "This is NOT Level.sav. Please select Level.sav file.")
            return
        raw_gvas, save_type = load_file(tmp)
        if not raw_gvas:
            messagebox.showerror("Error!", "Invalid file, must be Level.sav!")
            return
        print("Now loading the data from Source Save...")
        reader = MyReader(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
        group_save_section, _ = reader.load_section('GroupSaveDataMap', MAP_START, reverse=True)
        source_section_load_handle = threading.Thread(target=load_all_source_sections_async, args=(group_save_section, reader))
        source_section_load_handle.start()
        source_section_load_handle.join()
        load_players(group_save_section, True)
        source_level_path_label.config(text=tmp)
        level_sav_path = tmp
        selected_source_player = None
        current_selection_label.config(text=f"Source: {selected_source_player}, Target: {selected_target_player}")
        print("Done loading the data from Source Save!")
def load_all_target_sections_async(group_save_section, group_save_section_range, reader):
    global targ_lvl, target_section_ranges
    targ_lvl, target_section_ranges = reader.load_sections([
        ('CharacterSaveParameterMap', MAP_START),
        ('ItemContainerSaveData', MAP_START),
        ('DynamicItemSaveData', ARRAY_START),
        ('CharacterContainerSaveData', MAP_START)],
        path='.worldSaveData')
    targ_lvl.update(group_save_section)
    target_section_ranges.append(group_save_section_range)
def target_level_file():
    global t_level_sav_path, target_level_path_label, targ_lvl, target_level_cache, target_section_ranges, target_raw_gvas, target_save_type, selected_target_player, target_section_load_handle
    tmp = select_file()
    if tmp:
        if not tmp.endswith("Level.sav"):
            messagebox.showerror("Error!", "This is NOT Level.sav. Please select Level.sav file.")
            return
        raw_gvas, target_save_type = load_file(tmp)
        if not raw_gvas:
            messagebox.showerror("Error!", "Invalid file, must be Level.sav!")
            return
        print("Now loading the data from Target Save...")
        target_raw_gvas = raw_gvas
        reader = MyReader(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
        group_save_section, group_save_section_range = reader.load_section('GroupSaveDataMap', MAP_START, reverse=True)
        target_section_load_handle = threading.Thread(target=load_all_target_sections_async, args=(group_save_section, group_save_section_range, reader))
        target_section_load_handle.start()
        load_players(group_save_section, False)
        target_level_path_label.config(text=tmp)
        t_level_sav_path = tmp
        selected_target_player = None
        current_selection_label.config(text=f"Source: {selected_source_player}, Target: {selected_target_player}")
        print("Done loading the data from Target Save!")
def on_selection_of_source_player(event):
    global selected_source_player
    selections = source_player_list.selection()
    if len(selections):
        selected_source_player = source_player_list.item(selections[0])['values'][1]
        current_selection_label.config(text=f"Source: {selected_source_player}, Target: {selected_target_player}")
def on_selection_of_target_player(event):
    global selected_target_player
    selections = target_player_list.selection()
    if len(selections):
        selected_target_player = target_player_list.item(selections[0])['values'][1]
        current_selection_label.config(text=f"Source: {selected_source_player}, Target: {selected_target_player}")
def sort_treeview_column(treeview, col_index, reverse):
    data = [(treeview.set(child, col_index), child) for child in treeview.get_children('')]
    data.sort(reverse=reverse, key=lambda x: x[0])
    for index, (_, item) in enumerate(data): treeview.move(item, '', index)
    treeview.heading(col_index, command=lambda: sort_treeview_column(treeview, col_index, not reverse))
def filter_treeview(tree, query, is_source):
    query = query.lower()
    if is_source:
        if not hasattr(filter_treeview, "source_original_rows"):
            filter_treeview.source_original_rows = [row for row in tree.get_children()]
        original_rows = filter_treeview.source_original_rows
    else:
        if not hasattr(filter_treeview, "target_original_rows"):
            filter_treeview.target_original_rows = [row for row in tree.get_children()]
        original_rows = filter_treeview.target_original_rows
    for row in original_rows:
        tree.reattach(row, '', 'end')    
    for row in tree.get_children():
        values = tree.item(row, "values")
        if any(query in str(value).lower() for value in values):
            tree.reattach(row, '', 'end')
        else:
            tree.detach(row)
window = tk.Tk()
window.title("Character Transfer")
window.geometry("")
window.minsize(800, 300)
window.config(bg="#2f2f2f")
try:
    window.iconbitmap(ICON_PATH)
except Exception as e:
    print(f"Could not set icon: {e}")
font_style = ("Arial", 10)
heading_font = ("Arial", 12, "bold")
style = ttk.Style(window)
style.theme_use('clam')
style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#444444", foreground="white")
style.configure("Treeview", background="#333333", foreground="white", rowheight=25, fieldbackground="#333333", borderwidth=0)
style.configure("TFrame", background="#2f2f2f")
style.configure("TLabel", background="#2f2f2f", foreground="white")
style.configure("TEntry", fieldbackground="#444444", foreground="white")
style.configure("Dark.TButton", background="#555555", foreground="white", padding=6)
style.map("Dark.TButton",
    background=[("active", "#666666"), ("!disabled", "#555555")],
    foreground=[("disabled", "#888888"), ("!disabled", "white")]
)
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=2)
window.rowconfigure(3, weight=1)
window.rowconfigure(5, weight=1)
source_frame = ttk.Frame(window, style="TFrame")
source_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
ttk.Label(source_frame, text="Search Source Player:", font=font_style, style="TLabel").pack(side="left", padx=(0, 5))
source_search_var = tk.StringVar()
source_search_entry = ttk.Entry(source_frame, textvariable=source_search_var, font=font_style, style="TEntry", width=20)
source_search_entry.pack(side="left", fill="x", expand=True)
source_search_entry.bind("<KeyRelease>", lambda e: filter_treeview(source_player_list, source_search_entry.get(), is_source=True))
target_frame = ttk.Frame(window, style="TFrame")
target_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
ttk.Label(target_frame, text="Search Target Player:", font=font_style, style="TLabel").pack(side="left", padx=(0, 5))
target_search_var = tk.StringVar()
target_search_entry = ttk.Entry(target_frame, textvariable=target_search_var, font=font_style, style="TEntry", width=20)
target_search_entry.pack(side="left", fill="x", expand=True)
target_search_entry.bind("<KeyRelease>", lambda e: filter_treeview(target_player_list, target_search_entry.get(), is_source=False))
ttk.Button(window, text='Select Source Level File', command=source_level_file, style="Dark.TButton").grid(row=1, column=1, padx=10, pady=20, sticky="ew")
source_level_path_label = ttk.Label(window, text="Please select a file:", font=font_style, style="TLabel", wraplength=600)
source_level_path_label.grid(row=1, column=0, padx=10, pady=20, sticky="ew")
source_player_list = ttk.Treeview(window, columns=(0, 1, 2), show='headings', style="Treeview")
source_player_list.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
source_player_list.tag_configure("even", background="#333333", foreground="white")
source_player_list.tag_configure("odd", background="#444444", foreground="white")
source_player_list.tag_configure("selected", background="#555555", foreground="white")
source_player_list.column(0, anchor='center', width=100)
source_player_list.column(1, anchor='center', width=100)
source_player_list.column(2, anchor='center', width=100)
source_player_list.heading(0, text='Guild ID', command=lambda: sort_treeview_column(source_player_list, 0, False))
source_player_list.heading(1, text='Player UID', command=lambda: sort_treeview_column(source_player_list, 1, False))
source_player_list.heading(2, text='Nickname', command=lambda: sort_treeview_column(source_player_list, 2, False))
source_player_list.bind('<<TreeviewSelect>>', on_selection_of_source_player)
ttk.Button(window, text='Select Target Level File', command=target_level_file, style="Dark.TButton").grid(row=4, column=1, padx=10, pady=20, sticky="ew")
target_level_path_label = ttk.Label(window, text="Please select a file:", font=font_style, style="TLabel", wraplength=600)
target_level_path_label.grid(row=4, column=0, padx=10, pady=20, sticky="ew")
target_player_list = ttk.Treeview(window, columns=(0, 1, 2), show='headings', style="Treeview")
target_player_list.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
target_player_list.tag_configure("even", background="#333333", foreground="white")
target_player_list.tag_configure("odd", background="#444444", foreground="white")
target_player_list.tag_configure("selected", background="#555555", foreground="white")
target_player_list.column(0, anchor='center', width=100)
target_player_list.column(1, anchor='center', width=100)
target_player_list.column(2, anchor='center', width=100)
target_player_list.heading(0, text='Guild ID', command=lambda: sort_treeview_column(target_player_list, 0, False))
target_player_list.heading(1, text='Player UID', command=lambda: sort_treeview_column(target_player_list, 1, False))
target_player_list.heading(2, text='Nickname', command=lambda: sort_treeview_column(target_player_list, 2, False))
target_player_list.bind('<<TreeviewSelect>>', on_selection_of_target_player)
current_selection_label = ttk.Label(window, text=f"Source: N/A, Target: N/A", font=font_style, style="TLabel", wraplength=600)
current_selection_label.grid(row=8, column=0, padx=10, pady=20, sticky="ew")
ttk.Button(window, text='Start Transfer!', command=main, style="Dark.TButton").grid(row=8, column=1, padx=10, pady=20, sticky="ew")
keep_old_guild_id = True
def toggle_keep_old_guild():
    global keep_old_guild_id
    keep_old_guild_id = not keep_old_guild_id
    txt = "☑ " if keep_old_guild_id else "☐ "
    btn_toggle.config(text=txt + "Keep old Guild ID after Transfer")
    print("Keep old guild id after transfer:", "on" if keep_old_guild_id else "off")
btn_toggle = tk.Button(window, text="☑ Keep old Guild ID after Transfer", command=toggle_keep_old_guild, relief="flat", fg="white", bg="#2f2f2f", activebackground="black", activeforeground="white")
btn_toggle.grid(row=9, column=0, columnspan=2, sticky='w', padx=10, pady=5)
def character_transfer():
    def on_exit():
        if window.winfo_exists():
            window.destroy()
        sys.exit()
    window.protocol("WM_DELETE_WINDOW", on_exit)
    window.mainloop()

if __name__ == "__main__":
    character_transfer()