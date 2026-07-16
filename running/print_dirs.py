""" This program prints all subdirectories of a provided directory, in
    comma-separated format. While all subdirectories must have numerical names,
    this can provide an easy copy-paste solution to generating Slurm arrays
    for job queueing. The program takes 2 command line arguments:
        1. A path to a directory to read from.
        2. Whether to automatically copy the output to the clipboard for easy pasting."""

# """ Include these lines to change to the program's directory """
# import os
# from pathlib import Path

# os.chdir(Path(__file__).parent.absolute())
# os.chdir("..")
import run_scft

# os.chdir(Path(__file__).parent.absolute())

####### CURRENTLY MUST BE RUN FROM .. (~/running)

from pathlib import Path

#### NOTE PYPERCLIP DOES NOT WORK ON MSI
import pyperclip
import argparse


parser = argparse.ArgumentParser()

parser.add_argument("-d", "--dir", help = "The directory to read from.", required = True)
parser.add_argument("-c", "--copy", action = "store_true", help = "Automatically copy output to clipboard.")
parser.add_argument("-n", "--num", action = "store_true", help = "Assert that all directory names are numerical.")
parser.add_argument("-r", "--review", action = "store_true", help = "Review directories for previously converged SCFT log files")
parser.add_argument("-v", "--verbose", action = "store_true", help = "Print more detailed outputs (this can help with debugging)")
parser.add_argument("-g", "--groups", type = int, default = 500, help = "The number to divide groups into. 500 is recommended for this parameter.")

args = parser.parse_args()

target_dir = Path(args.dir)
clip = args.copy
num = args.num
rev = args.review
debug = args.verbose
groups = args.groups

# check for true command line argument and ignore capitalization
# clip = sys.argv[2].lower() == "true"

# target_dir = Path(sys.argv[1])

dir_amt = 0
out_str = ""

for d in sorted(target_dir.iterdir(), key = lambda d: int(d.stem) if num else d):
    if dir_amt > groups:
        print(f"DIR AMT reached! (dir_amt: {dir_amt}, groups: {groups})")
        print(out_str + "\n")
        dir_amt = 0
        out_str = ""
    if d.is_dir():
        if rev:
            log = d / "log"

            state = run_scft.get_state_cat(d.absolute(), debug = True)
            if debug:
                print(f"{d.name}'s state is: {state}")
            
            # only add if calc is not done/has not finished
            # also exclude ERR values as those likely hint at larger issues and should NOT be run
            if state == "WARN":
                out_str += d.name + ","
                dir_amt += 1

            # if not log.exists() or not log.is_file():
            #     out_str += d.name + ","
            #     dir_amt += 1
            # else:
            #     run_scft.get_state_cat(d.absolute, debug = True) == "WARN"
        else:
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
