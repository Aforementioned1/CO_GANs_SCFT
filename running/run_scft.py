""" This file contains functions related to preparing GAN outputs
for SCFT,running SCFT, and collecting the data from it """

import shutil
import os
import subprocess
import datetime
import csv
import json
from pathlib import Path
from enum import Enum
from itertools import repeat
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import colorsys

TRANSLATIONS = [("first_run", 1), ("second_run", 2), ("third_run", 3), ("fourth_run", 4), ("eighth_run", 8),
                ("ninth_run", 9), ("tenth_run", 10), ("eleventh_run", 11), ("twelfth_run", 12), ("thirteenth_run", 13)]


f_DG = 2.74517041186 # free energy of the double gyroid phase

max_iterations = 2500

# little enum for compare_groups(). Could be added to other functions maybe
OutputType = Enum("OutputType", "STDOUT_ONLY STDOUT_AND_FILE FILE_ONLY")

def print_output(output: str, output_type: OutputType, out_file: str):
    """Prints output to a location decided by the user using the OutputType enum.
    This function should always return True\n
    output: The text to output\n
    write_output: Where to put this output. Options are "STDOUT_ONLY",
    "STDOUT_AND_FILE", and "FILE_ONLY". Both file options will append text\n
    out_file: The path to write the text output of this function to, if output_type is
    STDOUT_ONLY or STDOUT_AND_FILE\n
    NOTE: This function automatically appends a new line character "\\n" to file outputs."""
    match output_type:
        case OutputType.STDOUT_ONLY:
            print(output)
        case OutputType.STDOUT_AND_FILE:
            print(output)
            with open(out_file, "a") as f:
                f.write(output + "\n")
        case OutputType.FILE_ONLY:
            with open(out_file, "a") as f:
                f.write(output + "\n")

    return True
    
def calc_state(in_path: str, log_name = "log", debug = False):
    """Returns (and prints if debug is enabled) some information about the state
    of a given SCFT calculation based on its log file. A list of possible outputs
    from this program is provided below. While this function is not yet
    widely used within this repository, there are many instances of similar code that
    could later be replaced.\n
    in_path: A directory with a log file to review."\n
    log_name: The name of the SCFT log file to review. Should almost always be "log".\n
    debug: Whether to print extra information for debugging\n
    Output codes are divided into three categories: Success (SUC), Warning (WARN) and Error (ERR).\n
    SUC is used for any SCFT calculations that successfully finished, regardless of convergence.\n
    WARN is used for any SCFT calculations that are partially finished or have not started.\n
    ERR is used for more serious problems (currently only if the directory at in_path does not exist).\n
    Each category's constituents begin with the category, followed by an underscore and any
    additional information. This allows for easier sorting of outputs, while still giving users
    the power to view more details about the state of the calculation. get_state_cat() provides
    a simple utility that runs this function and only returns the category of the output.\n
    List of all potential outputs:\n
    SUC_CONV: The SCFT calculation successfully converged\n
    SUC_MAX_ITER: The SCFT calculation reached the max amount of iterations without converging.
    This output takes precedence over SUC_NO_CONV, though any SUC_MAX_ITER should also meet the
    requirements for SUC_NO_CONV\n
    SUC_NO_CONV: The SCFT calculation did not converge. This is for a rare edge case in which
    an SCFT initial guess creates a tolerance value of "NaN", crashing SCFT.\n
    WARN_NO_LOG: The SCFT calculation has not log file and has therefore presumably not
    started running.\n
    WARN_NO_ITER: The SCFT log file has no recorded iterations\n
    WARN_NOT_FIN: The SCFT calculation has not finished running.
    WARN_NO_ITER takes precedence over this.\n
    ERR_NO_DIR: There is no directory at the path in_path"""

    in_dir = Path(in_path)

    if in_dir.exists() and in_dir.is_dir():
        # should only check if not converged and not at max iterations
        # if enabled, use the same process used in collect to find iterations and convergence
        # get text from log file for parsing
        log = in_dir / log_name

        if log.exists() and log.is_file():
            text = log.read_text()

            num = -1

            # get iteration number
            ind = text.rfind("Iteration  ")
            if ind != -1:
                ind += 11
                # read up to four digits
                # will never be 5, as current iteration limit is set to 2500
                # strip whitespace, then cast as int
                num = int(text[ind:ind+4].strip())
                if debug:
                    print("Highest iteration:",num)
            else:
                if debug:
                    print("No iterations found.")
                return "WARN_NO_ITER"
            
            # look for whether it converged
            converged = False
            ind = text.rfind("Converged")
            if ind != -1:
                converged = True
            
            if debug:
                print("Converged:", converged)

            # explicitly look for this to catch NaN issues
            unconv = False
            ind = text.rfind("Iterator failed to converge.")
            if ind != -1:
                unconv = True
            
            if debug:
                print("Not converged:", unconv)

            if converged:
                return "SUC_CONV"
            # do this later in case it converged on iteration #2500
            if num == max_iterations - 1:
                return "SUC_MAX_ITER"
            if unconv:
                return "SUC_NO_CONV"
            else:
                return "WARN_NOT_FIN"
        else:
            if debug:
                print(log_name, "log file does not exist or is not a file! Skipping...")
            return "WARN_NO_LOG"

    else:
        if debug:
            print(in_path, "does not exist or is not a directory! Skipping...")
        return "ERR_NO_DIR"

def get_state_cat(in_path: str, log_name = "log", debug = False):
    """Returns (and prints if debug is enabled) some categorical information about the
    state of a given SCFT calculation based on its log file. While this function is not yet
    widely used within this repository, there are many instances of similar code that
    could later be replaced. This function calls calc_state() with the provided parameters
    but only outputs the category ("SUC", "WARN" or "ERR") for easier string comparison.
    Some more detailed information about the categories is given below.\n
    in_path: A directory with a log file to review."\n
    log_name: The name of the SCFT log file to review. Should almost always be "log".\n
    debug: Whether to print extra information for debugging\n
    SUC is used for any SCFT calculations that successfully finished, regardless of convergence.\n
    WARN is used for any SCFT calculations that are partially finished or have not started.\n
    ERR is used for more serious problems (currently only if the directory at in_path does not exist).\n
    NULL is a special category exclusive to get_state_cat() that represents a problem that occured with
    calc_state() where no category could be found at the start of the string.\n
    For more detailed outputs, use calc_state()."""

    state = calc_state(in_path = in_path, log_name = log_name, debug = debug)

    if state.find("SUC") == 0:
        return "SUC"
    elif state.find("WARN") == 0:
        return "WARN"
    elif state.find("ERR") == 0:
        return "ERR"
    return "NULL"

def prepare_files(in_path: str, out_path: str, out_name: str,
                  param_path: str, command_path: str, run_path: str, debug = False,
                  in_name_lambda = lambda a: a.lstrip("guess_").rstrip(".rf")):
    """ Prepares inputs so that they can be easily run with execute.\n
        in_path: A path to a directory to copy .rf files from\n
        out_path: A path to a directory to copy the .rf files to
        and to prepare for PSCF in. Should not end in /\n
        out_name: The string used to rename all .rf files to (for easier execution).
        Defaults to rgrid.rf [ADDDDDDD]\n
        param_path: A path to the parameter file to use. Will be copied to out_path/name/param\n
        command_path: A path to the command file to use. Will be copied to out_path/name/command\n
        run_path: A path to run file to use. Will be copied to out_path/name/run\n
        in_name_lambda: A lambda to alter directory names.
        By default, removes leading "guess_" and trailing ".rf"\n
        debug: Whether to print extra information for debugging\n"""
    if debug:
        print("Debug mode ON for prepare_files")
        print("In path:", in_path)
        print("Out path:", out_path)
        print("Out name:", out_name)
        print("Param path:", param_path)
        print("Command path:", command_path)
        print("Run path:", run_path)

    dir_path = Path(in_path)
    if dir_path.is_dir():
        # find all files with a .rf extension in in_path
        extension = "*.rf"
        files = list(dir_path.glob(extension))

        for f in files:
            # prepare name with lambda
            name = in_name_lambda(f.name)

            if not Path(out_path + "/" + name + "/out").exists():
                
                if debug:
                    print("Pre-lambda name:", f.name)
                    print("Post-lambda name:", name)
                # make all directories to out_path/name/out (out must be included for later)
                os.makedirs(out_path + "/" + name + "/out")
                # copy the file to its target with predetermined name
                shutil.copy(str(f), out_path + "/" + name + "/" + out_name)
                # copy param file
                shutil.copy(param_path, out_path + "/"  + name + "/param")
                # copy command file
                shutil.copy(command_path, out_path + "/"  + name + "/command")
                # copy run file
                shutil.copy(run_path, out_path + "/"  + name + "/run")
                if debug:
                    print("Initialized", name, "directory")
            else:
                print(f"{f} already exists!")
    else:
        if debug:
            print(in_path, "does not exist or is not a directory! Skipping...")

def prepare_files_second(in_path: str, dir_names: list[str], out_path: str,
                  param_path: str, command_path: str, run_path: str,
                  sub_path = "out/w.bf", debug = False):
    """ Prepares inputs so that they can be easily run with execute.
        Unlike prepare_files(), this function is designed to be used to
        initialize the second pass of PSCF, so it takes some differing
        arguments and is structured slightly differently. As this code
        is more recent than prepare_files, it is slightly more straightforward.\n
        in_path: A path to a directory to copy PSCF outputs from. Should not end in /\n
        dir_names: A list of subdirectories within in_path to copy outputs from.
        Should not end in /\n
        out_path: A path to a directory to prepare new PSCF calculations in.
        Should not end in /\n
        param_path: A path to the parameter file to use. Will be copied to out_path/name/param\n
        command_path: A path to the command file to use. Will be copied to out_path/name/command\n
        run_path: A path to run file to use. Will be copied to out_path/name/run\n
        sub_path: A path within each PSCF directory to its output.
        The constructed path to copy will look like in_path/name/sub_path,
        where name is present in dir_names. Defaults to "out/w.bf"\n
        debug: Whether to print extra information for debugging\n
        NOTE: To fully prepare for second-step SCFT calculations, one must also use
        fix_w_basis() (or fix_w_basis_dir(), which can be used on initialized
        SCFT directories) to fix each w.bf file.
        """
    if len(dir_names) <= 0:
        print("Invalid list of allowed directory names found! Skipping...")
        return
    if debug:
        print("Debug mode ON for prepare_files_second")
        print("In path:", in_path)
        print("Allowed names:", dir_names)
        print("Sub-path:", sub_path)
        print("Example completed path:", (in_path + "/" + dir_names[0] + "/" + sub_path))
        print("Out path:", out_path)
        print("Param path:", param_path)
        print("Command path:", command_path)
        print("Run path:", run_path)

    ### TODO: make some of this naming make more sense!!!!!
    big_in_path = Path(in_path)
    big_out_path = Path(out_path)
    if big_in_path.is_dir():
        # find all directories located in in_path that have a name in dir_names
        for dir in dir_names:
            # make sure each name is a directory
            d = big_in_path / dir
            if d.exists() and d.is_dir():
                if debug:
                    print("Current:", dir)
                # make a Pathlib Path object to the current target directory
                this_path = big_out_path / dir
                # make all directories to out_path/name/out (out must be included for later)
                (this_path / "out").mkdir(parents = True, exist_ok = True)

                # get the text of this path to be used with shutil
                this_path_str = str(this_path)
                # copy the step 1 output file (in sub_path) to its target while keeping the name
                shutil.copy(str(d / sub_path), this_path_str)
                # copy param file
                shutil.copy(param_path, this_path_str)
                # copy command file
                shutil.copy(command_path, this_path_str)
                # copy run file
                shutil.copy(run_path, this_path_str)
                if debug:
                    print("Initialized", this_path_str, "directory")
            else:
                if debug:
                    print(d, "does not exist or is not a directory! Skipping...")
    else:
        if debug:
            print(in_path, "does not exist or is not a directory! Skipping...")

def fix_w_basis(in_path: str, out_path: str, debug = False):
    """ Fixes w.bf (W basis) files outputted from the first pass of SCFT,
        by:
            -changing the crystal system from orthorhombic to triclinic\n
            -chaning the number of cell parameters from 3 to 6\n
            -appending the 3 cell parameters 0, 0, and 1.5707963\n
            -limiting the amount of basis functions from 32768 to 17000\n
        See README.md: Second SCFT Step for more information on how to know if a
        w.bf file should be run through this function.\n
        in_path: A path to a properly structured w.bf file (see above)\n
        out_path: A path to output the fixed w.bf file to
        (this will often be the same as out_path)\n
        debug: Whether to print extra information for debugging\n"""
    if debug:
        print("Debug mode ON for fix_w_basis")
        print("In path:", in_path)
        print("Out path:", out_path)
    
    with open(in_path, "r") as f:
        # read as lines for easier processing
        lines = f.readlines()

    if debug:
        print("Initial line 5:", lines[4])
        print("Initial line 7:", lines[6])
        print("Initial line 9:", lines[8])
        print("Initial line 15:", lines[13])

    # change crystal_system to be triclinic
    lines[4] = lines[4].rstrip("orthorhombic\n") + "triclinic\n"

    # fix N_cell_param
    lines[6] = lines[6].rstrip("3\n") + "6\n"

    # fix cell_param
    lines[8] = lines[8].rstrip("\n") + "    0.000    0.000    1.5707963\n"

    lines[14] = lines[14].rstrip("32768\n") + "17000\n"

    if debug:
        print("Final line 5:", lines[4])
        print("Final line 7:", lines[6])
        print("Final line 9:", lines[8])
        print("Final line 15:", lines[13])

    with open(out_path, "w") as f:
        f.writelines(lines)

def save_w_basis(in_dir: str, names: list[str], sub_name = "w.bf", debug = False):
    """ Attempts to save w.bf (W basis) files that have been accidentally run through fix_w_basis()
        multiple times.\n
        in_dir: A path to a directory with subdirectories names to attempt to save\n
        names: A list of names to attempt to save
        sub_name: The name of w.bf file to look for. Defaults to "w.bf". An example
        full path would be in_dir / names[0] / sub_name\n
        debug: Whether to print extra information for debugging\n"""
    # if debug:
    #     print("Debug mode ON for fix_w_basis")
    #     print("In path:", in_path)
    #     print("Names:", names)

    in_path = Path(in_dir)

    for n in names:
        with open((in_path / n / sub_name).absolute(), "r") as f:
            # read as lines for easier processing
            lines = f.readlines()

        if debug:
            print("Initial line 5:", lines[4])
            print("Initial line 7:", lines[6])
            print("Initial line 9:", lines[8])
            print("Initial line 15:", lines[13])

        # can always make it triclinic
        lines[4] = "              triclinic\n"

        # can always fix N_cell_param
        lines[6] = "              6\n"

        # fix cell_param - this one is trickier
        lines[8] = lines[8].rstrip("\n")
        while lines[8].rfind("    0.000    0.000    1.5707963") != -1:
            lines[8] = lines[8].removesuffix("    0.000    0.000    1.5707963")

        lines[8] + "    0.000    0.000    1.5707963\n"

        # can always make it 17000
        lines[14] = "             17000\n"

        if debug:
            print("Final line 5:", lines[4])
            print("Final line 7:", lines[6])
            print("Final line 9:", lines[8])
            print("Final line 15:", lines[13])

        with open((in_path / n / sub_name).absolute(), "w") as f:
            f.writelines(lines)

def add_return(in_dir: str, names: list[str], sub_name = "w.bf", debug = False):
    """ Attempts to save w.bf (W basis) files that have been accidentally run through fix_w_basis()
        multiple times.\n
        in_dir: A path to a directory with subdirectories names to attempt to save\n
        names: A list of names to attempt to save
        sub_name: The name of w.bf file to look for. Defaults to "w.bf". An example
        full path would be in_dir / names[0] / sub_name\n
        debug: Whether to print extra information for debugging\n"""
    # if debug:
    #     print("Debug mode ON for fix_w_basis")
    #     print("In path:", in_path)
    #     print("Names:", names)

    in_path = Path(in_dir)

    for n in names:
        with open((in_path / n / sub_name).absolute(), "r") as f:
            # read as lines for easier processing
            lines = f.readlines()

        if debug:
            print("Initial line 5:", lines[4])
            print("Initial line 7:", lines[6])
            print("Initial line 9:", lines[8])
            print("Initial line 15:", lines[13])

        lines[4] += "\n"

        lines[6] += "\n"

        lines[8] += "\n"

        lines[14] = "\n"

        if debug:
            print("Final line 5:", lines[4])
            print("Final line 7:", lines[6])
            print("Final line 9:", lines[8])
            print("Final line 15:", lines[13])

        with open((in_path / n / sub_name).absolute(), "w") as f:
            f.writelines(lines)

def fix_w_basis_dir(in_path: str, ignored_names: list[str], out_path: str,
                    in_name: str, out_name: str, write_fixed = False,
                    fixed_path = "fixed.csv", debug = False):
    """ Fixes several w.bf (W basis) files outputted from the first pass of SCFT,
        by:
            -changing the crystal system from orthorhombic to triclinic\n
            -chaning the number of cell parameters from 3 to 6\n
            -appending the 3 cell parameters 0, 0, and 1.5707963\n
            -limiting the amount of basis functions from 32768 to 17000\n
        See README.md: Second SCFT Step for more information on how to know if a
        w.bf file should be run through this function. Unlike fix_w_basis(),
        this function allows for the fixing of several w.bf files within initialized
        SCFT directories.\n
        in_path: A path to a directory containing initialized SCFT subdirectories\n
        ignored_names: A list of string names to skip running. This feature
        can be used to prevent fixing the same file twice, as this will cause
        the file to have the extra text appended twice\n
        out_path: A path to a directory to output the fixed w.bf files to,
        while preserving each w.bf's corresponding parent directory.
        This should almost always be the same as in_path.\n
        in_name: The sub-path to be used to locate w.bf files within each subdirectory.
        Full paths will look like in_path/dir_name/in_name, where dir_name is a directory
        within in_path that is not present in ignored_names.\n
        out_name: The sub-path to be used to output w.bf files within each subdirectory to.
        Full paths will look like out_path/dir_name/out_name, where dir_name is a directory
        within in_path that is not present in ignored_names.\n
        write_fixed: Whether to write the names of each directory that was fixed to a file.
        This can later be read with read_csv_col and used as the ignored_names parameter.\n
        fixed_path: The path to write the names of each directory that was fixed to.
        Defaults to "fixed.csv". This parameter will not be used if write_fixed == False.
        This function currently does not write the CSV header ("names") to the file,
        so this must be done manually for now.
        debug: Whether to print extra information for debugging\n"""
    if debug:
        print("Debug mode ON for fix_w_basis")
        print("In path:", in_path)
        print("Ignored names:", ignored_names)
        print("Out path:", out_path)
        print("In name:", in_name)
        print("Out name:", out_name)
        print("Write fixed:", write_fixed)
        print("Write target:", fixed_path)

    fixed_list = []
    
    dir_path = Path(in_path)
    out = Path(out_path)
    if dir_path.is_dir():
        # find all directories located in in_path that have a name in dir_names
        for dir in dir_path.iterdir():
            # skip if ignored
            if dir.name in ignored_names:
                if debug:
                    print(dir.name, "is ignored! Skipping...")
            else:
                # make sure each name is a directory
                if dir.exists() and dir.is_dir():
                    if debug:
                        print("Current:", dir)
                    # make a Pathlib Path object to the current target directory
                    temp_out = out / dir.name
                    # make all directories to out_path/dir
                    temp_out.mkdir(parents = True, exist_ok = True)

                    # if debug:
                    #     print("In temp:", (dir / file_name))
                    #     print("Out temp:", (temp_out / file_name))

                    fix_w_basis(str(dir / in_name), str(temp_out / out_name))
                    
                    fixed_list.append(dir.name)

                    if debug:
                        print("Fixed", (dir / in_name), "to", (temp_out / out_name))
                else:
                    if debug:
                        print(dir, "does not exist or is not a directory! Skipping...")
    else:
        if debug:
            print(in_path, "does not exist or is not a directory! Skipping...")

    if (write_fixed):
        # add each name with linebreak
        text = ""
        for n in fixed_list:
            text += n + "\n"
        
        # append to file to preserve any names already there
        with open(fixed_path, 'a') as f:
            f.write(text)

    return fixed_list

def run(entry: Path, timing = False, debug = False):
    """ Executes the run file for the provided entry.\n
        entry: A Pathlib Path object to the directory containing a run file (named "run")\n
        timing: Whether the information about the time it took for
        the script to run should be printed)\n
        debug: Whether to print extra information for debugging\n
        Note: Will always return a dict of entry's name and
        timing information, regardless of whether timing is true"""
    start_time = datetime.datetime.now()

    run_path = entry / "run"
    if not run_path.exists() or not run_path.is_file():
        if debug:
            print("No run file found. Skipping...")
        time_dict = {"name":    entry.name,
                    "start":   0,
                    "end":     0,
                    "elapsed": 0} 
        return time_dict

    if debug:
        print(entry.name, "started!")
        print("Path: " + str(entry))
        # print((entry / "log").exists())

    result = subprocess.run(["./run"], shell=True,cwd=str(entry), text=True)
    if debug:
        print("Stdout: " + str(result.stdout))
        print(entry.name, "finished!")
    
    end_time = datetime.datetime.now()

    time_dict = {"name":    entry.name,
                 "start":   start_time,
                 "end":     end_time,
                 "elapsed": end_time - start_time}
    if timing:
        print("--- Timing Info ---")
        print("Start time:", start_time)
        print("End time:", end_time)
        print("Elapsed time:", time_dict['elapsed'])
    
    return time_dict

def execute_dir(in_path: str, adv_checking = True, timing = False, clean_timing = False, time_path = "timings.csv", debug = False):
    """ Executes the run script for every valid directory in in_path.\n
        in_path: A path to a directory with properly initialized subdirectories,
        as per the format specified in prepare_files\n
        adv_checking: Whether advanced checking should be used on subdirectories already
        containing a "log" final to find partially-completed calculations. This is recommended,
        but may be slightly slower (especially if many completed calculations are present in in_path)\n
        timing: Whether timing information should be printed and saved to time_path\n
        clean_timing: Whether to exclude certain timing values to attempt to "clean" it, if timing is True\n
        time_path: Where to write timing data to, if timing is True\n
        debug: Whether to print extra information for debugging"""
    if debug:
        print("Debug mode ON for execute_dir")
        print("In path:", in_path)
        print("Advanced checking:", adv_checking)
        print("Timing:", timing)
        print("Clean timing:", clean_timing)
        print("Time path:", time_path)

    # if timing is enabled, override time_path and write CSV headers
    col = ['name', 'start', 'end', 'elapsed']
    if timing:
        time = Path(time_path)

        # only write header if time_path does not exist yet
        if not time.exists():
            if debug:
                print("Creating timing file at", time_path)
            # create and write CSV header
            time.touch()

            with open(time_path, "w") as f:
                writer = csv.DictWriter(f, fieldnames=col)
                writer.writeheader()

    dir_path = Path(in_path)

    if dir_path.is_dir():
        # run on every directory in in_path
        for entry in sorted(dir_path.iterdir()):
            if entry.is_dir():
                time_data = {}
                add_time = timing
                if debug:
                    print("Current entry:", entry.name)
                    
                # if log does not exist, it's safe to assume that this has not been run
                if not (entry / "log").exists():
                    time_data = run(entry, timing, debug)
                # if log exists, go to convergence/iteration checking if enabled
                else:
                    if adv_checking:
                        # should only check if not converged and not at max iterations
                        # if enabled, use the same process used in collect to find iterations and convergence
                        if debug:
                            print("Going to advanced checking!")
                        # get text from log file for parsing
                        log = Path(in_path) / entry.name / "log"
                        text = log.read_text()

                        num = -1

                        # get iteration number
                        ind = text.rfind("Iteration  ")
                        if ind != -1:
                            ind += 11
                            # read up to four digits
                            # will never be 5, as current iteration limit is set to 2500
                            # strip whitespace, then cast as int
                            num = int(text[ind:ind+4].strip())
                            if debug:
                                print("Highest iteration:",num)
                        
                        # look for whether it converged
                        converged = False
                        ind = text.rfind("Converged")
                        if ind != -1:
                            converged = True
                        
                        should_check = (num != max_iterations - 1) and (not converged)
                        
                        if debug:
                            print("Converged:", converged)
                            print("Should check:", should_check)
                        
                        if should_check:
                            time_data = run(entry, timing, debug)
                        else:
                            add_time = timing and not clean_timing
                            time_data = {"name":    entry.name,
                                         "start":   0,
                                         "end":     0,
                                         "elapsed": 0}
                    else:
                        if debug:
                            print("Advanced checking is disabled. Skipping...")
                        add_time = timing and not clean_timing
                        time_data = {"name":    entry.name,
                                     "start":   0,
                                     "end":     0,
                                     "elapsed": 0}
                
                # use this to allow for bad data exclusion
                if add_time:
                    with open(time_path, "a") as f:
                        writer = csv.DictWriter(f, fieldnames=col)
                        # write CSV data
                        writer.writerow(time_data)
            else:
                if debug:
                    print(entry, "does not exist or is not a directory! Skipping...")
    else:
        if debug:
            print(in_path, "does not exist or is not a directory! Skipping...")

def execute_num(in_path: str, start: int, end: int, adv_checking = True, timing = False, clean_timing = False, time_path = "timings.csv", debug = False):
    """ Executes the run script for every valid directory in in_path that falls between start and end, inclusive.\n
        in_path: A path to a directory with properly initialized subdirectories with numerical names,
        as per the format specified in prepare_files\n
        start: The number to start at\n
        end: The number to end at\n
        adv_checking: Whether advanced checking should be used on subdirectories already
        containing a "log" final to find partially-completed calculations. This is recommended,
        but may be slightly slower (especially if many completed calculations are present in in_path)\n
        timing: Whether timing information should be printed and saved to time_path\n
        clean_timing: Whether to exclude certain timing values to attempt to "clean" it, if timing is True\n
        time_path: Where to write timing data to, if timing is True\n
        debug: Whether to print extra information for debugging"""
    if debug:
        print("Debug mode ON for execute_num")
        print("In path:", in_path)
        print("Start:", start)
        print("End:", end)
        print("Advanced checking:", adv_checking)
        print("Timing:", timing)
        print("Clean timing:", clean_timing)
        print("Time path:", time_path)

    # if timing is enabled, override time_path and write CSV headers
    col = ['name', 'start', 'end', 'elapsed']
    if timing:
        time = Path(time_path)

        # make sure that the parent directories exists
        time.parent.mkdir(parents = True, exist_ok = True)

        # only write header if time_path does not exist yet
        if not time.exists():
            if debug:
                print("Creating timing file at", time_path)
            # create and write CSV header
            time.touch()

            with open(time_path, "w") as f:
                writer = csv.DictWriter(f, fieldnames=col)
                writer.writeheader()
        # with open(time_path, "w") as f:
        #     writer = csv.DictWriter(f, fieldnames=col)
        #     writer.writeheader()

    dir_path = Path(in_path)

    if dir_path.is_dir():
        # run on every directory in in_path
        for i in range(start, end + 1):
            entry = dir_path / str(i)
            if entry.is_dir():
                time_data = {}
                add_time = timing
                if debug:
                    print("Current entry:", entry.name)
                    
                # if log does not exist, it's safe to assume that this has not been run
                if not (entry / "log").exists():
                    time_data = run(entry, timing, debug)
                # if log exists, go to convergence/iteration checking if enabled
                else:
                    if adv_checking:
                        # should only check if not converged and not at max iterations
                        # if enabled, use the same process used in collect to find iterations and convergence
                        if debug:
                            print("Going to advanced checking!")
                        # get text from log file for parsing
                        log = Path(in_path) / entry.name / "log"
                        text = log.read_text()

                        num = -1

                        # get iteration number
                        ind = text.rfind("Iteration  ")
                        if ind != -1:
                            ind += 11
                            # read up to four digits
                            # will never be 5, as current iteration limit is set to 2500
                            # strip whitespace, then cast as int
                            num = int(text[ind:ind+4].strip())
                            if debug:
                                print("Highest iteration:",num)
                        
                        # look for whether it converged
                        converged = False
                        ind = text.rfind("Converged")
                        if ind != -1:
                            converged = True
                        
                        should_check = (num != max_iterations - 1) and (not converged)
                        
                        if debug:
                            print("Converged:", converged)
                            print("Should check:", should_check)
                        
                        if should_check:
                            time_data = run(entry, timing, debug)
                        else:
                            # ignore if clean_timing is True
                            add_time = timing and not clean_timing
                            time_data = {"name":    entry.name,
                                         "start":   0,
                                         "end":     0,
                                         "elapsed": 0}
                    else:
                        if debug:
                            print("Advanced checking is disabled. Skipping...")
                        # ignore if clean_timing is True
                        add_time = timing and not clean_timing
                        time_data = {"name":    entry.name,
                                     "start":   0,
                                     "end":     0,
                                     "elapsed": 0}
                
                # use this to allow for bad data exclusion
                if add_time:
                    with open(time_path, "a") as f:
                        writer = csv.DictWriter(f, fieldnames=col)
                        # write CSV data
                        writer.writerow(time_data)
            else:
                if debug:
                    print(entry, "does not exist or is not a directory! Skipping...")
    else:
        if debug:
            print(in_path, "does not exist or is not a directory! Skipping...")

def execute(in_path: str, adv_checking = True, timing = False, clean_timing = False, time_path = "timings.csv", debug = False):
    """ Executes the run script for a single valid directory at in_path. Unlike run(), this
        program provides the same additional functionalities as execute_dir() and execute_num()
        while still only running one file.\n
        in_path: A path to a directory with a proper script file named "run"\n
        adv_checking: Whether advanced checking should be used in the case that in_path already
        contains a "log" final to find partially-completed calculations. This is recommended,
        but may be slightly slower.\n
        timing: Whether timing information should be printed and saved to time_path\n
        clean_timing: Whether to exclude certain timing values to attempt to "clean" it, if timing is True\n
        time_path: Where to write timing data to, if timing is True\n
        debug: Whether to print extra information for debugging"""
    if debug:
        print("Debug mode ON for execute_num")
        print("In path:", in_path)
        print("Advanced checking:", adv_checking)
        print("Timing:", timing)
        print("Clean timing:", clean_timing)
        print("Time path:", time_path)

    # if timing is enabled, override time_path and write CSV headers
    col = ['name', 'start', 'end', 'elapsed']
    if timing:
        time = Path(time_path)

        # make sure that the parent directories exists
        time.parent.mkdir(parents = True, exist_ok = True)

        # only write header if time_path does not exist yet
        if not time.exists():
            if debug:
                print("Creating timing file at", time_path)
            # create and write CSV header
            time.touch()

            with open(time_path, "w") as f:
                writer = csv.DictWriter(f, fieldnames=col)
                writer.writeheader()
    # run on in_path
    entry = Path(in_path)
    if entry.is_dir():
        time_data = {}
        add_time = timing
        if debug:
            print("Current entry:", entry.name)
            
        # if log does not exist, it's safe to assume that this has not been run
        if not (entry / "log").exists():
            time_data = run(entry, timing, debug)
        # if log exists, go to convergence/iteration checking if enabled
        else:
            if adv_checking:
                # should only check if not converged and not at max iterations
                # if enabled, use the same process used in collect to find iterations and convergence
                if debug:
                    print("Going to advanced checking!")
                # get text from log file for parsing
                # log = Path(in_path) / entry.name / "log"
                log = entry / "log"
                text = log.read_text()

                num = -1

                # get iteration number
                ind = text.rfind("Iteration  ")
                if ind != -1:
                    ind += 11
                    # read up to four digits
                    # will never be 5, as current iteration limit is set to 2500
                    # strip whitespace, then cast as int
                    num = int(text[ind:ind+4].strip())
                    if debug:
                        print("Highest iteration:",num)
                
                # look for whether it converged
                converged = False
                ind = text.rfind("Converged")
                if ind != -1:
                    converged = True
                
                should_check = (num != max_iterations - 1) and (not converged)
                
                if debug:
                    print("Converged:", converged)
                    print("Should check:", should_check)
                
                if should_check:
                    time_data = run(entry, timing, debug)
                else:
                    # ignore if clean_timing is True
                    add_time = timing and not clean_timing
                    time_data = {"name":    entry.name,
                                    "start":   0,
                                    "end":     0,
                                    "elapsed": 0}
            else:
                if debug:
                    print("Advanced checking is disabled. Skipping...")
                # ignore if clean_timing is True
                add_time = timing and not clean_timing
                time_data = {"name":    entry.name,
                                "start":   0,
                                "end":     0,
                                "elapsed": 0}
        
        # use this to allow for bad data exclusion
        if add_time:
            with open(time_path, "a") as f:
                writer = csv.DictWriter(f, fieldnames=col)
                # write CSV data
                writer.writerow(time_data)
    else:
        if debug:
            print(entry, "does not exist or is not a directory! Skipping...")

def to_csv(dir_path: str, output: str, debug = False):
    """ Reads name, log, iteration, convergence, and free_energy
    information for all existing directories within dir_path in alphanumeric order
    and writes to output in CSV format.\n
    dir_path: A path to a directory with subdirectories containing log files to read from\n
    output: A path to a file to write to\n
    debug: Whether to print extra information for debugging\n
    Note: if you are using numerical directory names (1, 2, 3...) and want them to be
    in numerical order, use to_csv_num. """
    path = Path(dir_path)
    data = []
    # CSV header
    col = ['name', 'log_exists', 'iterations', 'converged', 'free_energy']
    # number that converged
    num_conv = 0
    # number that have any iterations
    num_it = 0

    # alphanumerically sort all directories
    for entry in sorted(path.iterdir()):
        if entry.is_dir():
            temp_data = {}
            temp_data['name'] = entry.name

            # find log file
            log = entry / "log"
            if log.is_file():
                temp_data['log_exists'] = True

                if debug:
                    print(dir_path + "/" + entry.name)
                text = log.read_text()
                ind = text.rfind("Iteration  ")
                if ind != -1:
                    ind += 11
                    # read up to four digits
                    # will never be 5, as current iteration limit is set to 2500
                    # strip whitespace, then cast as int
                    num = int(text[ind:ind+4].strip())
                    temp_data['iterations'] = num
                    num_it += 1
                    print(num)
                else:
                    temp_data['iterations'] = -1
                
                # look for whether it converged
                converged = False
                ind = text.rfind("Converged")
                if ind != -1:
                    converged = True
                    num_conv += 1
                temp_data['converged'] = converged
                print(converged)

                ind = text.find("fHelmholtz")
                if ind != -1:
                    # each file seems to contain 5 spaces after fHelmholtz
                    ind += 15
                    free_text = text[ind:]
                    # read until newline
                    end = free_text.find("\n")
                    # strip whitespace to be safe
                    num = float(free_text[:end + 1].strip())
                    temp_data['free_energy'] = num
                else:
                    temp_data['free_energy'] = -1
            # if log file doesn't exist, set all data to defaults
            else:
                temp_data['log_exists'] = False
                temp_data['iterations'] = -1
                temp_data['converged'] = False
                temp_data['free_energy'] = -1

            # add dict of data to bigger list
            data.append(temp_data)
    if debug:
        print("Amount with iterations:", num_it)
        print("Amount converged:", num_conv)
        print("Percent convergence:", (num_conv / num_it))

    # make sure that the parent directories exists
    Path(output).parent.mkdir(parents = True, exist_ok = True)
    with open(output, "w") as f:
        writer = csv.DictWriter(f, fieldnames=col)
        # write CSV header
        writer.writeheader()
        # write CSV data
        writer.writerows(data)

def to_csv_num(dir_path: str, num_start: int, num_end: int, output: str, debug = False):
    """ Reads name, log, iteration, convergence, and free_energy
    information for directories named between num_start and num_end, inclusive,
    within dir_path in numerical order and writes to output in CSV format.\n
    dir_path: A path to a directory with subdirectories containing log files to read from\n
    num_start: The number to start at\n
    num_end: The number to end at\n
    output: A path to a file to write to\n
    debug: Whether to print extra information for debugging\n
    Note: if you are using alphanumeric directory names or want your data to be
    in alphanumeric order, use to_csv. """
    path = Path(dir_path)
    data = []
    # CSV header
    col = ['name', 'log_exists', 'iterations', 'converged', 'free_energy']
    # number that converged
    num_conv = 0
    # number that have any iterations
    num_it = 0

    # go through all directories from num_start to num_end, inclusive
    for i in range(num_start, num_end + 1):
        entry = path / str(i)
        if entry.is_dir():
            temp_data = {}
            temp_data['name'] = entry.name

            # find log file
            log = entry / "log"
            if log.is_file():
                temp_data['log_exists'] = True

                if debug:
                    print(dir_path + "/" + entry.name)
                text = log.read_text()
                ind = text.rfind("Iteration  ")
                if ind != -1:
                    ind += 11
                    # read up to four digits
                    # will never be 5, as current iteration limit is set to 2500
                    # strip whitespace, then cast as int
                    num = int(text[ind:ind+4].strip())
                    temp_data['iterations'] = num
                    num_it += 1
                    if debug:
                        print(num)
                else:
                    temp_data['iterations'] = -1
                    
                
                # look for whether it converged
                converged = False
                ind = text.rfind("Converged")
                if ind != -1:
                    converged = True
                    num_conv += 1
                temp_data['converged'] = converged
                if debug:
                    print(converged)

                ind = text.find("fHelmholtz")
                if ind != -1:
                    # each file seems to contain 5 spaces after fHelmholtz
                    ind += 15
                    free_text = text[ind:]
                    # read until newline
                    end = free_text.find("\n")
                    # strip whitespace to be safe
                    num = float(free_text[:end + 1].strip())
                    temp_data['free_energy'] = num
                else:
                    temp_data['free_energy'] = -1
            # if log file doesn't exist, set all data to defaults
            else:
                temp_data['log_exists'] = False
                temp_data['iterations'] = -1
                temp_data['converged'] = False
                temp_data['free_energy'] = -1

            # add dict of data to bigger list
            data.append(temp_data)
    if debug:
        print("Amount with iterations:", num_it)
        print("Amount converged:", num_conv)
        print("Percent convergence:", (num_conv / num_it))

    with open(output, "w") as f:
        writer = csv.DictWriter(f, fieldnames=col)
        # write CSV header
        writer.writeheader()
        # write CSV data
        writer.writerows(data)

def is_close(item_1: float, item_2: float, epsilon: float, debug = False):
    """ Determines whether two floats are close enough
    to each other within a specified tolerance. Returns true if
    abs(item_2 - item_1) < epsilon, and false otherwise.\n
    item_1: The first item to compare\n
    item_2: The second item to compare\n
    epsilon: The allowed tolerance/difference between item_1 and item_2\n
    debug: Whether to print extra information for debugging"""
    val = abs(item_2 - item_1) < epsilon
    if debug:
        print("----- Tol Checker -----")
        print("Item 1:", item_1)
        print("Item 2:", item_2)
        print("Epsilon:", epsilon)
        print("Difference:", (item_2 - item_1))
        print("Result:", val)
    return val

def find_neighbors(data: list[float], epsilon = 0.00001, excluded_vals = [],
                   tol_debug = False, const = f_DG, debug = False):
    """ Finds all "clusters" within a list that fall near each other.
    Returns a dict with "candidate" values as keys and how many
    data points fall into each candidate as values\n
    data: A list of floats to classify\n
    epsilon: The allowed tolerance/difference for each cluster. Defaults to 0.00001 (10^-5)\n
    excluded_vals: A list of values to ignore for forming clusters. Entries near it will be skipped.
    This can be used to help filter out bad/empty data values (such as free energies of -1.0)\n
    tol_debug: Whether to print extra information regarding tolerance calculations for debugging.
    Note that this will print several lines for every entry in data\n
    const: A constant that is subtracted from every value. This can be used
    to compare the relative free energies of structures. Defaults to f_DG,
    the free energy of the double gyroid phase.\n
    debug: Whether to print extra information for debugging. Defaults to False\n
    NOTE: Results may vary based on how the data is sorted.
    This function reads in the order of the provided list."""
    if debug:
        print("Debug mode ON for find_neighbors")
        print("Raw data:", data)
        print("Epsilon:", epsilon)
        print("Excluded values:", excluded_vals)
        print("Debug for tolerance calculations:", tol_debug)

    cands = []
    nums = {}
    for i in data:
        i -= const
        found_cand = False
        if tol_debug:
                print("Searching for exclusions...")
        for j in excluded_vals:
            if is_close(i, j, epsilon, tol_debug):
                # print on debug bc it's more important info
                if debug:
                    print("Found exclusion: " + str(j) + "!")
                # if it should be excluded, skip the rest of the search
                found_cand = True
                break
        # don't start searching if it should be excluded
        if not found_cand:
            if tol_debug:
                print("Searching for candidates...")
            for j in cands:
                if is_close(i, j, epsilon, tol_debug):
                    # print on debug bc it's more important info
                    if debug:
                        print("Found candidate: " + str(j) + "!")
                    found_cand = True
                    if j in nums:
                        nums[j] += 1
                    else:
                        # maybe should be 2
                        nums[j] = 2
                    # you can assume that something can never match two candidates
                    break
        if not found_cand:
            if debug:
                print("No candidate or exclusion found. Creating new candidate:", i)
            cands.append(i)
            nums[i] = 1
    if debug:
        print("Candidates:", cands)
        print("Numbers:", nums)

    return nums

def find_neighbors_list(data: list[float], names: list[str], epsilon = 0.00001,
                        excluded_vals = [], tol_debug = False, const = f_DG, debug = False):
    """ Finds all "clusters" within a list that fall near each other.
    Returns a dict with "candidate" values as keys and a list of the
    names of each datapoint that falls within the candidate.\n
    data: A list of floats to classify\n
    names: A list of names to associate with data\n
    epsilon: The allowed tolerance/difference for each cluster. Defaults to 0.00001 (10^-5)\n
    excluded_vals: A list of values to ignore for forming clusters, entries near it will be skipped.
    This can be used to help filter out bad/empty data values (such as free energies of -1.0)\n
    tol_debug: Whether to print extra information regarding tolerance calculations for debugging.
    Note that this will print several lines for every entry in data\n
    const: A constant that is subtracted from every value. This can be used
    to compare the relative free energies of structures. Defaults to f_DG,
    the free energy of the double gyroid phase.\n
    debug: Whether to print extra information for debugging. Defaults to False\n
    NOTE: Results may vary based on how the data is sorted.
    This function reads in the order of the provided list."""
    if debug:
        print("Debug mode ON for find_neighbors")
        print("Raw data:", data)
        print("Epsilon:", epsilon)
        print("Excluded values:", excluded_vals)
        print("Debug for tolerance calculations:", tol_debug)

    cands = []
    nums = {}
    for i in data:
        i -= const
        found_cand = False
        if tol_debug:
                print("Searching for exclusions...")
        for j in excluded_vals:
            if is_close(i, j, epsilon, tol_debug):
                # print on debug bc it's more important info
                if debug:
                    print("Found exclusion: " + str(j) + "!")
                # if it should be excluded, skip the rest of the search
                found_cand = True
                break
        # don't start searching if it should be excluded
        if not found_cand:
            if tol_debug:
                print("Searching for candidates...")
            for j in cands:
                if is_close(i, j, epsilon, tol_debug):
                    # print on debug bc it's more important info
                    if debug:
                        print("Found candidate: " + str(j) + "!")
                    found_cand = True
                    if j in nums:
                        name = names[data.index(i)]
                        nums[j].append(name)
                    else:
                        # maybe should be 2
                        # NOTE: this could throw a ValueError
                        nums[j] = [names[data.index(j)]]
                        name = names[data.index(i)]
                        nums[j].append(name)
                    # you can assume that something can never match two candidates
                    break
        if not found_cand:
            if debug:
                print("No candidate or exclusion found. Creating new candidate:", i)
            cands.append(i)
            nums[i] = [names[data.index(i)]]
    if debug:
        print("Candidates:", cands)
        print("Name data:", nums)

    return nums

# def make_histogram(data: list[float], out_path: str, figsize = (6, 4), dpi = 500, bins = 500):
#     """ Reads from a CSV file, and returns a list of all values in col\n
#         in_path: A path to a CSV file with a column named "free_energy"\n
#         col: A CSV column present in in_path to read\n
#         data_lambda: A lambda to be applied to each data value that is read.
#         This can be used to convert the values read (which are strings by default)
#         to int, float, or other data types. By default, returns itself (does nothing)\n
#         debug: Whether to print extra information for debugging\n
#         NOTE: This method will return a list of strings by default,
#         but you may use the data_lambda parameter to modify the data (including data type)."""

def read_csv_col(in_path: str, col: str, data_lambda = lambda text: text, debug = False):
    """ Reads from a CSV file, and returns a list of all values in col\n
        in_path: A path to a CSV file with a column named "free_energy"\n
        col: A CSV column present in in_path to read\n
        data_lambda: A lambda to be applied to each data value that is read.
        This can be used to convert the values read (which are strings by default)
        to int, float, or other data types. By default, returns itself (does nothing)\n
        debug: Whether to print extra information for debugging\n
        NOTE: This method will return a list of strings by default,
        but you may use the data_lambda parameter to modify the data (including data type)."""
    if debug:
        print("Debug mode ON for read_csv_col")
        print("In path:", in_path)
        print("Col:", col)

    # check that a file at in_path exists
    file = Path(in_path)

    if file.exists() and file.is_file():
        # initialize reader
        with open(in_path, "r") as f:
            reader = csv.DictReader(f = f)
            # add all data points to a list
            data = []
            for r in reader:
                # PREVIOUSLY: make sure to cast a float, as they are strings by default
                # now: apply lambda to allow for casting control
                data.append(data_lambda(r[col]))
            if debug:
                print("Data:", data)
            return data
            
    else:
        if debug:
            print(in_path, "does not exist or is not a file! Skipping...")
        return False

def find_true_names(bools: list[bool], names: list[str]):
    """ Performs a list comprehension, returning a list
    of all names with a corresponding value in bools that is true.
    Each value in bools is matched to its corresponding index in names
    (ex. bools[0] is matched with names[0]).\n
    bools: A list of booleans to use\n
    names: A list of names to relate to bools\n
    NOTE: It is currently assumed that len(bools) == len(names),
    which could potentially cause errors if not satisfied"""

    return [name for name, val in zip(names, bools) if val]

def review_csv_timings(in_path: str, sec_div = 3600, debug = False):
    """Prints some statistics about a valid CSV file containing timing data.\n
    in_path: The file to review. Must be in CSV format and must contain the columns
    "name", "start", "end", and "elapsed"\n
    sec_div: This number is used to divide data into sections.
    For example, the default value of 3600 will split items into
    sections for 0 hours, 1 hour, 2 hours, etc. based on how much
    elapsed time each data point has.\n
    debug: Whether to print extra information for debugging\n"""

    if debug:
        print("--- CSV Timing Data ---")

    file = Path(in_path)

    if file.exists() and file.is_file():
        if debug:
            print("Attempting to load data!")
        # initialize reader
        with open(in_path, "r") as f:
            reader = csv.DictReader(f = f)
            if debug:
                print("Loaded data!")

            # make these unrealistic values so they are overwritten
            start = datetime.datetime(year = 9999, month = 1, day = 1)
            start_name = "default"
            end = datetime.datetime(year = 1, month = 1, day = 1)
            end_name = "default"
            short = datetime.timedelta(days = 9999999)
            short_name = "default"
            long = datetime.timedelta(days = -9999999)
            long_name = "default"
            sum = datetime.timedelta(hours = 0)
            amt = 0
            dur_sec_more = {}
            dur_sec_less = {}

            for r in reader:
                # check start
                temp = datetime.datetime.fromisoformat(r['start'])
                if temp < start:
                    start = temp
                    start_name = r['name']

                # check end
                temp = datetime.datetime.fromisoformat(r['end'])
                if temp > end:
                    end = temp
                    end_name = r['name']

                # check time
                elapsed = datetime.datetime.strptime(r['elapsed'], "%H:%M:%S.%f")
                temp = elapsed - datetime.datetime.strptime("00:00:00", "%H:%M:%S")
                if temp < short:
                    short = temp
                    short_name = r['name']

                if temp > long:
                    long = temp
                    long_name = r['name']

                hours = int(temp.total_seconds() // sec_div)

                if hours not in dur_sec_more.keys():
                    dur_sec_more[hours] = [(r['name'], temp)]
                    dur_sec_less[hours] = 1
                else:
                    dur_sec_more[hours].append((r['name'], temp))
                    dur_sec_less[hours] += 1

                sum += temp
                amt += 1

            print("Parsed data!\n")
            print("Info for analysis:")
            print(f"Earliest start: {start} (Name: {start_name})")
            print(f"Latest end: {end} (Name: {end_name})")
            print(f"Total elapsed run time: {(end - start)}\n")
            print(f"Shortest calculation time: {short} (Name: {short_name})")
            print(f"Longest calculation time: {long} (Name: {long_name})")
            print(f"Total calculations: {amt}")
            print(f"Total computing time: {sum}")
            print(f"Average computing time: {sum / amt}")
            print(f"Duration sections: {dur_sec_less}")

            return dur_sec_more

    else:
        if debug:
            print(in_path, "does not exist or is not a file! Ignoring...")
        return False
    
def read_multi_csv(dirs: list[str], csv_cols = [("free_energy", lambda text: float(text)), ("name", lambda text: text)],
                   sub_path = "/data/scft_2.csv", debug = False) -> list[list[tuple]]:
    """ Reads multiple CSV columns and outputs them as a list of lists of tuples.\n
    dirs: A list of directory names to read from (see sub_path for how
    to target each directory's CSV files).\n
    csv_cols: A list of tuple str-lambda pairs. Each pair contains a CSV column to read
    and a lambda to apply to the column (such as converting its data to a float).
    See read_csv_col() for more information.\n
    sub_path: A path to a CSV file in each directory. If you are using this fork's
    default configurations, "/data/scft_2.csv" should be able to properly target
    the files in most scenarios.\n
    debug: Whether to print extra information for debugging\n"""
    data = []

    for d in dirs:
        temp_cols = []
        for c, lam in csv_cols:
            col = read_csv_col(d + sub_path, c, lam, debug)
            temp_cols.append(col)
        data.append(list(zip(*temp_cols,repeat(d))))

    return data

    
def improved_uniques(data: list[tuple[float, str, str]], epsilon = 0.00001, excluded_vals = [-1],
                     const = 0, tol_debug = False, debug = False) -> dict[str, list[tuple[float, str, str]]]:
    """ Finds information on unique solutions. This is designed to be an improved version
    of find_neighbors() (hence the name) that preserves more information for future use. It
    is also designed to work well with the output of read_multi_csv() (after being passed
    through combine_lists()), which can allow for the processing of multiple trials worth of data.\n
    data: A list of tuples consisting of float free energy values, string names, and string trail names.
    This structure can easily be obtained by passing the output of read_multi_csv (with its default
    configurations) through combine_lists().\n
    epsilon: The allowed tolerance/difference for each cluster. Defaults to 0.00001 (10^-5)\n
    excluded_vals: A list of values to ignore for forming clusters. Entries near it will be skipped.
    This can be used to help filter out bad/empty data values (such as free energies of -1.0)\n
    const: A constant that is subtracted from every value. This can be used
    to compare the relative free energies of structures. Defaults to 0.\n
    tol_debug: Whether to print extra information regarding tolerance calculations for debugging.
    Note that this will print several lines for every entry in data\n
    debug: Whether to print extra information for debugging. Defaults to False\n"""
    if debug:
        print("Debug mode ON for find_neighbors")
        print("Raw data:", data)
        print("Epsilon:", epsilon)
        print("Excluded values:", excluded_vals)
        print("Debug for tolerance calculations:", tol_debug)


    cands = []
    nums = {}
    for i, name, trial in data:
        i -= const
        found_cand = False
        if tol_debug:
                print("Searching for exclusions...")
        for j in excluded_vals:
            if is_close(i, j, epsilon, tol_debug):
                # print on debug bc it's more important info
                if debug:
                    print("Found exclusion: " + str(j) + "!")
                # if it should be excluded, skip the rest of the search
                found_cand = True
                break
        # don't start searching if it should be excluded
        if not found_cand:
            if tol_debug:
                print("Searching for candidates...")
            for j in cands:
                if is_close(i, j, epsilon, tol_debug):
                    # print on debug bc it's more important info
                    if debug:
                        print("Found candidate: " + str(j) + "!")
                    found_cand = True
                    if j in nums:
                        nums[j].append((i, name, trial,))
                    else:
                        print("Error: A candidate was likely lost!")
                        nums[j].append((i, name, trial,))
                    # you can assume that something can never match two candidates
                    break
        if not found_cand:
            if debug:
                print("No candidate or exclusion found. Creating new candidate:", i)
            cands.append(i)
            nums[i] = [(i, name, trial,)]
    if debug:
        print("Candidates:", cands)
        print("Numbers:", nums)

    return nums

def cluster_histogram(cluster: list[tuple[float, str, str]], out_path: str, colors: list[tuple[str, str]],
                      px_wd = 1200, px_ht = 800, dpi = 100, bins = 250, debug = False):
    """ Creates a histogram for a single unique cluster. The function's
    framework can also be utilized to visualize the output of read_multi_csv()
    after being run through combine_lines(). To use this function from the output
    of improved_uniques(), one must access one of the outputted dict's values and
    pass it in to this function as "cluster". See multi_cluster_histograms() to be
    able to make a histogram for every cluster in a data set.\n
    cluster: A list of tuples consisting of float free energy values, string names,
    and string trial names. This structure is present in the values of the dict returned
    by improved_uniques(). Additionally, this structure can be obtained by passing the
    output of read_multi_csv() (with its default parameters) through combine_lists().\n
    out_path: The path to write the histogram image to.\n
    colors: A list of tuples consisting of hex string colors and string trial names to use
    on the histogram. This allows for color-coding of each trial within the histogram.
    This parameter must contain color values for every trial present in the dataset,
    but may also provide additional (unused) colors. dynamic_hex_rainbow() can be used to
    dynamically generate hex string colors in the format accepted by this method using a list
    of inputted string trial names. An example of a valid string for data containing the names
    "first_run" and "second_run" is given below:\n
    [("#D7BDF2", "first_run"), ("#87F3E7", "second_run"), ("#85D6FF", "third_run"), ("#8693FF", "fourth_run")]\n
    Although only "first_run" and "second_run" are present in this scenario, it is still completely
    acceptable to give colors for additional trials such as "third_run" and "fourth_run".\n
    px_wd: The width to use, in pixels.\n
    px_ht: The height to use, in pixels.\n
    dpi: The dots per inch value to use.\n
    bins: The amount of histogram bins to use for each figure.\n
    debug: Whether to print extra information for debugging\n"""
    trial_clusters = {}

    # old colors: [("#D7BDF2", "first_run"), ("#87F3E7", "second_run"), ("#85D6FF", "third_run"),
    #             ("#8693FF", "fourth_run"), ("#CD83FF","eighth_run"), ("#D18BE5", "ninth_run"),
    #             ("#DB84D8", "tenth_run"), ("#F17BAF", "eleventh_run"), ("#FF7978", "twelfth_run"),
    #             ("#FF9155", "thirteenth_run")]

    for c in cluster:
        if c[2] in trial_clusters:
            trial_clusters[c[2]].append(c)
        else:
            trial_clusters[c[2]] = [c]

    trials = trial_clusters.keys()

    if debug:
        print(f"Trial-sorted clusters: {trial_clusters}")
        print(f"Trials present: {trials}")

    fixed_colors = []

    for k in trials:
        for c in colors:
            if k == c[1]:
                fixed_colors.append(c[0])
                continue

    if debug:
        print(f"Colors: {fixed_colors}")

    # fixed_colors = colors[:num_trials]

    # if debug:
    # print(trial_clusters.values())

    energies = {k: [j[0] for j in v] for k, v in trial_clusters.items()}

    # print(energies)
    
    fig, ax = plt.subplots(figsize=(px_wd / dpi, px_ht / dpi), dpi=dpi)
    print(fig.get_size_inches(), "inches")

    # ax.figure(figsize=(6,4), dpi=500)
    # plt.xticks(np.arange(-0.04001, -0.03999, 0.000003))
    # plt.ticklabel_format(style = 'plain', axis = 'both')
    # plt.tick_params()
    ax.hist(energies.values(), bins=bins, stacked = True, color = fixed_colors, label = trial_clusters.keys())
    # 
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    
    plt.savefig(out_path, dpi = dpi)

def multi_cluster_histograms(groups: dict[list[tuple[float, str, str]]], out_dir: str,
                             name_lambda = lambda text: str(text) + ".png", px_wd = 1200,
                             px_ht = 800, dpi = 100, bins = 200, debug  = False) -> None:
    """ Runs the function cluster_histogram() for every cluster in groups.
    This function is considerably slow and will end up producing many (somewhat unhelpful)
    histograms, so it is recommended to only run cluster_histogram() for all of the data
    or for specifically targeted clusters.\n
    groups: A dict of groups (each group is a list of tuples containing a
    free energy value, string name, and string trial name). This is the same structure as
    the output of improved_uniques().\n
    out_dir: A directory to output each image to.\n
    name_lambda: A lambda to apply to each name. By default, each cluster's free energy
    value is used as the name, and the suffix ".png" is appended to each file.\n
    px_wd: The width to use, in pixels.\n
    px_ht: The height to use, in pixels.\n
    dpi: The dots per inch value to use.\n
    bins: The amount of histogram bins to use for each figure.\n
    debug: Whether to print extra information for debugging\n"""
    for name, cluster in groups.items():
        cluster_histogram(cluster, out_path = out_dir + "/" + name_lambda(name), px_wd = px_wd, px_ht = px_ht,
                          dpi = dpi, bins = bins, debug = debug)


def combine_lists(lists: list[list]) -> list:
    """ Combines several lists into a single list, and returns it.\n
    lists: The lists to combine.\n"""

    out = []
    for l in lists:
        out.extend(l)

    return out

def hsv_to_hex(h: float, s: float, v: float) -> str:
    """ Converts an HSV color to a hex string by using colorsys' hsv_to_rgb()
    function and then applying formatting and a transformation.\n
    h: An HSV hue value, between 0.0 and 1.0 inclusive.\n
    s: An HSV saturation value, between 0.0 and 1.0 inclusive.\n
    v: An HSV value value, between 0.0 and 1.0 inclusive.\n"""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)

    return f"#{int(255 * r):02x}{int(255 * g):02x}{int(255 * b):02x}"

def dynamic_hex_rainbow(names: list[str], s: float, v: float, min_clamp = 0.0, max_clamp = 1.0) -> list[tuple[str, str]]:
    """ Creates a list of paired color-name tuples in an HSV gradient.
    Each name in names is given a hex string color in evenly-spaced
    intervals between min_clamp and max_clamp.\n
    names: A list of string names to create a gradient for. The length of
    the gradient will be the same as the length of names.\n
    s: An HSV saturation value, between 0.0 and 1.0 inclusive.\n
    v: An HSV value value, between 0.0 and 1.0 inclusive.\n
    min_clamp: The lowest hue value to use. 0.0-0.5 are warmer colors
    and 0.5-1.0 are cooler colors. Defaults to 0.0.\n
    max_clamp: The highest hue value to use. 0.0-0.5 are warmer colors
    and 0.5-1.0 are cooler colors. Defaults to 1.0.\n"""
    colors = []
    size = len(names)
    ran = max_clamp - min_clamp

    i = 0
    for n in names:
        hue = (ran * i) / size + min_clamp
        hex = hsv_to_hex(hue, s, v)
        colors.append((hex, n,))

        i += 1

    return colors

def get_first_in_cluster(groups: dict[str, list[tuple[float, str, str]]]):
    """ Returns the name and trial name of the first constituent of every inputted cluster\n
    groups: The clusters to use"""
    names = []
    for d in groups.values():
        names.append((d[0][1], d[0][2]))

    return names

def copy_files(pre_path: str, files: list[tuple[str, str]], temp_dir: str, name_end = "c.rf", translations = TRANSLATIONS,
               mid_path = "scft_2", post_path = "out/c.rf"):
    for name, trial in files:
        translation_name = trial
        for k, v in translations:
            if trial == k:
                translation_name = v

        shutil.copy((Path(pre_path) / trial / mid_path / name / post_path).absolute(), (Path(temp_dir) / f"{translation_name}_{name}_{name_end}").absolute())

# # colors = dynamic_hex_rainbow(["first_run", "second_run", "third_run", "fourth_run", "eighth_run", "ninth_run", "tenth_run", "eleventh_run", "twelfth_run", "thirteenth_run"], 0.5, 1.0, max_clamp = 1.0)

groups = improved_uniques(combine_lists(read_multi_csv(["first_run", "second_run", "third_run", "fourth_run", "eighth_run", "ninth_run", "tenth_run", "eleventh_run", "twelfth_run", "thirteenth_run"])),
                          const = f_DG, excluded_vals= [-1 - f_DG])

print(len(get_first_in_cluster(groups)))

# 
# print(groups)

# print(cluster_histogram(groups[2.70642211386], "ztest.png", debug = True))

# multi_cluster_histograms(groups, "zimages", debug = True)

# groups_2 = {}

# for k, v in groups.items():
#     if k > 3:
#         groups_2[k] = v

# print(groups_2)

# multi_cluster_histograms(groups_2, "all_excl", debug = True)

# x = [v for v in groups.values() if v[1] < 3]

# groups3 = []

# for v in groups.values():
#     for g in v:
#         if g[0] < 0:
#             groups3.append(g)

# # print(groups3)

# #[v for v in groups.values() for g in v if g[0] < 3]

# cluster_histogram(groups3,out_path= "zall_comp.png", bins = 2000, colors = colors)
# cluster_histogram(combine_lists(groups.values()),out_path= "zall.png", bins = 500, colors = colors)


# ch = 0
# for name, g in groups.items():
#     print(f"{name}:\t {len(g)}", end = "   ")
#     temp = f"{name}:\t {len(g)}   "
#     ch += len(temp)
#     if (ch > 90):
#         print("")
#         ch = 0
# print("")

# def compare_group(group_1: list[list[float | list[str]]], group_2: list[list[float | list[str]]],
#                   output_type = OutputType.STDOUT_ONLY, out_path = "out.txt"):
#     for num, vals in group_1:
#         for val in vals:
#             found = False
#             for num2, vals2 in group_2:
#                 if val in vals2:
#                     found = True
                    
#                     if sorted(vals) != sorted(vals2):
#                         print(f"diff detected! num: {num}, vals: {vals}, val: {val}, num2: {num2}, vals2: {vals2}")
#             if not found:
#                 print("something goes here if its not found maybe")

# def compare_groups(json_path: str, output_type = OutputType.STDOUT_ONLY, out_path = "out.txt"):
#     """Finds the difference between groups created by find_neighbors_list().\n
#     json_path: The path to the JSON file to use data from. Must contain the keys
#     "groups", pointing to a list of lists structured like:\n
#         [[1.0, ['1', '2', '3']]], where 1.0 is the value of
#         the group, and '1', '2', and '3' are its constituents.
#         While this is only an example of one group list, "groups"
#         consists of all group lists to review. A full example of groups could be:
#         [[[1.0, ['1', '2', '3']]], [[1.2, ['3']], [1.0, ['2', '1']]]]
#     Additionally, "num_groups" can be used to specify
#     the number of groups to review. If larger than len(groups)
#     or not present in json_path, it will default to len(groups).
#     Finally, group_names can be used to specify the names of different
#     group lists present in "groups". If not present all names will default
#     to their index (starting at 1 instead of 0) within "groups". If present but shorter than len(groups),
#     all groups without a name will be assigned their index (starting at 1 instead of 0) as their name.\n
#     write_output: Where to put the output of this file. Options are "STDOUT_ONLY",
#     "STDOUT_AND_FILE", and "FILE_ONLY".\n
#     out_path: The path to write the text output of this function to, if output_type is
#     STDOUT_ONLY or STDOUT_AND_FILE\n
#     debug: Whether to print extra information for debugging\n"""

#     with open(json_path, "r") as f:
#         data = json.load(f)

#     if 'groups' in data:
#         print_output("Found groups! Continuing...", output_type, out_path)
#         groups = data['groups']

#     else:
#         print_output("No groups found. Exiting function...", output_type, out_path)
#         return

#     group_num = len(groups)
#     if 'num_groups' in data:
#         group_num = data['num_groups']
#         print_output(f"Found number of groups: {group_num}", output_type, out_path)
#         if group_num > len(groups):
#             group_num = len(groups)
#             print_output(f"Number of groups is too big! Overriding to: {group_num}", output_type, out_path)
#     else:
#         print_output(f"No number of groups found. Defaulting to length of groups: {group_num}", output_type, out_path)

#     if 'group_names' in data:
#         group_names = data['group_names']
#         print_output(f"Found group names: {group_names}", output_type, out_path)
#         if len(group_names) < group_num:
#             while len(group_names) < group_num:
#                 group_names.append(len(group_names) + 1)
#             print_output(f"Too few group names found! Appending default names: {group_names}", output_type, out_path)

#     else:
#         group_names = []
#         while len(group_names) < group_num:
#                 group_names.append(len(group_names) + 1)
#         print_output(f"No group names found! Adding default names: {group_names}", output_type, out_path)

# compare_groups("temp.json", OutputType.STDOUT_AND_FILE)

# review_csv_timings("./first_run/data/scft_2_timings.csv", sec_div = 3600, debug = True)


# prepare_files("initial_guesses", "initial_guesses_prep", "rgrid", "param", "command", "run", True)
# execute_num("out_prepared", 1, 250, True, True, "timings.csv", True)

# to_csv("out_prepared", "output.csv")
# to_csv_num("scft_data/out_prepared", 1, 250, "output_new.csv", True)

# prepare_files('initial_guesses', 'the_files', 'rgrid.rf', "param", "command", "run", True, lambda a: a.rstrip(".rf"))

# # prepare_files("initial_guesses", "initial_guesses_prep", "rgrid", "param", "command", "run", True)
# execute_dir("the_files", True, True, "the_files/timings.csv", True)

# # to_csv("out_prepared", "output.csv")
# to_csv("the_files", "the_files/output.csv", True)

# f_e = read_csv_col("scft_data/output.csv", "free_energy", lambda text: float(text), True)
# # names = read_csv_col("output.csv", "name", debug = True)
# find_neighbors(f_e, epsilon = 0.000012, tol_debug = False, debug = True)