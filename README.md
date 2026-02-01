# tma_featured
## modarchive.org featured modules downloader

Download the latest featured modules from modarchive.org.

Makes use of the RSS feed for getting info about newly featured modules.

Up to 40 of the most recently featured modules can be downloaded, as that is the length of the RSS feed.

## Requires
* Python 3
* feedparser https://pypi.org/project/feedparser/
* wget Python module https://pypi.org/project/wget/
* urwid https://pypi.org/project/urwid/ (Optional. Only if you would like to use the TUI interactive mode.)
* systemd (Optional. It is possible to ignore this and still run the script.)

## Setup
The only thing for the user to configure is where modules should be downloaded to.

At the top of the script, tma_featured.py, change the value of the variable output_folder to the path of your choosing. If they directory that you specify here does not exist yet, it will be created automatically by the script. If the [systemd service](#systemd-service) will be used, then the path of output_folder cannot contain the tilde ~ character.

There is also a variable recent_mode_folder. This is where modules will be downloaded to when using the [-a or --all-recent command line option](#command-line-options). If you would like it to be the same output_folder, simply set it equal to output_folder. Like output_folder, this must not contain the tilde ~ character if the systemd service will be used.

Remember: If you choose to copy tma_featured.py to /usr/local/bin, then any changes made to the output_folder or all_mode_folder variables must be done on that copy. If you would prefer to edit some copy in your home directory while also having the executable in /usr/local/bin, use symlinks:

    sudo ln -s /**absolute**/path/to/tma_featured.py /usr/local/bin

(There is also a variable with the name "feed" that specifies the location of the RSS feed containing the latest featured modules. It is possible to change this to the path of a locally downloaded copy of the featured modules RSS feed. This may be useful for testing the script during development, as it will eliminate unnecessary internet traffic. If this is done, also change feed_from_file to True.)

## Behavior
By default, the root of the output directory will be scanned for any file that has an identical filename to one of the last 40 recently featured modules. If such a file is found, the script will download all modules that were featured after that file was featured. For example, if dream.it was featured two weeks ago, and your output directory contains a "dream.it" at its root level, the script will download all featured modules from the last two weeks.

In order to avoid any unexpected behavior (e.g. an old module having the same filename as a newly featured module), it is recommended to set the output directory to something unqiue where only featured modules will be stored.

To circumvent this default behavior and manually specify how many modules to download, use the [command line option -c](#command-line-options)

## Command line options

* -h: Display help
* -c [x], --count=[x]: Download the X most recently featured modules. Must be an integer less than or equal to 40. If the -a option is used, the count must be less than or equal to 100.
* -i, --interactive: Enter an interactive TUI mode where you can browse through modules, select an individual module, and choose to play it (stream) or download it.
* -a, --all-recent: Download from all of the most recently archived modules, including modules that were not featured.

## systemd service
Included are two files relevant to systemd. They can be used to have the script run automatically upon your computer's startup and then to run periodically while the computer is running.

To enable this systemd service:

* Ensure that the output_folder path does not use the tilde ~ character. ([This is only required for those using the systemd service](#setup))
* Ensure sure that the Python script is executable:
```
chmod +x tma_featured.py
```
* In tma_featured.service edit the ExecStart field to contain the path of where you keep tma_featured.py
* Optional: By default, the script will run every 12 hours. This can be changed by editing tma_featured.timer file (the comments there will explain what to edit)
* Copy the *contents* of the service directory (tma_featured.service and tma_featured.timer) to /etc/systemd/system/
* Enable the service, so that it will be started automatically whenever you boot your computer. (Note that the timer is used, not the service file. Also note that the only the name of the timer is typed and its path):
```
systemctl enable tma_featured.timer
```
* Start the service, so it will begin running immediately:
```
systemctl start tma_featured.timer
```
