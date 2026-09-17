import json

schedule_json = {}
schedule_text = """
Period 1	8:00 AM	8:34 AM	34 min
""" # format as above (you don't need the minute count)

periods = schedule_text.replace("\n", "|").strip().split("|")
for period in periods:
    if period == "":
        continue
    pd_dict = period.split("\t")
    schedule_json[pd_dict[0].replace("Period ", "")] = {
        "start": pd_dict[1],
        "end": pd_dict[2]
    }

name = input("Enter schedule name: ")
open(f"./schedules/{name}.json", "w").write(json.dumps(schedule_json, indent=2))