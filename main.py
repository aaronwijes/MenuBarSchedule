import os
import json
import time
import rumps
import threading
from datetime import datetime, timedelta
from pathlib import Path

VERSION = "0.2.0"

schedules = {}
json_path = Path(__file__).parent / "schedules"
for schedule_json in json_path.glob("*.json"):
    schedules[schedule_json.name.split(".")[0]] = json.loads((schedule_json.read_text()))

def get_title(timeframe, period, seconds):
    title = f"{timeframe.upper()} ({period}): "
    hours = seconds // 3600
    minutes = (seconds // 60) % 60
    if hours > 0:
        title += f"{seconds // 3600}h "
    if minutes > 0 or hours > 0:
        title += f"{(seconds // 60) % 60}m "
    title += f"{seconds % 60}s"
    return title

class ScheduleApp(rumps.App):
    def __init__(self):
        super().__init__(
            name="Schedule App",
            title="",
            quit_button=None
        )

        self.options = list(schedules.keys())
        self.sub_items = {
            opt: rumps.MenuItem(title=opt, callback=self.select_option)
            for opt in self.options
        }
        self.selected_schedule = "default"
        self.sub_items[self.selected_schedule].state = True

        self.menu = [
            ("Change Schedule", list(self.sub_items.values())),
            "About",
            rumps.separator,
            "Quit"
        ]

        self.us_thread = threading.Thread(target=self.update_schedule_loop, daemon=True)
        self.us_thread.start()

    def select_option(self, sender):
        self.sub_items[self.selected_schedule].state = False
        self.selected_schedule = sender.title
        sender.state = True

    def update_schedule_loop(self):
        while True:
            now = datetime.now()
            day = now.day
            month = now.month
            year = now.year
            found_period = False
            for period_id, period in schedules["3-assembly"].items():
                start_delta = round((datetime.strptime(f"{month}/{day}/{year} {period["start"]}", "%m/%d/%Y %I:%M%p") - now).total_seconds())
                end_delta = round((datetime.strptime(f"{month}/{day}/{year} {period["end"]}", "%m/%d/%Y %I:%M%p") - now).total_seconds())
                if start_delta > 0:
                    self.title = get_title("start", period_id, start_delta)
                    found_period = True
                    break
                elif end_delta > 0:
                    found_period = True
                    self.title = get_title("end", period_id, end_delta)
                    break
            if not found_period:
                tomorrow = datetime.today() + timedelta(days=1)
                day = tomorrow.day
                month = tomorrow.month
                year = tomorrow.year
                start_delta = round((datetime.strptime(f"{month}/{day}/{year} {schedules["3-assembly"][list(schedules["3-assembly"].keys())[0]]["start"]}", "%m/%d/%Y %I:%M%p") - now).total_seconds())
                self.title = get_title("start", list(schedules[self.selected_schedule].keys())[0], start_delta)
            time.sleep(0.5)

    @rumps.clicked("About")
    def about(self, _):
        rumps.alert(f"Menu Bar Schedule v{VERSION}\n\nAn easy way to see how much time is left until your next class!\n\nCreated by Aaron (GH: aaronwijes)")

    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    ScheduleApp().run()