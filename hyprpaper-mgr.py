"""
A script for managing hyprpaper

Skip/select/randomize wallpapers for each monitor from wallpapers folder
(Wallpapers folder can be set by changing wp_dir below)
State is logged to .wplog file in wallpapers folder

For keeping the state at each boot add these to hyprland.conf 
exec-once = hyprpaper
exec-once = python /path/to/hyprpaper-mgr.py

07.02.2024
"""
usage=\
"""
python /path/to/hyprpaper-mgr.py [Monitor Select] [Option]

No Arguments:         Refresh with current state

Monitor Select:
  -m  <Number>        Select monitor to make changes on
  --monitor <Number>  If not given changes are applied on all monitors
                      Number starts from 0
Option:
  -r                  Random wallpaper 
  --random            Selected monitor wallpaper(s) get randomized seperately
                      
  -n                  Next wallpaper
  --next              

  -p                  Previous wallpaper
  --previous

  -s <Number>         Select wallpaper 
  --select <Number>   Number starts from 0.
"""
#### WALLPAPERS FOLDER ####
wp_dir = "~/Wallpapers"
#### WALLPAPERS FOLER ####

from os import listdir
from os.path import expanduser
from random import randint
from sys import argv
from subprocess import check_output
import json

# Get file names, exclude unsupported ones
wp_dir = expanduser(wp_dir)
allow = (".jpg", ".jpeg", ".png", ".webp")
wp_list = [wp for wp in listdir(wp_dir) if wp.lower().endswith(allow)]
if wp_list == []:
    print(f"Error: No wallpaper found in {wp_dir}")
    exit()

# Preload (check_output instead of os.system in order to hide hyprctl outputs)
for wp in wp_list:
    check_output(f"hyprctl hyprpaper preload {wp_dir}/{wp}", shell=True)

# Get monitor info as json, extract monitor names into list
monitors = check_output("hyprctl monitors -j", shell=True)
monitors = [m["name"] for m in json.loads(monitors)]

# Get log : list of dicts that contain monitor name, wp index, mode
log = [] 
try:
    logf = open(f"{wp_dir}/.wplog", "r")
    log = json.load(logf)
except:
    logf = open(f"{wp_dir}/.wplog", "w")
logf.close()

# If there is a non logged monitor, log with default settings
non_logged = [m for m in monitors if m not in [l["monitor"] for l in log]]
for nl in non_logged:
    log.append({"monitor":nl, "i":0, "mode":"static"})

# Index Functions 
def rand_i(index):
    if len(wp_list) == 1:
        return 0
    old_i = index
    while old_i == index:
        index = randint(0, len(wp_list)-1)
    return index
 
def next_i(index):
    if index != len(wp_list)-1:
        return index + 1
    else:
        return 0

def prev_i(index):
    if index != 0:
        return index - 1
    else:
        return len(wp_list)-1

# Handle argv 
if set(argv).intersection(("-h", "--help", "help")) != set():
    print(usage)
    exit()

monitor_sel = None
if len(argv) > 1:
 
    if argv[1] in ("-m", "--monitor"):
        try:
            monitor_sel = int(argv[2])
            if monitor_sel > len(monitors)-1 : raise Exception
        except:
            print("Error: Monitor Selection")
            exit()
        del argv[1:3]

if len(argv) > 1:
 
    if argv[1] in ("-s", "--select"):
        try:
            wp_sel = int(argv[2])
            if wp_sel > len(wp_list)-1 : raise Exception
        except:
            print("Error: Wallpaper Selection")
            exit()
        if monitor_sel is not None:
            log[monitor_sel].update({"i":wp_sel, "mode":"static"})
        else:
            for l in log : l.update({"i":wp_sel, "mode":"static"})

    elif argv[1] in ("-r", "--random"):
        if monitor_sel is not None:
            log[monitor_sel]["mode"] = "rand_sel"
        else:
            for l in log : l["mode"] = "rand_sync"

    elif argv[1] in ("-n", "--next"):
        if monitor_sel is not None:
            log[monitor_sel].update({"i":next_i(log[monitor_sel]["i"]), "mode":"static"})
        else:
            for l in log : l.update({"i":next_i(l["i"]), "mode":"static"})

    elif argv[1] in ("-p", "--previous"):
        if monitor_sel is not None:
            log[monitor_sel].update({"i":prev_i(log[monitor_sel]["i"]), "mode":"static"})
        else:
            for l in log : l.update({"i":prev_i(l["i"]), "mode":"static"})

    else:
        print(f"Error: Argument {argv[1]} not allowed")
        exit()

# Handle Randoms
rand_sync_i = None 
for l in log:
    if l["mode"] == "rand_sel":
        l["i"] = rand_i(l["i"])
    if l["mode"] == "rand_sync":
        if rand_sync_i is not None: 
            l["i"] = rand_sync_i
        else:
            rand_sync_i = rand_i(l["i"])
            l["i"] = rand_sync_i

# Update log file 
logf = open(f"{wp_dir}/.wplog", "w")
json.dump(log, logf)
logf.close()

# Apply Changes
for l in log:
    check_output(
        f"hyprctl hyprpaper wallpaper \"{l['monitor']},{wp_dir}/{wp_list[l['i']]}\"",
        shell=True
    )
