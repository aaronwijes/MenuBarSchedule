"""
Menu Bar Schedule Release Build Tool
Derived from the RoSniper Release Build Tool
I'm open sourcing this component to be transparent on how the pre-built binaries are created.

DISCLAIMER: THIS BUILD SCRIPT MAY CHANGE AT ANY TIME.
DO NOT EXPECT THIS TO BE STABLE, NOR EXPECT IT TO WORK ON YOUR MACHINE.
For a more stable and consumer-friendly build script, see build.py!
"""

import os
import json
import shutil
import zipfile
import platform

gold = "\033[0;33m"
bold = "\033[1m"
end = "\033[0m"

op = platform.system()
def clear():
    os.system("clear;clear" if op == "Darwin" else "cls")

if not op == "Darwin":
    clear()
    input("The release build script is only available on macOS. ")
    exit()

def build():
    clear()
    print(f"{gold}[Building MenuBarSchedule]{end}")
    if os.path.exists("../main.py"):
        MenuBarSchedulePath = "../main.py"
    elif os.path.exists("./main.py"):
        MenuBarSchedulePath = "./main.py"
    else:
        input("main.py wasn't found. ")
        return

    shutil.copy(MenuBarSchedulePath, "./resources/MenuBarSchedule.py")

    version = open("./resources/MenuBarSchedule.py", "r").read().split("VERSION = \"")[1].split("\"")[0]
    print(f"MenuBarSchedule Version: {version}")
    input("Press ENTER to start building MenuBarSchedule. ")
    modifiedSPEC = open("./Resources/MenuBarSchedule.spec", "r").read().replace("0.0.0", version)
    open("MenuBarSchedule.spec", "w").write(modifiedSPEC)

    os.system(f"pyinstaller --windowed ./resources/MenuBarSchedule.py --icon ./Resources/AppIcon.icns")
    os.system("cp -r ./dist/MenuBarSchedule.app .")
    for delete in os.listdir("./MenuBarSchedule.app/Contents/Resources/"):
        if delete != "AppIcon.icns":
            os.system(f"rm -rf ./MenuBarSchedule.app/Contents/Resources/{delete}")
    os.system("rm -rf ./MenuBarSchedule.app/Contents/Frameworks/python3__dot__14")
    os.system("rm -rf build dist *.spec ./resources/MenuBarSchedule.py")

    with zipfile.ZipFile("./artifacts/MenuBarSchedule.app.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("./MenuBarSchedule.app"):
            for file in files:
                full_path = os.path.join(root, file)
                zipf.write(full_path, full_path)
    if os.path.exists("./MenuBarSchedule.app/"):
        shutil.rmtree("./MenuBarSchedule.app/")

def build_assets():
    schedules_version = json.loads(open("./schedules/metadata.json").read())["version"]
    with zipfile.ZipFile(f"./artifacts/schedules-v{schedules_version}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(f"./schedules/"):
            for file in files:
                full_path = os.path.join(root, file)
                zipf.write(full_path, full_path)

while True:
    clear()
    os.chdir(os.path.dirname(__file__))

    print(f"{gold}[MenuBarSchedule Build Release Tool]{end}")
    print(f"[1] Options 2 + 3")
    print(f"[2] Build MenuBarSchedule for macOS")
    print(f"[3] Package schedule packs")
    print(f"[4] Exit")

    option = input("\nSelect an option: ").strip()
    if not option.isnumeric() or not option in ["1", "2", "3", "4"]:
        input("Invalid option. ")
        continue
    else:
        option = int(option)

    match option:
        case 1:
            build()
            build_assets()
        case 2:
            build()
        case 3:
            build_assets()
        case 4:
            exit()