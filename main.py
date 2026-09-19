import os
import json
import time
import rumps
import requests
import shutil
import subprocess
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from platformdirs import user_config_dir

VERSION = "0.7.0"

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
                "selected_schedule": "Regular Bell Schedule"
            }
        else:
            self.config = json.loads(Path(self.config_path).read_text())

    def save_config(self):
        open(self.config_path, "w").write(json.dumps(self.config, indent=2))

class MenuBarSchedule(rumps.App):
    def __init__(self, config):
        super().__init__(
            name="Menu Bar Schedule",
            title=""
        )
        self.config = config.config
        self.config_handler = config

        self.sub_items = {}
        self.schedules = {}

        self.change_schedule = rumps.MenuItem(title="Change Schedule")
        self.change_schedule.add(rumps.MenuItem("Loading..."))

        self.menu = [
            self.change_schedule,
            "View Schedule",
            "Refresh Schedules",
            "About",
            rumps.separator,
            "Check For Updates",
            rumps.separator
        ]

        self.refresh_schedules(self.change_schedule)

        self.timer = rumps.Timer(self.update_time_left, 0.5)
        self.timer.start()

    def select_option(self, sender):
        self.sub_items[self.config["selected_schedule"]].state = False
        self.config["selected_schedule"] = sender.title
        self.config_handler.save_config()
        sender.state = True

    def update_time_left(self, _):
        now = datetime.now()
        day = now.day
        month = now.month
        year = now.year
        found_period = False
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
        json_path = Path(__file__).parent / "schedules"
        for schedule_json in json_path.glob("*.json"):
            schedule = json.loads((schedule_json.read_text()))
            self.schedules[schedule["name"]] = schedule

        self.options = sorted([schedule["name"] for schedule in self.schedules.values()])
        self.sub_items = {
            opt: rumps.MenuItem(title=opt, callback=self.select_option)
            for opt in self.options
        }
        self.sub_items[self.config["selected_schedule"]].state = True
        
        self.change_schedule.clear()
        for item in self.sub_items.values():
            self.change_schedule.add(item)

        self.config_handler.save_config()

    @rumps.clicked("Check For Updates")
    def check_updates(self, _):
        try:
            session = requests.Session()

            releases_req = session.get("https://api.github.com/repos/AaronWijesinghe/MenuBarSchedule/releases")
            if not releases_req.ok:
                rumps.alert(
                    title="MenuBarSchedule",
                    message="Couldn't connect to GitHub Releases."
                )
                return
            releases = releases_req.json()
            if releases[0]["name"] == VERSION:
                rumps.alert(
                    title="MenuBarSchedule",
                    message="No updates were found."
                )
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
                    except:
                        subprocess.run(["rm", "-rf", "/Applications/MenuBarSchedule.app"])
                        subprocess.run(["rm", "-rf", "MenuBarSchedule.app.zip"])
                        rumps.alert(
                            title="MenuBarSchedule",
                            message="Failed to install the update."
                        )
                        return
        except requests.exceptions.ConnectionError:
            return False

    @rumps.clicked("About")
    def about(self, _):
        rumps.alert(
            title=f"Menu Bar Schedule",
            message=f"An easy way to see how much time is left until your next class!\n\nVersion {VERSION}\nCreated by Aaron (GitHub: https://github.com/aaronwijes)"
        )

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    MenuBarSchedule(Config()).run()
