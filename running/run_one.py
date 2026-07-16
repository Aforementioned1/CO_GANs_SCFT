""" This is a helper program to be run in a Slurm job. It takes two command line arguments:\n
        1. A path to a directory with a valid executable file named "run"\n
        2. A path to a CSV file to write timing data to\n
    Currently, timing is always enabled unless the code is explicitly altered.\n

    Example usage: "python run_one.py scft_1/1 data/scft_1_timings.csv" """
import run_scft
import sys

run_scft.execute(in_path = sys.argv[1], timing = True, clean_timing = True, time_path = sys.argv[2], debug = True)