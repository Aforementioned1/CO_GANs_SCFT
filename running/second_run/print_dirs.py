""" This program prints all subdirectories of a provided directory, in
    comma-separated format. While all subdirectories must have numerical names,
    this can provide an easy copy-paste solution to generating Slurm arrays
    for job queueing. The program takes 2 command line arguments:
        1. A path to a directory to read from.
        2. Whether to automatically copy the output to the clipboard for easy pasting."""

from pathlib import Path
import pyperclip
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-d", "--dir", help = "The directory to read from.")
parser.add_argument("-c", "--copy", action = "store_true", help = "Automatically copy output to clipboard.")
parser.add_argument("-n", "--num", action = "store_true", help = "Assert that all directory names are numerical.")

args = parser.parse_args()

target_dir = Path(args.dir)
clip = args.copy
num = args.num

# check for true command line argument and ignore capitalization
# clip = sys.argv[2].lower() == "true"

# target_dir = Path(sys.argv[1])

dir_amt = 0
out_str = ""

for d in sorted(target_dir.iterdir(), key = lambda d: int(d.stem) if num else d):
    if d.is_dir():
        out_str += d.name + ","
        dir_amt += 1

    else:
        print(f"{d.name} is not a directory!")

if len(out_str) > 1:
    out_str = out_str.rstrip(",")

print(out_str)
print(dir_amt)

if clip:
    pyperclip.copy(out_str)
