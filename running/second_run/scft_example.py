""" This file contains an example test program to run through the
entire SCFT process, from GAN-generated guesses to analyzing free energy values.
This program requires a JSON parameter file to be passed in as a command line argument.
A sample parameter file is provided in defaults.json.\n
See README.md: SCFT Examples for information about the specifics of this program and
see JSON Parameters for information about what parameters are required by this program"""

######### CURRENTLY, THIS MUST BE RUN FROM .. (~/running) TO RESOLVE run_scft's IMPORT

# While some parameters may seem redundant, this program is intended to
# give users as much customizability as possible without touching this program's code.
# Despite this, custom modifications to the code could help repurpose parameters into real use.

import run_scft
# from pathlib import Path
import sys
import json
import argparse

parser = argparse.ArgumentParser()

step_choices = ["HELP", "PREP_SCFT_1", "SCFT_1_TO_CSV", "SCFT_1_CONV", "SCFT_1_TIME",
                "PREP_SCFT_2", "FIX_W_BASIS", "SCFT_2_TO_CSV", "SCFT_2_CONV",
                "PRINT_SCFT_2_TIME", "UNIQUE_SOLN"]
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
    print("HELP            -1         Print this informative display")
    print("PREP_SCFT_1     0          Prepare directories for GAN initial guesses so that they can be run through SCFT")
    print("SCFT_1_TO_CSV   1          Collect data from SCFT step 1 calculations and write it to a CSV file")
    print("SCFT_1_CONV     2          Print information regarding how many SCFT step 1 calculations converged")
    print("SCFT_1_TIME     3          Print information regarding how long SCFT step 1 calculations took")
    print("PREP_SCFT_2     4          Prepare directories for converged SCFT step 1 calculations so that they can be run through SCFT step 2")
    print("FIX_W_BASIS     5          Fix w.bf files outputted from SCFT step 1 in preparation for SCFT step 2")
    print("SCFT_2_TO_CSV   6          Collect data from SCFT step 2 calculations and write it to a CSV file")
    print("SCFT_2_CONV     7          Print information regarding how many SCFT step 2 calculations converged")
    print("SCFT_2_TIME     8          Print information regarding how long SCFT step 1 calculations took")
    print("UNIQUE_SOLN     9          Print information regarding how many converged solutions from SCFT step 2 can be considered unique")
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

        debug = param["debug"]

else:
    # end program if nothing is inputted
    print("No parameter file detected.")
    print("Ending program...")
    
    sys.exit()

# DEPRECATE THIS
def inc_step(param: dict, step_key: str, update_save: bool, path: str):
    """ Increments the integer parameter at step_key by one,
    then saves the new parameters to path if update_save == True\n
    param: A dict of parameter values, with an integer value at key step_key\n
    step_key: A string key that has an integer value in param\n
    update_save: Whether to save the updated parameters after incrementation\n
    path: The path to save the updated parameters to, if enabled """
    # increment step_key
    param[step_key] += 1

    # if enabled, save updated param to path
    if update_save:
        with open(path, "w") as f:
            json.dump(param, f, indent = 4)

# step 0
if num == 0:
    # print("--- Step", param['step'], "---")
    # prepare files
    run_scft.prepare_files(in_path = param_scft_1["in_path"], out_path = param_scft_1["out_path"],
                           out_name = param["rf_name"],
                param_path = param_scft_1["param"], command_path = param_scft_1["command"], run_path = param_scft_1["run"],
                debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 1
if num == 1:
    # print("--- Step", param['step'], "---")
    # run SCFT for directories 1-250 in scft_1
    run_scft.execute_num(in_path = param_scft_1["out_path"], start = min, end = max,
                         adv_checking = param_scft_1["adv_checking"],
                        timing = param_scft_1["timing"], clean_timing = True, time_path = param_scft_1["time_path"],
                        debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 2
if param['step'] == 2 and param['step'] != param['stop_step']:
    print("--- Step", param['step'], "---")
    # combine data to CSV file
    run_scft.to_csv_num(dir_path = param_scft_1["out_path"], num_start = min, num_end = max,
                        output = param_scft_1["data_path"], debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 3
if param['step'] == 3 and param['step'] != param['stop_step']:
    print("--- Step", param['step'], "---")
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
    inc_step(param, "step", True, sys.argv[1])

# step 4 - ELIMINATE
if param['step'] == 4 and param['step'] != param['stop_step']:
    print("--- Step", param['step'], "---")
    # get all guesses that converged with step 1
    conv_names = run_scft.find_true_names(bools = conv, names = names)
    inc_step(param, "step", True, sys.argv[1])

# step 5 - ELIMINATE
if param['step'] == 5 and param['step'] != param['stop_step']:
    print("--- Step", param['step'], "---")
    # prepare for second SCFT pass
    # scft_2's in should be the same as scft_1's out, but decided to make separate param
    run_scft.prepare_files_second(in_path = param_scft_2["in_path"], dir_names = conv_names,
                                  out_path = param_scft_2["out_path"],
                param_path = param_scft_2["param"], command_path = param_scft_2["command"],
                run_path = param_scft_2["run"], debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 6
if param['step'] == 6 and param['step'] != param['stop_step']:
    print("--- Step", param['step'], "---")
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
    inc_step(param, "step", True, sys.argv[1])

# step 7
if param['step'] == 7 and param['step'] != param['stop_step']:
    print("--- Step", param['step'], "---")
    # execute PSCF - can still be done in numerical order as nonexistent
    # directories will just get skipped (though this will lead to a lot of printing)
    run_scft.execute_num(in_path = param_scft_2["out_path"], start = min, end = max,
                         adv_checking = param_scft_2["adv_checking"], timing = param_scft_2["timing"], clean_timing = True,
                         time_path = param_scft_2["time_path"], debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 8
if param['step'] == 8 and param['step'] != param['stop_step']:
    print("--- Step", param['step'], "---")
    # combine data to CSV file
    run_scft.to_csv_num(dir_path = param_scft_2["out_path"], num_start = min, num_end = max,
                        output = param_scft_2["data_path"], debug = debug)
    inc_step(param, "step", True, sys.argv[1])

print("Finished!")
