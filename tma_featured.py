#!/usr/bin/env python3

import os
import re
import feedparser
import wget
import getopt, sys
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
# The feed variable should generally be left as is. 
# It represents the feed for *recently featured* modules. 
# (If a, --all-recent is used, a different feed will be used automatically. There is no need to configure anything in order for -a to work.)
# It may be changed to parse from a downloaded copy of TMA's RSS feed (e.g. for quicker load times when developing this script.)
# If this is done, change feed_from_file to True
feed = "https://modarchive.org/rss.php?request=featured"
feed_from_file = False
#feed = "~/Downloads/rss.php"

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
        print("OPTIONS:")
        print("-a, --all-recent\tDownload from the archive of all recently archived modules including modules that were not featured")
        print("-c [x], --count [x]\tDownload the last [x] modules that were featured. Must be less than or equal to 40.")
        print("                   \tIf -a is used with this option, must be less than or equal to 100")
        print("-i, --interactive\tInteractive TUI mode. Browse the recently featured modules and choose which to download or stream")
        print("-o, --output\tSpecify an output directory. (Without this, the output directory specified at the top of tma_featured.py is used)")
        sys.exit(0)
    if option in ("-a", "--all-recent"):
        all_mode = True
        count = 15
        feed = "https://modarchive.org/rss.php?request=uploads"
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

########################## Classes and methods ##############################

class FeaturedModule:
    """Represents one feed item/entry, which is the same as one recently featured module"""
    def __init__(self, feed_entry):
        self.title = feed_entry.title
        self.date = feed_entry.published
        self.filename = re.search('Filename:</b>(.*?)<br', feed_entry.summary)[1].strip()
        # The month as an integer from 1 to 12
        self.month = feed_entry.published_parsed[1]
        self.download = feed_entry.link
        self.page = feed_entry.link2

def create_entry_objects(parsed_entries, count):
    """Turn parsed feed entries into objects, then insert them into a dictionary. Dictionary keys are sequential integers, starting with 1"""
    entry_objects_dict = dict()
    for x in range(count):
        entry_objects_dict[str(x + 1)] = FeaturedModule(parsed.entries[x])
    return entry_objects_dict

def download_module(entry_object, output_folder, owned_modules):
    """Download the module using the URL in a FeaturedModule object's .download field. If the module already exists in the output directory, skip downloading it."""
    if entry_object.filename in owned_modules:
        print(f"{entry_object.filename} already exists in {output_folder}. Skipping its download.")
    else:
        print(f"\nDownloading {entry_object.filename}")
        wget.download(entry_object.download, output_folder)

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

entry_objects_dict = create_entry_objects(parsed.entries, count)

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

