""" This file contains functions related to preparing GAN outputs
for SCFT,running SCFT, and collecting the data from it """

import shutil
import os
import subprocess
import datetime
import csv
from pathlib import Path

max_iterations = 2500

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
        See [DOC PENDING] for more information on how to know if a
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

def fix_w_basis_dir(in_path: str, ignored_names: list[str], out_path: str,
                    in_name: str, out_name: str, write_fixed = False,
                    fixed_path = "fixed.csv", debug = False):
    """ Fixes several w.bf (W basis) files outputted from the first pass of SCFT,
        by:
            -changing the crystal system from orthorhombic to triclinic\n
            -chaning the number of cell parameters from 3 to 6\n
            -appending the 3 cell parameters 0, 0, and 1.5707963\n
            -limiting the amount of basis functions from 32768 to 17000\n
        See [DOC PENDING] for more information on how to know if a
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

def execute_dir(in_path: str, adv_checking = True, timing = False, time_path = "timings.csv", debug = False):
    """ Executes the run script for every valid directory in in_path.\n
        in_path: A path to a directory with properly initialized subdirectories,
        as per the format specified in prepare_files\n
        adv_checking: Whether advanced checking should be used on subdirectories already
        containing a "log" final to find partially-completed calculations. This is recommended,
        but may be slightly slower (especially if many completed calculations are present in in_path)\n
        timing: Whether timing information should be printed and saved to time_path\n
        time_path: Where to write timing data to, if timing is True\n
        debug: Whether to print extra information for debugging"""
    if debug:
        print("Debug mode ON for execute_dir")
        print("In path:", in_path)
        print("Advanced checking:", adv_checking)
        print("Timing:", timing)
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
        for entry in dir_path.iterdir():
            if entry.is_dir():
                time_data = {}
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
                            time_data = {"name":    entry.name,
                                         "start":   0,
                                         "end":     0,
                                         "elapsed": 0}
                    else:
                        if debug:
                            print("Advanced checking is disabled. Skipping...")
                        time_data = {"name":    entry.name,
                                     "start":   0,
                                     "end":     0,
                                     "elapsed": 0}
                
                if timing:
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

def execute_num(in_path: str, start: int, end: int, adv_checking = True, timing = False, time_path = "timings.csv", debug = False):
    """ Executes the run script for every valid directory in in_path that falls between start and end, inclusive.\n
        in_path: A path to a directory with properly initialized subdirectories with numerical names,
        as per the format specified in prepare_files\n
        start: The number to start at\n
        end: The number to end at\n
        adv_checking: Whether advanced checking should be used on subdirectories already
        containing a "log" final to find partially-completed calculations. This is recommended,
        but may be slightly slower (especially if many completed calculations are present in in_path)\n
        timing: Whether timing information should be printed and saved to time_path\n
        time_path: Where to write timing data to, if timing is True\n
        debug: Whether to print extra information for debugging"""
    if debug:
        print("Debug mode ON for execute_num")
        print("In path:", in_path)
        print("Start:", start)
        print("End:", end)
        print("Advanced checking:", adv_checking)
        print("Timing:", timing)
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
                            time_data = {"name":    entry.name,
                                         "start":   0,
                                         "end":     0,
                                         "elapsed": 0}
                    else:
                        if debug:
                            print("Advanced checking is disabled. Skipping...")
                        time_data = {"name":    entry.name,
                                     "start":   0,
                                     "end":     0,
                                     "elapsed": 0}
                
                if timing:
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

def find_neighbors(data: list[float], epsilon = 0.00001, excluded_vals = [], tol_debug = False, debug = False):
    """ Finds all "clusters" within a list that fall near each other.
    Returns a dict with "candidate" values as keys and how many
    data points fall into each candidate as values\n
    data: A list of floats to classify\n
    epsilon: The allowed tolerance/difference for each cluster. Defaults to 0.00001 (10^-5)\n
    excluded_vals: A list of values to ignore for forming clusters, entries near it will be skipped.
    This can be used to help filter out bad/empty data values (such as free energies of -1.0)\n
    tol_debug: Whether to print extra information regarding tolerance calculations for debugging.
    Note that this will print several lines for every entry in data\n
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
                    if nums[j] is not None:
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

def find_neighbors_list(data: list[float], names: list[str], epsilon = 0.00001, excluded_vals = [], tol_debug = False, debug = False):
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
                    if nums[j] is not None:
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

### TODO: ADD MORE SAFETY FEATURES
### TODO: ADD MORE DEBUGGING
### TODO: ADD EXECUTE AND COLLECT AND CREATE FHELM INTERPRETTER


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