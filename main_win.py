import sys
import ctypes
import pystray
import platform
import threading
from pathlib import Path
from modules.database import Database
from modules.updater import Updater
from modules.common import MBSCommonFunctions
from pystray import Menu, MenuItem as Item
from PIL import Image, ImageDraw, ImageFont

class MenuBarSchedule(pystray.Icon):
    def __init__(self, common: MBSCommonFunctions, font_path: str):
        super().__init__(
            name="Menu Bar Schedule",
            title=""
        )

        self.font_path = font_path
        self.font = ImageFont.truetype(self.font_path, size=24)

        self.is_running = True
        self.icon = self.create_image("MBS")
        self.common = common

        self.pack_items = {"NONE": Item("Loading...", action=None)}
        self.schedule_items = {"NONE": Item("Loading...", action=None)}
        self.settings_items = (
            Item(text="Shorten Title", action=self.toggle_settings, checked=lambda item: self.common.settings["use_shorthand"]),
            Item(text="Hide Seconds Unit (>1 min)", action=self.toggle_settings, checked=lambda item: self.common.settings["hide_seconds"]),
            Item(text="Show Notifications Before Period Ends", action=self.toggle_settings, checked=lambda item: self.common.settings["show_almost_end_notifs"]),
            Item(text="Set Schedule Based on Calendar", action=self.toggle_settings, checked=lambda item: self.common.settings["set_schedule_based_on_calendar"]),
            pystray.Menu.SEPARATOR,
            Item(text="Check for App Updates on Startup", action=self.toggle_settings, checked=lambda item: self.common.settings["check_app_updates_on_startup"]),
            Item(text="Check for Schedule Updates on Startup", action=self.toggle_settings, checked=lambda item: self.common.settings["check_schedule_updates_on_startup"]),
        )

        self.menu = (
            Item(text="Change Schedule", action=Menu(self.generate_schedule_menu)),
            Item(text="Configure Schedule Packs", action=Menu(self.generate_pack_menu)),
            Item(text="View Current Schedule", action=self.view_schedule),
            pystray.Menu.SEPARATOR,
            Item(text="Check for App Updates", action=self.check_updates),
            Item(text="Check for Schedule Updates", action=self.update_schedules),
            pystray.Menu.SEPARATOR,
            Item(text="Settings", action=Menu(*self.settings_items)),
            Item(text="About", action=self.about),
            pystray.Menu.SEPARATOR,
            Item(text="Quit", action=self.stop)
        )

        self.refresh_schedules(force_load_json=True)
        if self.common.check_updates_on_startup() == "quit":
            self.stop()

        self.timer = threading.Timer(1.0, self.update_time_left)
        self.timer.start()

    def show_info(self, title, message):
        threading.Thread(target=ctypes.windll.user32.MessageBoxW, args=(0, message, title, 0x40)).start()

    def create_image(self, text):
        image = Image.new('RGBA', (64, 64), (198, 169, 73))
        mask = Image.new("L", image.size, 0)

        dc = ImageDraw.Draw(image)
        dc.text((5, 5), text, fill=(0, 0, 0, 255), font=self.font)

        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), image.size], radius=15, fill=255)

        image.putalpha(mask)
        return image

    def generate_schedule_menu(self):
        return self.schedule_items.values()

    def generate_pack_menu(self):
        return self.pack_items.values()

    def select_option_schedule(self, icon, item):
        if not self.common.settings["set_schedule_based_on_calendar"]:
            self.common.select_schedule(item.text)

    def select_option_pack(self, icon, item):
        self.common.select_pack(item.text)
        self.refresh_schedules(force_load_json=False)

    def toggle_settings(self, icon, item):
        self.common.toggle_settings(item.text)

        if item.text == "Set Schedule Based on Calendar":
            self.refresh_schedules(force_load_json=False)

    def update_time_left(self, continue_thread=True):
        if not self.is_running:
            return

        use_calendar, old_schedule_id, schedule_id, proposed_title, day_is_off = self.common.update_time_left_calendar()

        if proposed_title != "":
            if self.title != proposed_title:
                self.title = proposed_title
                if len(self.title.split(": ")) > 1:
                    icon_text = self.title.split(": ")[1].replace("No Schedule", "MBS").replace(" ", "\n")
                else:
                    icon_text = self.title.replace("No Schedule", "MBS").replace(" ", "\n")
                self.icon = self.create_image(icon_text)
        else:
            proposed_title, notification_title, notification_message = self.common.update_time_left(day_is_off)
            if notification_title != "" and notification_message != None:
                self.notify(
                    title=notification_title,
                    message=notification_message
                )
            if self.title != proposed_title:
                self.title = proposed_title
                if len(self.title.split(": ")) > 1:
                    icon_text = self.title.split(": ")[1].replace("No Schedule", "MBS").replace(" ", "\n")
                else:
                    icon_text = self.title.replace("No Schedule", "MBS").replace(" ", "\n")
                self.icon = self.create_image(icon_text)

        if use_calendar and old_schedule_id != schedule_id:
            self.update_menu()

        if self.is_running and continue_thread and platform.system() == "Windows":
            self.timer = threading.Timer(1.0, self.update_time_left)
            self.timer.start()

    def refresh_schedules(self, force_load_json=True):
        if not self.common.schedule_dir_exists(force_load_json=force_load_json):
            self.pack_items = {"NONE": Item(text="No Packs Found", action=None, enabled=False)}
            self.schedule_items = {"NONE": Item(text="No Schedules Found", action=None, enabled=False)}
            return

        self.pack_options, selected_pack_id = self.common.load_packs()
        if self.pack_options != {}:
            self.pack_items = {
                id: pystray.MenuItem(text=name, action=self.select_option_pack, checked=lambda item, id=id: (self.common.settings["selected_online_pack_id"] == id))
                for id, name in self.pack_options.items()
            }
        else:
            self.pack_items = {"NONE": Item(text="No Packs Found", action=None, enabled=False)}

        self.schedule_options, selected_schedule_id, set_schedule_based_on_calendar = self.common.load_schedules()
        if self.schedule_options != {}:
            self.schedule_items = {
                id: pystray.MenuItem(text=name, action=self.select_option_schedule, checked=lambda item, id=id: (self.common.settings["selected_schedule_id"] == id), enabled=lambda item: (self.common.settings["set_schedule_based_on_calendar"] == False))
                for id, name in self.schedule_options.items()
            }

            if selected_schedule_id != "":
                self.update_time_left(continue_thread=False)
        else:
            self.schedule_items = {"NONE": Item(text="No Schedules Found", action=None, enabled=False)}

    def view_schedule(self, sender):
        title, message = self.common.view_schedule()
        self.show_info(
            title=title,
            message=message
        )

    def update_schedules_thread(self):
        if self.common.update_schedules(True):
            self.refresh_schedules(force_load_json=True)

    def check_updates(self, sender):
        threading.Thread(target=self.common.update_app, args=(True,), daemon=True).start()

    def update_schedules(self, sender):
        threading.Thread(target=self.update_schedules_thread, daemon=True).start()

    def about(self, sender):
        title, message = self.common.about()
        self.show_info(
            title=title,
            message=message
        )

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        font_path = Path(sys.executable).resolve().parent / "resources" / "Gidole-Regular.ttf"
    else:
        font_path = Path(__file__).resolve().parent / "resources" / "Gidole-Regular.ttf"

    database = Database()
    updater = Updater(database)
    common = MBSCommonFunctions(database, updater)
    app = MenuBarSchedule(common, font_path)
    app.run()
    app.is_running = False
    database.conn.close()
