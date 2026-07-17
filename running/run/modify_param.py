""" This program changes the param.json file in run from using placeholder
    values to using actual names. Specifically, this program replaces all
    instances of the word "input" in param.json with a specified directory
    name, then creates the file at that directory.
    
    NOTE: This program automatically prepends ".." to the specfied path and
    should therefore only be run from the directory "run" """

import argparse
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()

parser.add_argument("-d", "--dir", help = "The directory to use", required = True)
# parser.add_argument("-c", "--copy", action = "store_true", help = "Automatically copy output to clipboard.")

args = parser.parse_args()

target_dir = ".." / Path(args.dir)

if target_dir.exists() and target_dir.is_dir():
    with open("param.json", "r") as param:
        text = param.read()
        print("Read original parameter file!")

        text = text.replace("input", args.dir)
        print(f"Replaced all instances of \"input\" with \"{args.dir}\"")

    with open(target_dir / "param.json", "w") as f:
        f.write(text)
        print("Wrote file!")

else:
    print("The specified directory does not exist or is not a directory! Skipping...")