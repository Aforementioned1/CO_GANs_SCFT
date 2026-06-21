""" This file contains an example test program to run through the
entire SCFT process, from GAN-generated guesses to analyzing free energy values.
While it should be possible to resume where you left off after temporarily
stopping this program, scft_example_cont.py offers a more advanced control system
to completely prevent any issues caused upon restarting the program. """

import run_scft

# prepare files
run_scft.prepare_files(in_path = "gan_guesses", out_path = "scft_1", out_name = "rgrid.rf",
            param_path = "first/param", command_path = "first/command", run_path = "first/run",
            debug = True)

# run SCFT for directories 1-250 in scft_1
run_scft.execute_num(in_path = "scft_1", start = 1, end = 250, adv_checking = True,
            timing = True, time_path =  "data/scft_1_timings.csv", debug = True)

# combine data to CSV file
run_scft.to_csv_num("scft_1", 1, 250, "data/scft_1.csv", True)

# read names of each initial guess (should be 1-250) and whether they converged
names = run_scft.read_csv_col(in_path = "data/scft_1.csv", col = "name", debug = True)
# make sure to cast string boolean values as booleans - requires more complex logic
# as bool() method considers any non-empty str true
conv = run_scft.read_csv_col(in_path = "data/scft_1.csv", col = "converged",
            data_lambda = lambda text: True if text == "True" else False, debug = True)

# get all guesses that converged with step 1
conv_names = run_scft.find_true_names(bools = conv, names = names)

# prepare for second SCFT pass
run_scft.prepare_files_second(in_path = "scft_1", names = conv_names, out_path = "scft_2",
            param_path = "second/param", command_path = "second/command",
            run_path = "second/run", debug = True)

# get ignored names for fixing w.bf files
ignored_names = run_scft.read_csv_col(in_path = "data/ignored_names.csv", col = "name", debug = True)

# if the file doesn't exist, make it
if ignored_names == False:
    print("Creating ignored name file at data/ignored_names.csv...")
    # create and write CSV header (name\n)
    with open("data/ignored_names.csv", "w") as f:
        f.write("name\n")

    ignored_names = []

# fix w.bf files for second SCFT pass
run_scft.fix_w_basis_dir(in_path = "scft_2", ignored_names = ignored_names, 
                         out_path = "scft_2", in_name = "w.bf", out_name = "w.bf",
                         write_fixed = True, fixed_path = "data/ignored_names.csv",
                         debug = True)

# execute PSCF - can still be done in numerical order as nonexistent
# directories will just get skipped (though this will lead to a lot of printing)
run_scft.execute_num(in_path = "scft_2", start = 1, end = 250, adv_checking = True,
                     timing = True, time_path = "data/scft_2_timings.csv", debug = True)

# combine data to CSV file
run_scft.to_csv_num("scft_2", 1, 250, "data/scft_2.csv", True)
