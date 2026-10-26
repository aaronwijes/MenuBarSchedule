# This script is mainly for internal use.
# It may or may not be adapted for public use in future commits.

import os
import json
import time
import webbrowser
from datetime import datetime

class SITHSParser():
    def __init__(self):
        self.pack_id = "siths"
        self.source_url = "https://docs.google.com/document/d/1tWuGMQiozVi_5sD5Gh2AuUA33sc5ioHV3_2t4ekDnZc/edit?tab=t.0#heading=h.nvtvl7yw9tcx"

        self.calendar = ""
        self.calendar_events = []
        self.execption_dates = {}

        self.now = datetime.now()
        self.start_year = "2026"
        self.end_year = "2027"
        self.this_year_months = list(range(9, 12 + 1))
        self.next_year_months = list(range(1, 6 + 1))

        self.infer_map = {
            "1f": "Evac/Lockdown Drill (1F)",
            "2f": "Evac/Lockdown Drill (2F)",
            "3f": "Evac/Lockdown Drill (3F)",
            "4f": "Evac/Lockdown Drill (4F)",
            "5f": "Evac/Lockdown Drill (5F)",
            "6f": "Evac/Lockdown Drill (6F)",
            "7f": "Evac/Lockdown Drill (7F)",
            "8f": "Evac/Lockdown Drill (8F)",
            "9f": "Evac/Lockdown Drill (9F)",
            "ten": "10 Minute Homeroom",
            "faculty": "Faculty Conference",
            "pt": "Parent Teacher Conference",
            "parent": "Parent Teacher Conference",
            "3a/3b": "Assembly (3A/3B)",
            "third": "Assembly (Period 3)",
            "first": "First Day of School",
            "freshmen": "Freshman Social",
            "club": "Club Fair",
            "field": "Field Day",
            "survey": "School Survey"
        }

        self.calendar_obj = {
            "default": "Regular Bell Schedule",
            "exceptions": {},
            "off_days": [5, 6],
            "off_dates": []
        }

    def get_inferred_schedule(self, event_name):
        for guess, schedule in self.infer_map.items():
            if guess in event_name:
                return schedule

    def prompt_download(self):
        webbrowser.open(self.source_url)
        print(f"Pack ID: {self.pack_id}")
        print(f"Download calendar as markdown: {self.source_url}")
        print("Waiting for download...")
        while not os.path.exists(os.path.expanduser("~/Downloads/2026-27 Google Calendar (*This is a Fluid Document).md")):
            time.sleep(0.2)
        self.calendar = open(os.path.expanduser("~/Downloads/2026-27 Google Calendar (*This is a Fluid Document).md")).readlines()
        self.calendar_events = [event[2:-3].split(" | ") for event in self.calendar if "|" in event and event.isascii()]

    def remove_download(self):
        if os.path.exists(os.path.expanduser("~/Downloads/2026-27 Google Calendar (*This is a Fluid Document).md")):
            os.remove(os.path.expanduser("~/Downloads/2026-27 Google Calendar (*This is a Fluid Document).md"))

    def parse_schedules(self):
        for event in self.calendar_events:
            if event[0] in ["-----", ":---:"] or event[-1] in ["-----", ":---:"]:
                continue
            if (event[-1] in ["", "Bell Schedule"]) or not "https" in event[-1]:
                continue

            event[0] = event[0].strip().replace("*", "").split(",")[0]
            event_month = int(event[0].split("/")[0])
            if event_month in self.this_year_months:
                event[0] += f"/{self.start_year}"
            elif event_month in self.next_year_months:
                event[0] += f"/{self.end_year}"
        
        
            event[-1] = event[-1].split("]")[0].replace("[", "").replace("*", "").lower()
            schedule = self.get_inferred_schedule(event[-1])
            if schedule == None:
                raise Exception(f"InferError: Couldn't infer the schedule name for event \"{event[-1]}\"")
            
            self.calendar_obj["exceptions"][event[0]] = schedule

        open(f"./schedules/{self.pack_id}/calendar.json", "w").write(json.dumps(self.calendar_obj, indent=2))
        print("Success")

parser = SITHSParser()
parser.prompt_download()
parser.parse_schedules()
parser.remove_download()
