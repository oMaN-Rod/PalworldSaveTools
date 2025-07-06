```
  ___      _                _    _ ___              _____         _    
 | _ \__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___
 |  _/ _` | \ V  V / _ \ '_| / _` \__ \/ _` \ V / -_)| |/ _ \/ _ \ (_-<
 |_| \__,_|_|\_/\_/\___/_| |_\__,_|___/\__,_|\_/\___||_|\___/\___/_/__/

```
---
- **Contact me on Discord:** Pylar1991
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

### 3. ### 3. **[Visual Studio Build Tools](https://aka.ms/vs/17/release/vs_BuildTools.exe)**
- Download Visual Studio Build Tools.
- During installation, **CHECK** the box that says:  
  **"Desktop development with C++"** 🟩  
  (*This allows the `cityhash` and `oozlib` library to install!*)  
  ![CityHash Screenshot](https://i.imgur.com/RZGZ9So.png)

### 4. ***Start Menu.cmd***

---

## Features:

- **Fast parsing/reading** tool—one of the quickest available.  
- Lists all players/guilds.  
- Lists all pals and their details.  
- Displays last online time for players.  
- Logs players and their data into `players.log`.  
- Filters and deletes players based on inactivity or maximum number of pals.  
- Logs and sorts players by the number of pals owned.  
- Deletes players with fewer than a specified number of pals.  
- Provides a **base map view**.  
- Provides automated killnearestbase commands for PalDefender targeting inactive bases.  
- Transfers saves between dedicated servers and single/coop worlds.  
- Fix Host Save via GUI editing.  
- Includes Steam ID conversion.  
- Includes coordinate conversion.  
- Includes GamePass ⇔ Steam conversion.  
- Slot injector to increase slots per player on world/server, compatible with Bigger PalBox mod.  
- Automated backup between tool usages.

---

# Known bugs/issues:

1. **Hostile Pals After Character Transfer**  
   - After transferring a character, some Pals may act aggressive due to ownership issues.  
   - Workaround: Add the affected Pal to your party, drop it, then pick it up again to fix ownership.

2. **Bases get wiped when transferring from server to local**  
   - Status: No known fix yet. Caused by patch v0.4.15 changes.