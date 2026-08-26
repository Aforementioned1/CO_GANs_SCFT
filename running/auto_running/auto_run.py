""" This program is intended to be able to moderate and automate an entire
run through, from GAN training to SCFT step 2.\n
Example usage: python auto_run.py log.txt param.json param_custom.json"""

""" FOR NOW, THIS ASSUMES THAT run_env.sh CONTAINS YOUR JSON PARAMETER'S "name" values as $RUN_NAME!!!!!! """

import subprocess
import sys
from enum import Enum
import json
from pathlib import Path
import shutil
import time

from datetime import timedelta
from datetime import datetime
import re

import logging
logger = logging.getLogger(__name__)

def init_template(text: str, replace: dict) -> str:
    """ Replaces all key-value pairs in a provided string.=\n
    text: The text to modify\n
    replace: A dict containing keys to be replaced and
    values to replace each key with\n
    NOTE: If a key is present in a value, it could
    potentially be overwritten!"""
    for key, value in replace.items():
        text = text.replace(key, value)

    return text

def init_template_file(in_path: str, out_path: str, replace: dict):
    logger.info(f"Attempting to replace template at {in_path}...")

    with open(in_path, "r") as f:
        text = f.read()

    repl = init_template(text, replace)

    with open(out_path, "w") as f:
        f.write(repl)

    logger.info(f"Wrote file to {out_path}!")

def str_to_timedelta(time: str):
    """ Converts a string formatted like "HH:MM:SS" to a
    datetime timedelta object\n
    time: A string formatted like "HH:MM:SS" """
    h, m, s = time.split(":")
    delta = timedelta(hours = int(h), minutes = int(m), seconds = int(s))

    return delta

def timedelta_to_str(delta: timedelta):
    """ Converts a datetime.timedelta object into a string
    formatted like "HH:MM:SS"\n
    delta: A timedelta object"""
    h = int(delta.total_seconds() // 3600)
    m = int((delta.total_seconds() % 3600) // 60)
    s = int(delta.total_seconds() % 60)

    return f"{h:02d}:{m:02d}:{s:02d}"

def add_time_strings(time_1: str, time_2: str):
    """ Converts two time strings to timedelta objects using str_to_timedelta(),
    adds them, then converts the timedelta back into a string and returns it.
    Each string must be formatted like "HH:MM:SS"\n
    time_1: The first time to add, in string "HH:MM:SS" format\n
    time_2: The second time to add, in string "HH:MM:SS" format"""
    delt1 = str_to_timedelta(time_1)
    delt2 = str_to_timedelta(time_2)

    total = delt1 + delt2

    return timedelta_to_str(total)

class Job:
    """ Represents a Slurm job\n
    job_id: The ID of this job\n
    job_type: The type of this job, either JobType.SINGLE or JobType.SCFT_ARRAY
    status: The last-updated status of this job\n
    template_path: An absolute path to the Slurm template to use when scheduling this job\n
    param: The parameters to use to fill in the template\n
    slurm_path: The path to the Slurm script to run (generated from template_path)\n
    timeouts: How many times this job timed out\n
    auto_reschedule: Whether this job should automatically reschedule itself with more time
    when entering "TIMEOUT" Slurm status. If false, the program will end execution if a 
    TIMEOUT occurs.\n
    reschedule_add: How much time to add when rescheduling the job for a TIMEOUT, if
    auto_reschedule is True. This should be a string formatted like "HH:MM:SS".
    This will vary between jobs, but a general rule of thumb for this value is 1/4 of
    the original time."""
    job_id: str
    status: str
    template_path: str
    param: dict
    slurm_path: str
    timeouts: int
    auto_reschedule: bool
    reschedule_add: str

    def __init__(self, template_path: str, param: dict,
                 slurm_path: str, auto_reschedule: bool):
        self.job_id = "UNSCHEDULED"
        self.status = "UNSCHEDULED"
        self.template_path = template_path
        self.param = param
        self.slurm_path = slurm_path
        self.timeouts = 0
        self.auto_reschedule = auto_reschedule
        self.reschedule_add = param['time_inc']

    def print_attrs(self, param = False):
        """ This is a debug method that prints all of this
        object's instance variables\n
        param: Whether to print the param dict"""
        logger.info(f"Job ID: {self.job_id} | Status: {self.status}")
        logger.info(f"Template Path: {self.template_path}")
        logger.info(f"Slurm Path: {self.slurm_path}")
        logger.info(f"Timeouts: {self.timeouts}")
        logger.info(f"AutoRes: {self.auto_reschedule} | ResAdd: {self.reschedule_add}")
        if param:
            logger.info(f"Param: {self.param}")

    def read_template(self):
        """ Reads all template parameters (enclosed in "{}") from
        this Job's template, and returns a list of all template parameters,
        including their enclosing {} characters"""
        logger.info(f"Attempting to read template parameters at {self.template_path}...")
        regex = r"(\{.*?\})"

        with open(self.template_path, 'r') as f:
            text = f.read()

        params = list(set(re.findall(regex, text)))

        logger.info("Done!")

        return params

    def create_script(self):
        """ Writes a script filling in the template parameters of this
        Job's template_path, writing the script to this Job's slurm_path"""
        logger.info("Attempting to write template...")

        params = self.read_template()

        replacements = {}

        logger.info("Attempting to locate parameters...")

        for p in params:
            if "\\" in p:
                replacements[p] = p.replace("\\", "")
                continue

            # convert template parameters (styled like {MY_PARAM}) to
            # lowercase dict keys (styled like my_param)
            p_target = p.strip("{}").lower()
            # set each template parameter to its corresponding dict parameter
            replacements[p] = self.param[p_target]

        logger.info("Done!")

        init_template_file(self.template_path, self.slurm_path, replacements)

    def schedule(self):
        """ Schedules this job to run """
        logger.info("Attempting to schedule job...")
        command = ["sbatch", "--parsable", self.slurm_path]
        result = subprocess.run(command, capture_output = True, text = True, check = True)

        logger.info("Done!")
    
        # strip text to be safe
        self.job_id = result.stdout.strip()
        logger.info(f"Result: {result.stdout.strip()} | Job ID: {self.job_id}")

        return self.job_id

    def check(self):
        """ Checks the current status of a specified Slurm job.
            If the job's status is FAILED, NODE_FAIL, or OUT_OF_MEMORY,
            reports it and ends the program. Otherwise, outputs the job's status."""
        logger.info(f"Attempting to view job {self.job_id}'s status...")
        
        command = ["sacct", "--format=State", "--noheader", "-P", "-j", self.job_id]
        result = subprocess.run(command, capture_output = True, text = True, check = True)
    
        code = result.stdout.splitlines()[0]
        logger.info(f"Job {self.job_id}'s code: {code}")
    
        # automatically exit if smth bad happens
        if code == "FAILED":
            logger.critical(f"Slurm job {self.job_id} ended with state FAILED!")
            logger.critical("Ending process...")
            sys.exit()
    
        if code == "NODE_FAIL":
            logger.critical(f"Slurm job {self.job_id} ended with state NODE_FAIL!")
            logger.critical("Ending process...")
            sys.exit()
    
        if code == "OUT_OF_MEMORY":
            logger.critical(f"Slurm job {self.job_id} ended with state OUT_OF_MEMORY!")
            logger.critical("Ending process...")
            sys.exit()
    
        return code

    def add_reschedule_time(self):
        """ Modifies this Job's time parameter by adding the rescheduling time to itself """
        add = self.reschedule_add
        curr = self.param['time']
        total = add_time_strings(curr, add)
        logger.warning("Adding Slurm time for rescheduling!")
        logger.warning(f"Current: {curr} | Addition: {add} | Total: {total}")
        logger.warning(f"Setting parameter time config to be {total}...")
        self.param['time'] = total
        logger.warning("Done!")
        logger.warning("Overwriting Slurm script...")
        self.create_script()
        logger.warning("Done!")

    def wait_for_slurm_end(self, period = 120.0):
        """ Periodically checks for this Slurm job to finish.
        If the Slurm job's status becomes "FAILED", "NODE_FAIL" or
        "OUT_OF_MEMORY", terminates the program\n
        This function is blocking and will not return execution until this job's
        status becomes "COMPLETED"\n
        If auto_reschedule is True, this function will continue to schedule jobs
        with longer times and recursively run this function until the job does not
        timeout\n
        period: The period between Slurm checks, in seconds. Defaults to 120s"""
        if self.job_id == "UNSCHEDULED":
            logger.error("This job has not been scheduled yet! Returning...")
            return

        finished = False

        while not finished:
            code = self.check()
            if code == "COMPLETED":
                finished = True
            if code == "TIMEOUT":
                logger.warning(f"Slurm job {self.job_id} timed out!")
                if self.auto_reschedule:
                    logger.info("Auto reschedule is ON!")
                    logger.info("Attempting to reschedule...")
                    self.timeouts += 1
                    self.add_reschedule_time()
                    self.schedule()
                    self.wait_for_slurm_end()
                else:
                    logger.critical("Auto reschedule is OFF!")
                    logger.critical("Ending process...")
                    sys.exit()

            time.sleep(period)

class BranchedJob(Job):
    """ Represents a "branched" Slurm array job, where multiple
    jobs are run at the same time with the same purpose. The
    major difference between Job and BranchedJob is that its
    param dict should contain an "array" key that points to a
    list of Slurm array strings to use."""
    job_ids = []
    statuses = []
    callback = lambda self: logger.info("No specified callback. Continuing program...")

    def print_attrs(self, param=False):
        logger.info(f"Job IDs: {self.job_ids}")
        logger.info(f"Statuses: {self.statuses}")
        super().print_attrs(param)

    def schedule(self):
        """ Schedules a job for all of the items in the "array" key """
        for i, a in enumerate(self.param['array']):
            logger.info(f"Attempting to schedule job {i}...")
            logger.info(f"Prepping specific template...")
            init_template_file(f"{self.slurm_path.replace('.sh', '')}_no_array.sh", f"{self.slurm_path.replace('.sh', '')}_{i}.sh", {"{ARRAY}": a})
            logger.info("Done!")

            command = ["sbatch", "--parsable", f"{self.slurm_path.replace('.sh', '')}_{i}.sh"]
            result = subprocess.run(command, capture_output = True, text = True, check = True)

            logger.info("Done!")
        
            # strip text to be safe
            self.job_ids.append(result.stdout.strip())
            logger.info(f"Result: {result.stdout} | Job ID: {self.job_id}")

        logger.info(f"Scheduled {len(self.param['array'])} job(s) for all arrays!")

        return self.job_ids

    def create_script(self):
        """ Writes 
        Excludes the parameter "array" """
        logger.info("Attempting to write template...")

        params = self.read_template()
        # remove array
        params.remove("{ARRAY}")

        replacements = {}

        logger.info("Attempting to locate parameters...")

        for p in params:
            if "\\" in p:
                replacements[p] = p.replace("\\", "")
                continue

            # convert template parameters (styled like {MY_PARAM}) to
            # lowercase dict keys (styled like my_param)
            p_target = p.strip("{}").lower()
            # set each template parameter to its corresponding dict parameter
            replacements[p] = self.param[p_target]

        logger.info("Done!")

        init_template_file(self.template_path, f"{self.slurm_path.replace('.sh', '')}_no_array.sh", replacements)

    def check(self):
        """ Checks the current status of a specified Slurm job.
            If the job's status is FAILED, NODE_FAIL, or OUT_OF_MEMORY,
            reports it and ends the program. Otherwise, outputs the job's status."""
        for i, j in enumerate(self.job_ids):
            logger.info(f"Attempting to view job {j} (branch index {i})'s status...")

            command = ["sacct", "--format=State", "--noheader", "-P", "-j", j]
            result = subprocess.run(command, capture_output = True, text = True, check = True)
        
            code = result.stdout.splitlines()[0]
            logger.info(f"Job {j} (branch index {i})'s code: {code}")

            # make sure to append it instead of setting the
            # value if the index doesnt exist yet
            if 0 <= i < len(self.statuses):
                self.statuses[i] = code
            else:
                self.statuses.append(code)
                if not (0 <= i < len(self.statuses)):
                    logger.warning(f"Code {code} not added to index {i} of statuses (job {j}, branch index {i}).")
            logger.info(f"Added code {code} to statuses!")
        
            # automatically exit if smth bad happens
            if code == "FAILED":
                logger.critical(f"Slurm job {j} (branch index {i}) ended with state FAILED!")
                logger.critical("Ending process...")
                sys.exit()
        
            if code == "NODE_FAIL":
                logger.critical(f"Slurm job {j} (branch index {i}) ended with state NODE_FAIL!")
                logger.critical("Ending process...")
                sys.exit()
        
            if code == "OUT_OF_MEMORY":
                logger.critical(f"Slurm job {j} (branch index {i}) ended with state OUT_OF_MEMORY!")
                logger.critical("Ending process...")
                sys.exit()
        
        return self.statuses

    def wait_for_slurm_end(self, period = 240.0):
        """ Periodically checks for this Slurm job to finish.
        If the Slurm job's status becomes "FAILED", "NODE_FAIL" or
        "OUT_OF_MEMORY", terminates the program\n
        This function is blocking and will not return execution until this job's
        status becomes "COMPLETED"\n
        If auto_reschedule is True, this function will continue to schedule jobs
        with longer times and recursively run this function until the job does not
        timeout\n
        period: The period between Slurm checks, in seconds. Defaults to 240s"""

        finished = False

        while not finished:
            codes = self.check()
            for c in codes:
                # iterate over all codes to see if theyre done
                if not (c == "COMPLETED" or c == "TIMEOUT"):
                    finished = True

            time.sleep(period)

        # execute the callback function
        self.callback(self)

    # def bind_callback(self, new_callback: function):
    #     """ Binds a new callback function to this BranchedJob. By default,
    #     the callback prints a message and continues.\n
    #     new_callback: The callback function to use when all branches finish execution.
    #     Must take a BranchedJob object as a parameter."""
        # self.callback = new_callback

def scft_callback(job: BranchedJob):
    """ This function is intended to be used as a callback for
    a BranchedJob object"""
    # use code from print_dirs.py to find which ones are left, in array form
    left = scft_array_timeout_check(str(Path(job.param['abs_path']) / job.param['name'] / job.param['job_dir_name']))

    # exit early if there's nothing left to avoid getting stuck in a loop
    if len(left) == 0:
        return

    # override existing arrays
    job.param['array'] = left

    # prepare parameters for next run to be safe
    job.timeouts += 1
    job.job_ids = []
    job.statuses = []

    # make sure to increase time!!!
    job.add_reschedule_time()

    # schedule and wait
    job.schedule()
    job.wait_for_slurm_end()

def scft_array_timeout_check(dir: str):
    """ Taken from print_dirs.py """

    # force certain parameters to avoid having to modify the
    # original code and allow for potential future changes
    target_dir = Path(dir)
    num = True
    rev = True
    debug = False
    groups = 500

    out_strs = []
    total_dirs = 0

    dir_amt = 0
    out_str = ""

    for d in sorted(target_dir.iterdir(), key = lambda d: int(d.stem) if num else d):
        if dir_amt >= groups:
            logger.info(f"DIR AMT reached! (dir_amt: {dir_amt}, groups: {groups})")
            if len(out_str) > 1:
                out_str = out_str.rstrip(",")
            if debug:
                logger.debug(out_str + "\n")
            out_strs.append(out_str)
            total_dirs += dir_amt
            dir_amt = 0
            out_str = ""
        if d.is_dir():
            if rev:
                log = d / "log"

                state = run_scft.get_state_cat(str(d), debug = debug)
                if debug:
                    logger.debug(f"{d.name}'s state is: {state}")
                
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
            logger.error(f"{d.name} is not a directory!")

    out_strs.append(out_str.rstrip(","))
    total_dirs += dir_amt

    if len(out_str) > 1:
        out_str = out_str.rstrip(",")

    for string in out_strs:
        logger.info(string)
    logger.info(f"Final directory amount: {dir_amt}\nTotal directory amount: {total_dirs}")

    return out_strs

def deep_merge(dict_1: dict, dict_2: dict, recursive = False):
    """ Merges two dicts. Any individual keys of dict_1 and dict_2 are preserved,
    but shared keys preserve only the value of dict_2. Unlike the built-in Python merge (|)
    operator, this function finds instances of shared keys amongst the two dicts where both
    values are nested dicts. Instead of only preserving the value of dict_2, as it would with
    the merge operator, the program merges the two dicts. If recursive is True, the program
    searches both nested dicts for any duplicate keys with even further nested dicts, properly
    combining them until the dicts have no more shared dict keys.\n
    dict_1: The dict to merge two\n
    dict_2: The dict to merge with dict_1\n
    recursive: Whether to recursively search for further nested dicts"""
    # logger.info(f"dict_1: {dict_1}")
    # logger.info(f"dict_2: {dict_2}")
    out = dict_1.copy()

    for k, v in dict_2.items():
        if k in dict_1:
            if isinstance(v, dict) and isinstance(dict_1[k], dict):
                if recursive:
                    deeper_merge = False

                    for v2 in v.values():
                        # print(f"First {v2}")
                        if isinstance(v2, dict):
                            deeper_merge = True
                    for v2 in dict_1[k].values():
                        # print(f"Second {v2}")
                        if isinstance(v2, dict):
                            deeper_merge = True
                    if deeper_merge:
                        out[k] = deep_merge(dict_1[k], v, recursive)
                    else:
                        # print(f"one: {dict_1[k]}")
                        # print(f"two: {v}")
                        out[k] = v | out[k]
                else:
                    out[k] = v | out[k]
            else:
                out[k] = v

    return out

### scft_helpers.py functions

def prep_scft_1(run_path: Path, co_gans_path: Path, param: dict):
    """ Originally from scft_helpers.py (name PREP_SCFT_1, number 0)\n
        Prepares subdirectories to be run through SCFT step 1 using a directory
        of GAN guesses\n
        run_path: The path to a directory containing the directory gan_guesses
        (with 5000 guesses guess_1.rf-guess_5000.rf)\n
        co_gans_path: The path to the CO_GANs_SCFT repo clone\n
        param: A dictionary containing parameters. This function requires a
        nested dictionary 'scft_1' that contains keys 'param_path', 'command_path',
        and 'run_path'. These should be relative paths to param, command, and run files,
        respectively, from co_gans_path"""
    logger.info("[HELPER] PREP_SCFT_1 (0)")
    # prepare files
    run_scft.prepare_files(in_path = str(run_path / "gan_guessees"),
            out_path = str(run_path / "scft_1"),
            out_name = "rgrid.rf",
            param_path = str(co_gans_path / param['scft_1']['param_path']),
            command_path = str(co_gans_path / param['scft_1']['command_path']),
            run_path =  str(co_gans_path / param['scft_1']['run_path']),
            debug = False)

def scft_1_to_csv(run_path: Path):
    """ Originally from scft_helpers.py (name SCFT_1_TO_CSV, number 1)\n
        Collects and writes CSV convergence data from the directory scft_1
        run_path: The path to a directory containing the directory scft_1\n"""
    logger.info("[HELPER] SCFT_1_TO_CSV (1)")
    # combine data to CSV file
    run_scft.to_csv_num(dir_path = str(run_path / "scft_1"),
            num_start = 1,
            num_end = 5000,
            output = str(run_path / "data/scft_1.csv"),
            debug = False)

def scft_1_conv(run_path: Path, param: dict):
    """ Originally from scft_helpers.py (name SCFT_1_CONV, number 2)\n
        Prints SCFT step 1 convergence data with optional detailed information\n
        run_path: The path to a directory containing the directory scft_1\n
        param: A dictionary containing parameters. This function requires a
        nested dictionary 'scft_1' that contains the key 'detailed_conv', which
        should be a boolean value."""
    logger.info("[HELPER] SCFT_1_CONV (2)")
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

    for d in sorted((run_path / "scft_1").iterdir(), key = lambda d: int(d.stem)):
        state = run_scft.calc_state(d.absolute(), debug = False)

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
        logger.info(f"Finished (total):           {data['suc']}")
        logger.info(f"Finished (converged):       {data['conv']}")
        logger.info(f"Finished (not converged):   {data['fin']}")
        if param['scft_1']['detailed_conv']:
            logger.info(f"Finished (max iterations):  {data['iter']}")
            logger.info(f"Finished (no convergence):  {data['nocv']}")
    
        # WARN
        logger.info(f"Unfinished (total):         {data['warn']}")
        if param['scft_1']['detailed_conv']:
            logger.info(f"Unfinished (no log):        {data['log']}")
            logger.info(f"Unfinished (no iterations): {data['noit']}")
            logger.info(f"Unfinished (iterations):    {data['unf']}")
    
        # ERR
        logger.info(f"Error (no directory):        {data['err']}")

def scft_1_time(run_path: Path, param: dict):
    logger.info("[HELPER] SCFT_1_TIME (3)")
    run_scft.review_csv_timings(str(run_path / "data/scft_1.csv"), sec_div = param["scft_1"]["sec_div"], debug = False)

def prep_scft_2(run_path: Path, co_gans_path: Path, param: dict):
    logger.info("PREP_SCFT_2 (4)")
    # read names of each initial guess (should be 1-250) and whether they converged
    names = run_scft.read_csv_col(in_path = str(run_path / "data/scft_1.csv"), 
                                  col = "name", debug = False)
    
    # make sure to cast string boolean values as booleans - requires more complex logic
    # as bool() method considers any non-empty str true

    # not adding the lambda as a parameter as it would likely be hard to
    # serialize/deserialize and should not change
    # despite this, the column names have still been
    # included as parameters, which should also never change
    conv = run_scft.read_csv_col(in_path = str(run_path / "data/scft_1.csv"), col = "converged",
                data_lambda = lambda text: True if text == "True" else False, debug = False)

    # get all guesses that converged with step 1
    conv_names = run_scft.find_true_names(bools = conv, names = names)

    # prepare for second SCFT pass
    # scft_2's in should be the same as scft_1's out, but decided to make separate param
    run_scft.prepare_files_second(in_path = str(run_path / "scft_1"), dir_names = conv_names,
                out_path = str(run_path / "scft_2"),
                param_path = str(co_gans_path / param['scft_2']['param_path']),
                command_path = str(co_gans_path / param['scft_2']['command_path']),
                run_path =  str(co_gans_path / param['scft_2']['run_path']),
                debug = False)

    logger.info("FIX_W_BASIS (4.5)")
    # this uses the more advanced save_w_basis_dir() rather than the outdated fix_w_basis_dir()

    # fix w.bf files for second SCFT pass
    run_scft.save_w_basis_dir(in_dir = str(run_path / "scft_2"), debug = False)

def scft_2_to_csv(run_path: Path):
    logger.info("SCFT_2_TO_CSV (5)")
    # combine data to CSV file
    run_scft.to_csv_num(dir_path = str(run_path / "scft_2"), num_start = 1, num_end = 5000,
                        output = str(run_path / "data/scft_2.csv"), debug = False)

def scft_2_conv(run_path: Path, param: dict):
    logger.info("SCFT_2_CONV (6)")
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

    for d in sorted((run_path / "scft_2").iterdir(), key = lambda d: int(d.stem)):
        state = run_scft.calc_state(d.absolute(), debug = False)

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
    logger.info(f"Finished (total):           {data['suc']}")
    logger.info(f"Finished (converged):       {data['conv']}")
    logger.info(f"Finished (not converged):   {data['fin']}")
    if param['scft_2']['detailed_conv']:
        logger.info(f"Finished (max iterations):  {data['iter']}")
        logger.info(f"Finished (no convergence):  {data['nocv']}")

    # WARN
    logger.warning(f"Unfinished (total):         {data['warn']}")
    if param['scft_2']['detailed_conv']:
        logger.warning(f"Unfinished (no log):        {data['log']}")
        logger.warning(f"Unfinished (no iterations): {data['noit']}")
        logger.warning(f"Unfinished (iterations):    {data['unf']}")

    # ERR
    logger.error(f"Error (no directory):        {data['err']}")

def load_params(paths: list[str]):
    """ Attempts to load JSON parameters from all file paths in paths.
    This can be used to easily change small amounts of JSON parameters while
    keeping the original defaults intact\n
    NOTE: Any duplicate parameters in later files will automatically override
    existing duplicates from earlier files\n
    paths: A list of all paths to read. This program uses sys.argv[2:] by default"""
    # sys.argv[1:]
    if len(paths) != 0:
        logger.info(f"{len(paths)} parameter files detected.")
        params = []

        for p in paths:
            logger.info(f"Attempting to read input file at {p} for custom parameters.")
            with open(p, "r") as f:
                params.append(json.load(f))

        params.reverse()

        param = params[0]

        for p in params:
            param = deep_merge(param, p, True)

        return param

    else:
        # end program if nothing is inputted
        logger.critical("No parameter file detected.")
        logger.critical("Ending program...")
        sys.exit()

def write_step(step: int, step_path: Path):
    logger.info(f"Updating step to {step}")
    step_path.write_text(str(step))

    return step

def main():
    # load JSON parameters
    # using sys.argv for now

    logging.basicConfig(level = logging.INFO, filename = sys.argv[1], format='%(asctime)s [%(levelname)s] %(message)s')

    param = load_params(sys.argv[2:])

    main_param = param['main']

    run_path = Path(main_param['abs_path']) / main_param['name']
    co_gans_path = Path(main_param['co_gans_path'])
    move_path = Path(main_param['move_path'])

    main_paths = {
        "run_path": run_path,
        "co_gans_path": co_gans_path,
        "move_path": move_path
    }

    logger.info("Attempting to load run_scft...")
    # add path using param file
    sys.path.append(str(co_gans_path / "CO_GANs_SCFT/running"))
    logger.info(f"Appended {(co_gans_path / 'CO_GANs_SCFT.running')} to Python search path!")

    # make sure other functions can access it
    global run_scft

    import run_scft

    logger.info("Successfully loaded run_scft!")

    step = 0

    if main_param['check_step']:
        logger.info("Attempting to locate step file...")
        step_path = (run_path / "step")
        if step_path.is_file():
            logger.info("Found step file!")
            step = int(step_path.read_text())
            logger.info(f"Step: {step}")

        else:
            logger.info("No step file found. Defaulting to step 0...")

    # basic init
    if step == 0:
        # make run directory if it doesnt exist already
        if not run_path.exists():
            run_path.mkdir(parents = True, exist_ok = True)

        # copy 
        shutil.copy(param['data_path'], str(run_path / "data.pt"))

        step = write_step(step + 1, run_path / "step")

    # GAN stuff
    if step == 1:
        # init gan train job object
        train_job = Job(co_gans_path / "CO_GANs_SCFT/running/auto_running/train_template.sh",
                        param['train']['slurm'] | param['train'] | main_param,
                        run_path / "train.sh", True)

        # init script file with parameters
        train_job.create_script()

        # run and wait
        train_job.schedule()
        train_job.wait_for_slurm_end()

        step = write_step(step + 1, run_path / "step")

    # locating the model to use + generating guesses
    if step == 2:
        # use manually inputted model if enabled
        if param['gen']['use_absolute_model']:
            logger.info("Absolute model usage is enabled!")
            logger.info("Attempting to load from param...")
            target_model = param['gen']['absolute_model_path']

        else:
            logger.info("Absolute model usage is disabled!")
            logger.info("Attempting to search for most recently modified Gweights file...")
            # find latest model file
            time_sorted_models = sorted([f for f in (run_path / "model").iterdir() if f.is_file()], key = lambda x: x.stat().st_mtime)
            target_model = ""

            for f in time_sorted_models:
                if f.name.startswith("Gweights"):
                    logger.info(f"Last modified Gweights file: {f.name}")
                    target_model = f.name
                    break

        if target_model == "":
            logger.critical("No model found!")
            logger.critical("Ending program...")
            sys.exit()

        logger.info(f"Found model {target_model}!")
        
        logger.info("Attempting to generate guesses...")
        # init generation job object
        gen_job = Job(co_gans_path / "CO_GANs_SCFT/running/auto_running/generate_template.sh",
                    param['gen']['slurm'] | param['gen'] | main_param | {"gweights": target_model},
                    run_path / "generate.sh", True)

        # init script file with parameters
        gen_job.create_script()

        # schedule and wait
        gen_job.schedule()
        gen_job.wait_for_slurm_end()

        logger.info("Successfully generated guesses!")

        # move data.pt and model if enabled
        if main_param['move']:
            logger.info("Moving is enabled!!!")
            logger.info(f"Making directories for move path at {move_path}")
            move_path.mkdir(parents = True, exist_ok = True)
            logger.info(f"Moving data.pt ({run_path / 'data.pt'}) to {move_path}")
            shutil.move(run_path / "data.pt", move_path)
            logger.info(f"Moving model ({run_path / 'model'}) to {move_path}")
            shutil.move(run_path / "model", move_path)

        step = write_step(step + 1, run_path / "step")

    # Step 3: init SCFT step 1
    if step == 3:
    # initialize SCFT step 1 directories
        prep_scft_1(run_path, co_gans_path, param)
        
        # move gan_guesses if enabled
        if main_param['move']:
            logger.info(f"Moving gan_guesses ({run_path / 'gan_guesses'}) to {move_path}")
            shutil.move(run_path / "gan_guesses", move_path)

        step = write_step(step + 1, run_path / "step")

    # Step 4: Run SCFT step 1
    if step == 4:
        # initialize SCFT 1 job object
        scft_1_job = BranchedJob(co_gans_path / "CO_GANs_SCFT/running/auto_running/scft_multi_template.sh",
                                param['scft_1']['slurm'] | param['scft_1'] | main_param,
                                run_path / "scft_multi.sh", True)

        # bind the callback function
        scft_1_job.callback = scft_callback

        # init script (no multi)
        scft_1_job.create_script()

        # schedule and wait
        # as this uses the scft_callback function, it will continue rescheduling
        # unfinished calculations with longer times until none are left
        scft_1_job.schedule()
        scft_1_job.wait_for_slurm_end()

        step = write_step(step + 1, run_path / "step")

    # Step 5: Collect SCFT step 1 data
    if step == 5:
        # collect csv data
        scft_1_to_csv(run_path)

        # get convergence info
        scft_1_conv(run_path, param)

    # Step 6: Prepare SCFT step 2
    if step == 6:
        # prepare for scft step 2
        prep_scft_2(run_path, co_gans_path, param)

        step = write_step(step + 1, run_path / "step")

    # Step 7: Run SCFT step 2
    if step == 7:
        # use code from print_dirs.py to find which ones are left, in array form
        scft_2_calcs = scft_array_timeout_check(str(run_path / param['scft_2']['job_dir_name']))

        # initialize SCFT 2 job object
        # make a dict for the array from scft_2_calcs
        scft_2_job = BranchedJob(co_gans_path / "CO_GANs_SCFT/running/auto_running/scft_multi_2_template.sh",
                                    param['scft_2']['slurm'] | param['scft_2'] | main_param | {"array": scft_2_calcs},
                                    run_path / "scft_multi_2.sh", True)

        # bind the callback function
        scft_2_job.callback = scft_callback

        # init script (no multi)
        scft_2_job.create_script()

        # schedule and wait
        # as this uses the scft_callback function, it will continue rescheduling
        # unfinished calculations with longer times until none are left
        scft_2_job.schedule()
        scft_2_job.wait_for_slurm_end()

        step = write_step(step + 1, run_path / "step")

    # Step 8: Collect SCFT step 2 data
    if step == 8:
        # collect csv data
        scft_2_to_csv(run_path)

        # get convergence info
        scft_2_conv(run_path, param)

        step = write_step(step + 1, run_path / "step")   

main()

# logging.basicConfig(level = logging.INFO, filename = "test.txt", format='%(asctime)s [%(levelname)s] %(message)s')

# print(load_params(["param.json", "custom.json"]))