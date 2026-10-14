import json
import rumps
import zipfile
from pathlib import Path
from modules.info import VERSION, VERSION_LIST, REPO_NAME, GITHUB_USERNAME

lazy import requests
lazy import shutil
lazy import subprocess

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
        rumps.alert(
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
    def __init__(self, database):
        self.database = database

    def update_app(self, show_alerts):
        try:
            session = requests.Session()
            releases = get_releases(session)
            if releases is None:
                return

            if not is_update([int(component) for component in releases[0]["tag_name"].split(".")]):
                if show_alerts:
                    rumps.alert(
                        title="You're Up to Date",
                        message=f"You're on the latest available version ({VERSION})."
                    )
                return

            update = rumps.alert(
                title="Update Available",
                message=f"You can update to version {releases[0]["tag_name"]}.\nInstall the update?",
                cancel=True,
                ok="Update"
            )
            if not update:
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
                        if rumps.alert(
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
                        rumps.alert(
                            title="Update Failed",
                            message="Failed to install the update."
                        )
        except requests.exceptions.ConnectionError:
            rumps.alert(
                title="Connection Error",
                message="An unexpected error occured!"
            )

    def install_schedules_core(self, session, releases, show_alerts=True):
        for asset in releases[0]["assets"]:
            if asset["name"] == "schedules.zip":
                schedules_zip = download_file(session, asset["browser_download_url"])
                open("schedules.zip", "wb").write(schedules_zip)
                if Path("./schedules/").exists():
                    shutil.rmtree("./schedules/")
                try:
                    with zipfile.ZipFile("schedules.zip", 'r') as zip_ref:
                        zip_ref.extractall(".")
                    subprocess.run(["rm", "-rf", "schedules.zip"])
                    if show_alerts:
                        rumps.alert(
                            title="Update Successful",
                            message="Successfully updated schedules."
                        )
                    return True
                except:
                    subprocess.run(["rm", "-rf", "schedules"])
                    subprocess.run(["rm", "-rf", "schedules.zip"])
                    rumps.alert(
                        title="Update Failed",
                        message="Failed to update schedules."
                    )
                    return False
        return False

    def update_schedules(self, show_alerts):
        try:
            session = requests.Session()
            releases = get_releases(session)

            schedules_present = False
            schedules_metadata_present = False
            for asset in releases[0]["assets"]:
                if asset["name"] == "schedules.zip":
                    schedules_present = True
                elif asset["name"] == "schedule_version.txt":
                    schedules_metadata_present = True
                    schedules_metadata_url = asset["browser_download_url"]

            if not (schedules_present and schedules_metadata_present):
                rumps.alert(
                    title="Cannot Update Schedules",
                    message=f"Either the schedule files or schedule metadata are not present."
                )
                return False

            metadata = Path(self.database.database_dir) / "schedules" / "metadata.json"
            if metadata.exists():
                metadata_json = json.loads(metadata.read_text())
            else:
                metadata_json = {"version": 0}

            latest_schedule_version = int(download_file(session, schedules_metadata_url).decode())
            is_schedule_update = latest_schedule_version > metadata_json["version"]
            is_app_version_same = releases[0]["tag_name"] == VERSION
            is_later_app_version = is_update([int(component) for component in releases[0]["tag_name"].split(".")])

            if is_schedule_update and is_app_version_same:
                update = rumps.alert(
                    title="Schedule Updates Available",
                    message=f"You can update to schedule version {latest_schedule_version}.\nInstall the update?",
                    cancel=True,
                    ok="Update"
                )
                if not update:
                    return False
            elif is_schedule_update and not is_app_version_same and is_later_app_version:
                rumps.alert(
                    title="Cannot Update Schedules",
                    message=f"The latest version of Menu Bar Schedule ({releases[0]["tag_name"]}) must be installed to continue receiving schedule updates.",
                )
                return False
            elif is_schedule_update and not is_app_version_same and not is_later_app_version:
                continue_update = rumps.alert(
                    title="Schedule Updates Available",
                    message=f"You can update to schedule version {latest_schedule_version}, but it was made for an earlier version of Menu Bar Schedule ({releases[0]["tag_name"]}).\nOlder schedules may not be compatible with this version of the app.\nInstall the update?",
                    cancel=True,
                    ok="Update"
                )
                if not continue_update:
                    return False
            else:
                if show_alerts:
                    rumps.alert(
                        title="You're Up to Date",
                        message=f"You're on the latest available schedule version ({metadata_json["version"]})."
                    )
                return False

            return self.install_schedules_core(session, releases)
        except requests.exceptions.ConnectionError:
            rumps.alert(
                title="Connection Error",
                message="An unexpected error occured!"
            )
            return False
        except ValueError:
            rumps.alert(
                title="Cannot Update Schedules",
                message=f"The schedule metadata seems to be corrupt."
            )
            return False

    def install_schedules(self):
        download_schedules = rumps.alert(
            title="Schedules Not Found",
            message="Schedules are required for Menu Bar Schedule to function.\nInstall schedules?",
            cancel=True,
            ok="Install"
        )
        if not download_schedules:
            return False

        session = requests.Session()
        releases = get_releases(session)

        return self.install_schedules_core(session, releases, False)
