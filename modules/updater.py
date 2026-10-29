import platform
from pathlib import Path
from .database import Database
from .info import VERSION, VERSION_LIST, REPO_NAME, GITHUB_USERNAME

lazy import requests
lazy import shutil
lazy import subprocess

OPSYS = platform.system()
if OPSYS == "Darwin":
    import rumps
else:
    import ctypes

def show_info(title, message):
    if OPSYS == "Darwin":
        rumps.alert(
            title=title,
            message=message
        )
    else:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)

def show_error(title, message):
    if OPSYS == "Darwin":
        rumps.alert(
            title=title,
            message=message
        )
    else:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)

def askokcancel(title, message, ok="OK", cancel="Cancel"):
    if OPSYS == "Darwin":
        return rumps.alert(
            title=title,
            message=message,
            ok=ok,
            cancel=cancel
        )
    else:
        return ctypes.windll.user32.MessageBoxW(0, message, title, 0x04) == 6

def is_update(new_version_list):
    if new_version_list[0] > VERSION_LIST[0]:
        return True
    elif new_version_list[0] == VERSION_LIST[0]:
        if new_version_list[1] > VERSION_LIST[1]:
            return True
        elif new_version_list[1] == VERSION_LIST[1]:
            if new_version_list[2] > VERSION_LIST[2]:
                return True
    return False

def get_releases(session):
    releases_req = session.get(f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/releases")
    if not releases_req.ok:
        show_error(
            title="Connection Error",
            message="Couldn't connect to GitHub Releases."
        )
        return
    return releases_req.json()

def download_file(session, url):
    try:
        file_request = session.get(url)
        if not file_request.ok:
            raise requests.exceptions.ConnectionError
        return file_request.content
    except requests.exceptions.ConnectionError:
        return False

class Updater():
    def __init__(self, database: Database):
        self.database = database

    def update_app_macos(self, show_alerts):
        try:
            session = requests.Session()
            releases = get_releases(session)
            if releases is None:
                return

            if not is_update([int(component) for component in releases[0]["tag_name"].split(".")]):
                if show_alerts:
                    show_info(
                        title="You're Up to Date",
                        message=f"You're on the latest available version ({VERSION})."
                    )
                return

            update = askokcancel(
                title="Update Available",
                message=f"You can update to version {releases[0]["tag_name"]}.\nInstall the update?",
                cancel=True,
                ok="Update"
            )
            if not update:
                return

            if OPSYS == "Windows":
                import webbrowser
                webbrowser.open(f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}/releases/tag/{releases[0]["tag_name"]}")
                return

            for asset in releases[0]["assets"]:
                if "MenuBarSchedule.app.zip" == asset["name"]:
                    app_darwin = download_file(session, asset["browser_download_url"])
                    open("MenuBarSchedule.app.zip", "wb").write(app_darwin)
                    if Path("/Applications/MenuBarSchedule.app").exists():
                        shutil.rmtree("/Applications/MenuBarSchedule.app")
                    try:
                        subprocess.run(["unzip", "-oq", "MenuBarSchedule.app.zip", "-d", "/Applications"])
                        subprocess.run(["chmod", "+x", "/Applications/MenuBarSchedule.app/Contents/MacOS/MenuBarSchedule"])
                        subprocess.run(["xattr", "-dr", "com.apple.quarantine", "/Applications/MenuBarSchedule.app"])
                        subprocess.run(["rm", "-rf", "MenuBarSchedule.app.zip"])
                        if askokcancel(
                            title="Update Successful",
                            message="Successfully installed the update!\nRestart Menu Bar Schedule to finish the update.",
                            ok="Restart Now",
                            cancel="Later"
                        ) == True:
                            subprocess.run(["open", "-n", "/Applications/MenuBarSchedule.app"])
                            return "restart"
                    except:
                        subprocess.run(["rm", "-rf", "/Applications/MenuBarSchedule.app"])
                        subprocess.run(["rm", "-rf", "MenuBarSchedule.app.zip"])
                        show_error(
                            title="Update Failed",
                            message="Failed to install the update."
                        )
        except requests.exceptions.ConnectionError:
            show_error(
                title="Connection Error",
                message="An unexpected error occured!"
            )

    def update_schedules(self, show_alerts):
        try:
            session = requests.Session()
            releases = get_releases(session)
            force_install = False

            is_app_version_same = releases[0]["tag_name"] == VERSION
            is_later_app_version = is_update([int(component) for component in releases[0]["tag_name"].split(".")])

            saved_metadata_json = self.database.get_all_online_schedule_packs()
            current_metadata_json = self.database.download_schedule_packs_from_sb()

            if saved_metadata_json == {}:
                force_install = True
                is_schedule_update = True
            else:
                is_schedule_update = False
                for metadata_obj in current_metadata_json:
                    if saved_metadata_json.get(metadata_obj["pack_id"], {"pack_version": 0})["pack_version"] < metadata_obj["pack_version"]:
                        is_schedule_update = True

            if force_install and is_app_version_same:
                download_schedules = askokcancel(
                    title="Schedules Not Found",
                    message="Schedules are required for Menu Bar Schedule to function.\nInstall schedules?",
                    cancel="Cancel",
                    ok="Install"
                )
                if not download_schedules:
                    return False
            elif is_schedule_update and is_app_version_same:
                update = askokcancel(
                    title="Schedule Updates Available",
                    message=f"A schedule update is available.\nInstall the update?",
                    cancel="Cancel",
                    ok="Update"
                )
                if not update:
                    return False
            elif is_schedule_update and not is_app_version_same and is_later_app_version:
                show_error(
                    title="Cannot Update Schedules",
                    message=f"The latest version of Menu Bar Schedule ({releases[0]["tag_name"]}) must be installed to continue receiving schedule updates.\nYou can update the app by clicking \"Check for App Updates\".",
                )
                return False
            elif is_schedule_update and not is_app_version_same and not is_later_app_version:
                continue_update = askokcancel(
                    title="Schedule Updates Available",
                    message=f"A schedule update is available, but it was made for an earlier version of Menu Bar Schedule ({releases[0]["tag_name"]}).\nOlder schedules may not be compatible with this version of the app.\nInstall the update?",
                    cancel="Cancel",
                    ok="Update"
                )
                if not continue_update:
                    return False
            else:
                if show_alerts:
                    show_info(
                        title="You're Up to Date",
                        message=f"You're on the latest available schedule version."
                    )
                return False

            try:
                self.database.download_online_schedules_from_sb()
                if show_alerts:
                    show_info(
                        title="Update Successful",
                        message="Successfully updated schedules."
                    )
                return True
            except:
                show_error(
                    title="Update Failed",
                    message="Failed to update schedules."
                )
                return False
        except requests.exceptions.ConnectionError:
            show_error(
                title="Connection Error",
                message="An unexpected error occured!"
            )
            return False
        except ValueError:
            show_error(
                title="Cannot Update Schedules",
                message=f"The schedule metadata seems to be corrupt."
            )
            return False
