import json

schedule_data = """
1	8:00 AM	38	8:38 AM	4
2	8:42 AM	30	9:12 AM	4
3	9:16 AM	33	9:49 AM	4
4	9:53 AM	30	10:23 AM	4
5	10:27 AM	30	10:57 AM	4
6	11:01 AM	30	11:31 AM	4
7	11:35 AM	30	12:05 PM	4
8	12:09 PM	30	12:39 PM	4
9	12:43 PM	30	1:13 PM	9
FAIR	1:22 PM	85	2:47 PM
"""

name_map = {
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
    "HR": "Homeroom"
}
schedule = {"name": "", "schedule": {}}
rows = schedule_data.strip().split("\n")

for row in rows:
    temp = row.split("\t")
    if temp[0] not in name_map:
        temp[0] = input(f"Enter period ID for '{temp[0]}': ")
    schedule["schedule"][temp[0]] = {
      "start": temp[1],
      "end": temp[3],
      "name": input(f"Enter period name for '{temp[0]}': ") if temp[0] not in name_map else name_map[temp[0]]
    }

schedule["name"] = input("Enter schedule name: ")
schedule_id = input("Enter schedule ID: ")
open(f"./schedules/{schedule_id}.json", "w").write(json.dumps(schedule, indent=2))