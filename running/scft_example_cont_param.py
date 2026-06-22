""" This file contains an example test program to run through the
entire SCFT process, from GAN-generated guesses to analyzing free energy values.
Unlike example.py, this program is able to resume where is stopped execution through
a file that holds an integer that is the current step."""

### LIST OF PARAMETERS
# step
# debug
# gan_path
# scft_1_path
# scft_1

# While some parameters may seem redundant, this program is intended to
# give users as much customizability as possible without touching this program's code.
# Despite this, custom modifications to the code could help repurpose parameters into real use.

import run_scft
# from pathlib import Path
import sys
import json

if len(sys.argv) > 1:
    print("Parameter file detected.")
    print("Attempting to read input file at", sys.argv[1], "for custom parameters.")
    with open(sys.argv[1], "r") as f:
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
if param['step'] == 0:
    print("--- Step", param['step'], "---")
    # prepare files
    run_scft.prepare_files(in_path = param_scft_1["in_path"], out_path = param_scft_1["out_path"],
                           out_name = param["rf_name"],
                param_path = param_scft_1["param"], command_path = param_scft_1["command"], run_path = param_scft_1["run"],
                debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 1
if param['step'] == 1:
    print("--- Step", param['step'], "---")
    # run SCFT for directories 1-250 in scft_1
    run_scft.execute_num(in_path = param_scft_1["in_path"], start = min, end = max,
                         adv_checking = param_scft_1["adv_checking"],
                        timing = param_scft_1["timing"], time_path = param_scft_1["time_path"],
                        debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 2
if param['step'] == 2:
    print("--- Step", param['step'], "---")
    # combine data to CSV file
    run_scft.to_csv_num(dir_path = param_scft_1["out_path"], num_start = min, num_end = max,
                        output = param_scft_1["data_path"], debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 3
if param['step'] == 3:
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

# step 4
if param['step'] == 4:
    print("--- Step", param['step'], "---")
    # get all guesses that converged with step 1
    conv_names = run_scft.find_true_names(bools = conv, names = names)
    inc_step(param, "step", True, sys.argv[1])

# step 5
if param['step'] == 5:
    print("--- Step", param['step'], "---")
    # prepare for second SCFT pass
    # scft_2's in should be the same as scft_1's out, but decided to make separate param
    run_scft.prepare_files_second(in_path = param_scft_2["in_path"], names = conv_names,
                                  out_path = param_scft_2["out_path"],
                param_path = param_scft_2["param"], command_path = param_scft_2["command"],
                run_path = param_scft_2["run"], debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 6
if param['step'] == 6:
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
if param['step'] == 7:
    print("--- Step", param['step'], "---")
    # execute PSCF - can still be done in numerical order as nonexistent
    # directories will just get skipped (though this will lead to a lot of printing)
    run_scft.execute_num(in_path = param_scft_2["out_path"], start = min, end = max,
                         adv_checking = param_scft_2["adv_checking"], timing = param_scft_2["timing"],
                         time_path = param_scft_2["time_path"], debug = debug)
    inc_step(param, "step", True, sys.argv[1])

# step 8
if param['step'] == 8:
    print("--- Step", param['step'], "---")
    # combine data to CSV file
    run_scft.to_csv_num(dir_path = param_scft_2["out_path"], num_start = min, num_end = max,
                        output = param_scft_2["data_path"], debug = debug)
    inc_step(param, "step", True, sys.argv[1])

print("Finished!")
