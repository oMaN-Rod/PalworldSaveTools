import os, sys, copy, uuid, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from scan_save import decompress_sav_to_gvas, GvasFile, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, compress_gvas_to_sav

def as_uuid(val): return str(val).lower() if val else ''
def are_equal_uuids(a,b): return as_uuid(a)==as_uuid(b)

def sav_to_json(path):
    with open(path,"rb") as f: data = f.read()
    raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return g.dump()

def json_to_sav(j,path):
    g = GvasFile.load(j)
    t = 0x32 if "Pal.PalworldSaveGame" in g.header.save_game_class_name else 0x31
    data = compress_gvas_to_sav(g.write(SKP_PALWORLD_CUSTOM_PROPERTIES),t)
    with open(path,"wb") as f: f.write(data)

source_data, target_data, source_path, target_path = None, None, None, None

def load_source():
    global source_data, source_path
    p = filedialog.askopenfilename(filetypes=[("SAV","*.sav")])
    if not p or os.path.basename(p).lower() != "level.sav":
        messagebox.showerror("Error", "Please select a valid Level.sav file")
        return
    source_path = p
    source_data = sav_to_json(p)
    refresh_guilds(source_data, guild_tree)

def load_target():
    global target_data, target_path
    p = filedialog.askopenfilename(filetypes=[("SAV","*.sav")])
    if not p or os.path.basename(p).lower() != "level.sav":
        messagebox.showerror("Error", "Please select a valid Level.sav file")
        return
    target_path = p
    target_data = sav_to_json(p)
    refresh_guilds(target_data, guild_tree_target)
    refresh_target_bases()

def refresh_guilds(data, tree):
    tree.delete(*tree.get_children())
    if not data: return
    for g in data['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value']=='EPalGroupType::Guild':
            name=g['value']['RawData']['value'].get('guild_name',"Unknown")
            gid=as_uuid(g['key'])
            tree.insert("","end",values=(name,gid))

def refresh_target_bases():
    base_tree_target.delete(*base_tree_target.get_children())
    if not target_data: return
    bases = target_data['properties']['worldSaveData']['value'].get('BaseCampSaveData', {}).get('value', [])
    for b in bases:
        base_tree_target.insert("", "end", values=(str(b['key']),))

def on_guild_select(event=None):
    sel = guild_tree.selection()
    base_tree.delete(*base_tree.get_children())
    if not sel or not source_data: return
    gid = guild_tree.item(sel[0])['values'][1]
    for b in source_data['properties']['worldSaveData']['value']['BaseCampSaveData']['value']:
        if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
            base_tree.insert("", "end", values=(str(b['key']),))

def replace_mapobjs_for_base(source_base, source_map_objs, target_data, target_base):
    old_source_base_id = source_base['key']
    target_base_id = target_base['key']

    tgt_map_list = target_data['properties']['worldSaveData']['value']['MapObjectSaveData']['value']['values']
    tgt_map_list[:] = [obj for obj in tgt_map_list if not are_equal_uuids(
        obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('base_camp_id_belong_to'), target_base_id)]

    new_map_objs = []
    new_map_obj_ids = []
    for obj in source_map_objs:
        obj_base_id = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('base_camp_id_belong_to')
        if are_equal_uuids(obj_base_id, old_source_base_id):
            new_obj = copy.deepcopy(obj)
            new_obj_id = str(uuid.uuid4())
            new_obj['Model']['value']['RawData']['value']['instance_id'] = new_obj_id
            new_obj['Model']['value']['RawData']['value']['base_camp_id_belong_to'] = target_base_id
            new_map_objs.append(new_obj)
            new_map_obj_ids.append(new_obj_id)

    tgt_map_list.extend(new_map_objs)

    tgt_group_id = target_base['value']['RawData']['value'].get('group_id_belong_to')
    tgt_group = next((g for g in target_data['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
                      if are_equal_uuids(g['key'], tgt_group_id)), None)
    if tgt_group:
        raw = tgt_group['value']['RawData']['value']
        raw['map_object_instance_ids_base_camp_points'] = new_map_obj_ids

def copy_base_to_target():
    sel_g = guild_tree.selection()
    sel_b = base_tree.selection()
    sel_tg = guild_tree_target.selection()
    sel_btgt = base_tree_target.selection()
    if not (sel_g and sel_b and sel_tg and sel_btgt and source_data and target_data):
        messagebox.showerror("Error", "Please select source guild, source base, target guild and target base")
        return
    base_id = base_tree.item(sel_b[0])['values'][0]
    base = next((b for b in source_data['properties']['worldSaveData']['value']['BaseCampSaveData']['value'] if str(b['key']) == base_id), None)
    if not base: return
    target_gid = guild_tree_target.item(sel_tg[0])['values'][1]
    target_base_id = base_tree_target.item(sel_btgt[0])['values'][0]
    target_base = next((b for b in target_data['properties']['worldSaveData']['value']['BaseCampSaveData']['value']
                        if str(b['key']) == target_base_id), None)
    if not target_base:
        messagebox.showerror("Error", "Target base not found")
        return

    new_base = copy.deepcopy(base)
    new_base['key'] = target_base['key']
    new_base['value']['RawData']['value']['group_id_belong_to'] = target_gid

    bases_list = target_data['properties']['worldSaveData']['value']['BaseCampSaveData']['value']
    for i, b in enumerate(bases_list):
        if str(b['key']) == target_base['key']:
            bases_list[i] = new_base
            break

    src_map_objs = source_data['properties']['worldSaveData']['value']['MapObjectSaveData']['value']['values']
    replace_mapobjs_for_base(base, src_map_objs, target_data, new_base)

    refresh_target_bases()
    messagebox.showinfo("Success", "Target base fully replaced with source base and map objects!")

def save_target():
    if not target_data or not target_path: return
    json_to_sav(target_data, target_path)
    messagebox.showinfo("Saved", "Target save overwritten successfully!")

window = tk.Tk()
window.title("Base Transfer")
window.geometry("1000x600")
try: window.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "resources", "pal.ico"))
except Exception: pass

s = ttk.Style(window)
s.theme_use('clam')
window.config(bg="#2f2f2f")
font=("Arial",10)
for opt in [("Treeview.Heading",{"font":("Arial",12,"bold"),"background":"#444","foreground":"white"}),
            ("Treeview",{"background":"#333","foreground":"white","fieldbackground":"#333"}),
            ("TFrame",{"background":"#2f2f2f"}),
            ("TLabel",{"background":"#2f2f2f","foreground":"white"}),
            ("Dark.TButton",{"background":"#555","foreground":"white","font":font,"padding":6})]:
    s.configure(opt[0],**opt[1])
s.map("Dark.TButton",background=[("active","#666"),("!disabled","#555")],foreground=[("!disabled","white")])

def panel(label_text,tree_columns,tree_headings,tree_col_widths,x,y,w,h):
    panel = ttk.Frame(window,style="TFrame")
    panel.place(x=x,y=y,width=w,height=h)
    ttk.Label(panel,text=label_text,font=font,style="TLabel").pack(anchor="w")
    tree = ttk.Treeview(panel,columns=tree_columns,show='headings',height=20)
    tree.pack(fill="both",expand=True)
    for c,h,wid in zip(tree_columns,tree_headings,tree_col_widths):
        tree.heading(c,text=h)
        tree.column(c,width=wid,anchor='w')
    return tree

btn_load_src = ttk.Button(window,text="Load Source Level.sav",command=load_source,style="Dark.TButton")
btn_load_tgt = ttk.Button(window,text="Load Target Level.sav",command=load_target,style="Dark.TButton")
btn_copy = ttk.Button(window,text="Replace Target Base",command=copy_base_to_target,style="Dark.TButton")
btn_save = ttk.Button(window,text="Save Target",command=save_target,style="Dark.TButton")

btn_load_src.place(x=10,y=10)
btn_load_tgt.place(x=200,y=10)
btn_copy.place(x=400,y=10)
btn_save.place(x=600,y=10)

guild_tree = panel("Source Guilds:",["Name","ID"],["Guild Name","Guild ID"],[130,200],10,50,300,250)
guild_tree_target = panel("Target Guilds:",["Name","ID"],["Guild Name","Guild ID"],[130,200],330,50,300,250)
base_tree = panel("Source Guild's Bases:",["ID"],["Base ID"],[300],660,50,300,250)
base_tree_target = panel("Target Guild's Bases:",["ID"],["Base ID"],[300],10,320,950,250)

guild_tree.bind("<<TreeviewSelect>>", on_guild_select)

window.mainloop()
