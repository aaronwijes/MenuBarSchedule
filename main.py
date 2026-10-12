# Currently broken right now! This file will be fixed soon :)
# Sorry for any inconvenience to those trying to run this from source!!
# There's a lot of things that need to be rewritten and thought out more.

import os
import json
import rumps
import sqlite3
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from platformdirs import user_config_dir

lazy import requests
lazy import shutil
lazy import subprocess

VERSION = "3.1.0"
VERSION_LIST = [int(component) for component in VERSION.split(".")]

REPO_NAME = "MenuBarSchedule"
GITHUB_USERNAME = "aaronwijes"

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

def get_title(config, timeframe, period, seconds):
    use_shorthand = config.fetch_value("use_shorthand")
    hide_seconds = config.fetch_value("hide_seconds")

    title = f"{timeframe.upper()} ({period}): "
    hours = seconds // 3600
    minutes = (seconds // 60) % 60

    prefix = f"{timeframe.upper()} ({period}): " if not use_shorthand else f"{timeframe[0].upper()}({period}): "
    if hours > 0:
        title = f"{prefix}{hours}h {minutes}m"
    elif minutes > 0:
        title = f"{prefix}{minutes}m" + (f" {seconds % 60}s" if not hide_seconds else "")
    else:
        title = f"{prefix}{seconds % 60}s"

    return title

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

class Config():
    def __init__(self):
        self.config_dir = Path(user_config_dir(REPO_NAME, GITHUB_USERNAME))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = f"{self.config_dir}/data.db"
        
        self.default_config = {
            "config_version": 1,
            "use_shorthand": 0,
            "hide_seconds": 0,
            "show_almost_end_notifs": 0,
            "check_app_updates_on_startup": 0,
            "check_schedule_updates_on_startup": 0,
            "set_schedule_based_on_calendar": 0,
            "selected_schedule": ""
        }

        os.chdir(self.config_dir)
        self.conn = sqlite3.connect("data.db")
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS online_schedules (
                pack_id TEXT,
                schedule_id TEXT,
                schedule_name TEXT,
                period_id TEXT,
                period_name TEXT,
                start_time TEXT,
                end_time TEXT,
                PRIMARY KEY (pack_id, schedule_id, period_id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_packs (
                pack_id TEXT PRIMARY KEY,
                pack_name TEXT,
                pack_version INT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enabled_packs (
                id TEXT PRIMARY KEY,
                name TEXT
            );
        """)

        self.conn.commit()

        for key, value in self.default_config.items():
            if not self.key_exists(key):
                self.set_value(key, value)

    def fetch_value(self, key):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT value FROM config WHERE key = ?", [key])
        value = cursor.fetchall()
        # print(key, value)
        value = value[0][0]
        if key != "selected_schedule":
            return int(value)
        else:
            return value

    def set_value(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO config (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value;
        """, [key, value])
        self.conn.commit()

    def key_exists(self, key):
        cursor = self.conn.cursor()
        return len(cursor.execute("SELECT * FROM config WHERE key = ?", [key]).fetchall()) > 0

    def add_enabled_pack(self, pack_name):
        cursor = self.conn.cursor()
        pack_id = self.get_online_pack_id(pack_name)
        cursor.execute(f"INSERT INTO enabled_packs (id, name) VALUES (?, ?) ON CONFLICT DO NOTHING;", [pack_id, pack_name])
        self.conn.commit()

    def remove_enabled_pack(self, pack_name):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM enabled_packs WHERE name = ?;", [pack_name])
        self.conn.commit()

    def remove_all_enabled_packs(self):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM enabled_packs;")
        self.conn.commit()

    def query_enabled_pack(self, pack_name):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM enabled_packs WHERE name=?;", [pack_name])
        return len(cursor.fetchall()) > 0

    def add_online_schedule(self, pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO online_schedules (pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING;
        """, [pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time])
        self.conn.commit()

    def add_online_schedule_pack(self, pack_id, pack_name, pack_version):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO schedule_packs (pack_id, pack_name, pack_version)
            VALUES (?, ?, ?)
            ON CONFLICT DO NOTHING;
        """, [pack_id, pack_name, pack_version])
        self.conn.commit()

    def remove_online_schedule_pack(self, pack_id):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            DELETE FROM online_schedules
            WHERE pack_id = ?
        """, [pack_id])
        self.conn.commit()

    def get_all_online_schedule_packs(self):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM schedule_packs;")
        rows = cursor.fetchall()

        packs = {}
        for row in rows:
            packs[row[0]] = row[1]

        return packs

    def get_online_pack_id(self, pack_name):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT pack_id FROM schedule_packs
            WHERE pack_name = ?;
        """, [pack_name])
        return cursor.fetchall()[0][0]

    def get_schedule_from_os_pack(self, pack_id, schedule_id):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT * FROM online_schedules
            WHERE pack_id = ?
            AND schedule_id = ?;
        """, [pack_id, schedule_id])

        periods = cursor.fetchall()
        schedule = {"name": periods[0][2], "schedule_id": periods[0][1], "pack_id": periods[0][0], "schedule": {}}
        print(schedule)
        for period in periods:
            schedule["schedule"][period[3]] = {
                "start": period[5],
                "end": period[6],
                "parsed_start": datetime.strptime(period[5], "%I:%M %p"),
                "parsed_end": datetime.strptime(period[6], "%I:%M %p"),
                "name": period[4]
            }

        return schedule

    def get_all_online_schedules(self):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT schedule_id, schedule_name
            FROM online_schedules os
            INNER JOIN enabled_packs ep
                ON ep.id = os.pack_id;
        """)
        rows = set(cursor.fetchall())

        schedules = {}
        for row in rows:
            schedules[row[0]] = row[1]

        return schedules

    def convert_schedule_jsons_to_sql(self):
        schedule_path = Path(self.config_dir) / "schedules"
        if schedule_path.exists():
            metadata = Path(self.config_dir) / "schedules" / "metadata.json"
            metadata_json = json.loads(metadata.read_text())
            for pack in metadata_json["packs"]:
                self.add_online_schedule_pack(pack["id"], pack["name"], pack["version"])
                schedule_path = Path(self.config_dir) / "schedules" / pack["id"] / "json"
                for schedule_json in schedule_path.glob("*.json"):
                    schedule = json.loads((schedule_json.read_text()))
                    for period_id, period in schedule["schedule"].items():
                        period["parsed_start"] = datetime.strptime(period["start"], "%I:%M %p")
                        period["parsed_end"] = datetime.strptime(period["end"], "%I:%M %p")
                        self.add_online_schedule(pack["id"], Path(schedule_json).name.replace(".json", ""), schedule["name"], period_id, period["name"], period["start"], period["end"])
                        
class Updater():
    def __init__(self, config):
        self.config_handler = config

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
                cancel=True
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

            metadata = Path(self.config_handler.config_dir) / "schedules" / "metadata.json"
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
                    message=f"A schedule update was found.\nInstall the update?",
                    cancel=True
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
                    message=f"A schedule update was found, but it was made for an earlier version of Menu Bar Schedule ({releases[0]["tag_name"]}).\nOlder schedules may not be compatible with this version of the app.\nInstall the update?",
                    cancel=True
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
            message="Schedules are required for Menu Bar Schedule to function.\nDownload schedules?",
            cancel=True
        )
        if not download_schedules:
            return False

        session = requests.Session()
        releases = get_releases(session)

        return self.install_schedules_core(session, releases, False)

class MenuBarSchedule(rumps.App):
    def __init__(self, config: Config, updater: Updater):
        super().__init__(
            name="Menu Bar Schedule",
            title=""
        )
        self.config = config
        self.config_handler = config
        self.updater = updater
        self.calendar = None

        self.sub_items = {}
        self.schedules = {}
        self.current_schedule = {}

        self.change_schedule = rumps.MenuItem(title="Change Schedule")
        self.change_schedule.add(rumps.MenuItem("Loading..."))

        self.change_schedule_pack = rumps.MenuItem(title="Configure Schedule Packs")
        self.change_schedule_pack.add(rumps.MenuItem("Loading..."))

        self.last_notified_period = None

        self.settings = rumps.MenuItem(title="Settings")
        self.settings_items = {
            "use_shorthand": rumps.MenuItem(title="Shorten Title", callback=self.toggle_settings),
            "hide_seconds": rumps.MenuItem(title="Hide Seconds Unit (>1 min)", callback=self.toggle_settings),
            "show_almost_end_notifs": rumps.MenuItem(title="Show Notifications Before Period Ends", callback=self.toggle_settings),
            "set_schedule_based_on_calendar": rumps.MenuItem(title="Set Schedule Based on Calendar", callback=self.toggle_settings),
            "NO_CONFIG_1": rumps.separator,
            "check_app_updates_on_startup": rumps.MenuItem(title="Check for App Updates on Startup", callback=self.toggle_settings),
            "check_schedule_updates_on_startup": rumps.MenuItem(title="Check for Schedule Updates on Startup", callback=self.toggle_settings),
            "NO_CONFIG_2": rumps.separator,
            "NO_CONFIG_3": rumps.MenuItem(title="Refresh Schedules from JSON", callback=self.refresh_schedules),
        }
        for id, item in self.settings_items.items():
            if not "NO_CONFIG" in id:
                item.state = self.config.fetch_value(id)
            self.settings.add(item)

        self.menu = [
            self.change_schedule,
            self.change_schedule_pack,
            "View Current Schedule",
            rumps.separator,
            "Check for App Updates",
            "Check for Schedule Updates",
            rumps.separator,
            self.settings,
            "About",
            rumps.separator,
        ]

        self.refresh_schedules(self.change_schedule)
        self.timer = rumps.Timer(self.update_time_left, interval=1.0)
        self.timer.start()

        if self.config.fetch_value("check_app_updates_on_startup"):
            self.updater.update_app(False)
        elif self.config.fetch_value("check_schedule_updates_on_startup"):
            self.updater.update_schedules(False)

    def select_option_schedule(self, sender):
        if self.config.fetch_value("selected_schedule") != "":
            self.schedule_items[self.config.fetch_value("selected_schedule")].state = False
            self.current_schedule = self.config.get_schedule_from_os_pack(self.config.get_online_pack_id(sender.title), [id for id, name in self.schedule_options.items() if name == sender.title][0])
        self.config.set_value("selected_schedule", sender.title)
        sender.state = True

    def select_option_pack(self, sender):
        if not self.config.query_enabled_pack(sender.title):
            self.config.add_enabled_pack(sender.title)
        else:
            self.config.remove_enabled_pack(sender.title)
        self.refresh_schedules(None)

    def toggle_settings(self, sender):
        cfg_lookup = {
            "Check for App Updates on Startup": "check_app_updates_on_startup",
            "Check for Schedule Updates on Startup": "check_schedule_updates_on_startup",
            "Shorten Title": "use_shorthand",
            "Hide Seconds Unit (>1 min)": "hide_seconds",
            "Show Notifications Before Period Ends": "show_almost_end_notifs",
            "Set Schedule Based on Calendar": "set_schedule_based_on_calendar"
        }
        if sender.title in cfg_lookup:
            config_key = cfg_lookup[sender.title]
            new_key_value = not self.config.fetch_value(config_key)
            self.config.set_value(config_key, new_key_value)
            sender.state = new_key_value

        if sender.title == "Set Schedule Based on Calendar":
            self.refresh_schedules(None)

    def update_time_left(self, sender):
        now = datetime.now()
        found_period = False

        if self.config.fetch_value("set_schedule_based_on_calendar"):
            if self.calendar != None:
                if f"{now.month}/{now.day}/{now.year}" in self.calendar["exceptions"]:
                    if self.calendar["exceptions"][f"{now.month}/{now.day}/{now.year}"] in self.schedules:
                        self.config.set_value("selected_schedule", self.calendar["exceptions"][f"{now.month}/{now.day}/{now.year}"])
                elif self.calendar["default"] in self.schedules:
                    self.config.set_value("selected_schedule", self.calendar["default"])

                self.schedule_options = sorted([schedule["name"] for schedule in self.schedules.values()])
                if self.schedule_options != []:
                    self.sub_items = {
                        opt: rumps.MenuItem(title=opt, callback=self.select_option_schedule if not self.config.fetch_value("set_schedule_based_on_calendar") else None)
                        for opt in self.schedule_options
                    }

                    if self.config.fetch_value("selected_schedule") not in self.schedule_options:
                        self.config.set_value("selected_schedule", "")
                    if self.config.fetch_value("selected_schedule") != "":
                        self.sub_items[self.config.fetch_value("selected_schedule")].state = True

                    self.change_schedule.clear()
                    for item in self.sub_items.values():
                        self.change_schedule.add(item)

        if self.config.fetch_value("selected_schedule") == "":
            if self.title != "No Schedule":
                self.title = "No Schedule"
            return

        proposed_title = ""
        for period_id, period in self.current_schedule["schedule"].items():
            start = datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                hour=period["parsed_start"].hour,
                minute=period["parsed_start"].minute
            )
            end = datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                hour=period["parsed_end"].hour,
                minute=period["parsed_end"].minute
            )
            time_until_start = round((start - now).total_seconds())
            time_until_end = round((end - now).total_seconds())

            if time_until_start > 0:
                found_period = True
                proposed_title = get_title(self.config, "start", period_id, time_until_start)
                break
            elif time_until_end > 0:
                found_period = True
                proposed_title = get_title(self.config, "end", period_id, time_until_end)
                if self.config.fetch_value("show_almost_end_notifs") and time_until_end <= 300 and self.last_notified_period != period_id:
                    rumps.notification(title="Menu Bar Schedule", subtitle="", message=f"{period["name"]} is ending in five minutes ({period["end"]}).", sound=False)
                    self.last_notified_period = period_id
                break
        if not found_period:
            tomorrow = datetime.today() + timedelta(days=1)
            start = datetime(
                year=tomorrow.year,
                month=tomorrow.month,
                day=tomorrow.day,
                hour=list(self.current_schedule["schedule"].values())[0]["parsed_start"].hour,
                minute=list(self.current_schedule["schedule"].values())[0]["parsed_start"].minute
            )
            time_until_start = round((start - now).total_seconds())
            proposed_title = get_title(self.config, "start", list(self.current_schedule["schedule"].keys())[0], time_until_start)

        if self.title != proposed_title:
            self.title = proposed_title

    def refresh_schedules(self, sender):
        self.schedules = {}

        schedule_path = Path(self.config_handler.config_dir) / "schedules"
        if not schedule_path.exists():
            self.change_schedule.clear()
            self.change_schedule.add(rumps.MenuItem(title="No Schedules Found"))

            self.change_schedule_pack.clear()
            self.change_schedule_pack.add(rumps.MenuItem(title="No Packs Found"))

            if not self.updater.install_schedules():
                self.config.set_value("selected_schedule", "")
                self.config.remove_all_enabled_packs()

        if schedule_path.exists():
            self.config.convert_schedule_jsons_to_sql()

            metadata = Path(self.config_handler.config_dir) / "schedules" / "metadata.json"
            metadata_json = json.loads(metadata.read_text())
            for pack in metadata_json["packs"]:
                calendar_path = Path(self.config_handler.config_dir) / "schedules" / pack["id"] / "calendar.json"
                if calendar_path.exists():
                    self.calendar = json.loads((calendar_path.read_text()))
                else:
                    self.calendar = None

            self.schedule_options = self.config.get_all_online_schedules()
            if self.schedule_options != {}:
                self.schedule_items = {
                    id: rumps.MenuItem(title=name, callback=self.select_option_schedule if not self.config.fetch_value("set_schedule_based_on_calendar") else None)
                    for id, name in self.schedule_options.items()
                }

                if self.config.fetch_value("selected_schedule") not in self.schedule_options.values():
                    self.config.set_value("selected_schedule", "")
                if self.config.fetch_value("selected_schedule") != "":
                    schedule_id = [id for id, name in self.schedule_options.items() if name == self.config.fetch_value("selected_schedule")][0]
                    self.schedule_items[schedule_id].state = True
                    self.current_schedule = self.config.get_schedule_from_os_pack(self.config.get_online_pack_id(sender.title), schedule_id)

                self.change_schedule.clear()
                for item in self.schedule_items.values():
                    self.change_schedule.add(item)
            else:
                self.change_schedule.clear()
                self.change_schedule.add(rumps.MenuItem(title="No Schedules Found"))
                self.config.set_value("selected_schedule", "")

            self.packs = self.config.get_all_online_schedule_packs()
            self.pack_options = {id: name for id, name in self.packs.items()}
            if self.pack_options != {}:
                self.pack_items = {
                    id: rumps.MenuItem(title=name, callback=self.select_option_pack)
                    for id, name in self.pack_options.items()
                }
                self.change_schedule_pack.clear()
                for item in self.pack_items.values():
                    if self.config.query_enabled_pack(item.title):
                        item.state = True
                    self.change_schedule_pack.add(item)
            else:
                self.change_schedule_pack.clear()
                self.change_schedule_pack.add(rumps.MenuItem(title="No Packs Found"))

    @rumps.clicked("View Current Schedule")
    def view_schedule(self, sender):
        if self.config.fetch_value("selected_schedule") != "":
            message = ""
            for period in self.schedules[self.config.fetch_value("selected_schedule")]["schedule"].values():
                message += f"{period["name"]}: {period["start"]} - {period["end"]}\n"
            rumps.alert(
                title=self.schedules[self.config.fetch_value("selected_schedule")]["name"],
                message=message
            )
        else:
            rumps.alert(
                title="No Schedule Selected",
                message="No schedule is currently selected.\nSelect a schedule to view its timetable!"
            )

    @rumps.clicked("Check for App Updates")
    def check_updates(self, sender):
        self.updater.update_app(True)

    @rumps.clicked("Check for Schedule Updates")
    def update_schedules(self, sender):
        if self.updater.update_schedules(True):
            self.refresh_schedules(None)

    @rumps.clicked("About")
    def about(self, sender):
        rumps.alert(
            title=f"About",
            message=f"Menu Bar Schedule shows how much time is left until your next class!\n\nVersion {VERSION}\nCreated by Aaron (GitHub: https://github.com/{GITHUB_USERNAME})"
        )

if __name__ == "__main__":
    config = Config()
    updater = Updater(config)
    MenuBarSchedule(config, updater).run()
    config.conn.close()
