#!/usr/bin/env python3

import os
import re
import feedparser
import wget
import getopt, sys
import webbrowser
# Try to import optional libraries needed for interactive mode.
no_tui = False
try:
    import urwid
except:
    no_tui = True

########################## User configuration ##############################

# Change these variables to your liking
# output_folder cannot use the tilde character ~ if the systemd service will be used
output_folder = "~/Music/featured_modules"
all_mode_folder = "~/Music/all_recent_modules"

### The feed variable should generally be left as is. 
# It represents the feed for *recently featured* modules. 
# (If a, --all-recent is used, a different feed will be used automatically. There is no need to configure anything in order for -a to work.)
# It may be changed to parse from a downloaded copy of TMA's RSS feed (e.g. for quicker load times when developing this script.)
# If this is done, change feed_from_file to True
feed = "https://modarchive.org/rss.php?request=featured"
feed_from_file = False

########################## Setup ##############################

args = sys.argv[1:]
shortopts = "hc:iao:"
longopts = ["help", "count=", "interactive", "all-recent", "output"]
options_list, arguments_list = getopt.getopt(args, shortopts, longopts)

count = 40
count_option = False
interactive_mode = False
all_mode = False
custom_output = False
for option, value in options_list:
    if option in ("-h", "--help"):
        print("DEFAULT:") 
        print("Will search the root level of the output directory for a module that was recently featured")
        print("If found, all modules that were featured more recently than the found module will be downloaded")
        print("If not found, the 40 most recently featured modules will be downloaded")
        print("OPTIONS (all options may be combined besides for -h):")
        print("-a, --all-recent\tDownload from the archive of all recently archived modules including modules that were not featured")
        print("-c [x], --count [x]\tDownload the last [x] modules that were featured. Must be less than or equal to 40.")
        print("                   \tIf -a is used with this option, must be less than or equal to 100")
        print("-i, --interactive\tInteractive TUI mode. Browse the recently featured modules and choose which to download or stream")
        print("                 \tWhen combined with the -a option, all recently archived modules will be displayed")
        print("-o, --output\tSpecify an output directory. (Without this, the output directory specified at the top of tma_featured.py is used)")
        print("-h, --help\tDisplay this help message")
        sys.exit(0)
    if option in ("-a", "--all-recent"):
        all_mode = True
        count = 15
        #feed = "https://modarchive.org/rss.php?request=uploads"
        feed = os.path.expanduser("~/Downloads/rss-1.php")
        if not custom_output:
            output_folder = all_mode_folder
    if option in ("-o", "--output"):
        output_folder = value
        custom_output = True
    if option in ("-c", "--count"):
        count = int(value)
        count_option = True
        if all_mode and count > 100:
            sys.exit("Count must be less than or equal to 100 when using -a, --all-recent option")
        elif not all_mode and count > 40:
            sys.exit("Count must be less than or equal to 40")
    if option in ("-i", "--interactive"):
        if no_tui:
            sys.exit("Cannot start interactive mode because the urwid library was not found\nhttps://pypi.org/project/urwid/")
        else:
            interactive_mode = True

output_folder = os.path.expanduser(output_folder)
output_folder = os.path.abspath(output_folder)
if not os.path.isdir(output_folder):
    os.mkdir(output_folder)

owned_modules = os.listdir(output_folder)

if feed_from_file:
    feed = os.path.expanduser(feed)
    feed = os.path.abspath(feed)

parsed = feedparser.parse(feed)

# If no count is specified, interactive mode should display as many modules as possible.
if not count_option:
    if interactive_mode and all_mode:
        count = 100
    elif interactive_mode:
        count = 40

########################## Classes and methods ##############################

class FeaturedModule:
    """Represents one feed item/entry, which is the same as one recently featured module"""
    def __init__(self, feed_entry):
        self.title = feed_entry.title
        self.date = feed_entry.published
        self.filename = re.search('Filename:</b>(.*?)<br', feed_entry.summary)[1].strip()
        # The month as an integer from 1 to 12
        self.month = feed_entry.published_parsed[1]
        self.page = feed_entry.link2
        self.download = feed_entry.link
        self.mod_id = re.search('moduleid=([0-9]*?)#', self.download)[1].strip()
        self.stream_page = f"modarchive.org/index.php?request=view_player&query={self.mod_id}"
        if self.filename in owned_modules:
            self.owned = True
        else:
            self.owned = False

def create_entry_objects(parsed_entries, count, owned_modules):
    """Turn parsed feed entries into objects, then insert them into a dictionary. Dictionary keys are sequential integers, starting with 1"""
    entry_objects_dict = dict()
    for x in range(count):
        key = str(x + 1)
        entry_objects_dict[key] = FeaturedModule(parsed.entries[x])
        entry_objects_dict[key].number = key
    return entry_objects_dict

def download_module(entry_object, output_folder, owned_modules):
    """Download the module using the URL in a FeaturedModule object's .download field. If the module already exists in the output directory, skip downloading it."""
    if entry_object.filename in owned_modules:
        print(f"{entry_object.filename} already exists in {output_folder}. Skipping its download.")
    else:
        print(f"\nDownloading {entry_object.filename}")
        wget.download(entry_object.download, output_folder)
        entry_object.owned = True
        owned_modules.append(entry_object)

def find_recent_module(entry_objects_dict, output_folder, owned_modules):
    """Search the root level of the output directory for a module that was recently featured. If it is found, return the dictionary key that corresponds with that module"""
    for x in range(len(entry_objects_dict.keys())):
        obj = entry_objects_dict[str(x + 1)]
        if obj.filename in owned_modules:
            print(f"Found recently downloaded module {obj.filename} in {output_folder}")
            if x == 0:
                print(f"{obj.filename} is the most recent module. Nothing to download.")
                sys.exit(0)
            else:
                print(f"Modules that were featured after {obj.filename} will be downloaded")
                return str(x + 1)
        else:
            continue

########################## Main ##############################

entry_objects_dict = create_entry_objects(parsed.entries, count, owned_modules)

if not interactive_mode:
    # Only use find_recent_module if the user did not specify a count
    if count_option:
        recent_key = ""
    else:
        recent_key = find_recent_module(entry_objects_dict, output_folder, owned_modules)

    for key in entry_objects_dict.keys():
        if key == recent_key:
            break 
        else:
            download_module(entry_objects_dict[key], output_folder, owned_modules)

########################## Urwid TUI ##############################

if not no_tui and interactive_mode:
    
    palette = [
    ("featured", "white", "dark blue"),
    ("number", "black", "white"),
    ("downloaded", "dark green", "black"),
    ]

    def handle_input(key):
        if key in {"q", "Q"}:
            raise urwid.ExitMainLoop()
        elif key == "esc":
            loop.widget = main_menu

    def menu(title, choices):
        """Creates a simple menu. Takes a title and a list of choices (buttons). Returns an urwid ListBox containing SimpleFocusListWalker."""
        body = [urwid.Text(title), urwid.Divider(), *choices]
        return urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def main_menu_choices(entry_objects_list): 
        """Takes a list of FeaturedModule objects. Returns them as a list of urwid buttons. When these buttons are clicked they open a submenu."""
        formatted_choices = list()
        for choice in entry_objects_list:
            if choice.owned:
                downloaded = ("downloaded", " (Downloaded) ")
            else:
                downloaded = ""

            number = ("number", choice.number + ":")

            if ">> Featured <<" in choice.title:
                button_label = [number,
                                " ", 
                                ("featured", ">> Featured <<"), 
                                choice.title.removeprefix(">> Featured <<"), downloaded]
            else:
                button_label = [number, " ", choice.title, downloaded]

            button = urwid.Button(button_label)
            urwid.connect_signal(button, "click", submenu, user_args=[choice, downloaded])
            formatted_choices.append(urwid.AttrMap(button, None, focus_map="reversed"))
        return formatted_choices

    def submenu(choice, downloaded, button):
        """Creates a submenu to be displayed when a module is selected from the main menu. Returns an urwid ListBox containing SimpleFocusListWalker."""
        global main_menu
        choices = list()
        dl_button = urwid.Button("Download")
        urwid.connect_signal(dl_button, "click", dl_mod, choice)
        choices.append(urwid.AttrMap(dl_button, None, focus_map="reversed"))
        if downloaded != "":
            choices.append(urwid.Text(downloaded))
        stream_button = urwid.Button("Play in browser")
        urwid.connect_signal(stream_button, "click", stream_mod, choice)
        choices.append(urwid.AttrMap(stream_button, None, focus_map="reversed"))
        choices.extend([urwid.Divider(), urwid.Text("ESC to go back")])
        submenu_window = menu(choice.filename, choices)
        loop.widget = urwid.Overlay(
                urwid.LineBox(submenu_window),
                main_menu,
                align=urwid.CENTER,
                width=(urwid.RELATIVE, 60),
                valign=urwid.MIDDLE,
                height=(urwid.RELATIVE, 60))

    def stream_mod(button, choice):
        """Stream the selected module using the chiptune2.js player on modarchive.org. Opens a new browser window"""
        webbrowser.open(choice.stream_page, new=1)

    def dl_mod(button, choice):
        """Download the selected module using download_module"""
        download_module(choice, output_folder, owned_modules)
        # Render the main menu again, so that (Downloaded) is shown next to this module.
        global main_menu
        main_menu = menu(title_string, main_menu_choices(entry_objects_list))
        #loop.widget = menu(title_string, main_menu_choices(entry_objects_list))

    entry_objects_list = list()
    for entry_object in entry_objects_dict.values():
        entry_objects_list.append(entry_object)

    if all_mode:
        title_string = "Recently Uploaded Modules (all)"
    else:
        title_string = "Recently Featured Modules"

    main_menu = menu(title_string, main_menu_choices(entry_objects_list))

    loop = urwid.MainLoop(main_menu, palette, unhandled_input=handle_input)
    loop.run()
