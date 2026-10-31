import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from platform import system
from .database import Database
from .updater import Updater
from .info import VERSION, GITHUB_USERNAME

MBS_LAUNCHD_PLIST = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Label</key>
        <string>org.aaron.menubarschedule</string>

        <key>ProgramArguments</key>
        <array>
            <string>/Applications/MenuBarSchedule.app/Contents/macOS/MenuBarSchedule</string>
        </array>

        <key>RunAtLoad</key>
        <true/>
        
        <key>KeepAlive</key>
        <false/>
        
        <key>StandardOutPath</key>
        <string>/tmp/menubarschedule.log</string>
        
        <key>StandardErrorPath</key>
        <string>/tmp/menubarschedule.log</string>
    </dict>
</plist>
"""

class MBSCommonFunctions():
    def __init__(self, database: Database, updater: Updater):
        self.database = database
        self.updater = updater

        self.calendar = None
        self.last_notified_period = None
        self.current_schedule = {}

        self.settings = {}
        self.settings_keys = [
            "use_shorthand",
            "hide_seconds",
            "show_almost_end_notifs",
            "set_schedule_based_on_calendar",
            "check_app_updates_on_startup",
            "check_schedule_updates_on_startup",
            "selected_online_pack",
            "selected_online_pack_id",
            "selected_schedule",
            "selected_schedule_id",
            "open_at_login"
        ]
        for key in self.settings_keys:
            self.settings[key] = self.database.fetch_value(key)

    def schedule_dir_exists(self):
        if self.database.get_all_online_schedule_packs() == {}:
            if not self.update_schedules(False):
                for key in ["selected_schedule", "selected_schedule_id", "selected_online_pack", "selected_online_pack_id"]:
                    self.settings[key] = ""
                    self.database.set_value(key, "")
                return False

            return self.database.get_all_online_schedule_packs() != {}
        else:
            return True

    def load_packs(self):
        self.packs = self.database.get_all_online_schedule_packs()
        if self.packs != {}:
            self.pack_options = {id: pack_obj["pack_name"] for id, pack_obj in self.packs.items()}
                
            selected_pack_id = ""
            if self.settings["selected_online_pack"] not in self.pack_options.values():
                for key in ["selected_online_pack", "selected_online_pack_id"]:
                    self.settings[key] = ""
                    self.database.set_value(key, "")
                self.calendar = None
            if self.settings["selected_online_pack"] != "":
                selected_pack_id = self.settings["selected_online_pack_id"]
                calendar = self.database.get_calendar(selected_pack_id)
                if calendar != {}:
                    self.calendar = calendar
                else:
                    self.calendar = None
            return self.pack_options, selected_pack_id
        else:
            for key in ["selected_online_pack", "selected_online_pack_id"]:
                self.settings[key] = ""
                self.database.set_value(key, "")
            return {}, ""

    def load_schedules(self):
        self.schedule_options = self.database.get_all_online_schedules()
        if self.schedule_options != {}:
            selected_pack_id = ""
            selected_schedule_id = ""
            set_schedule_based_on_calendar = self.settings["set_schedule_based_on_calendar"]

            if self.settings["selected_schedule_id"] not in self.schedule_options.keys():
                self.current_schedule = {}
                for key in ["selected_schedule", "selected_schedule_id"]:
                    self.settings[key] = ""
                    self.database.set_value(key, "")
            if self.settings["selected_schedule"] != "":
                selected_pack_id = self.settings["selected_online_pack_id"]
                selected_schedule_id = self.settings["selected_schedule_id"]
                self.current_schedule = self.database.get_schedule_from_os_pack(selected_pack_id, selected_schedule_id)

            return self.schedule_options, selected_schedule_id, set_schedule_based_on_calendar
        else:
            self.current_schedule = {}
            for key in ["selected_schedule", "selected_schedule_id"]:
                self.settings[key] = ""
                self.database.set_value(key, "")
            return {}, "", False

    def get_title(self, timeframe, period, seconds):
        use_shorthand = self.settings["use_shorthand"]
        hide_seconds = self.settings["hide_seconds"]

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

    def get_daily_schedule(self, calendar, schedule_options, now):
        date = f"{now.month}/{now.day}/{now.year}"
        schedule = calendar["exceptions"].get(date, calendar["default"])

        if schedule["id"] in schedule_options:
            return schedule["id"], schedule["name"]

        return "", ""

    def select_schedule(self, title):
        old_schedule_id = ""
        if self.settings["selected_schedule_id"] != "":
            old_schedule_id = self.settings["selected_schedule_id"]
        pack_id = self.settings["selected_online_pack_id"]
        schedule_id = self.database.get_online_schedule_id(pack_id, title)
        self.current_schedule = self.database.get_schedule_from_os_pack(pack_id, schedule_id)
        for key, value in {"selected_schedule": title, "selected_schedule_id": schedule_id}.items():
            self.settings[key] = value
            self.database.set_value(key, value)
        
        return old_schedule_id

    def select_pack(self, title):
        old_pack_id = ""
        selected_online_pack = self.settings["selected_online_pack"]
        if selected_online_pack == title:
            self.current_schedule = {}
            old_pack_id = self.database.get_online_pack_id(selected_online_pack)
            for key in ["selected_schedule", "selected_schedule_id", "selected_online_pack", "selected_online_pack_id"]:
                self.settings[key] = ""
                self.database.set_value(key, "")
        else:
            old_pack_id = self.database.get_online_pack_id(selected_online_pack)
            pack_id = self.database.get_online_pack_id(title)
            for key, value in {"selected_online_pack": title, "selected_online_pack_id": pack_id}.items():
                self.settings[key] = value
                self.database.set_value(key, value)

        return old_pack_id

    def toggle_settings(self, title):
        cfg_lookup = {
            "Check for App Updates on Startup": "check_app_updates_on_startup",
            "Check for Schedule Updates on Startup": "check_schedule_updates_on_startup",
            "Shorten Title": "use_shorthand",
            "Hide Seconds Unit (>1 min)": "hide_seconds",
            "Show Notifications Before Period Ends": "show_almost_end_notifs",
            "Set Schedule Based on Calendar": "set_schedule_based_on_calendar",
            "Open at Login": "open_at_login"
        }
        if title in cfg_lookup:
            config_key = cfg_lookup[title]
            self.settings[config_key] = not self.settings[config_key]
            self.database.set_value(config_key, self.settings[config_key])
        
        return self.settings[config_key]

    def update_time_left_calendar(self):
        now = datetime.now()
        tomorrow = datetime.today() + timedelta(days=1)
        day_is_off = False
        day_is_over = False
        proposed_title = ""
        schedule_id = ""
        old_schedule_id = self.settings["selected_schedule_id"]

        use_calendar = self.settings["set_schedule_based_on_calendar"] and self.calendar != None
        if use_calendar:
            temp_schedule_id = self.get_daily_schedule(self.calendar, self.schedule_options, now)[0]
            temp_schedule = self.database.get_schedule_from_os_pack(self.calendar["pack_id"], temp_schedule_id)
            last_period_end = datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                hour=list(temp_schedule["schedule"].values())[-1]["parsed_end"].hour,
                minute=list(temp_schedule["schedule"].values())[-1]["parsed_end"].minute
            )
            if (now - last_period_end).total_seconds() > 0:
                day_is_over = True

            if day_is_over:
                now = tomorrow
            if now.weekday() in self.calendar["off_days"]:
                day_is_off = True
                self.current_schedule = {}
                for key in ["selected_schedule", "selected_schedule_id"]:
                    self.settings[key] = ""
                    self.database.set_value(key, "")
            else:
                schedule_id, schedule_name = self.get_daily_schedule(self.calendar, self.schedule_options, now)
                if schedule_id != self.current_schedule.get("schedule_id", None):
                    for key, value in {"selected_schedule": schedule_name, "selected_schedule_id": schedule_id}.items():
                        self.settings[key] = value
                        self.database.set_value(key, value)
                    self.current_schedule = self.database.get_schedule_from_os_pack(self.calendar["pack_id"], schedule_id)

            if day_is_over and not day_is_off:
                now = datetime.now()
                start = datetime(
                    year=tomorrow.year,
                    month=tomorrow.month,
                    day=tomorrow.day,
                    hour=list(self.current_schedule["schedule"].values())[0]["parsed_start"].hour,
                    minute=list(self.current_schedule["schedule"].values())[0]["parsed_start"].minute
                )
                time_until_start = round((start - now).total_seconds())
                proposed_title = self.get_title("start", list(self.current_schedule["schedule"].keys())[0], time_until_start)

        if self.settings["selected_schedule"] == "":
            proposed_title = "No Schedule" if not day_is_off else "Day Off"

        return use_calendar, old_schedule_id, schedule_id, proposed_title, day_is_off

    def update_time_left(self, day_is_off):
        now = datetime.now()
        tomorrow = datetime.today() + timedelta(days=1)

        proposed_title = ""
        notification_title = ""
        notification_message = ""
        found_period = False

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
                proposed_title = self.get_title("start", period_id, time_until_start)
                break
            elif time_until_end > 0:
                found_period = True
                proposed_title = self.get_title("end", period_id, time_until_end)
                if self.settings["show_almost_end_notifs"] and time_until_end <= 300 and self.last_notified_period != period_id:
                    notification_title = "Menu Bar Schedule"
                    notification_message = f"{period["name"]} is ending in five minutes ({period["end"]})."
                    self.last_notified_period = period_id
                break
        if not found_period and not day_is_off:
            start = datetime(
                year=tomorrow.year,
                month=tomorrow.month,
                day=tomorrow.day,
                hour=list(self.current_schedule["schedule"].values())[0]["parsed_start"].hour,
                minute=list(self.current_schedule["schedule"].values())[0]["parsed_start"].minute
            )
            time_until_start = round((start - now).total_seconds())
            proposed_title = self.get_title("start", list(self.current_schedule["schedule"].keys())[0], time_until_start)

        return proposed_title, notification_title, notification_message

    def view_schedule(self):
        if self.settings["selected_schedule"] != "":
            message = "\n".join(
                f"{period["name"]}: {period["start"]} - {period["end"]}"
                for period in self.current_schedule["schedule"].values()
            )
            title = self.current_schedule["name"]
        else:
            title = "No Schedule Selected"
            message = "No schedule is currently selected.\nSelect a schedule to view its timetable!"

        return title, message

    def about(self):
        title = "About"
        message = f"Menu Bar Schedule shows how much time is left until your next class/event!\n\nVersion {VERSION}\nCreated by Aaron with <3\nhttps://github.com/{GITHUB_USERNAME}"

        return title, message

    def check_updates_on_startup(self):
        if self.settings["check_app_updates_on_startup"]:
            if self.update_app(False) == "restart":
                return "quit"
        if self.settings["check_schedule_updates_on_startup"]:
            self.update_schedules(False)

    def update_app(self, show_alerts):
        return self.updater.update_app_macos(show_alerts)

    def update_schedules(self, show_alerts):
        return self.updater.update_schedules(show_alerts)

    def toggle_login_item(self):
        if system() == "Darwin":
            uid = os.getuid()
            plist_path = os.path.expanduser("~/Library/LaunchAgents/org.aaron.menubarschedule.plist")
            
            if self.settings["open_at_login"]:
                Path(plist_path).write_text(MBS_LAUNCHD_PLIST)
                subprocess.run(["chmod", "644", plist_path])
                subprocess.run(["launchctl", "bootout", f"gui/{uid}", plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["launchctl", "bootout", f"gui/{uid}", plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if Path(plist_path).exists():
                    os.remove(plist_path)
        elif system() == "Windows":
            return # To enable open on startup for Windows, use the installer