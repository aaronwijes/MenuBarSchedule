# <img width="32" height="32" alt="icon_32x32" src="https://github.com/user-attachments/assets/d95dcabc-404c-4586-b13d-3e6504c3f477" /> Menu Bar Schedule

![GitHub Release](https://img.shields.io/github/v/release/aaronwijes/MenuBarSchedule)
![GitHub commit activity](https://img.shields.io/github/commit-activity/w/aaronwijes/MenuBarSchedule)
![GitHub License](https://img.shields.io/github/license/aaronwijes/MenuBarSchedule)

Menu Bar Schedule shows how much time is left until your next class starts/ends.

<img width="479" height="320" alt="Pasted 2026-10-09 at 9 54 32 PM" src="https://github.com/user-attachments/assets/24d86454-303b-473e-ba07-3ff8c24d8384" />

## Current Features
* See how much time is left until your next class/event
* Select between 10+ schedule variants
* See your schedule timetable in detail
* Install schedule updates without updating the entire app
* Check for updates on app startup
* Automatically set the correct schedule with a calendar (may not work with all schedule packs)

## Building From Source
Install Python 3.15.x and install all of the modules in requirements.txt.<br>
Then, build the app using PyInstaller: `pyinstaller ./resources/MenuBarSchedule.spec`

To test your own schedule packs, make your changes and move the `/schedules` directory to `~/Library/Application Support/MenuBarSchedule/schedules`.<br>
You can reload schedule packs without restarting the app by clicking *Settings > Refresh Schedules from JSON*.