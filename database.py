import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from platformdirs import user_config_dir

VERSION = "3.1.0"
VERSION_LIST = [int(component) for component in VERSION.split(".")]

REPO_NAME = "MenuBarSchedule"
GITHUB_USERNAME = "aaronwijes"

class Config():
    def __init__(self):
        self.config_dir = Path(user_config_dir(REPO_NAME, GITHUB_USERNAME))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = f"{self.config_dir}/data.db"
        
        self.default_config = {
            "config_version": 1,
            "use_shorthand": 0,
            "hide_seconds": 0,
            "show_almost_end_notifs": 0,
            "check_app_updates_on_startup": 0,
            "check_schedule_updates_on_startup": 0,
            "set_schedule_based_on_calendar": 0,
            "selected_schedule": "",
            "selected_online_pack": ""
        }

        os.chdir(self.config_dir)
        self.conn = sqlite3.connect("data.db")
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS online_schedules (
                pack_id TEXT,
                schedule_id TEXT,
                schedule_name TEXT,
                period_id TEXT,
                period_name TEXT,
                start_time TEXT,
                end_time TEXT,
                PRIMARY KEY (pack_id, schedule_id, period_id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_packs (
                pack_id TEXT PRIMARY KEY,
                pack_name TEXT,
                pack_version INT
            );
        """)

        self.conn.commit()

        for key, value in self.default_config.items():
            if not self.key_exists(key):
                self.set_value(key, value)

    def fetch_value(self, key):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT value FROM config WHERE key = ?", [key])
        value = cursor.fetchall()[0]["value"]
        if key not in ["selected_schedule", "selected_online_pack"]:
            return int(value)
        else:
            return value

    def set_value(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO config (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value;
        """, [key, value])
        self.conn.commit()

    def key_exists(self, key):
        cursor = self.conn.cursor()
        return len(cursor.execute("SELECT * FROM config WHERE key = ?", [key]).fetchall()) > 0

    def query_enabled_pack(self, pack_name):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM config WHERE key = \"selected_online_pack\" AND value = ?;", [pack_name])
        return len(cursor.fetchall()) > 0

    def add_online_schedule(self, pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO online_schedules (pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING;
        """, [pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time])
        self.conn.commit()

    def add_online_schedule_pack(self, pack_id, pack_name, pack_version):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO schedule_packs (pack_id, pack_name, pack_version)
            VALUES (?, ?, ?)
            ON CONFLICT DO NOTHING;
        """, [pack_id, pack_name, pack_version])
        self.conn.commit()

    def remove_online_schedule_pack(self, pack_id):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            DELETE FROM online_schedules
            WHERE pack_id = ?
        """, [pack_id])
        self.conn.commit()

    def get_all_online_schedule_packs(self):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM schedule_packs;")
        rows = cursor.fetchall()

        packs = {}
        for row in rows:
            packs[row["pack_id"]] = row["pack_name"]

        return packs

    def get_online_pack_id(self, pack_name):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT pack_id FROM schedule_packs
            WHERE pack_name = ?;
        """, [pack_name])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return ""
        return rows[0]["pack_id"]

    def get_schedule_from_os_pack(self, pack_id, schedule_id):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT * FROM online_schedules
            WHERE pack_id = ?
            AND schedule_id = ?;
        """, [pack_id, schedule_id])

        periods = cursor.fetchall()
        schedule = {"name": periods[0]["schedule_name"], "schedule_id": periods[0]["schedule_id"], "pack_id": periods[0]["pack_id"], "schedule": {}}
        for period in periods:
            schedule["schedule"][period[3]] = {
                "start": period["start_time"],
                "end": period["end_time"],
                "parsed_start": datetime.strptime(period["start_time"], "%I:%M %p"),
                "parsed_end": datetime.strptime(period["end_time"], "%I:%M %p"),
                "name": period["period_name"]
            }

        return schedule

    def get_all_online_schedules(self):
        pack_id = self.get_online_pack_id(self.fetch_value("selected_online_pack"))
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT schedule_id, schedule_name
            FROM online_schedules
            WHERE pack_id = ?
            ORDER BY schedule_name COLLATE NOCASE;
        """, [pack_id])
        rows = cursor.fetchall()

        schedules = {}
        for row in rows:
            if row["schedule_id"] not in schedules:
                schedules[row["schedule_id"]] = row["schedule_name"]

        return schedules

    def convert_schedule_jsons_to_sql(self):
        schedule_path = Path(self.config_dir) / "schedules"
        if schedule_path.exists():
            metadata = Path(self.config_dir) / "schedules" / "metadata.json"
            metadata_json = json.loads(metadata.read_text())
            for pack in metadata_json["packs"]:
                self.add_online_schedule_pack(pack["id"], pack["name"], pack["version"])
                schedule_path = Path(self.config_dir) / "schedules" / pack["id"] / "json"
                for schedule_json in schedule_path.glob("*.json"):
                    schedule = json.loads((schedule_json.read_text()))
                    for period_id, period in schedule["schedule"].items():
                        period["parsed_start"] = datetime.strptime(period["start"], "%I:%M %p")
                        period["parsed_end"] = datetime.strptime(period["end"], "%I:%M %p")
                        self.add_online_schedule(pack["id"], Path(schedule_json).name.replace(".json", ""), schedule["name"], period_id, period["name"], period["start"], period["end"])
