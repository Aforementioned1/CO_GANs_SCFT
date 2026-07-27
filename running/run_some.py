""" This is a helper program to be run in a Slurm job. It takes two command line arguments:\n
        1. A path to a directory with a valid executable file named "run"\n
        2. A path to a CSV file to write timing data to\n
    Currently, timing is always enabled unless the code is explicitly altered.\n

    Example usage: "python run_one.py scft_1/1 data/scft_1_timings.csv" """
import run_scft
import sys
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()

parser.add_argument("-d", "--dir", help = "The directory to read from.", required = True)
parser.add_argument("-n", "--num", type = int, help = "The section number to run.")
parser.add_argument("-s", "--size", type = int, help = "The size of each section.")
parser.add_argument("-t", "--timing", help = "The path to write CSV timing data to.")


args = parser.parse_args()

in_path = Path(args.dir)
time_path = args.timing
num = args.num
size = args.size
base = (int(num) - 1) * size

for i in range(1, size + 1):
    run_scft.execute(in_path = in_path / str(i + base), timing = True, clean_timing = True, time_path = time_path, debug = True)
