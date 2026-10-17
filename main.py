import rumps
from modules.database import Database
from modules.updater import Updater
from modules.common import MBSCommonFunctions

class MenuBarSchedule(rumps.App):
    def __init__(self, database: Database, common: MBSCommonFunctions):
        super().__init__(
            name="Menu Bar Schedule",
            title=""
        )
        self.database = database
        self.common = common

        self.change_schedule = rumps.MenuItem(title="Change Schedule")
        self.change_schedule.add(rumps.MenuItem("Loading..."))

        self.change_schedule_pack = rumps.MenuItem(title="Configure Schedule Packs")
        self.change_schedule_pack.add(rumps.MenuItem("Loading..."))

        self.last_notified_period = None

        self.settings = rumps.MenuItem(title="Settings")
        self.settings_items = {
            "use_shorthand": rumps.MenuItem(title="Shorten Title", callback=self.toggle_settings),
            "hide_seconds": rumps.MenuItem(title="Hide Seconds Unit (>1 min)", callback=self.toggle_settings),
            "show_almost_end_notifs": rumps.MenuItem(title="Show Notifications Before Period Ends", callback=self.toggle_settings),
            "set_schedule_based_on_calendar": rumps.MenuItem(title="Set Schedule Based on Calendar", callback=self.toggle_settings),
            "NO_CONFIG_1": rumps.separator,
            "check_app_updates_on_startup": rumps.MenuItem(title="Check for App Updates on Startup", callback=self.toggle_settings),
            "check_schedule_updates_on_startup": rumps.MenuItem(title="Check for Schedule Updates on Startup", callback=self.toggle_settings),
            "NO_CONFIG_2": rumps.separator,
            "NO_CONFIG_3": rumps.MenuItem(title="Refresh Schedules from JSON", callback=self.refresh_schedules),
        }
        for id, item in self.settings_items.items():
            if not "NO_CONFIG" in id:
                item.state = self.database.fetch_value(id)
            self.settings.add(item)

        self.menu = [
            self.change_schedule,
            self.change_schedule_pack,
            "View Current Schedule",
            rumps.separator,
            "Check for App Updates",
            "Check for Schedule Updates",
            rumps.separator,
            self.settings,
            "About",
            rumps.separator,
        ]

        self.refresh_schedules(self.change_schedule)
        self.timer = rumps.Timer(self.update_time_left, interval=1.0)
        self.timer.start()

        if self.common.check_updates_on_startup() == "quit":
            rumps.quit_application()

    def select_option_schedule(self, sender):
        old_schedule_id = self.common.select_schedule(sender.title)
        if old_schedule_id != "":
            self.schedule_items[old_schedule_id].state = False
        sender.state = True

    def select_option_pack(self, sender):
        pack_id = self.common.select_pack(sender.title)
        if pack_id != "":
            self.pack_items[pack_id].state = False
        self.refresh_schedules(None)

    def toggle_settings(self, sender):
        state = self.common.toggle_settings(sender.title)
        sender.state = state

        if sender.title == "Set Schedule Based on Calendar":
            self.refresh_schedules(None)

    def update_time_left(self, sender):
        use_calendar, schedule_id, proposed_title, day_is_off = self.common.update_time_left_calendar()
        if use_calendar and self.schedule_options != []:
            self.schedule_items = {
                id: rumps.MenuItem(title=value, callback=None)
                for id, value in self.schedule_options.items()
            }

            if schedule_id != "":
                self.schedule_items[schedule_id].state = True

            self.change_schedule.clear()
            for item in self.schedule_items.values():
                self.change_schedule.add(item)

        if proposed_title != "":
            if self.title != proposed_title:
                self.title = proposed_title
            return

        proposed_title, notification_title, notification_message = self.common.update_time_left(day_is_off)
        if notification_title != "" and notification_message != None:
            rumps.notification(
                title=notification_title,
                message=notification_message,
                sound=False
            )
        if self.title != proposed_title:
            self.title = proposed_title

    def refresh_schedules(self, sender):
        if not self.common.schedule_dir_exists():
            self.change_schedule.clear()
            self.change_schedule.add(rumps.MenuItem(title="No Schedules Found"))

            self.change_schedule_pack.clear()
            self.change_schedule_pack.add(rumps.MenuItem(title="No Packs Found"))

            self.common.prompt_install_schedules()

        self.pack_options, selected_pack_id = self.common.load_packs()
        if self.pack_options != {}:
            self.pack_items = {
                id: rumps.MenuItem(title=name, callback=self.select_option_pack)
                for id, name in self.pack_options.items()
            }

            if selected_pack_id != "":
                self.pack_items[selected_pack_id].state = True
            
            self.change_schedule_pack.clear()
            for item in self.pack_items.values():
                self.change_schedule_pack.add(item)
        else:
            self.change_schedule_pack.clear()
            self.change_schedule_pack.add(rumps.MenuItem(title="No Packs Found"))

        self.schedule_options, selected_schedule_id, set_schedule_based_on_calendar = self.common.load_schedules()
        if self.schedule_options != {}:
            self.schedule_items = {
                id: rumps.MenuItem(title=name, callback=self.select_option_schedule if not set_schedule_based_on_calendar else None)
                for id, name in self.schedule_options.items()
            }

            if selected_schedule_id != "":
                self.schedule_items[selected_schedule_id].state = True
                self.update_time_left(sender)

            self.change_schedule.clear()
            for item in self.schedule_items.values():
                self.change_schedule.add(item)
        else:
            self.change_schedule.clear()
            self.change_schedule.add(rumps.MenuItem(title="No Schedules Found"))

    @rumps.clicked("View Current Schedule")
    def view_schedule(self, sender):
        title, message = self.common.view_schedule()
        rumps.alert(
            title=title,
            message=message
        )

    @rumps.clicked("Check for App Updates")
    def check_updates(self, sender):
        if self.common.update_app(True) == "restart":
            rumps.quit_application()

    @rumps.clicked("Check for Schedule Updates")
    def update_schedules(self, sender):
        if self.common.update_schedules(True):
            self.refresh_schedules(None)

    @rumps.clicked("About")
    def about(self, sender):
        title, message = self.common.about()
        rumps.alert(
            title=title,
            message=message
        )

if __name__ == "__main__":
    database = Database()
    updater = Updater(database)
    common = MBSCommonFunctions(database, updater)
    MenuBarSchedule(database, common).run()
    database.conn.close()
