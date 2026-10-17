from datetime import datetime, timedelta
from pathlib import Path
from platform import system
from .database import Database
from .updater import Updater
from .info import VERSION, GITHUB_USERNAME

class MBSCommonFunctions():
    def __init__(self, database: Database, updater: Updater):
        self.database = database
        self.updater = updater

        self.calendar = None
        self.current_schedule = {}

    def schedule_dir_exists(self):
        schedule_path = Path(self.database.database_dir) / "schedules"

        if self.database.get_all_online_schedule_packs() == {}:
            if not self.updater.install_schedules():
                self.prompt_install_schedules()

        if schedule_path.exists():
            self.database.convert_schedule_jsons_to_sql()
            return True
        else:
            return False

    def prompt_install_schedules(self):
        if not self.updater.install_schedules():
            self.database.set_value("selected_schedule", "")
            self.database.set_value("selected_online_pack", "")

    def load_packs(self):
        self.packs = self.database.get_all_online_schedule_packs()
        if self.packs != {}:
            self.pack_options = {id: pack_obj["pack_name"] for id, pack_obj in self.packs.items()}
                
            if self.pack_options != {}:
                selected_pack_id = ""
                if self.database.fetch_value("selected_online_pack") not in self.pack_options.values():
                    self.database.set_value("selected_online_pack", "")
                    self.calendar = None
                if self.database.fetch_value("selected_online_pack") != "":
                    selected_pack_id = [id for id, name in self.pack_options.items() if name == self.database.fetch_value("selected_online_pack")][0]

                    calendar = self.database.get_calendar(selected_pack_id)
                    if calendar != {}:
                        self.calendar = calendar
                    else:
                        self.calendar = None
                return self.pack_options, selected_pack_id
            else:
                self.database.set_value("selected_online_pack", "")
                return {}, ""

    def load_schedules(self):
        self.schedule_options = self.database.get_all_online_schedules()
        if self.schedule_options != {}:
            selected_pack_id = ""
            selected_schedule_id = ""
            set_schedule_based_on_calendar = self.database.fetch_value("set_schedule_based_on_calendar")

            if self.database.fetch_value("selected_schedule") not in self.schedule_options.values():
                self.database.set_value("selected_schedule", "")
            if self.database.fetch_value("selected_schedule") != "":
                selected_schedule = self.database.fetch_value("selected_schedule")
                selected_pack_id = self.database.get_online_pack_id(self.database.fetch_value("selected_online_pack"))
                selected_schedule_id = [id for id, name in self.schedule_options.items() if name == selected_schedule][0]
                self.current_schedule = self.database.get_schedule_from_os_pack(selected_pack_id, selected_schedule_id)

            return self.schedule_options, selected_schedule_id, set_schedule_based_on_calendar
        else:
            self.database.set_value("selected_schedule", "")
            return {}, "", False

    def get_title(self, config, timeframe, period, seconds):
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

    def get_daily_schedule(self, database: Database, calendar, schedule_options, now):
        if f"{now.month}/{now.day}/{now.year}" in calendar["exceptions"]:
            if calendar["exceptions"][f"{now.month}/{now.day}/{now.year}"] in schedule_options.values():
                schedule_name = calendar["exceptions"][f"{now.month}/{now.day}/{now.year}"]
                schedule_id = database.get_online_schedule_id(calendar["pack_id"], schedule_name)
        elif calendar["default"] in schedule_options.values():
            schedule_name = calendar["default"]
            schedule_id = database.get_online_schedule_id(calendar["pack_id"], schedule_name)

        return schedule_id, schedule_name

    def select_schedule(self, title):
        old_schedule_id = ""
        if self.database.fetch_value("selected_schedule") != "":
            pack_id = self.database.get_online_pack_id(self.database.fetch_value("selected_online_pack"))
            old_schedule_id = self.database.get_online_schedule_id(pack_id, self.database.fetch_value("selected_schedule"))
        pack_id = self.database.get_online_pack_id(self.database.fetch_value("selected_online_pack"))
        schedule_id = self.database.get_online_schedule_id(pack_id, title)
        self.current_schedule = self.database.get_schedule_from_os_pack(pack_id, schedule_id)
        self.database.set_value("selected_schedule", title)
        
        return old_schedule_id

    def select_pack(self, title):
        pack_id = ""
        selected_online_pack = self.database.fetch_value("selected_online_pack")
        if selected_online_pack == title:
            pack_id = self.database.get_online_pack_id(selected_online_pack)
            self.database.set_value("selected_schedule", "")
            self.database.set_value("selected_online_pack", "")
        elif selected_online_pack != "":
            pack_id = self.database.get_online_pack_id(selected_online_pack)
            self.database.set_value("selected_online_pack", title)
        else:
            self.database.set_value("selected_online_pack", title)

        return pack_id

    def toggle_settings(self, title):
        cfg_lookup = {
            "Check for App Updates on Startup": "check_app_updates_on_startup",
            "Check for Schedule Updates on Startup": "check_schedule_updates_on_startup",
            "Shorten Title": "use_shorthand",
            "Hide Seconds Unit (>1 min)": "hide_seconds",
            "Show Notifications Before Period Ends": "show_almost_end_notifs",
            "Set Schedule Based on Calendar": "set_schedule_based_on_calendar"
        }
        if title in cfg_lookup:
            config_key = cfg_lookup[title]
            new_key_value = not self.database.fetch_value(config_key)
            self.database.set_value(config_key, new_key_value)
        
        return new_key_value

    def update_time_left_calendar(self):
        now = datetime.now()
        tomorrow = datetime.today() + timedelta(days=1)
        day_is_off = False
        day_is_over = False
        proposed_title = ""
        schedule_id = ""

        use_calendar = self.database.fetch_value("set_schedule_based_on_calendar") and self.calendar != None
        if use_calendar:
            temp_schedule_id = self.get_daily_schedule(self.database, self.calendar, self.schedule_options, now)[0]
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
                self.database.set_value("selected_schedule", "")
                self.current_schedule = {}
            else:
                schedule_id, schedule_name = self.get_daily_schedule(self.database, self.calendar, self.schedule_options, now)
                if schedule_id != self.current_schedule.get("schedule_id", ""):
                    self.database.set_value("selected_schedule", schedule_name)
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
                proposed_title = self.get_title(self.database, "start", list(self.current_schedule["schedule"].keys())[0], time_until_start)

        if self.database.fetch_value("selected_schedule") == "":
            proposed_title = "No Schedule" if not day_is_off else "Day Off"

        return use_calendar, schedule_id, proposed_title, day_is_off

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
                proposed_title = self.get_title(self.database, "start", period_id, time_until_start)
                break
            elif time_until_end > 0:
                found_period = True
                proposed_title = self.get_title(self.database, "end", period_id, time_until_end)
                if self.database.fetch_value("show_almost_end_notifs") and time_until_end <= 300 and self.last_notified_period != period_id:
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
            proposed_title = self.get_title(self.database, "start", list(self.current_schedule["schedule"].keys())[0], time_until_start)

        return proposed_title, notification_title, notification_message

    def view_schedule(self):
        if self.database.fetch_value("selected_schedule") != "":
            message = ""
            for period in self.current_schedule["schedule"].values():
                message += f"{period["name"]}: {period["start"]} - {period["end"]}\n"
            title = self.current_schedule["name"]
        else:
            title = "No Schedule Selected",
            message = "No schedule is currently selected.\nSelect a schedule to view its timetable!"

        return title, message

    def about(self):
        title = "About"
        message = f"Menu Bar Schedule shows how much time is left until your next class/event!\n\nVersion {VERSION}\nCreated by Aaron (GitHub: https://github.com/{GITHUB_USERNAME})"

        return title, message

    def check_updates_on_startup(self):
        if self.database.fetch_value("check_app_updates_on_startup"):
            if self.update_app(False) == "restart":
                return "quit"
        if self.database.fetch_value("check_schedule_updates_on_startup"):
            self.update_schedules(False)

    def update_app(self, show_alerts):
        if system() == "Darwin":
            return self.updater.update_app_macos(show_alerts)

    def update_schedules(self, show_alerts):
        if system() == "Darwin":
            return self.updater.update_schedules_macos(show_alerts)
