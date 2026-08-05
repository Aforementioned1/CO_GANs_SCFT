""" This file contains an example test program to run through the
entire SCFT process, from GAN-generated guesses to analyzing free energy values.
This program requires a JSON parameter file to be passed in as a command line argument.
A sample parameter file is provided in defaults.json.\n
See README.md: SCFT Examples for information about the specifics of this program and
see JSON Parameters for information about what parameters are required by this program"""

############# ALSO ADDED SEC_DIV!!!

# While some parameters may seem redundant, this program is intended to
# give users as much customizability as possible without touching this program's code.
# Despite this, custom modifications to the code could help repurpose parameters into real use.

import run_scft
from pathlib import Path
import sys
import json
import argparse
import csv

parser = argparse.ArgumentParser()

step_choices = ["HELP", "PREP_SCFT_1", "SCFT_1_TO_CSV", "SCFT_1_CONV", "SCFT_1_TIME",
                "PREP_SCFT_2", "SCFT_2_TO_CSV", "SCFT_2_CONV",
                "SCFT_2_TIME", "UNIQUE_SOLN", "SCFT_1_CONV_OLD", "SCFT_2_CONV_OLD",
                "FIX_W_BASIS_OLD"]
num_choices = [i for i in range(-1, len(step_choices) - 1)] 

group = parser.add_mutually_exclusive_group(required = True)

group.add_argument("-n", "--num", type = int, choices = num_choices, help =
                   """The step to execute, in numerical format. This can be used to make running the program easier,
                   but requires knowledge of which number correlates to which step. More information can be found
                   by using \"--num -1\" or \"--step HELP\".""", default = -2)
group.add_argument("-s", "--step", type = lambda text: text.upper(), choices = step_choices,
                help = "The step to execute. Use \"--num -1\" or \"--step HELP\" for more information about each step.", default = "NULL")
parser.add_argument("-p", "--param", help = "The parameter file to use")
parser.add_argument("-v", "--verbose", action = "store_true",
                help = "Enable verbose output from run_scft's functions (for debugging purposes)")
# parser.add_argument("-c", "--copy", action = "store_true", help = "Automatically copy output to clipboard.")

args = parser.parse_args()
num = args.num
step = args.step
param_path = args.param
debug = args.verbose

# if step is chosen
if (num == -2):
    num = num_choices[step_choices.index(step)]
# otherwise, the proper num is already present (but still update string for printing help)
else:
    step = step_choices[num_choices.index(num)]

print("Step number:", num)
print("Step name:", step)


# -1 (HELP)
# print help information before crashing the program from having a bad param file
if num == -1:
    # print("Sorry! No documentation here yet...............")
    print("---------------------------------------------------------------------------------------------------------------------------------")
    print("Step Name    |  Number  |  Description")
    print("---------------------------------------------------------------------------------------------------------------------------------")
    print("HELP           -1          Print this informative display")
    print("PREP_SCFT_1     0          Prepare directories for GAN initial guesses so that they can be run through SCFT")
    print("SCFT_1_TO_CSV   1          Collect data from SCFT step 1 calculations and write it to a CSV file")
    print("SCFT_1_CONV     2          Print information regarding how many SCFT step 1 calculations converged")
    print("SCFT_1_TIME     3          Print information regarding how long SCFT step 1 calculations took")
    print("PREP_SCFT_2     4          Prepare directories for converged SCFT step 1 calculations so that they can be run through SCFT step 2. This also fixes w.bf files so that they will work for step 2.")
    print("SCFT_2_TO_CSV   5          Collect data from SCFT step 2 calculations and write it to a CSV file")
    print("SCFT_2_CONV     6          Print information regarding how many SCFT step 2 calculations converged")
    print("SCFT_2_TIME     7          Print information regarding how long SCFT step 1 calculations took")
    print("UNIQUE_SOLN     8          Print information regarding how many converged solutions from SCFT step 2 can be considered unique")
    print("SCFT_1_CONV_OLD 9          (Deprecated): Print information regarding how many SCFT step 1 calculations converged")
    print("SCFT_2_CONV_OLD 10         (Deprecated): Print information regarding how many SCFT step 2 calculations converged")
    print("FIX_W_BASIS_OLD 11         Fix w.bf files outputted from SCFT step 1 in preparation for SCFT step 2 (included in step 4)")
    print("---------------------------------------------------------------------------------------------------------------------------------")

if param_path != None:
    print("Parameter file detected.")
    print(f"Attempting to read input file at {param_path} for custom parameters.")
    with open(param_path, "r") as f:
        param = json.load(f)

        # add the scft_1 and scft_2 JSON objects to their
        # own variables for easier access later
        param_scft_1 = param["scft_1"]
        param_scft_2 = param["scft_2"]

        # add certain frequently used parameters as variables for easier access later
        min = param["gan_min"]
        max = param["gan_max"]

else:
    # end program if nothing is inputted
    print("No parameter file detected.")
    print("Ending program...")
    
    sys.exit()

# 0 (PREP_SCFT_1)
if num == 0:
    print("PREP_SCFT_1 (0)")
    # prepare files
    run_scft.prepare_files(in_path = param_scft_1["in_path"], out_path = param_scft_1["out_path"],
                           out_name = param["rf_name"],
                param_path = param_scft_1["param"], command_path = param_scft_1["command"], run_path = param_scft_1["run"],
                debug = debug)

# 1 (SCFT_1_TO_CSV)
if num == 1:
    print("SCFT_1_TO_CSV (1)")
    # combine data to CSV file
    run_scft.to_csv_num(dir_path = param_scft_1["out_path"], num_start = min, num_end = max,
                        output = param_scft_1["data_path"], debug = debug)
    
# 2 (SCFT_1_CONV)
# this code is from conv_helper.py
if num == 2:
    print("SCFT_1_CONV (2)")
    data = {
        "suc":  0, # all in group SUC
        "conv": 0, # SUC_CONV
        "fin":  0, # SUC_MAX_ITER and SUC_NO_CONV
        "iter": 0, # SUC_MAX_ITER
        "nocv": 0, # SUC_NO_CONV
        "warn": 0, # all in group WARN
        "log":  0, # WARN_NO_LOG
        "noit": 0, # WARN_NO_ITER
        "unf":  0, # WARN_NOT_FIN
        "err":  0  # ERR_NO_DIR
    }

    for d in sorted(Path(param_scft_1["out_path"]).iterdir(), key = lambda d: int(d.stem) if num else d):
        state = run_scft.calc_state(d.absolute(), debug = debug)

        match state:
            # group SUC
            case "SUC_CONV":
                data["suc"] += 1
                data["conv"] += 1 
            case "SUC_MAX_ITER":
                data["suc"] += 1
                data["fin"] += 1
                data["iter"] += 1
            case "SUC_NO_CONV":
                data["suc"] += 1
                data["fin"] += 1
                data["nocv"] += 1
            # group WARN
            case "WARN_NO_LOG":
                data["warn"] += 1
                data["log"] += 1
            case "WARN_NO_ITER":
                data["warn"] += 1
                data["noit"] += 1 
            case "WARN_NOT_FIN":
                data["warn"] += 1
                data["unf"] += 1 
            # group ERR
            case "ERR_NO_DIR":
                data["err"] += 1

    # SUC
    print(f"Finished (total):           {data['suc']}")
    print(f"Finished (converged):       {data["conv"]}")
    print(f"Finished (not converged):   {data["fin"]}")
    if param['detailed_conv']:
        print(f"Finished (max iterations):  {data['iter']}")
        print(f"Finished (no convergence):  {data['nocv']}")

    # WARN
    print(f"Unfinished (total):         {data['warn']}")
    if param['detailed_conv']:
        print(f"Unfinished (no log):        {data['log']}")
        print(f"Unfinished (no iterations): {data['noit']}")
        print(f"Unfinished (iterations):    {data['unf']}")

    # ERR
    print(f"Error (no directory):        {data['err']}")

# 3 (SCFT_1_TIME)
if num == 3:
    print("SCFT_1_TIME (3)")
    run_scft.review_csv_timings(param_scft_1["time_path"], sec_div = param_scft_1["sec_div"], debug = debug)

# 4 (PREP_SCFT_2)
if num == 4:
    print("PREP_SCFT_2 (4)")
    # read names of each initial guess (should be 1-250) and whether they converged
    names = run_scft.read_csv_col(in_path = param_scft_1["data_path"], 
                                  col = param["name_col"], debug = debug)
    
    # make sure to cast string boolean values as booleans - requires more complex logic
    # as bool() method considers any non-empty str true

    # not adding the lambda as a parameter as it would likely be hard to
    # serialize/deserialize and should not change
    # despite this, the column names have still been
    # included as parameters, which should also never change
    conv = run_scft.read_csv_col(in_path = param_scft_1["data_path"], col = param["conv_col"],
                data_lambda = lambda text: True if text == "True" else False, debug = debug)

    # get all guesses that converged with step 1
    conv_names = run_scft.find_true_names(bools = conv, names = names)

    # prepare for second SCFT pass
    # scft_2's in should be the same as scft_1's out, but decided to make separate param
    run_scft.prepare_files_second(in_path = param_scft_2["in_path"], dir_names = conv_names,
                                  out_path = param_scft_2["out_path"],
                param_path = param_scft_2["param"], command_path = param_scft_2["command"],
                run_path = param_scft_2["run"], debug = debug)

    print("FIX_W_BASIS (4.5)")
    # this uses the more advanced save_w_basis_dir() rather than the outdated fix_w_basis_dir()

    # fix w.bf files for second SCFT pass
    run_scft.save_w_basis_dir(in_dir = param_scft_2["out_path"], debug = debug)

# 6 (SCFT_2_TO_CSV)
if num == 5:
    print("SCFT_2_TO_CSV (5)")
    # combine data to CSV file
    run_scft.to_csv_num(dir_path = param_scft_2["out_path"], num_start = min, num_end = max,
                        output = param_scft_2["data_path"], debug = debug)
    
# 7 (SCFT_2_CONV)
# this code is from conv_helper.py
if num == 6:
    print("SCFT_2_CONV (6)")
    data = {
        "suc":  0, # all in group SUC
        "conv": 0, # SUC_CONV
        "fin":  0, # SUC_MAX_ITER and SUC_NO_CONV
        "iter": 0, # SUC_MAX_ITER
        "nocv": 0, # SUC_NO_CONV
        "warn": 0, # all in group WARN
        "log":  0, # WARN_NO_LOG
        "noit": 0, # WARN_NO_ITER
        "unf":  0, # WARN_NOT_FIN
        "err":  0  # ERR_NO_DIR
    }

    for d in sorted(Path(param_scft_2["out_path"]).iterdir(), key = lambda d: int(d.stem) if num else d):
        state = run_scft.calc_state(d.absolute(), debug = debug)

        match state:
            # group SUC
            case "SUC_CONV":
                data["suc"] += 1
                data["conv"] += 1 
            case "SUC_MAX_ITER":
                data["suc"] += 1
                data["fin"] += 1
                data["iter"] += 1
            case "SUC_NO_CONV":
                data["suc"] += 1
                data["fin"] += 1
                data["nocv"] += 1
            # group WARN
            case "WARN_NO_LOG":
                data["warn"] += 1
                data["log"] += 1
            case "WARN_NO_ITER":
                data["warn"] += 1
                data["noit"] += 1 
            case "WARN_NOT_FIN":
                data["warn"] += 1
                data["unf"] += 1 
            # group ERR
            case "ERR_NO_DIR":
                data["err"] += 1

    # SUC
    print(f"Finished (total):           {data['suc']}")
    print(f"Finished (converged):       {data["conv"]}")
    print(f"Finished (not converged):   {data["fin"]}")
    if param['detailed_conv']:
        print(f"Finished (max iterations):  {data['iter']}")
        print(f"Finished (no convergence):  {data['nocv']}")

    # WARN
    print(f"Unfinished (total):         {data['warn']}")
    if param['detailed_conv']:
        print(f"Unfinished (no log):        {data['log']}")
        print(f"Unfinished (no iterations): {data['noit']}")
        print(f"Unfinished (iterations):    {data['unf']}")

    # ERR
    print(f"Error (no directory):        {data['err']}")

# 8 (SCFT_2_TIME)
if num == 7:
    print("SCFT_2_TIME (7)")
    run_scft.review_csv_timings(param_scft_2["time_path"], sec_div = param_scft_2["sec_div"], debug = debug)

# 9 (UNIQUE_SOLN)
if num == 8:
    print("UNIQUE_SOLN (8)")
    data = run_scft.read_csv_col(param_scft_2["data_path"], "free_energy", lambda text: float(text), True)
    clusters = run_scft.find_neighbors(data = data, excluded_vals = [-1], const = 0, tol_debug = False, debug = debug)
    print("--- Original Clusters ---")
    print(clusters)

    sorted_clusters = run_scft.find_neighbors(data = sorted(data), excluded_vals = [-1], const = 0, tol_debug = False, debug = debug)
    print("--- Sorted Clusters ---")
    print(sorted_clusters)

    print(f"Number of clusters (original order): {len(clusters)}")
    print(f"Number of clusters (sorted order): {len(sorted_clusters)}")

# 10 (SCFT_1_CONV_OLD)
# this code is from conv_helper.py
# NOTE: this function is deprecated and will likely be removed in a later version of the code!!!
if num == 9:
    print("SCFT_1_CONV_OLD (9)")
    print("This function is deprecated and will likely be removed in a later version of the code!!!")
    iter = 0
    conv = 0
    i = 0
    neither = 0

    # should utilize run_scft's calc_state()
    with open(param_scft_1['data_path'], "r") as f:

        reader = csv.DictReader(f)
        for r in reader:
            #print(r['iterations'])
            if r['converged'] == "True":
                if debug:
                    print("CONV", r)
                i += 1
                conv += 1
            elif r['iterations'] == "2499":
                if debug:
                    print("ITER", r)
                i += 1
                iter += 1

            else:
                # assumed to not have converged and not have maxed iterations
                neither += 1
                if debug:
                    print("NEIT", r)

    print("Number CONV(erged):", conv)
    print("Number (fully) ITER(ated):", iter)
    print("Number CONV(erged)/(fully) ITER(ated):", i)
    print("Number NEIT(her)", neither)

# 7 (SCFT_2_CONV_OLD)
# this code is from conv_helper.py
# NOTE: this function is deprecated and will likely be removed in a later version of the code!!!
if num == 10:
    print("SCFT_2_CONV_OLD (10)")
    print("This function is deprecated and will likely be removed in a later version of the code!!!")
    iter = 0
    conv = 0
    i = 0
    neither = 0

    # should utilize run_scft's calc_state()
    with open(param_scft_2['data_path'], "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            #print(r['iterations'])
            if r['converged'] == "True":
                if debug:
                    print("CONV", r)
                i += 1
                conv += 1
            elif r['iterations'] == "2499":
                if debug:
                    print("ITER", r)
                i += 1
                iter += 1

            else:
                # assumed to not have converged and not have maxed iterations
                neither += 1
                if debug:
                    print("NEIT", r)

    print("Number CONV(erged):", conv)
    print("Number (fully) ITER(ated):", iter)
    print("Number CONV(erged)/(fully) ITER(ated):", i)
    print("Number NEIT(her)", neither)

if num == 11:
    print("FIX_W_BASIS_OLD (11)")
    print("This function is deprecated and will likely be removed in a later version of the code!!!")
    # get ignored names for fixing w.bf files
    ignored_names = run_scft.read_csv_col(in_path = param["ignored_path"], col = param["ignored_col"], debug = debug)

    # if the file doesn't exist, make it
    if ignored_names == False:
        # make sure to cast as a string to be safe
        print("Creating ignored name file at " + str(param["ignored_path"]) + "...")
        # create and write CSV header (name\n)
        with open(param["ignored_path"], "w") as f:
            f.write(str(param["ignored_col"]) + "\n")

        ignored_names = []

    # fix w.bf files for second SCFT pass
    # use out_path for both, as this should just replace the existing w.bf files
    run_scft.fix_w_basis_dir(in_path = param_scft_2["out_path"], ignored_names = ignored_names,
                            out_path = param_scft_2["out_path"], in_name = param["w_in_name"],
                            out_name = param["w_out_name"], write_fixed = param["write_fixed_w_basis"],
                            fixed_path = param["fixed_w_basis_path"], debug = debug)

print("Finished!")
