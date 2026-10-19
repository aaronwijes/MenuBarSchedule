import sys
import pystray
from modules.database import Database
from modules.updater import Updater
from modules.common import MBSCommonFunctions
from pystray import Menu, MenuItem as Item
from PIL import Image, ImageDraw
import threading
import platform

OPSYS = platform.system()

class MenuBarSchedule(pystray.Icon):
    def __init__(self, database: Database, common: MBSCommonFunctions):
        super().__init__(
            name="Menu Bar Schedule",
            title=""
        )
        self.icon = self.create_image(64, 64, 'black', 'white')
        self.database = database
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
            pystray.Menu.SEPARATOR,
            Item(text="Refresh Schedules from JSON", action=self.refresh_schedules),
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

        self.refresh_schedules()
        self.timer = threading.Timer(1.0, self.update_time_left)
        self.timer.start()

        if self.common.check_updates_on_startup() == "quit":
            self.stop()

    def show_info(self, title, message):
        import ctypes
        threading.Thread(target=ctypes.windll.user32.MessageBoxW, args=(0, message, title, 0x40)).start()

    def create_image(self, width, height, color1, color2):
        # Generate an image and draw a pattern
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle(
            (width // 2, 0, width, height // 2),
            fill=color2)
        dc.rectangle(
            (0, height // 2, width // 2, height),
            fill=color2)

        return image

    def generate_schedule_menu(self):
        return self.schedule_items.values()

    def generate_pack_menu(self):
        return self.pack_items.values()

    def select_option_schedule(self, icon, item):
        self.common.select_schedule(item.text)
        # self.update_menu()

    def select_option_pack(self, icon, item):
        self.common.select_pack(item.text)
        self.refresh_schedules()

    def toggle_settings(self, icon, item):
        self.common.toggle_settings(item.text)

        if item.text == "Set Schedule Based on Calendar":
            self.refresh_schedules()

        self.update_menu()

    def update_time_left(self):
        use_calendar, old_schedule_id, schedule_id, proposed_title, day_is_off = self.common.update_time_left_calendar()
        if use_calendar and self.schedule_options != [] and old_schedule_id != schedule_id:
            if old_schedule_id != "":
                self.schedule_items[old_schedule_id].state = False
            if schedule_id != "":
                self.schedule_items[schedule_id].state = True

        if proposed_title != "":
            if self.title != proposed_title:
                self.title = proposed_title
            return

        proposed_title, notification_title, notification_message = self.common.update_time_left(day_is_off)
        if notification_title != "" and notification_message != None:
            pass
            # rumps.notification(
            #     title=notification_title,
            #     subtitle="",
            #     message=notification_message,
            #     sound=False
            # )
        if self.title != proposed_title:
            self.title = proposed_title

    def refresh_schedules(self):
        if not self.common.schedule_dir_exists():
            self.pack_items = {"NONE": Item(text="No Packs Found", action=False)}
            self.schedule_items = {"NONE": Item(text="No Schedules Found", action=False)}
            return

        self.pack_options, selected_pack_id = self.common.load_packs()
        if self.pack_options != {}:
            self.pack_items = {
                id: pystray.MenuItem(text=name, action=self.select_option_pack, checked=lambda item, id=id: (self.common.settings["selected_online_pack_id"] == id))
                for id, name in self.pack_options.items()
            }
        else:
            self.pack_items = {"NONE": Item(text="No Packs Found", action=False)}

        self.schedule_options, selected_schedule_id, set_schedule_based_on_calendar = self.common.load_schedules()
        if self.schedule_options != {}:
            self.schedule_items = {
                id: pystray.MenuItem(text=name, action=self.select_option_schedule if not set_schedule_based_on_calendar else None, checked=lambda item, id=id: (self.common.settings["selected_schedule_id"] == id))
                for id, name in self.schedule_options.items()
            }

            if selected_schedule_id != "":
                self.update_time_left()
        else:
            self.schedule_items = {"NONE": Item(text="No Schedules Found", action=False)}

        # self.update_menu()

    def view_schedule(self, sender):
        title, message = self.common.view_schedule()
        self.show_info(
            title=title,
            message=message
        )

    def check_updates(self, sender):
        if self.common.update_app(True) == "restart":
            self.stop()

    def update_schedules_thread(self):
        if self.common.update_schedules(True):
            self.refresh_schedules(None)

    def update_schedules(self, sender):
        threading.Thread(target=self.update_schedules_thread, daemon=True).start()

    def about(self, sender):
        title, message = self.common.about()
        self.show_info(
            title=title,
            message=message
        )

if __name__ == "__main__":
    database = Database()
    updater = Updater(database)
    common = MBSCommonFunctions(database, updater)
    MenuBarSchedule(database, common).run()
    database.conn.close()
