import os
import sys
import shutil
import platform

gold = "\033[0;33m"
bold = "\033[1m"
faint = "\033[2m"
end = "\033[0m"

op = platform.system()
def clear():
    os.system("clear;clear" if op == "Darwin" else "cls")

if op in ["Darwin", "Windows"]:
    def build():
        clear()
        print(f"{gold}[Build MenuBarSchedule]{end}")
        print(f"{bold}Here are the minimum requirements to build MenuBarSchedule:{end}")
        print("    - 200MB+ space (app ~55MB, launcher ~2MB, rest is temporary files)")
        print("    - The modules in requirements.txt")
        print("    - MenuBarSchedule.py in the (parent) directory of the build script")
        print("    - AppIcon(.icns/.ico), launcher.py, and Info.plist in ./Resources/")
        print("    - Any version of MenuBarSchedule (MacOS) or MenuBarSchedule v1.0.0+ (Windows)")
        print(f"\n{bold}If you're running Option 1 for a complete install:{end}")
        print("    - ./assets/ with docs.txt, changelog.txt, and donations.json in the (parent) directory of the build script")

        if os.path.exists("../MenuBarSchedule.py"):
            MenuBarSchedulePath = "../MenuBarSchedule.py"
        elif os.path.exists("./MenuBarSchedule.py"):
            MenuBarSchedulePath = "./MenuBarSchedule.py"
        else:
            input("MenuBarSchedule.py wasn't found. ")
            return

        version = open(MenuBarSchedulePath, "r").read().split("VERSION = \"")[1].split("\"")[0]
        print(f"\nMenuBarSchedule Version: {version}")
        input("Press ENTER to start building MenuBarSchedule. ")
        modifiedPLIST = open("./Resources/Info.plist", "r").read().replace("0.0.0", version)

        if op == "Darwin":
            os.system(f"pyinstaller --windowed {MenuBarSchedulePath} --icon ./Resources/AppIcon.icns")
            os.system("cp -r ./dist/MenuBarSchedule.app .")
            for delete in os.listdir("./MenuBarSchedule.app/Contents/Resources/"):
                if delete != "AppIcon.icns":
                    os.system(f"rm -rf ./MenuBarSchedule.app/Contents/Resources/{delete}")
            os.system("rm -rf ./MenuBarSchedule.app/Contents/Frameworks/python3__dot__14")
            open("./MenuBarSchedule.app/Contents/Info.plist", "w").write(modifiedPLIST)
            os.system("rm -rf build dist *.spec")
        else:
            os.system(f"pyinstaller {MenuBarSchedulePath} --icon ./Resources/AppIcon.ico")
            os.system("xcopy .\\dist\\MenuBarSchedule . /E /Q")
            shutil.rmtree("./build/")
            shutil.rmtree("./dist/")
            os.system("erase *.spec /Q")

    def transfer_assets(output=True):
        clear()
        if output:
            print(f"{gold}[Transfer Asset Directory into MenuBarSchedule]{end}")
        
        if os.path.exists(f"../schedules"):
            path = f"../schedules"
        elif os.path.exists(f"./schedules"):
            path = f"./schedules"
        elif os.path.exists(f"./Resources/schedules"):
            path = f"./Resources/schedules"
        else:
            input(f"The asset directory wasn't found. ")
            return

        if output:
            print(f"The asset directory was found at {path}.")

        if op == "Windows":
            if not os.path.exists("./_internal/schedules/"):
                os.mkdir("./_internal/schedules/")

        executable = "copy /Y" if op == "Windows" else "cp -r"
        dest = ".\\_internal\\schedules" if op == "Windows" else "MenuBarSchedule.app/Contents/Frameworks/schedules"
        path = path if op == "Darwin" else path.replace("/", "\\")
        os.system(f"{executable} {path} {dest}")

        if output:
            input(f"The asset directory was injected into MenuBarSchedule. ")

    def transfer_to_applications(output=True):
        clear()
        if output:
            print(f"{gold}[Transfer MenuBarSchedule to /Applications]{end}")

        if os.path.exists("/Applications/MenuBarSchedule.app"):
            os.system("rm -rf /Applications/MenuBarSchedule.app")
        os.system("mv MenuBarSchedule.app /Applications/")
        if output:
            input("MenuBarSchedule.app was moved to the Applications folder. ")

    def delete_from_applications():
        clear()
        print(f"{gold}[Delete MenuBarSchedule from /Applications]{end}")
        os.system("rm -rf /Applications/MenuBarSchedule.app")
        input("MenuBarSchedule.app was deleted from the Applications folder. ")

    while True:
        clear()
        os.chdir(os.path.dirname(__file__))

        app_location = "_internal" if op == "Windows" else "MenuBarSchedule.app"
        app_exists = "" if os.path.exists(app_location) else faint
        app_exists_a = "" if os.path.exists("/Applications/MenuBarSchedule.app") else faint

        args = sys.argv[1:]
        if len(args) == 0:
            print(f"{gold}[MenuBarSchedule Build Tool]{end}")
            print(f"{bold}[1] Install MenuBarSchedule from source (Options 2{", 3, and 4" if op == "Darwin" else " and 3"} combined){end}")
            print("[2] Build MenuBarSchedule")
            print(f"{app_exists}[3] Inject the asset directory into MenuBarSchedule{end}")
            if op == "Darwin":
                print(f"{app_exists}[4] Transfer MenuBarSchedule to /Applications (macOS Only){end}")
                print(f"{app_exists_a}[5] Delete MenuBarSchedule from /Applications (macOS Only){end}")
            print(f"[{"4" if op == "Windows" else "6"}] Exit")
            option = input("\nSelect an option: ").strip()
        else:
            option = args[-1].strip()

        if not option.isnumeric() or not option in ["1", "2", "3", "4", "5" if op == "Darwin" else "1", "6" if op == "Darwin" else "1"]:
            input("Invalid option. ")
        else:
            option = int(option)

        match option:
            case 1:
                build()
                transfer_assets(output=False)
                if op == "Darwin":
                    transfer_to_applications(output=False)
            case 2:
                build()
            case 3:
                if os.path.exists(app_location):
                    transfer_assets()
            case 4:
                if os.path.exists(app_location) and op == "Darwin":
                    transfer_to_applications()
                elif op == "Windows":
                    exit()
            case 5:
                if os.path.exists("/Applications/MenuBarSchedule.app") and op == "Darwin":
                    delete_from_applications()
            case 6:
                exit()
        
        if len(args) > 0:
            exit()
else:
    clear()
    input("The build script is not available for Linux at this time. ")
