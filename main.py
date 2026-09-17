import os
import time
import rumps
import threading
from datetime import datetime

schedules = {
    "regular": {
        "1": {
            "start": "8:00AM",
            "end": "8:41AM"
        },
        "2": {
            "start": "8:45AM",
            "end": "9:26AM"
        },
        "3": {
            "start": "9:30AM",
            "end": "10:17AM" # 47 mins instead of 41 mins
        },
        "4": {
            "start": "10:21AM",
            "end": "11:02AM"
        },
        "5": {
            "start": "11:06AM",
            "end": "11:47AM"
        },
        "6": {
            "start": "11:51AM",
            "end": "12:32PM"
        },
        "7": {
            "start": "12:36PM",
            "end": "1:17PM"
        },
        "8": {
            "start": "1:21PM",
            "end": "2:02PM"
        },
        "9": {
            "start": "2:06PM",
            "end": "2:47PM"
        }
    },
    "3-assembly": {
        "1": {
            "start": "8:00AM",
            "end": "8:38AM"
        },
        "2": {
            "start": "8:42AM",
            "end": "9:20AM"
        },
        "3": {
            "start": "9:24AM",
            "end": "10:32AM" # 47 mins instead of 41 mins
        },
        "4": {
            "start": "10:36AM",
            "end": "11:14AM"
        },
        "5": {
            "start": "11:18AM",
            "end": "11:56AM"
        },
        "6": {
            "start": "12:00AM",
            "end": "12:38PM"
        },
        "7": {
            "start": "12:42PM",
            "end": "1:20PM"
        },
        "8": {
            "start": "1:24PM",
            "end": "2:02PM"
        },
        "9": {
            "start": "2:06PM",
            "end": "2:47PM"
        }
    }
}

class ScheduleApp(rumps.App):
    def __init__(self):
        super().__init__(
            name="Schedule App",
            title="⏰",
            quit_button=None
        )

        self.menu = [
            "Start Updating Schedule",
            "Stop Updating Schedule",
            "Change Schedule",
            "About",
            rumps.separator,
            "Quit"
        ]

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

    @rumps.clicked("Start Updating Schedule")
    def start_updating(self, _):
        self.us_thread = threading.Thread(target=self.update_schedule_loop, daemon=True)
        self.us_thread.start()

    @rumps.clicked("About")
    def about(self, _):
        rumps.alert("Schedule App v0.0.0\n\nAn easy way to see how much time is left until your next class!\n\nCreated by Aaron (GH: aaronwijes)")

    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    ScheduleApp().run()