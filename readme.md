```
  ___      _                _    _ ___              _____         _    
 | _ \__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___
 |  _/ _` | \ V  V / _ \ '_| / _` \__ \/ _` \ V / -_)| |/ _ \/ _ \ (_-<
 |_| \__,_|_|\_/\_/\___/_| |_\__,_|___/\__,_|\_/\___||_|\___/\___/_/__/

```
---
- **Contact me on Discord:** Pylar1991
---

If you get errors installing or using my tools, **PLEASE** install the prerequisites below first.  
Afterwards, reset and update PST using **Option #18** from the menu.

---
## Prerequisites

### 1. **Updated Saves**
- Ensure your saves were updated on/after the current patch.

### 2. **[Python Installation](https://www.python.org/downloads)**
- Download Python from the official website.  
- Before clicking **Install Now**, **CHECK** the box at the bottom that says:  
  **"Add Python to PATH"** 🟩  
  (*This ensures Python is accessible from the command line!*)  
  ![Add Python to PATH checkbox](https://i.imgur.com/SCJEkdJ.png)

### 3. **[Visual Studio Build Tools](https://aka.ms/vs/17/release/vs_BuildTools.exe)**
- Download Visual Studio Build Tools.
- During installation, **CHECK** the box that says:  
  **"Desktop development with C++"** 🟩  
  (*This allows the `cityhash` and `oozlib` library to install!*)  
  ![CityHash Screenshot](https://i.imgur.com/RZGZ9So.png)
  
### 4. **[Git](https://gitforwindows.org/)**
- Download and install Git.  
(*This allows Git commands to be used by scripts and Python subprocesses!*)  

### 5. ***Start Menu.cmd***

---

## Features:

- **Fast parsing/reading** tool—one of the quickest available.  
- Lists all players/guilds.  
- Lists all pals and their details.  
- Displays last online time for players.  
- Logs players and their data into `players.log`.  
- Logs and sorts players by the number of pals owned.  
- Provides a **base map view**.  
- Provides automated killnearestbase commands for PalDefender targeting inactive bases.  
- Transfers saves between dedicated servers and single/coop worlds.  
- Fix Host Save via GUID editing.  
- Includes Steam ID conversion.  
- Includes coordinate conversion.  
- Includes GamePass ⇔ Steam conversion.  
- Slot injector to increase slots per player on world/server, compatible with Bigger PalBox mod.  
- Automated backup between tool usages.
- All in One Deletion Tool (Delete Guilds, Delete Bases, Delete Players).

---

## Steps to Restore Your Map(Fog and icons):

### This only applies if you do NOT want to use the "Restore Map" option.

### 1. Find the Old Server/World ID:
- **Join your old server/world**.
- Open File Explorer and run the search for: 
	```
	%localappdata%\Pal\Saved\SaveGames\
	```
- Look for a folder with a **random ID** (this should be your **Steam ID**).
- Open that folder and **sort the subfolders by the "Last Modified" date**.
- Look for the folder that matches your **old server/world ID** (e.g., `FCC47F5F4DD6AC48D3C0E2B30059973D`). The folder with the most recent modification date is typically the one for your **old server/world**.
- Once you've found the correct folder, **copy** the `LocalData.sav` file from it.

### 2. Find the New Server/World ID:
- **Join your new server/world**.
- Open File Explorer and run the search for: 
	```
	%localappdata%\Pal\Saved\SaveGames\
	```
- Look for a folder with a **random ID** (this should be your **Steam ID**).
- Open that folder and **sort the subfolders by the "Last Modified" date**.
- Look for the folder that matches your **new server/world ID**.
- Once you've found the correct folder, **paste** the `LocalData.sav` file from the old server/world ID into this folder.
- If the `LocalData.sav` file already exists in the new folder, **confirm the overwrite** when prompted to replace the existing file.

### 3. Restore Your Map
- Now, go into your **new server/world**, and your map should be restored with the old server/world data.

Done! Your map is back in your **new server/world**!



## 🔁 To Move from Host/Co-op to Server or Vice Versa

For **host/co-op**, the save folder is typically located at:

```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```


For **dedicated servers**, the save folder is typically located at:

```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```


---

### 🧪 Transfer Process

1. Copy either your **host/co-op** or **dedicated server** save files.
2. Paste them into the opposite type (host ↔ server).
3. Start the game/server.
4. When prompted to create a new character, go ahead and do it.
5. Exit once the game auto-saves (~2 minutes).
6. Copy the updated save files (Level.sav + Players folder).
7. Paste them into a **temporary folder**.
8. Open **PST (Palworld Save Tool)** and select the **Fix Host Save** option.
9. Load the `Level.sav` from the temporary folder (the one just created).
10. Select:
    - The **old character** (source)
    - The **new character** (target)
11. Click **Migrate**.
12. After migration, copy the updated files from the temporary folder.
13. Paste them into your **actual world save** (host or server).
14. Start the game/server and enjoy your character with all progress intact! 🎉

# Known bugs/issues:

1. **Hostile Pals After Character Transfer**  
   - After transferring a character, some Pals may act aggressive due to ownership issues.  
   - **Workaround:** Add the affected Pal to your party, drop it, then pick it up again to fix ownership.

2. **Steam to GamePass Converter Not Working or Not Keeping Changes**  
   - Please make sure to **close the game** on GamePass.  
   - Wait a few minutes.  
   - Run the **Steam to GamePass converter**.  
   - Wait a few more minutes.  
   - Open the game on GamePass and enjoy your updated save.

3. **Character Transfer: Guild Not Included**  
   - Guilds do **not** transfer with your character—this is intentional.  
   - `Character Transfer` is meant for **cross-world/server transfers**.  
   - It moves your **character, inventory, and Pals**, but **not your guild**.  
   - **Solutions:**  
     - Use `Fix Host Save` for transfers **within the same save** to keep your guild.  
     - Make someone else the **guild leader**, leave the guild, transfer, then get re-invited.