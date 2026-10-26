# This script is mainly for internal use.
# It may or may not be adapted for public use in future commits.

import os
import json
import time
import webbrowser
from datetime import datetime

class SITHSCalendarParser():
    def __init__(self):
        self.pack_id = "siths"
        self.source_url = "https://docs.google.com/document/d/1tWuGMQiozVi_5sD5Gh2AuUA33sc5ioHV3_2t4ekDnZc/export?gid=0&format=md"

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
        print(f"Downloading calendar as markdown: {self.source_url}")
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
        print(f"Added {len(list(self.calendar_obj["exceptions"].keys()))} exception dates to {self.pack_id}'s calendar.json")
        print("Success")

class SITHSScheduleParser():
    def __init__(self):
        self.pack_id = "siths"
        self.source_url = "https://docs.google.com/spreadsheets/d/1DoLxQ897fl0cQ3PCllsXuJh7sfg2R-sCYnSdO5hR_Ak/export?gid=0&format=csv"
        self.source_url_2 = "https://docs.google.com/spreadsheets/u/2/d/1DoLxQ897fl0cQ3PCllsXuJh7sfg2R-sCYnSdO5hR_Ak/export?gid=254459468&format=csv"

        self.calendar = ""
        self.calendar_events = []
        self.execption_dates = {}

        self.schedule_map = {
            "DRILL 1F": "Evac/Lockdown Drill (1F)",
            "DRILL 2F": "Evac/Lockdown Drill (2F)",
            "DRILL 3F": "Evac/Lockdown Drill (3F)",
            "DRILL 4F": "Evac/Lockdown Drill (4F)",
            "DRILL 5F": "Evac/Lockdown Drill (5F)",
            "DRILL 6F": "Evac/Lockdown Drill (6F)",
            "DRILL 7F": "Evac/Lockdown Drill (7F)",
            "DRILL 8F": "Evac/Lockdown Drill (8F)",
            "DRILL 9F": "Evac/Lockdown Drill (9F)",
            "10 MINUTE HOMEROOM SCHEDULE": "10 Minute Homeroom",
            "FACULTY CONFERENCE": "Faculty Conference",
            "PARENT TEACHER CONFERENCE SCHEDULE": "Parent Teacher Conference",
            "3A/3B Schedule": "Assembly (3A/3B)",
            "THIRD PERIOD ASSEMBLY SCHEDULE": "Assembly (Period 3)",
            "FIRST DAY OF SCHOOL": "First Day of School",
            "FRESHMEN SOCIAL SCHEDULE": "Freshman Social",
            "CLUB FAIR SCHEDULE 2027": "Club Fair",
            "FIELD DAY SCHEDULE": "Field Day",
            "SCHOOL SURVEY SCHEDULE": "School Survey",
            "STANDARD SCHEDULE": "Regular Bell Schedule"
        }

        self.schedule_id_map = {
            "DRILL 1F": "drill-1f",
            "DRILL 2F": "drill-2f",
            "DRILL 3F": "drill-3f",
            "DRILL 4F": "drill-4f",
            "DRILL 5F": "drill-5f",
            "DRILL 6F": "drill-6f",
            "DRILL 7F": "drill-7f",
            "DRILL 8F": "drill-8f",
            "DRILL 9F": "drill-9f",
            "10 MINUTE HOMEROOM SCHEDULE": "10m-homeroom",
            "FACULTY CONFERENCE": "fac-conf",
            "PARENT TEACHER CONFERENCE SCHEDULE": "ptc",
            "3A/3B Schedule": "assembly-3a-3b",
            "THIRD PERIOD ASSEMBLY SCHEDULE": "assembly-3",
            "FIRST DAY OF SCHOOL": "first-day",
            "FRESHMEN SOCIAL SCHEDULE": "fresh-social",
            "CLUB FAIR SCHEDULE 2027": "club-fair",
            "FIELD DAY SCHEDULE": "field-day",
            "SCHOOL SURVEY SCHEDULE": "school-survey",
            "STANDARD SCHEDULE": "default"
        }

        self.id_map = {
            "1": "1",
            "2": "2",
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7",
            "8": "8",
            "9": "9",
            "1F": "1F",
            "2F": "2F",
            "3F": "3F",
            "4F": "4F",
            "5F": "5F",
            "6F": "6F",
            "7F": "7F",
            "8F": "8F",
            "9F": "9F",
            "HR": "HR",
            "Event": "FD",
            "FAIR": "CF",
            "Fac Conf": "FC",
            "Lunch": "LUN",
            "Teacher Org Time": "TO",
            "Fresh Social": "FS",
            "3A": "3A",
            "3B": "3B"
        }

        self.name_map = {
            "1": "Period 1",
            "2": "Period 2",
            "3": "Period 3",
            "4": "Period 4",
            "5": "Period 5",
            "6": "Period 6",
            "7": "Period 7",
            "8": "Period 8",
            "9": "Period 9",
            "1F": "Period 1F",
            "2F": "Period 2F",
            "3F": "Period 3F",
            "4F": "Period 4F",
            "5F": "Period 5F",
            "6F": "Period 6F",
            "7F": "Period 7F",
            "8F": "Period 8F",
            "9F": "Period 9F",
            "HR": "Homeroom",
            "FD": "Field Day",
            "CF": "Club Fair",
            "FC": "Faculty Conference",
            "LUN": "Lunch",
            "TO": "Teacher Org Time",
            "FS": "Freshmen Social",
            "3A": "Assembly 3A",
            "3B": "Assembly 3B"
        }

    def prompt_download(self):
        print(f"Pack ID: {self.pack_id}")
        
        webbrowser.open(self.source_url)
        print(f"[1/2] Downloading schedule spreadsheets as CSV: {self.source_url}")
        while not os.path.exists(os.path.expanduser("~/Downloads/Bell Schedules - Various.csv")):
            time.sleep(0.2)

        webbrowser.open(self.source_url_2)
        print(f"[2/2] Downloading schedule spreadsheets as CSV: {self.source_url_2}")
        while not os.path.exists(os.path.expanduser("~/Downloads/Bell Schedules - Evac Drill.csv")):
            time.sleep(0.2)

    def remove_download(self):
        if os.path.exists(os.path.expanduser("~/Downloads/Bell Schedules - Various.csv")):
            os.remove(os.path.expanduser("~/Downloads/Bell Schedules - Various.csv"))

        if os.path.exists(os.path.expanduser("~/Downloads/Bell Schedules - Evac Drill.csv")):
            os.remove(os.path.expanduser("~/Downloads/Bell Schedules - Evac Drill.csv"))

    def get_period_name(self, period_name):
        period_id = self.id_map[period_name]
        correct_period_name = self.name_map[period_id]

        return period_id, correct_period_name

    def parse_schedules(self):
        self.schedules = open(os.path.expanduser("~/Downloads/Bell Schedules - Various.csv")).readlines()
        self.evac_schedules = open(os.path.expanduser("~/Downloads/Bell Schedules - Evac Drill.csv")).readlines()
        self.schedule_lines = [line.split(",") for line in self.schedules] + [line.split(",") for line in self.evac_schedules]

        schedules = {}
        for i in [0, 6]:
            for line in self.schedule_lines:
                if line[1 + i] == "Period":
                    continue
                elif line[1 + i] == "":
                    current_schedule = ""
                    continue
                elif current_schedule == "" and line[1 + i] != "":
                    current_schedule = line[1 + i]
                    if current_schedule not in schedules:
                        schedules[current_schedule] = {
                            "name": self.schedule_map[current_schedule],
                            "schedule": {}
                        }
                    continue

                try:
                    period_id, period_name = self.get_period_name(line[1 + i])
                except:
                    print(line)
                    print(line[1 + i])
                    exit()
                schedules[current_schedule]["schedule"][period_id] = {"start": line[2 + i], "end": line[4 + i], "name": period_name}

        for csv_schedule_name, schedule in schedules.items():
            open(f"./schedules/{self.pack_id}/json/{self.schedule_id_map[csv_schedule_name]}.json", "w").write(json.dumps(schedule, indent=2))

        print(f"Added {len(list(schedules.keys()))} schedules")
        print("Success")

cparser = SITHSCalendarParser()
cparser.prompt_download()
cparser.parse_schedules()
cparser.remove_download()

print("")
sparser = SITHSScheduleParser()
sparser.prompt_download()
sparser.parse_schedules()
sparser.remove_download()