import os
import sqlite3
from datetime import datetime
from pathlib import Path
from platformdirs import user_config_dir
from .info import REPO_NAME, GITHUB_USERNAME
from supabase import create_client, Client

class Database():
    def __init__(self):
        self.database_dir = Path(user_config_dir(REPO_NAME, GITHUB_USERNAME))
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.database_path = f"{self.database_dir}/data.db"

        self.url: str = "https://fhswspxqmwffxpbwcyik.supabase.co"
        self.key: str = "sb_publishable_ttXyIjhBhl6fIAvcOddqWA_imqtCPXK"
        self.supabase: Client = create_client(self.url, self.key)
        
        self.default_config = {
            "config_version": 1,
            "use_shorthand": 0,
            "hide_seconds": 0,
            "show_almost_end_notifs": 0,
            "check_app_updates_on_startup": 0,
            "check_schedule_updates_on_startup": 0,
            "set_schedule_based_on_calendar": 0,
            "open_at_login": 0,
            "selected_schedule": "",
            "selected_schedule_id": "",
            "selected_online_pack": "",
            "selected_online_pack_id": ""
        }

        os.chdir(self.database_dir)
        self.conn = sqlite3.connect("data.db", check_same_thread=False)
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
                insertion_order INT,
                schedule_format_version INT DEFAULT 1,
                PRIMARY KEY (pack_id, schedule_id, period_id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS online_schedule_packs (
                pack_id TEXT PRIMARY KEY,
                pack_name TEXT,
                pack_version INT,
                schedule_format_version INT DEFAULT 1
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_schedules (
                pack_id TEXT,
                schedule_id TEXT,
                schedule_name TEXT,
                period_id TEXT,
                period_name TEXT,
                start_time TEXT,
                end_time TEXT,
                insertion_order INT,
                schedule_format_version INT DEFAULT 1,
                PRIMARY KEY (pack_id, schedule_id, period_id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_schedule_packs (
                pack_id TEXT PRIMARY KEY,
                pack_name TEXT,
                pack_version INT,
                schedule_format_version INT DEFAULT 1
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS online_calendars (
                calendar_id TEXT,
                calendar_name TEXT,
                pack_id TEXT,
                schedule_name TEXT,
                schedule_id TEXT,
                is_default INT,
                exception_date TEXT,
                calendar_format_version INT DEFAULT 1,
                PRIMARY KEY (calendar_id, pack_id, exception_date)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS online_calendars_off_days (
                calendar_id TEXT,
                calendar_name TEXT,
                pack_id TEXT,
                off_day INT,
                calendar_format_version INT DEFAULT 1,
                PRIMARY KEY (calendar_id, pack_id, off_day)
            );
        """)

        # Migration code from MBS <=3.4.7
        try:
            cursor.execute("""
                ALTER TABLE online_calendars
                ADD calendar_format_version INT DEFAULT 1;
            """)

            cursor.execute("""
                ALTER TABLE online_calendars_off_days
                ADD calendar_format_version INT DEFAULT 1;
            """)
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                pass

        self.conn.commit()

        for key, value in self.default_config.items():
            if not self.key_exists(key):
                self.set_value(key, value)

    def fetch_value(self, key):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT value FROM config WHERE key = ?", [key])
        value = cursor.fetchall()[0]["value"]
        try:
            return int(value)
        except ValueError:
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
        return len(cursor.execute("SELECT * FROM config WHERE key = ?;", [key]).fetchall()) > 0

    def query_enabled_pack(self, pack_name):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM config
            WHERE key = "selected_online_pack"
            AND value = ?;
        """, [pack_name])
        return len(cursor.fetchall()) > 0

    # def add_online_schedule(self, pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time, insertion_order):
    #     cursor = self.conn.cursor()
    #     cursor.execute(f"""
    #         INSERT INTO online_schedules (pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time, insertion_order)
    #         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    #         ON CONFLICT DO UPDATE SET
    #             pack_id = excluded.pack_id,
    #             schedule_id = excluded.schedule_id,
    #             schedule_name = excluded.schedule_name,
    #             period_id = excluded.period_id,
    #             period_name = excluded.period_name,
    #             start_time = excluded.start_time,
    #             end_time = excluded.end_time,
    #             insertion_order = excluded.insertion_order;
    #     """, [pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time, insertion_order])
    #     self.conn.commit()

    # def add_online_calendar(self, calendar_id, calendar_name, pack_id, schedule_name, schedule_id, is_default, exception_date):
    #     cursor = self.conn.cursor()
    #     cursor.execute(f"""
    #         INSERT INTO online_calendars (calendar_id, calendar_name, pack_id, schedule_name, schedule_id, is_default, exception_date)
    #         VALUES (?, ?, ?, ?, ?, ?, ?)
    #         ON CONFLICT DO UPDATE SET
    #             calendar_id = excluded.calendar_id,
    #             calendar_name = excluded.calendar_name,
    #             pack_id = excluded.pack_id,
    #             schedule_name = excluded.schedule_name,
    #             schedule_id = excluded.schedule_id,
    #             is_default = excluded.is_default,
    #             exception_date = excluded.exception_date;
    #     """, [calendar_id, calendar_name, pack_id, schedule_name, schedule_id, is_default, exception_date])
    #     self.conn.commit()

    # def add_online_calendar_off_date(self, calendar_id, calendar_name, pack_id, off_day):
    #     cursor = self.conn.cursor()
    #     cursor.execute(f"""
    #         INSERT INTO online_calendars_off_days (calendar_id, calendar_name, pack_id, off_day)
    #         VALUES (?, ?, ?, ?)
    #         ON CONFLICT DO UPDATE SET
    #             calendar_id = excluded.calendar_id,
    #             calendar_name = excluded.calendar_name,
    #             pack_id = excluded.pack_id,
    #             off_day = excluded.off_day;
    #     """, [calendar_id, calendar_name, pack_id, off_day])
    #     self.conn.commit()

    # def add_online_schedule_pack(self, pack_id, pack_name, pack_version):
    #     cursor = self.conn.cursor()
    #     cursor.execute(f"""
    #         INSERT INTO online_schedule_packs (pack_id, pack_name, pack_version)
    #         VALUES (?, ?, ?)
    #         ON CONFLICT DO UPDATE SET
    #             pack_id = excluded.pack_id,
    #             pack_name = excluded.pack_name,
    #             pack_version = excluded.pack_version;
    #     """, [pack_id, pack_name, pack_version])
    #     self.conn.commit()

    def add_online_schedule_em(self, rows):
        cursor = self.conn.cursor()
        cursor.executemany(f"""
            INSERT INTO online_schedules (pack_id, schedule_id, schedule_name, period_id, period_name, start_time, end_time, insertion_order)
            VALUES (:pack_id, :schedule_id, :schedule_name, :period_id, :period_name, :start_time, :end_time, :insertion_order)
            ON CONFLICT DO UPDATE SET
                pack_id = excluded.pack_id,
                schedule_id = excluded.schedule_id,
                schedule_name = excluded.schedule_name,
                period_id = excluded.period_id,
                period_name = excluded.period_name,
                start_time = excluded.start_time,
                end_time = excluded.end_time,
                insertion_order = excluded.insertion_order;
        """, rows)
        self.conn.commit()

    def add_online_calendar_em(self, rows):
        cursor = self.conn.cursor()
        cursor.executemany(f"""
            INSERT INTO online_calendars (calendar_id, calendar_name, pack_id, schedule_name, schedule_id, is_default, exception_date)
            VALUES (:calendar_id, :calendar_name, :pack_id, :schedule_name, :schedule_id, :is_default, :exception_date)
            ON CONFLICT DO UPDATE SET
                calendar_id = excluded.calendar_id,
                calendar_name = excluded.calendar_name,
                pack_id = excluded.pack_id,
                schedule_name = excluded.schedule_name,
                schedule_id = excluded.schedule_id,
                is_default = excluded.is_default,
                exception_date = excluded.exception_date;
        """, rows)
        self.conn.commit()

    def add_online_calendar_off_date_em(self, rows):
        cursor = self.conn.cursor()
        cursor.executemany(f"""
            INSERT INTO online_calendars_off_days (calendar_id, calendar_name, pack_id, off_day)
            VALUES (:calendar_id, :calendar_name, :pack_id, :off_day)
            ON CONFLICT DO UPDATE SET
                calendar_id = excluded.calendar_id,
                calendar_name = excluded.calendar_name,
                pack_id = excluded.pack_id,
                off_day = excluded.off_day;
        """, rows)
        self.conn.commit()

    def add_online_schedule_pack_em(self, rows):
        cursor = self.conn.cursor()
        cursor.executemany(f"""
            INSERT INTO online_schedule_packs (pack_id, pack_name, pack_version)
            VALUES (:pack_id, :pack_name, :pack_version)
            ON CONFLICT DO UPDATE SET
                pack_id = excluded.pack_id,
                pack_name = excluded.pack_name,
                pack_version = excluded.pack_version;
        """, rows)
        self.conn.commit()

    def remove_online_schedule_pack(self, pack_id):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            DELETE FROM online_schedules
            WHERE pack_id = ?;
        """, [pack_id])
        cursor.execute(f"""
            DELETE FROM online_schedule_packs
            WHERE pack_id = ?;
        """, [pack_id])
        self.conn.commit()

    def get_online_pack_id(self, pack_name):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT pack_id FROM online_schedule_packs
            WHERE pack_name = ?;
        """, [pack_name])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return ""
        return rows[0]["pack_id"]

    def get_online_schedule_id(self, pack_id, schedule_name):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT schedule_id FROM online_schedules
            WHERE pack_id = ?
            AND schedule_name = ?;
        """, [pack_id, schedule_name])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return ""
        return rows[0]["schedule_id"]

    def get_schedule_from_os_pack(self, pack_id, schedule_id):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT * FROM online_schedules
            WHERE pack_id = ?
            AND schedule_id = ?
            ORDER BY insertion_order ASC;
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

    def get_all_online_schedule_packs(self):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM online_schedule_packs;")
        rows = cursor.fetchall()

        packs = {}
        for row in rows:
            packs[row["pack_id"]] = {
                "pack_name": row["pack_name"],
                "pack_version": row["pack_version"]
            }

        return packs

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

    def get_calendar(self, pack_id):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT * FROM online_calendars
            WHERE pack_id = ?
            AND calendar_id = "calendar";
        """, [pack_id])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return {}

        calendar = {"pack_id": pack_id, "exceptions": {}, "off_days": []}
        for row in rows:
            if row["is_default"] == True:
                calendar["default"] = {
                    "name": row["schedule_name"],
                    "id": row["schedule_id"]
                }
            else:
                calendar["exceptions"][row["exception_date"]] = {
                    "name": row["schedule_name"],
                    "id": row["schedule_id"]
                }

        cursor.execute(f"""
            SELECT * FROM online_calendars_off_days
            WHERE pack_id = ?
            AND calendar_id = "calendar";
        """, [pack_id])
        rows = cursor.fetchall()
        for row in rows:
            calendar["off_days"].append(row["off_day"])

        return calendar

    def remove_all_online_schedule_packs(self):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            DELETE FROM online_schedules;
        """)
        cursor.execute(f"""
            DELETE FROM online_schedule_packs;
        """)
        self.conn.commit()

    def remove_all_online_calendars(self):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            DELETE FROM online_calendars;
        """)
        cursor.execute(f"""
            DELETE FROM online_calendars_off_days;
        """)
        self.conn.commit()

    def download_schedule_packs_from_sb(self):
        return (
            self.supabase.table("online_schedule_packs")
            .select("*")
            .execute()
        ).data

    def download_online_schedules_from_sb(self):
        schedules = (
            self.supabase.table("online_schedules")
            .select("*")
            .execute()
        )
        schedule_packs = (
            self.supabase.table("online_schedule_packs")
            .select("*")
            .execute()
        )
        schedule_calendars = (
            self.supabase.table("online_calendars")
            .select("*")
            .execute()
        )
        schedule_calendars_off_days = (
            self.supabase.table("online_calendars_off_days")
            .select("*")
            .execute()
        )

        self.remove_all_online_schedule_packs()
        self.remove_all_online_calendars()
        self.add_online_schedule_em(schedules.data)
        self.add_online_schedule_pack_em(schedule_packs.data)
        self.add_online_calendar_em(schedule_calendars.data)
        self.add_online_calendar_off_date_em(schedule_calendars_off_days.data)

    # def convert_schedule_jsons_to_sql(self):
    #     schedule_path = Path(self.database_dir) / "schedules"
    #     if schedule_path.exists():
    #         metadata = Path(self.database_dir) / "schedules" / "metadata.json"
    #         metadata_json = json.loads(metadata.read_text())
    #         self.remove_all_online_calendars()
    #         self.remove_all_online_schedule_packs()
    #         for pack_id, pack_obj in metadata_json.items():
    #             self.add_online_schedule_pack(pack_id, pack_obj["pack_name"], pack_obj["pack_version"])
    #             schedule_json_path = Path(self.database_dir) / "schedules" / pack_id / "json"
    #             calendar_path = schedule_json_path / ".." / "calendar.json"

    #             for schedule_json in schedule_json_path.glob("*.json"):
    #                 schedule = json.loads((schedule_json.read_text()))
    #                 for i, (period_id, period) in enumerate(schedule["schedule"].items(), start=1):
    #                     period["parsed_start"] = datetime.strptime(period["start"], "%I:%M %p")
    #                     period["parsed_end"] = datetime.strptime(period["end"], "%I:%M %p")
    #                     self.add_online_schedule(pack_id, Path(schedule_json).name.replace(".json", ""), schedule["name"], period_id, period["name"], period["start"], period["end"], i)

    #             if calendar_path.exists():
    #                 calendar = json.loads((calendar_path.read_text()))
    #                 default_schedule_id = self.get_online_schedule_id(pack_id, calendar["default"])
    #                 self.add_online_calendar("calendar", pack_obj["pack_name"], pack_id, calendar["default"], default_schedule_id, 1, "")
    #                 for key, value in calendar["exceptions"].items():
    #                     exception_schedule_id = self.get_online_schedule_id(pack_id, calendar["exceptions"][key])
    #                     self.add_online_calendar("calendar", pack_obj["pack_name"], pack_id, value, exception_schedule_id, 0, key)
    #                 for day_int in calendar["off_days"]:
    #                     self.add_online_calendar_off_date("calendar", pack_obj["pack_name"], pack_id, day_int)