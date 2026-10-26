# <img width="32" height="32" alt="icon_32x32" src="https://github.com/user-attachments/assets/d95dcabc-404c-4586-b13d-3e6504c3f477" /> Menu Bar Schedule

![GitHub Release](https://img.shields.io/github/v/release/aaronwijes/MenuBarSchedule)
![GitHub commit activity](https://img.shields.io/github/commit-activity/w/aaronwijes/MenuBarSchedule)
![GitHub License](https://img.shields.io/github/license/aaronwijes/MenuBarSchedule)

Menu Bar Schedule shows how much time is left until your next class or event starts/ends.

<img width="479" height="320" alt="Menu Bar Schedule - Demo" src="https://github.com/user-attachments/assets/24d86454-303b-473e-ba07-3ff8c24d8384" />

## How to Use
**Install the app:**
* Windows: Download and extract `MenuBarSchedule.zip` to any folder before running the app.
* macOS: Download and extract `MenuBarSchedule.app.zip` and drag the .app file into the Applications folder. (If Gatekeeper blocks the app from running, go to *Settings > Privacy and Security > click Open Anyway*.)

**Regardless of your operating system:**
* Download schedules when prompted
* Select the schedule you want to follow!

## Features
**Schedule countdowns** - This is the main feature of the app! Make sure that both a school and schedule are selected to see the countdown in your menu bar.

**Selecting a school** - This shows the respective school’s schedules for selection. To select a school, go to *Configure Schedule Packs* > click the desired school. You may only have one school selected at a time.

**Selecting a schedule** - This sets the schedule which is used to calculate countdowns. To select a schedule, go to *Change Schedule* > click the desired schedule. The underlying menu is disabled when the *Set Schedule Based on Calendar* feature is enabled (see below).

**Viewing a schedule’s timetable** - This shows the selected schedule’s timetable. To view the current schedule, click *View Current Schedule*.

**Automatic schedule setting** - This sets the schedule automatically depending on the date. To enable/disable this feature, go to *Settings* > click *Set Schedule Based on Calendar*. Subject to the currently selected school’s support for a school calendar.

## Updates
On macOS, you can check for and install app updates by clicking *Check for App Updates*. This option exists on Windows, but does nothing when clicked. You must download app updates manually on Windows.

On both macOS and Windows, you can check for and install schedule updates by clicking *Check for Schedule Updates*. Make sure to check for schedule updates at least once a week!

## Building From Source
Install Python 3.15.x and install all of the modules in requirements.txt.<br>
Then, build the app using PyInstaller: `pyinstaller ./resources/macos.spec` or `pyinstaller ./resources/win.spec`

To test your own schedule packs, make your changes and move the `/schedules` directory to `~/Library/Application Support/MenuBarSchedule/schedules` or `%LOCALAPPDATA%\aaronwijes\MenuBarSchedule\schedules` depending on your operating system.<br>
You can reload schedule packs by clicking *Settings > Refresh Schedules from JSON*.