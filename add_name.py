import json

name = input("Enter a json to edit: ")
schedule_json = json.loads(open(f"./schedules/{name}.json").read())

for id, period in schedule_json["schedule"].items():
    if "name" not in period:
        if id.isdigit():
            schedule_json["schedule"][id]["name"] = f"Period {id}"
        else:
            schedule_json["schedule"][id]["name"] = input(f"Enter a name for '{id}': ")

open(f"./schedules/{name}.json", "w").write(json.dumps(schedule_json, indent=2))