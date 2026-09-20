import os
import json
import time
import rumps
import requests
import shutil
import subprocess
import zipfile
import sys
from datetime import datetime, timedelta
from pathlib import Path
from platformdirs import user_config_dir

VERSION = "0.10.1"

def get_title(timeframe, period, seconds):
    title = f"{timeframe.upper()} ({period}): "
    hours = seconds // 3600
    minutes = (seconds // 60) % 60
    if hours > 0:
        title = f"{timeframe.upper()} ({period}): {seconds // 3600}h {(seconds // 60) % 60}m"
    elif minutes > 0:
        title = f"{timeframe.upper()} ({period}): {(seconds // 60) % 60}m {seconds % 60}s"
    else:
        title = f"{timeframe.upper()} ({period}): {seconds % 60}s"
    return title

def get_releases(session):
    releases_req = session.get("https://api.github.com/repos/aaronwijes/MenuBarSchedule/releases")
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

class Config():
    def __init__(self):
        self.config_dir = Path(user_config_dir("MenuBarSchedule", "aaronwijes"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = f"{self.config_dir}/config.json"

        if not Path(self.config_path).exists():
            self.config = {
                "version": VERSION,
                "selected_schedule": "",
                "show_almost_end_notifs": False,
                "check_app_updates_on_startup": False,
                "check_schedule_updates_on_startup": False,
                "enabled_packs": ["siths"]
            }
        else:
            self.config = json.loads(Path(self.config_path).read_text())
            # run migration code here
            self.config["version"] = VERSION
            self.save_config()

    def save_config(self):
        open(self.config_path, "w").write(json.dumps(self.config, indent=2))

class Updater():
    def __init__(self, config):
        self.config_handler = config

    def update_app(self, show_alerts):
        try:
            session = requests.Session()
            releases = get_releases(session)
            if releases is None:
                return

            if releases[0]["tag_name"] == VERSION:
                if show_alerts:
                    rumps.alert(
                        title="You're Up to Date",
                        message=f"You're on the latest available version ({VERSION})."
                    )
                return

            update = rumps.alert(
                title="Update Available",
                message=f"You can update to version {releases[0]["tag_name"]}.\nInstall the update?",
                cancel=True
            )
            if not update:
                return

            for asset in releases[0]["assets"]:
                if "MenuBarSchedule.app.zip" == asset["name"]:
                    app_darwin = download_file(session, asset["browser_download_url"])
                    open("MenuBarSchedule.app.zip", "wb").write(app_darwin)
                    if os.path.exists("/Applications/MenuBarSchedule.app"):
                        shutil.rmtree("/Applications/MenuBarSchedule.app")
                    try:
                        with zipfile.ZipFile("MenuBarSchedule.app.zip", 'r') as zip_ref:
                            zip_ref.extractall("/Applications/")
                        subprocess.run(["chmod", "+x", "/Applications/MenuBarSchedule.app/Contents/MacOS/MenuBarSchedule"])
                        subprocess.run(["xattr", "-dr", "com.apple.quarantine", "/Applications/MenuBarSchedule.app"])
                        subprocess.run(["rm", "-rf", "MenuBarSchedule.app.zip"])
                        rumps.alert(
                            title="Update Successful",
                            message="Successfully installed the update!\nRestart Menu Bar Schedule to finish the update."
                        )
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
            if "schedules-" in asset["name"]:
                schedules_zip = download_file(session, asset["browser_download_url"])
                open(asset["name"], "wb").write(schedules_zip)
                if os.path.exists("./schedules/"):
                    shutil.rmtree("./schedules/")
                try:
                    with zipfile.ZipFile(asset["name"], 'r') as zip_ref:
                        zip_ref.extractall(".")
                    subprocess.run(["rm", "-rf", asset["name"]])
                    if show_alerts:
                        rumps.alert(
                            title="Update Successful",
                            message="Successfully updated schedules."
                        )
                    return True
                except:
                    subprocess.run(["rm", "-rf", "schedules"])
                    subprocess.run(["rm", "-rf", asset["name"]])
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
            for asset in releases[0]["assets"]:
                if "schedules-" in asset["name"]:
                    metadata = Path(self.config_handler.config_dir) / "schedules" / "metadata.json"
                    metadata_json = json.loads(metadata.read_text())
                    if f"schedules-v{metadata_json["version"]}.zip" != asset["name"]:
                        update = rumps.alert(
                            title="Schedule Updates Available",
                            message=f"A schedule update was found.\nInstall the update?",
                            cancel=True
                        )
                        if not update:
                            return
                    else:
                        if show_alerts:
                            rumps.alert(
                                title="You're Up to Date",
                                message=f"You're on the latest available schedule version ({metadata_json["version"]})."
                            )
                        return

            self.install_schedules_core(session, releases)
        except requests.exceptions.ConnectionError:
            rumps.alert(
                title="Connection Error",
                message="An unexpected error occured!"
            )

    def install_schedules(self):
        download_schedules = rumps.alert(
            title="Schedules Not Found",
            message="Schedules are required for Menu Bar Schedule to function.\nDownload schedules?",
            cancel=True
        )
        if not download_schedules:
            sys.exit()

        session = requests.Session()
        releases = get_releases(session)

        if not self.install_schedules_core(session, releases):
            exit()

class MenuBarSchedule(rumps.App):
    def __init__(self, config, updater):
        super().__init__(
            name="Menu Bar Schedule",
            title=""
        )
        self.config = config.config
        self.config_handler = config
        self.updater = updater

        self.sub_items = {}
        self.schedules = {}

        self.change_schedule = rumps.MenuItem(title="Change Schedule")
        self.change_schedule.add(rumps.MenuItem("Loading..."))

        self.change_schedule_pack = rumps.MenuItem(title="Configure Schedule Packs")
        self.change_schedule_pack.add(rumps.MenuItem("Loading..."))

        self.app_startup_updates = rumps.MenuItem(title="Check for Updates on Startup")
        self.app_startup_items = {
            "app": rumps.MenuItem(title="App Updates", callback=self.toggle_startup_updates),
            "schedule": rumps.MenuItem(title="Schedule Updates", callback=self.toggle_startup_updates)
        }
        for id, item in self.app_startup_items.items():
            item.state = self.config[f"check_{id}_updates_on_startup"]
            self.app_startup_updates.add(item)

        self.menu = [
            self.change_schedule,
            self.change_schedule_pack,
            "Refresh Schedules",
            "View Schedule",
            "About",
            rumps.separator,
            "Check for App Updates",
            "Check for Schedule Updates",
            self.app_startup_updates,
            rumps.separator
        ]

        self.refresh_schedules(self.change_schedule)
        self.timer = rumps.Timer(self.update_time_left, 0.5)
        self.timer.start()

        if self.config["check_app_updates_on_startup"]:
            self.updater.update_app(False)
        elif self.config["check_schedule_updates_on_startup"]:
            self.updater.update_schedules(False)

    def select_option_schedule(self, sender):
        if self.config["selected_schedule"] != "":
            self.sub_items[self.config["selected_schedule"]].state = False
        self.config["selected_schedule"] = sender.title
        self.config_handler.save_config()
        sender.state = True

    def select_option_pack(self, sender):
        if sender.title not in self.config["enabled_packs"]:
            self.config["enabled_packs"].append(sender.title)
            # sender.state = True
        else:
            self.config["enabled_packs"].remove(sender.title)
            # sender.state = False
        self.config_handler.save_config()
        self.refresh_schedules(None)

    def toggle_startup_updates(self, sender):
        if sender.title == "App Updates":
            if self.config["check_app_updates_on_startup"]:
                self.config["check_app_updates_on_startup"] = False
            else:
                self.config["check_app_updates_on_startup"] = True
            sender.state = self.config["check_app_updates_on_startup"]
        elif sender.title == "Schedule Updates":
            if self.config["check_schedule_updates_on_startup"]:
                self.config["check_schedule_updates_on_startup"] = False
            else:
                self.config["check_schedule_updates_on_startup"] = True
            sender.state = self.config["check_schedule_updates_on_startup"]

        self.config_handler.save_config()

    def update_time_left(self, _):
        now = datetime.now()
        day = now.day
        month = now.month
        year = now.year
        found_period = False

        if self.config["selected_schedule"] == "":
            self.title = "No Schedule Selected"
            return

        for period_id, period in self.schedules[self.config["selected_schedule"]]["schedule"].items():
            time_until_start = round((datetime.strptime(f"{month}/{day}/{year} {period["start"]}", "%m/%d/%Y %I:%M %p") - now).total_seconds())
            time_until_end = round((datetime.strptime(f"{month}/{day}/{year} {period["end"]}", "%m/%d/%Y %I:%M %p") - now).total_seconds())

            if time_until_start > 0:
                self.title = get_title("start", period_id, time_until_start)
                found_period = True
                break
            elif time_until_end > 0:
                found_period = True
                self.title = get_title("end", period_id, time_until_end)
                # rumps.notification(title=self.config["selected_schedule"], subtitle=f"{period["name"]} is almost ending!", message=f"{period["name"]} ends in {self.title}.")
                break
        if not found_period:
            tomorrow = datetime.today() + timedelta(days=1)
            day = tomorrow.day
            month = tomorrow.month
            year = tomorrow.year
            time_until_start = round((datetime.strptime(f"{month}/{day}/{year} {self.schedules[self.config["selected_schedule"]]["schedule"][list(self.schedules[self.config["selected_schedule"]]["schedule"].keys())[0]]["start"]}", "%m/%d/%Y %I:%M %p") - now).total_seconds())
            self.title = get_title("start", list(self.schedules[self.config["selected_schedule"]]["schedule"].keys())[0], time_until_start)
        time.sleep(0.5)

    @rumps.clicked("View Schedule")
    def view_schedule(self, _):
        message = ""
        for period in self.schedules[self.config["selected_schedule"]]["schedule"].values():
            message += f"{period["name"]}: {period["start"]} - {period["end"]}\n"
        rumps.alert(
            title=self.schedules[self.config["selected_schedule"]]["name"],
            message=message
        )

    @rumps.clicked("Refresh Schedules")
    def refresh_schedules(self, _):
        self.schedules = {}

        schedule_path = Path(self.config_handler.config_dir) / "schedules"
        if not schedule_path.exists():
            self.updater.install_schedules()

        metadata = Path(self.config_handler.config_dir) / "schedules" / "metadata.json"
        metadata_json = json.loads(metadata.read_text())
        for pack in metadata_json["packs"]:
            if pack["name"] in self.config["enabled_packs"]:
                schedule_path = Path(self.config_handler.config_dir) / "schedules" / pack["id"]
                for schedule_json in schedule_path.glob("*.json"):
                    schedule = json.loads((schedule_json.read_text()))
                    self.schedules[schedule["name"]] = schedule

        self.schedule_options = sorted([schedule["name"] for schedule in self.schedules.values()])
        self.pack_options = [pack for pack in metadata_json["packs"]]
        if self.pack_options != []:
            self.sub_items = {
                opt["name"]: rumps.MenuItem(title=opt["name"], callback=self.select_option_pack)
                for opt in self.pack_options
            }
            self.change_schedule_pack.clear()
            for item in self.sub_items.values():
                if item.title in self.config["enabled_packs"]:
                    item.state = True
                self.change_schedule_pack.add(item)

        if self.schedule_options != []:
            self.sub_items = {
                opt: rumps.MenuItem(title=opt, callback=self.select_option_schedule)
                for opt in self.schedule_options
            }

            if self.config["selected_schedule"] not in self.schedule_options:
                self.config["selected_schedule"] = ""
            if self.config["selected_schedule"] != "":
                self.sub_items[self.config["selected_schedule"]].state = True

            self.change_schedule.clear()
            for item in self.sub_items.values():
                self.change_schedule.add(item)
        else:
            self.change_schedule.clear()
            self.change_schedule.add(rumps.MenuItem(title="No Schedules Found"))
            self.config["selected_schedule"] = ""

        self.config_handler.save_config()

    @rumps.clicked("Check for App Updates")
    def check_updates(self, _):
        self.updater.update_app(True)

    @rumps.clicked("Check for Schedule Updates")
    def update_schedules(self, _):
        self.updater.update_schedules(True)
        self.refresh_schedules(None)

    @rumps.clicked("About")
    def about(self, _):
        rumps.alert(
            title=f"About",
            message=f"Menu Bar Schedule shows how much time is left until your next class!\n\nVersion {VERSION}\nCreated by Aaron (GitHub: https://github.com/aaronwijes)"
        )

if __name__ == "__main__":
    config = Config()
    updater = Updater(config)
    os.chdir(config.config_dir)
    MenuBarSchedule(config, updater).run()
