from os import listdir
from os.path import isfile, join
import time
import os
import shutil
import json
from configparser import ConfigParser
import hashlib

"""
This script monitors a specified directory (default "Images") for files and automatically moves
them into subdirectories based on matching prefixes. It can also generate file hashes and store
them in a JSON file. The operational parameters (hash method, directory name, whether to run,
etc.) are read from a 'config.ini' file, and the target subdirectory names are loaded from a
'filePaths.json' file.

Usage:
1. 'config.ini' controls whether the script is running, which directory to monitor, which hash
   method to use, and whether to generate hashes.
2. 'filePaths.json' lists all the subdirectory names to which files can be moved.
3. The script sleeps in a loop, checking for new files every 3 seconds while `isRunning = true`.
4. Files that match a given prefix (e.g., 'prefix XYZ.png') are moved to the corresponding
   subdirectory, and the prefix is removed from the filename.
5. If 'getHashes' is enabled, it computes the hash of each moved file and writes it to 'fileHashes.json'.

Supported Hash Methods:
- MD5
- SHA-1
- SHA-224
- SHA-256
"""

currentPath = "Images"
path = []
hashStore = {}

# Flags for controlling the script's behavior
isRunning = False
getHashes = False
hashCode = "MD5"

# Create a parser to handle our config.ini file
parser = ConfigParser()

# If config.ini doesn't exist, create it with default settings
if not os.path.exists('config.ini'):
    parser['settings'] = {
        'isRunning': "true",
        'getHashes': "true",
        'hashMethod': "MD5",
        'currentPathName': "Images"
    }
    with open('config.ini', 'w') as f:
        parser.write(f)

# If filePaths.json doesn't exist, create it with a default entry
if not os.path.exists('filePaths.json'):
    data = ["empty"]
    with open('filePaths.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Read settings from config.ini
parser.read('config.ini')
currentPath = parser.get('settings', 'currentPathName')
hashCode = parser.get('settings', 'hashMethod')

# Convert string booleans to actual bool
getHashes = True if parser.get('settings', 'getHashes') == 'true' else False
isRunning = True if parser.get('settings', 'isRunning') == 'true' else False

# Prepare the hash object based on the chosen hash method
hash_ = hashlib.md5()
if hashCode == 'SHA-1':
    hash_ = hashlib.sha1()
elif hashCode == 'SHA-256':
    hash_ = hashlib.sha256()
elif hashCode == 'SHA-224':
    hash_ = hashlib.sha224()
# Otherwise, default remains MD5

def hashFile(fname: str) -> str:
    """
    Computes and returns the hash of a file specified by fname using the
    hash method selected in the config.ini ('hashMethod').
    
    :param fname: The path to the file whose hash is to be calculated.
    :return: The computed hash in hexadecimal string form.
    """
    # We create a fresh hash object each time to avoid reusing state between files
    if hashCode == 'MD5':
        h = hashlib.md5()
    elif hashCode == 'SHA-1':
        h = hashlib.sha1()
    elif hashCode == 'SHA-256':
        h = hashlib.sha256()
    elif hashCode == 'SHA-224':
        h = hashlib.sha224()
    else:
        # Fallback to MD5 if for some reason an unknown method is set
        h = hashlib.md5()

    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    """
    Main function that:
    1. Lists all files in the currentPath directory.
    2. Checks each file to see if its name starts with any of the prefixes in 'path'.
    3. If a file's name starts with a prefix, moves the file into a matching subdirectory
       (which has the same name as the prefix) and removes the prefix from the file name.
    4. If 'getHashes' is True, computes the file's hash and stores it in 'fileHashes.json'.
    """
    onlyfiles = [f for f in listdir(currentPath) if isfile(join(currentPath, f))]
    print("Running")
    print(onlyfiles)
    for file in onlyfiles:
        for b in path:
            # Check if the file name starts with our prefix
            if file.startswith(b):
                # Move the file to the subdirectory named 'b'
                src = os.path.join(currentPath, file)
                dest_name = file.replace(b + " ", "")
                dest = os.path.join(b, dest_name)
                shutil.move(src, dest)

                # If hashing is enabled, compute the hash and store it
                if getHashes:
                    if not os.path.exists("fileHashes.json"):
                        open("fileHashes.json", 'a').close()  # Create empty file if it doesn't exist
                    hashStore.update({ f"{b} | {dest_name}" : hashFile(dest) })
                    with open('fileHashes.json', 'w', encoding='utf-8') as outfile:
                        json.dump(hashStore, outfile, ensure_ascii=False, indent=4)

time.sleep(2)

if isRunning:
    # Load the list of prefixes/subdirectories from filePaths.json
    with open('filePaths.json') as paths_file:
        pathData = json.load(paths_file)
        for i in pathData:
            path.append(i)

    # Ensure these subdirectories exist; if not, create them
    for a in path:
        if not os.path.exists(a):
            os.makedirs(a)

    # Ensure the directory we're monitoring exists
    if not os.path.exists(currentPath):
        os.makedirs(currentPath)

    # Keep running until 'isRunning' in config.ini is set to false
    while isRunning:
        parser.read('config.ini')
        # Update isRunning in case it's changed externally
        if parser.get('settings', 'isRunning') == "true":
            isRunning = True
        else:
            isRunning = False

        main()
        time.sleep(3)
