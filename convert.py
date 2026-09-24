import json

schedule_data = """

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