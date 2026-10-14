import json
import rumps
from datetime import datetime, timedelta
from pathlib import Path
from modules.database import Database
from modules.updater import Updater
from modules.info import VERSION, GITHUB_USERNAME

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

class MenuBarSchedule(rumps.App):
    def __init__(self, database: Database, updater: Updater):
        super().__init__(
            name="Menu Bar Schedule",
            title=""
        )
        self.database = database
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
                item.state = self.database.fetch_value(id)
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

        if self.database.fetch_value("check_app_updates_on_startup"):
            if self.updater.update_app(False) == "restart":
                rumps.quit_application()
        elif self.database.fetch_value("check_schedule_updates_on_startup"):
            self.updater.update_schedules(False)

    def select_option_schedule(self, sender):
        if self.database.fetch_value("selected_schedule") != "":
            pack_id = self.database.get_online_pack_id(self.database.fetch_value("selected_online_pack"))
            schedule_id = self.database.get_online_schedule_id(pack_id, self.database.fetch_value("selected_schedule"))
            self.schedule_items[schedule_id].state = False
        pack_id = self.database.get_online_pack_id(self.database.fetch_value("selected_online_pack"))
        schedule_id = self.database.get_online_schedule_id(pack_id, sender.title)
        self.current_schedule = self.database.get_schedule_from_os_pack(pack_id, schedule_id)
        self.database.set_value("selected_schedule", sender.title)
        sender.state = True

    def select_option_pack(self, sender):
        selected_online_pack = self.database.fetch_value("selected_online_pack")
        if selected_online_pack == sender.title:
            pack_id = self.database.get_online_pack_id(selected_online_pack)
            self.pack_items[pack_id].state = False
            self.database.set_value("selected_schedule", "")
            self.database.set_value("selected_online_pack", "")
        elif selected_online_pack != "":
            pack_id = self.database.get_online_pack_id(selected_online_pack)
            self.pack_items[pack_id].state = False
            self.database.set_value("selected_online_pack", sender.title)
        else:
            self.database.set_value("selected_online_pack", sender.title)
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
            new_key_value = not self.database.fetch_value(config_key)
            self.database.set_value(config_key, new_key_value)
            sender.state = new_key_value

        if sender.title == "Set Schedule Based on Calendar":
            self.refresh_schedules(None)

    def update_time_left(self, sender):
        now = datetime.now()
        found_period = False

        if self.database.fetch_value("set_schedule_based_on_calendar"):
            if self.calendar != None:
                if f"{now.month}/{now.day}/{now.year}" in self.calendar["exceptions"]:
                    if self.calendar["exceptions"][f"{now.month}/{now.day}/{now.year}"] in self.schedules:
                        self.database.set_value("selected_schedule", self.calendar["exceptions"][f"{now.month}/{now.day}/{now.year}"])
                elif self.calendar["default"] in self.schedule_items.values():
                    self.database.set_value("selected_schedule", self.calendar["default"])

                self.schedule_options = sorted([schedule["name"] for schedule in self.schedules.values()])
                if self.schedule_options != []:
                    self.sub_items = {
                        opt: rumps.MenuItem(title=opt, callback=None)
                        for opt in self.schedule_options
                    }

                    if self.database.fetch_value("selected_schedule") not in self.schedule_options:
                        self.database.set_value("selected_schedule", "")
                    if self.database.fetch_value("selected_schedule") != "":
                        self.sub_items[self.database.fetch_value("selected_schedule")].state = True

                    self.change_schedule.clear()
                    for item in self.sub_items.values():
                        self.change_schedule.add(item)

        if self.database.fetch_value("selected_schedule") == "":
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
                proposed_title = get_title(self.database, "start", period_id, time_until_start)
                break
            elif time_until_end > 0:
                found_period = True
                proposed_title = get_title(self.database, "end", period_id, time_until_end)
                if self.database.fetch_value("show_almost_end_notifs") and time_until_end <= 300 and self.last_notified_period != period_id:
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
            proposed_title = get_title(self.database, "start", list(self.current_schedule["schedule"].keys())[0], time_until_start)

        if self.title != proposed_title:
            self.title = proposed_title

    def refresh_schedules(self, sender):
        self.schedules = {}

        schedule_path = Path(self.database.database_dir) / "schedules"
        if not schedule_path.exists():
            self.change_schedule.clear()
            self.change_schedule.add(rumps.MenuItem(title="No Schedules Found"))

            self.change_schedule_pack.clear()
            self.change_schedule_pack.add(rumps.MenuItem(title="No Packs Found"))

            if not self.updater.install_schedules():
                self.database.set_value("selected_schedule", "")
                self.database.set_value("selected_online_pack", "")

        if schedule_path.exists():
            self.database.convert_schedule_jsons_to_sql()

            metadata = Path(self.database.database_dir) / "schedules" / "metadata.json"
            metadata_json = json.loads(metadata.read_text())
            for pack in metadata_json["packs"]:
                calendar_path = Path(self.database.database_dir) / "schedules" / pack["id"] / "calendar.json"
                if calendar_path.exists():
                    self.calendar = json.loads((calendar_path.read_text()))
                else:
                    self.calendar = None

            self.packs = self.database.get_all_online_schedule_packs()
            self.pack_options = {id: name for id, name in self.packs.items()}
            if self.pack_options != {}:
                self.pack_items = {
                    id: rumps.MenuItem(title=name, callback=self.select_option_pack)
                    for id, name in self.pack_options.items()
                }

                if self.database.fetch_value("selected_online_pack") not in self.pack_options.values():
                    self.database.set_value("selected_online_pack", "")
                if self.database.fetch_value("selected_online_pack") != "":
                    pack_id = [id for id, name in self.pack_options.items() if name == self.database.fetch_value("selected_online_pack")][0]
                    self.pack_items[pack_id].state = True
                
                self.change_schedule_pack.clear()
                for item in self.pack_items.values():
                    self.change_schedule_pack.add(item)
            else:
                self.change_schedule_pack.clear()
                self.change_schedule_pack.add(rumps.MenuItem(title="No Packs Found"))

            self.schedule_options = self.database.get_all_online_schedules()
            if self.schedule_options != {}:
                self.schedule_items = {
                    id: rumps.MenuItem(title=name, callback=self.select_option_schedule if not self.database.fetch_value("set_schedule_based_on_calendar") else None)
                    for id, name in self.schedule_options.items()
                }

                if self.database.fetch_value("selected_schedule") not in self.schedule_options.values():
                    self.database.set_value("selected_schedule", "")
                if self.database.fetch_value("selected_schedule") != "":
                    pack_id = self.database.get_online_pack_id(self.database.fetch_value("selected_online_pack"))
                    schedule_id = [id for id, name in self.schedule_options.items() if name == self.database.fetch_value("selected_schedule")][0]
                    self.schedule_items[schedule_id].state = True
                    self.current_schedule = self.database.get_schedule_from_os_pack(pack_id, schedule_id)

                self.change_schedule.clear()
                for item in self.schedule_items.values():
                    self.change_schedule.add(item)
            else:
                self.change_schedule.clear()
                self.change_schedule.add(rumps.MenuItem(title="No Schedules Found"))
                self.database.set_value("selected_schedule", "")

    @rumps.clicked("View Current Schedule")
    def view_schedule(self, sender):
        if self.database.fetch_value("selected_schedule") != "":
            message = ""
            for period in self.current_schedule["schedule"].values():
                message += f"{period["name"]}: {period["start"]} - {period["end"]}\n"
            rumps.alert(
                title=self.current_schedule["name"],
                message=message
            )
        else:
            rumps.alert(
                title="No Schedule Selected",
                message="No schedule is currently selected.\nSelect a schedule to view its timetable!"
            )

    @rumps.clicked("Check for App Updates")
    def check_updates(self, sender):
        if self.updater.update_app(True) == "restart":
            rumps.quit_application()

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
    database = Database()
    updater = Updater(database)
    MenuBarSchedule(database, updater).run()
    database.conn.close()
