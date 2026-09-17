import os
import json
import time
import rumps
from datetime import datetime, timedelta
from pathlib import Path

VERSION = "0.4.0"

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

class ScheduleApp(rumps.App):
    def __init__(self):
        super().__init__(
            name="Schedule App",
            title="",
            quit_button=None
        )

        self.sub_items = {}
        self.schedules = {}
        self.selected_schedule = "default"

        self.change_schedule = rumps.MenuItem(title="Change Schedule")
        self.change_schedule.add(rumps.MenuItem("Loading..."))

        self.menu = [
            self.change_schedule,
            "Update Schedules",
            "About",
            rumps.separator,
            "Quit"
        ]

        self.update_schedules(self.change_schedule)

        self.timer = rumps.Timer(self.update_time_left, 0.5)
        self.timer.start()

    def select_option(self, sender):
        self.sub_items[self.selected_schedule].state = False
        self.selected_schedule = sender.title
        sender.state = True

    def update_time_left(self, _):
        now = datetime.now()
        day = now.day
        month = now.month
        year = now.year
        found_period = False
        for period_id, period in self.schedules[self.selected_schedule].items():
            if datetime.now().hour > datetime.strptime(period["start"], "%I:%M %p").hour:
                tomorrow = datetime.today() + timedelta(days=1)
                day = tomorrow.day
                month = tomorrow.month
                year = tomorrow.year

            time_until_start = round((datetime.strptime(f"{month}/{day}/{year} {period["start"]}", "%m/%d/%Y %I:%M %p") - now).total_seconds())
            time_until_end = round((datetime.strptime(f"{month}/{day}/{year} {period["end"]}", "%m/%d/%Y %I:%M %p") - now).total_seconds())
            if time_until_start > 0:
                self.title = get_title("start", period_id, time_until_start)
                found_period = True
                break
            elif time_until_end > 0:
                found_period = True
                self.title = get_title("end", period_id, time_until_end)
                break
        if not found_period:
            tomorrow = datetime.today() + timedelta(days=1)
            day = tomorrow.day
            month = tomorrow.month
            year = tomorrow.year
            time_until_start = round((datetime.strptime(f"{month}/{day}/{year} {self.schedules[self.selected_schedule][list(self.schedules[self.selected_schedule].keys())[0]]["start"]}", "%m/%d/%Y %I:%M %p") - now).total_seconds())
            self.title = get_title("start", list(self.schedules[self.selected_schedule].keys())[0], time_until_start)
        time.sleep(0.5)

    @rumps.clicked("Update Schedules")
    def update_schedules(self, _):
        self.schedules = {}
        json_path = Path(__file__).parent / "schedules"
        for schedule_json in json_path.glob("*.json"):
            self.schedules[schedule_json.name.split(".")[0]] = json.loads((schedule_json.read_text()))

        self.options = sorted(list(self.schedules.keys()))
        self.sub_items = {
            opt: rumps.MenuItem(title=opt, callback=self.select_option)
            for opt in self.options
        }
        self.selected_schedule = "default"
        self.sub_items[self.selected_schedule].state = True
        
        self.change_schedule.clear()
        for item in self.sub_items.values():
            self.change_schedule.add(item)

    @rumps.clicked("About")
    def about(self, _):
        rumps.alert(
            title=f"Menu Bar Schedule",
            message=f"An easy way to see how much time is left until your next class!\n\nVersion {VERSION}\nCreated by Aaron (GitHub: https://github.com/aaronwijes)"
        )

    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    ScheduleApp().run()