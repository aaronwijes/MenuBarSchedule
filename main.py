import os
import json
import time
import rumps
import threading
from datetime import datetime
from pathlib import Path

VERSION = "0.1.0"

schedules = {}
json_path = Path(__file__).parent / "schedules"
for schedule_json in json_path.glob("*.json"):
    schedules[schedule_json.name.split(".")[0]] = json.loads((schedule_json.read_text()))

class ScheduleApp(rumps.App):
    def __init__(self):
        super().__init__(
            name="Schedule App",
            title="",
            quit_button=None
        )

        self.menu = [
            "Change Schedule",
            "About",
            rumps.separator,
            "Quit"
        ]

        self.us_thread = threading.Thread(target=self.update_schedule_loop, daemon=True)
        self.us_thread.start()

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
                    self.title = f"START ({period_id}): {start_delta // 60}m {start_delta % 60}s"
                    found_period = True
                    break
                elif end_delta > 0:
                    found_period = True
                    self.title = f"END ({period_id}): {end_delta // 60}m {end_delta % 60}s"
                    break
            if not found_period:
                self.title = "School's out!"
            time.sleep(0.5)

    @rumps.clicked("About")
    def about(self, _):
        rumps.alert(f"Schedule App v{VERSION}\n\nAn easy way to see how much time is left until your next class!\n\nCreated by Aaron (GH: aaronwijes)")

    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    ScheduleApp().run()