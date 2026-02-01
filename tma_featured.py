#!/usr/bin/env python3

import os
import re
import feedparser
import wget
import getopt, sys

# Change these variables to your liking
output_folder = "~/Music/featured_modules"
# The feed variable should generally be left as is. 
# It may be changed to parse from a downloaded copy of TMA's RSS feed.
feed = "https://modarchive.org/rss.php?request=featured"

########################## Setup ##############################

output_folder = os.path.expanduser(output_folder)
if not os.path.isdir(output_folder):
    os.mkdir(output_folder)

owned_modules = os.listdir(output_folder)

parsed = feedparser.parse(feed)

args = sys.argv[1:]
shortopts = "hc:"
longopts = ["help", "count="]
options_list, arguments_list = getopt.getopt(args, shortopts, longopts)

count = 40
count_option = False
for option, value in options_list:
    if option in ("-c", "--count"):
        count = int(value)
        count_option = True
        if count > 40:
            sys.exit("Count must be less than or equal to 40")
    elif option in ("-h", "--help"):
        print("DEFAULT: Will search the root level of the output directory for a module that was recently featured")
        print("         If found, all modules that were featured more recently than the found module will be downloaded")
        print("         If not found, the 40 most recently featured modules will be downloaded")
        print("OPTIONS:")
        print("         -c [x], --count [x]\tDownload the last [x] modules that were featured. Must be less than or equal to 40")

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
                print(f"{obj.filename} is the most recently featured module. Nothing to download.")
                sys.exit(0)
            else:
                print(f"Modules that were featured after {obj.filename} will be downloaded")
                return str(x + 1)
        else:
            continue

########################## Main ##############################

entry_objects_dict = create_entry_objects(parsed.entries, count)

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
