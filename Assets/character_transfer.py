from import_libs import *
from datetime import datetime, timedelta
STRUCT_START = b'\x0f\x00\x00\x00StructProperty\x00'
MAP_START = b'\x0c\x00\x00\x00MapProperty\x00'
ARRAY_START = b'\x0e\x00\x00\x00ArrayProperty\x00'
def backup_whole_directory(source_folder, backup_folder):
    if not os.path.exists(backup_folder): os.makedirs(backup_folder)
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
OwnerPlayerUIdSearchPrefix = b'\x0f\x00\x00\x00OwnerPlayerUId\x00\x0f\x00\x00\x00StructProperty\x00\x10\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00Guid\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
LocalIdSearchPrefix = b'\x16\x00\x00\x00LocalIdInCreatedWorld\x00\x0f\x00\x00\x00StructProperty\x00\x10\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00Guid\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
def find_id_match_prefix(encoded_bytes, prefix):
    if isinstance(encoded_bytes, dict):
        encoded_bytes = encoded_bytes.get('value', b'')
    start_idx = encoded_bytes.find(prefix)
    if start_idx == -1:
        return None
    start_idx += len(prefix)
    return encoded_bytes[start_idx:start_idx + 16]
def find_all_ids_match_prefix(encoded_bytes, prefix):
    if isinstance(encoded_bytes, dict):
        encoded_bytes = encoded_bytes.get('value', b'')
    last_idx = 0
    start_idx = encoded_bytes.find(prefix)
    ids = []
    while start_idx != last_idx - 1 and start_idx != -1:
        start_idx += len(prefix)
        last_idx = start_idx + 16
        ids.append(encoded_bytes[start_idx:last_idx])
        start_idx = encoded_bytes[last_idx:].find(prefix)
        if start_idx != -1:
            start_idx += last_idx
    return ids
def find_all_occurrences_with_prefix(encoded_bytes, prefix):
    last_idx = 0
    start_idx = encoded_bytes.find(prefix)
    end_indices = []
    while start_idx != last_idx - 1:
        start_idx += len(prefix)
        last_idx = start_idx
        end_indices.append(start_idx)
        start_idx = encoded_bytes[last_idx:].find(prefix) + last_idx
    return end_indices
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
def load_player_data():
    global host_json, targ_json, targ_json_gvas
    host_json_gvas = load_player_file(level_sav_path, selected_source_player)
    if host_json_gvas is None: return False
    host_json = host_json_gvas.properties
    targ_json_gvas = load_player_file(t_level_sav_path, selected_target_player)
    if targ_json_gvas is None: return False
    targ_json = targ_json_gvas.properties
    return True
def find_host_and_pals():
    global exported_map, param_maps, palcount
    host_guid = UUID(selected_source_player)
    host_instance_id = host_json["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
    pal_player_uid_filters = [b'\x00'*16, b'\x00'*12 + b'\x01\x00\x00\x00']
    found = False
    exported_map = {}
    param_maps = []
    palcount = 0
    for character_save_param in level_json["CharacterSaveParameterMap"]["value"]:
        instance_id = character_save_param["key"]["InstanceId"]["value"]
        if instance_id == host_instance_id:
            exported_map = character_save_param
            found = True
        elif character_save_param["key"]["PlayerUId"]["value"] in pal_player_uid_filters:
            if find_id_match_prefix(character_save_param['value']['RawData']['value'], OwnerPlayerUIdSearchPrefix) == host_guid:
                param_maps.append(fast_deepcopy(character_save_param))
                palcount += 1
    if not found:
        messagebox.showerror("Error!", "Couldn't find source character instance data in the source world save!")
        return False
    return True
def gather_host_containers():
    global inv_main, inv_key, inv_weps, inv_armor, inv_foodbag, inv_pals, inv_otomo
    global host_main, host_key, host_weps, host_armor, host_foodbag, host_pals, host_otomo, dynamic_guids
    inv_info = host_json["SaveData"]["value"].get("InventoryInfo", host_json["SaveData"]["value"].get("inventoryInfo"))["value"]
    inv_main = inv_info["CommonContainerId"]
    inv_key = inv_info["EssentialContainerId"]
    inv_weps = inv_info["WeaponLoadOutContainerId"]
    inv_armor = inv_info["PlayerEquipArmorContainerId"]
    inv_foodbag = inv_info["FoodEquipContainerId"]
    inv_pals = host_json["SaveData"]["value"]["PalStorageContainerId"]
    inv_otomo = host_json["SaveData"]["value"]["OtomoCharacterContainerId"]
    host_main = host_key = host_weps = host_armor = host_foodbag = host_pals = host_otomo = {}
    count = 0
    for container in level_json["CharacterContainerSaveData"]["value"]:
        container_id = container["key"]["ID"]["value"]
        if container_id == inv_pals["value"]["ID"]["value"]:
            host_pals = container
            count += 1
        elif container_id == inv_otomo["value"]["ID"]["value"]:
            host_otomo = container
            count += 1
        if count >= 2: break
    dynamic_guids = set()
    for container in level_json["ItemContainerSaveData"]["value"]:
        container_id = container["key"]["ID"]["value"]
        if container_id == inv_main["value"]["ID"]["value"]:
            dynamic_guids |= set(find_all_ids_match_prefix(container['value']['Slots']['value'], LocalIdSearchPrefix))
            host_main = container
            count += 1
        elif container_id == inv_key["value"]["ID"]["value"]:
            dynamic_guids |= set(find_all_ids_match_prefix(container['value']['Slots']['value'], LocalIdSearchPrefix))
            host_key = container
            count += 1
        elif container_id == inv_weps["value"]["ID"]["value"]:
            dynamic_guids |= set(find_all_ids_match_prefix(container['value']['Slots']['value'], LocalIdSearchPrefix))
            host_weps = container
            count += 1
        elif container_id == inv_armor["value"]["ID"]["value"]:
            dynamic_guids |= set(find_all_ids_match_prefix(container['value']['Slots']['value'], LocalIdSearchPrefix))
            host_armor = container
            count += 1
        elif container_id == inv_foodbag["value"]["ID"]["value"]:
            dynamic_guids |= set(find_all_ids_match_prefix(container['value']['Slots']['value'], LocalIdSearchPrefix))
            host_foodbag = container
            count += 1
        if count >= 7: break
    dynamic_guids.discard(b'\x00' * 16)
def update_targ_tech_and_data():
    targ_save = targ_json["SaveData"]["value"]
    host_save = host_json["SaveData"]["value"]
    if "TechnologyPoint" in host_save:
        targ_save["TechnologyPoint"] = host_save["TechnologyPoint"]
    elif "TechnologyPoint" in targ_save:
        targ_save["TechnologyPoint"]["value"] = 0
    if "bossTechnologyPoint" in host_save:
        targ_save["bossTechnologyPoint"] = host_save["bossTechnologyPoint"]
    elif "bossTechnologyPoint" in targ_save:
        targ_save["bossTechnologyPoint"]["value"] = 0
    targ_save["UnlockedRecipeTechnologyNames"] = host_save["UnlockedRecipeTechnologyNames"]
    targ_save["PlayerCharacterMakeData"] = host_save["PlayerCharacterMakeData"]
    if 'RecordData' in host_save:
        targ_save["RecordData"] = host_save["RecordData"]
    elif 'RecordData' in targ_save:
        del targ_json['RecordData']
def update_target_character_instance():
    char_instanceid = targ_json["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
    found = False
    for i, char_save_instance in enumerate(targ_lvl["CharacterSaveParameterMap"]["value"]):
        instance_id = char_save_instance["key"]["InstanceId"]["value"]
        if instance_id == char_instanceid:
            char_save_instance['value'] = exported_map['value']
            found = True
            break
    if not found:
        messagebox.showerror("Error!", "Couldn't find target character instance in target world save.")
        return False
    return True
def update_guild_data(targ_json, targ_lvl, keep_old_guild_id, host_guid, source_guild_dict):
    inv_pals = targ_json["SaveData"]["value"]["PalStorageContainerId"]
    inv_otomo = targ_json["SaveData"]["value"]["OtomoCharacterContainerId"]
    group_id = None
    targ_uid = targ_json["SaveData"]["value"]["IndividualId"]["value"]["PlayerUId"]["value"]
    guild_item_instances = set()
    if not keep_old_guild_id:
        for group_data in targ_lvl["GroupSaveDataMap"]["value"]:
            if group_data["value"]["GroupType"]["value"]["value"] == "EPalGroupType::Guild":
                raw_data = group_data.get("value", {}).get("RawData", {}).get("value", {})
                players_list = raw_data.get("players", []) if isinstance(raw_data, dict) else []
                if targ_uid in [p['player_uid'] for p in players_list]:
                    group_id = raw_data.get('group_id')
                    guild_items_json = raw_data.get("individual_character_handle_ids", [])
                    guild_item_instances = {guild_item['instance_id'] for guild_item in guild_items_json}
                    break
        if group_id is None:
            messagebox.showerror("Error!", "Guild ID not found, aborting!")
            return False, None, None
    else:
        for group_idx, group_data in enumerate(targ_lvl["GroupSaveDataMap"]["value"]):
            if group_data["value"]["GroupType"]["value"]["value"] == "EPalGroupType::Guild" and group_data["key"] not in source_guild_dict:
                players = group_data["value"]["RawData"]["value"].get("players", [])
                new_character_guild_found = False
                for player_idx, player_item in enumerate(players):
                    if player_item['player_uid'] == targ_uid:
                        new_character_guild_found = True
                        break
                if new_character_guild_found:
                    players.pop(player_idx)
                    if players:
                        raw_data = group_data["value"]["RawData"]["value"]
                        if raw_data.get("admin_player_uid") == targ_uid:
                            raw_data["admin_player_uid"] = players[0]['player_uid']
                        individual_ids = raw_data.get("individual_character_handle_ids", [])
                        for handle_idx, character_handle_id in enumerate(individual_ids):
                            if character_handle_id['guid'] == targ_uid:
                                individual_ids.pop(handle_idx)
                                break
                    else:
                        targ_lvl["GroupSaveDataMap"]["value"].pop(group_idx)
                    break
        for group_data in targ_lvl["GroupSaveDataMap"]["value"]:
            if group_data["key"] in source_guild_dict:
                players = group_data["value"]["RawData"]["value"].get("players", [])
                old_player_found = False
                for player_item in players:
                    if player_item['player_uid'] == host_guid:
                        old_player_found = True
                        player_item['player_uid'] = targ_uid
                        break
                if old_player_found:
                    raw_data = group_data["value"]["RawData"]["value"]
                    for character_handle_id in raw_data.get("individual_character_handle_ids", []):
                        if character_handle_id['guid'] == host_guid:
                            character_handle_id['guid'] = targ_uid
                            character_handle_id['instance_id'] = targ_json["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
                            break
                    if raw_data.get("admin_player_uid") == host_guid:
                        raw_data["admin_player_uid"] = targ_uid
                    group_id = group_data["key"]
                    break
        if group_id is None:
            old_guild = None
            for group_data in source_guild_dict.values():
                players = group_data["value"]["RawData"]["value"].get("players", [])
                for player_item in players:
                    if player_item['player_uid'] == host_guid:
                        old_guild = fast_deepcopy(group_data)
                        break
                if old_guild:
                    break
            if old_guild is None:
                messagebox.showerror("Error!", "No guild containing the source player is found in the source either, either this is a bug or the files are corrupted. Aborting.")
                return False, None, None
            group_id = old_guild["key"]
            raw_data = old_guild["value"]["RawData"]["value"]
            if raw_data.get("admin_player_uid") == host_guid:
                raw_data["admin_player_uid"] = targ_uid
            for player_item in raw_data.get("players", []):
                if player_item['player_uid'] == host_guid:
                    player_item['player_uid'] = targ_uid
                    break
            for character_handle_id in raw_data.get("individual_character_handle_ids", []):
                if character_handle_id['guid'] == host_guid:
                    character_handle_id['guid'] = targ_uid
                    character_handle_id['instance_id'] = targ_json["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
                    break
            targ_lvl["GroupSaveDataMap"]["value"].append(old_guild)
    return True, group_id, guild_item_instances
def patch_pal_data():
    for pal_param in param_maps:
        pal_data = pal_param['value']['RawData']['value']
        slot_id_idx = pal_data.find(b'\x07\x00\x00\x00SlotID\x00\x0f\x00\x00\x00StructProperty\x00')
        if slot_id_idx == -1: continue
        pal_container_id_bytes = pal_data[slot_id_idx + 217:slot_id_idx + 233]
        pal_data_bytearray = bytearray(pal_data)
        if pal_container_id_bytes == host_inv_pals["value"]["ID"]["value"]:
            pal_data_bytearray[slot_id_idx + 217:slot_id_idx + 233] = inv_pals["value"]["ID"]["value"]
        elif pal_container_id_bytes == host_inv_otomo["value"]["ID"]["value"]:
            pal_data_bytearray[slot_id_idx + 217:slot_id_idx + 233] = inv_otomo["value"]["ID"]["value"]
        player_uid_start_idx = pal_data.find(OwnerPlayerUIdSearchPrefix) + len(OwnerPlayerUIdSearchPrefix)
        pal_data_bytearray[player_uid_start_idx:player_uid_start_idx + 16] = targ_uid
        pal_data_bytearray[-16:] = group_id
        pal_param['value']['RawData']['value'] = bytes(pal_data_bytearray)
        if not keep_old_guild_id and pal_param["key"]["InstanceId"]["value"] not in guild_item_instances:
            guild_items_json.append({"guid": pal_param["key"]["PlayerUId"]["value"], "instance_id": pal_param["key"]["InstanceId"]["value"]})
def replace_character_save_params(targ_lvl, param_maps, targ_uid, OwnerPlayerUIdSearchPrefix):
    new_character_save_param_map = []
    removed = 0
    for entity in targ_lvl["CharacterSaveParameterMap"]["value"]:
        if find_id_match_prefix(entity['value']['RawData']['value'], OwnerPlayerUIdSearchPrefix) == targ_uid:
            removed += 1
            continue
        new_character_save_param_map.append(entity)
    new_character_save_param_map += param_maps
    targ_lvl["CharacterSaveParameterMap"]["value"] = new_character_save_param_map
def replace_containers():
    global targ_lvl, inv_pals, inv_otomo, host_pals, host_otomo
    global inv_main, inv_key, inv_weps, inv_armor, inv_foodbag
    global host_main, host_key, host_weps, host_armor, host_foodbag
    count = 0
    for container in targ_lvl["CharacterContainerSaveData"]["value"]:
        container_id = container["key"]["ID"]["value"]
        if container_id == inv_pals["value"]["ID"]["value"]:
            container['value']['Slots']['value'] = host_pals['value']['Slots']['value']
            count += 1
        elif container_id == inv_otomo["value"]["ID"]["value"]:
            container['value']['Slots']['value'] = host_otomo['value']['Slots']['value']
            count += 1
        if count >= 2: break
    for container in targ_lvl["ItemContainerSaveData"]["value"]:
        container_id = container["key"]["ID"]["value"]
        if container_id == inv_main["value"]["ID"]["value"]:
            container["value"] = host_main["value"]
            count += 1
        elif container_id == inv_key["value"]["ID"]["value"]:
            container["value"] = host_key["value"]
            count += 1
        elif container_id == inv_weps["value"]["ID"]["value"]:
            container["value"] = host_weps["value"]
            count += 1
        elif container_id == inv_armor["value"]["ID"]["value"]:
            container["value"] = host_armor["value"]
            count += 1
        elif container_id == inv_foodbag["value"]["ID"]["value"]:
            container["value"] = host_foodbag["value"]
            count += 1
        if count >= 7: break
def update_dynamic_containers():
    global level_additional_dynamic_containers
    target_dynamic_containers = targ_lvl['DynamicItemSaveData']['value']['values']
    repeated_indices = set()
    for i, target_dynamic_container in enumerate(target_dynamic_containers):
        target_container_id = target_dynamic_container.get('ID')
        if target_container_id is None:
            continue
        target_guid = find_id_match_prefix(target_container_id['value'], LocalIdSearchPrefix)
        if target_guid in dynamic_guids:
            for j, (dynamic_container, container_local_id) in enumerate(level_additional_dynamic_containers):
                if target_guid == container_local_id:
                    target_dynamic_containers[i] = dynamic_container
                    repeated_indices.add(j)
                    break
    targ_lvl['DynamicItemSaveData']['value']['values'] += [container for i, (container, local_id) in enumerate(level_additional_dynamic_containers) if i not in repeated_indices]
def sync_inventory_to_targ_json():
    save_data = targ_json["SaveData"]["value"]
    save_data["InventoryInfo"] = host_json["SaveData"]["value"].get("InventoryInfo", host_json["SaveData"]["value"].get("inventoryInfo"))
    save_data["PalStorageContainerId"] = host_json["SaveData"]["value"]["PalStorageContainerId"]
    save_data["OtomoCharacterContainerId"] = host_json["SaveData"]["value"]["OtomoCharacterContainerId"]
def save_and_backup():
    global targ_json_gvas
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
def main():
    if not validate_inputs(): return
    global host_guid, host_instance_id, exported_map, param_maps, palcount
    global host_main, host_key, host_weps, host_armor, host_foodbag
    global host_pals, host_otomo, dynamic_guids, inv_pals, inv_otomo
    global targ_uid, group_id, guild_item_instances, guild_items_json
    global host_inv_pals, host_inv_otomo, level_additional_dynamic_containers
    host_guid = UUID.from_str(selected_source_player)
    if not load_player_data(): return
    if not find_host_and_pals(): return
    gather_host_containers()
    update_targ_tech_and_data()
    if not update_target_character_instance(): return
    if not update_guild_data(targ_json, targ_lvl, keep_old_guild_id, host_guid, source_guild_dict): return
    patch_pal_data()
    targ_uid = targ_json["SaveData"]["value"]["IndividualId"]["value"]["PlayerUId"]["value"]
    host_inv_pals = host_pals
    host_inv_otomo = host_otomo
    if 'level_additional_dynamic_containers' not in globals():
        level_additional_dynamic_containers = []
    replace_character_save_params(targ_lvl, param_maps, targ_uid, OwnerPlayerUIdSearchPrefix)
    replace_containers()
    sync_inventory_to_targ_json()
    update_dynamic_containers()
    save_and_backup()
    print("Transfer Successful!")
    messagebox.showinfo(title="Transfer Successful!", message='Transfer Successful!')
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
def ishex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False
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
    list_box.delete(*list_box.get_children())
    if is_source:
        filter_treeview.source_original_rows = []
    else:
        filter_treeview.target_original_rows = []    
    for guild_id, player_items in players.items():
        for player_item in player_items:
            playerUId = ''.join(safe_uuid_str(player_item['player_uid']).split('-')).upper()
            row_id = list_box.insert('', tk.END, values=(safe_uuid_str(guild_id), playerUId, player_item['player_info']['player_name']))
            if is_source:
                filter_treeview.source_original_rows.append(row_id)
            else:
                filter_treeview.target_original_rows.append(row_id)
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
        reader = MyReader(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
        group_save_section, _ = reader.load_section('GroupSaveDataMap', MAP_START, reverse=True)
        source_section_load_handle = threading.Thread(target=load_all_source_sections_async, args=(group_save_section, reader))
        source_section_load_handle.start()
        load_players(group_save_section, True)
        source_level_path_label.config(text=tmp)
        level_sav_path = tmp
        selected_source_player = None
        current_selection_label.config(text=f"Source: {selected_source_player}, Target: {selected_target_player}")
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
    global t_level_sav_path, target_level_path_label, targ_lvl, target_level_cache, target_section_ranges, target_raw_gvas, target_save_type, selected_target_player, target_section_load_handle, TARGET_CNK_DATA_HEADER
    tmp = select_file()
    if tmp:
        if not tmp.endswith("Level.sav"):
            messagebox.showerror("Error!", "This is NOT Level.sav. Please select Level.sav file.")
            return
        raw_gvas, target_save_type = load_file(tmp)
        if not raw_gvas:
            messagebox.showerror("Error!", "Invalid file, must be Level.sav!")
            return
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
def on_exit():
    global level_sav_path, host_sav_path, t_level_sav_path, t_host_sav_path
    root.destroy() 
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
def on_keep_old_guild_check():
    global keep_old_guild_id
    keep_old_guild_id = bool(checkbox_var.get())
    print("Keep old guild id after transfer:", "on" if keep_old_guild_id else "off")
    checkbox_var.set(1 if keep_old_guild_id else 0)
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
level_sav_path, host_sav_path, t_level_sav_path, t_host_sav_path = None, None, None, None
level_json, host_json, targ_lvl, targ_json = None, None, None, None
target_section_ranges, target_save_type, target_raw_gvas, targ_json_gvas = None, None, None, None
selected_source_player, selected_target_player = None, None
keep_old_guild_id, output_old_save_version = False, False
TARGET_CNK_DATA_HEADER = None
source_guild_dict, target_guild_dict = dict(), dict()
source_section_load_handle, target_section_load_handle = None, None
root = tk.Tk()
root.title(f"Character Transfer")
root.geometry("")
root.minsize(800, 300)
root.iconphoto(True, PhotoImage(file=os.path.join(os.path.dirname(__file__), 'resources', 'pal.png')))
root.config(bg="#2f2f2f")
root.tk_setPalette(background="#2f2f2f", foreground="white")
font_style = ("Arial", 10)
heading_font = ("Arial", 12, "bold")
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=2)
root.rowconfigure(3, weight=1)
root.rowconfigure(5, weight=1)
source_frame = tk.Frame(root, bg="#444")
source_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
tk.Label(source_frame, text="Search Source Player:", font=font_style, bg="#444", fg="white").pack(side="left", padx=(0, 5))
source_search_var = tk.StringVar()
source_search_entry = tk.Entry(source_frame, textvariable=source_search_var, font=font_style, bg="#444", fg="white", insertbackground="white", width=20)
source_search_entry.pack(side="left", fill="x", expand=True)
source_search_var.trace_add("write", lambda *args: filter_treeview(source_player_list, source_search_var.get(), is_source=True))
target_frame = tk.Frame(root, bg="#444")
target_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
tk.Label(target_frame, text="Search Target Player:", font=font_style, bg="#444", fg="white").pack(side="left", padx=(0, 5))
target_search_var = tk.StringVar()
target_search_entry = tk.Entry(target_frame, textvariable=target_search_var, font=font_style, bg="#444", fg="white", insertbackground="white", width=20)
target_search_entry.pack(side="left", fill="x", expand=True)
target_search_var.trace_add("write", lambda *args: filter_treeview(target_player_list, target_search_var.get(), is_source=False))
tk.Button(root, text='Select Source Level File', command=source_level_file).grid(row=1, column=1, padx=10, pady=20, sticky="ew")
source_level_path_label = tk.Label(root, text="Please select a file:", font=font_style, bg="#2f2f2f", fg="white", wraplength=600)
source_level_path_label.grid(row=1, column=0, padx=10, pady=20, sticky="ew")
style = ttk.Style()
style.theme_use('clam')
style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#444444", foreground="white")
style.configure("Treeview", background="#333333", foreground="white", rowheight=25, fieldbackground="#333333", borderwidth=0)
source_player_list = ttk.Treeview(root, columns=(0, 1, 2), show='headings', style="Treeview")
source_player_list.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
source_player_list.tag_configure("even", background="#333333", foreground="white")
source_player_list.tag_configure("odd", background="#444444", foreground="white")
source_player_list.tag_configure("selected", background="#555555", foreground="white")
source_player_list.column(0, anchor='center')
source_player_list.column(1, anchor='center')
source_player_list.column(2, anchor='center')
source_player_list.heading(0, text='Guild ID', command=lambda: sort_treeview_column(source_player_list, 0, False))
source_player_list.heading(1, text='Player UID', command=lambda: sort_treeview_column(source_player_list, 1, False))
source_player_list.heading(2, text='Nickname', command=lambda: sort_treeview_column(source_player_list, 2, False))
source_player_list.column(0, width=100)
source_player_list.column(1, width=100)
source_player_list.column(2, width=100)
source_player_list.bind('<<TreeviewSelect>>', on_selection_of_source_player)
tk.Button(root, text='Select Target Level File', command=target_level_file).grid(row=4, column=1, padx=10, pady=20, sticky="ew")
target_level_path_label = tk.Label(root, text="Please select a file:", font=font_style, bg="#2f2f2f", fg="white", wraplength=600)
target_level_path_label.grid(row=4, column=0, padx=10, pady=20, sticky="ew")
target_player_list = ttk.Treeview(root, columns=(0, 1, 2), show='headings', style="Treeview")
target_player_list.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
target_player_list.tag_configure("even", background="#333333", foreground="white")
target_player_list.tag_configure("odd", background="#444444", foreground="white")
target_player_list.tag_configure("selected", background="#555555", foreground="white")
target_player_list.column(0, anchor='center')
target_player_list.column(1, anchor='center')
target_player_list.column(2, anchor='center')
target_player_list.heading(0, text='Guild ID', command=lambda: sort_treeview_column(target_player_list, 0, False))
target_player_list.heading(1, text='Player UID', command=lambda: sort_treeview_column(target_player_list, 1, False))
target_player_list.heading(2, text='Nickname', command=lambda: sort_treeview_column(target_player_list, 2, False))
target_player_list.column(0, width=100)
target_player_list.column(1, width=100)
target_player_list.column(2, width=100)
target_player_list.bind('<<TreeviewSelect>>', on_selection_of_target_player)
current_selection_label = tk.Label(root, text=f"Source: N/A, Target: N/A", font=font_style, bg="#2f2f2f", fg="white", wraplength=600)
current_selection_label.grid(row=8, column=0, padx=10, pady=20, sticky="ew")
tk.Button(root, text='Start Transfer!', font=font_style, command=main).grid(row=8, column=1, padx=10, pady=20, sticky="ew")
checkbox_var = tk.IntVar(value=1)
keep_old_guild_check = tk.Checkbutton(
    root, 
    text="Keep old Guild ID after Transfer", 
    variable=checkbox_var, 
    command=on_keep_old_guild_check,
    indicatoron=True,
    selectcolor="#2f2f2f",
    activebackground="black",
    activeforeground="white",
    foreground="white", 
    bg="#2f2f2f"
)
keep_old_guild_check.grid(row=9, column=0, columnspan=2, sticky='w', padx=10, pady=5)
root.protocol("WM_DELETE_WINDOW", on_exit)
root.mainloop()