import datetime
import os
import re
import shutil
import sys
import uuid
from sys import exit
from container_types import ContainerIndex, NotSupportedError, ContainerFile, ContainerFileList, FILETIME, Container
def add_container(container_index: ContainerIndex, source_save_path: str, save_filename: str, container_name: str,
                  container_path: str):
    try:
        data = open(save_filename, "rb").read()
    except FileNotFoundError:
        print(f"Warning: Missing file {save_filename}, skipping...")
        return
    files = [
        ContainerFile("Data", uuid.uuid4(), data),
    ]
    container_file_list = ContainerFileList(seq=1, files=files)
    container_uuid = uuid.uuid4()
    mtime = FILETIME.from_timestamp(os.path.getmtime(source_save_path))
    size = os.path.getsize(save_filename)
    container = Container(
        container_name=container_name,
        cloud_id="",
        seq=1,
        flag=5,
        container_uuid=container_uuid,
        mtime=mtime,
        size=size,
    )
    container_index.containers.append(container)
    container_index.mtime = FILETIME.from_timestamp(datetime.datetime.now().timestamp())
    container_content_path = os.path.join(container_path, container_uuid.bytes_le.hex().upper())
    os.makedirs(container_content_path, exist_ok=True)
    container_file_list.write_container(container_content_path)
    print(f"Wrote new container to {container_content_path}")
def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <save_folder>")
        os.system("pause")
        exit(1)
    print("WARNING: This tool is experimental. Always manually back up your existing saves!\n")
    package_path = os.path.expandvars(r"%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt")
    if not os.path.exists(package_path):
        print("Error: Could not find the package path. Make sure you have Xbox Palworld installed.")
        os.system("pause")
        exit(2)
    wgs_path = os.path.join(package_path, "SystemAppData", "wgs")
    container_regex = re.compile(r"[0-9A-F]{16}_[0-9A-F]{32}$")
    container_path = None
    for d in os.listdir(wgs_path):
        if container_regex.match(d):
            container_path = os.path.join(wgs_path, d)
            break
    if container_path is None:
        print("Error: Could not find the container path. Please try to run the game once to create it.")
        os.system("pause")
        exit(2)
    print(f"Found container path: {container_path}")
    container_index_path = os.path.join(container_path, "containers.index")
    with open(container_index_path, "rb") as container_index_file:
        try:
            container_index = ContainerIndex.from_stream(container_index_file)
        except NotSupportedError as e:
            print(f"Error: Detected unsupported container format, please report this issue: {e}")
            os.system("pause")
            exit(3)
    print("Parsed container index:")
    print(f"  Package name: {container_index.package_name}")
    print(f"  {len(container_index.containers)} containers:")
    for container in container_index.containers:
        print(f"    {container.container_name} ({container.size} bytes)")
        c = os.path.join(container_path, container.container_uuid.bytes_le.hex().upper())
        for f in os.listdir(c):
            if f.startswith("container."):
                file_list = ContainerFileList.from_stream(open(os.path.join(c, f), "rb"))
                for file in file_list.files:
                    print(f"      {file.name}")
    print()
    source_save_path = os.path.normpath(sys.argv[1])
    if not os.path.exists(source_save_path):
        print(f"Error: Source save path does not exist: {source_save_path}")
        os.system("pause")
        exit(4)
    if os.path.isfile(source_save_path):
        source_save_path = os.path.dirname(source_save_path)
    if not os.path.exists(os.path.join(source_save_path, "level.sav")):
        print(f"Error: Source save folder doesn't seem like a Palworld save folder: {source_save_path}")
        os.system("pause")
        exit(4)
    save_name = os.path.basename(source_save_path)
    print("Save file:")
    print(f"  Folder: {source_save_path}\n")
    existing_names = {c.container_name for c in container_index.containers}
    base_name = f"{save_name}-Level"
    new_name = base_name
    i = 1
    while new_name in existing_names:
        new_name = f"{base_name}_{i}"
        i += 1
    if new_name != base_name:
        print(f"Warning: Save file name conflict detected. Renaming to {new_name}")
    container_backup_path = os.path.join(container_path, f"{os.path.basename(container_path)}.backup.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
    shutil.copytree(container_path, container_backup_path)
    print(f"Created backup of container: {container_backup_path}")
    print("Creating new containers")
    save_file_list = [
        ("Level", new_name),
        ("LevelMeta", f"{save_name}-LevelMeta"),
        ("LocalData", f"{save_name}-LocalData"),
        ("WorldOption", f"{save_name}-WorldOption")
    ]
    for save_file, container_file_name in save_file_list:
        filename = os.path.join(source_save_path, f"{save_file}.sav")
        add_container(container_index, source_save_path, filename, container_file_name, container_path)
    player_path = os.path.join(source_save_path, "Players")
    for save_file in os.listdir(player_path):
        filename = os.path.join(player_path, save_file)
        add_container(container_index, source_save_path, filename, f"{save_name}-Players-{save_file.replace('.sav', '')}", container_path)
    container_index.write_file(container_path)
    print("Updated container index")
    print("Done!")
if __name__ == '__main__':
    main()