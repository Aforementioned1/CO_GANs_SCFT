""" This program is intended to be able to moderate and automate an entire
run through, from GAN training to SCFT step 2."""

""" FOR NOW, THIS ASSUMES THAT run_env.sh CONTAINS YOUR JSON PARAMETER'S "name" values as $RUN_NAME!!!!!! """

import subprocess
import sys
from enum import Enum
import json
from pathlib import Path
import shutil
import time

sys.path.append("/home/coasr2026/CO_GANs_SCFT/running") # change to running path

import run_scft
from datetime import timedelta
from datetime import datetime
import re

import logging
logger = logging.getLogger(__name__)

# JobType = Enum("JobType", "SINGLE SCFT_ARRAY")

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
    print(f"Attempting to replace template at {in_path}...")

    with open(in_path, "r") as f:
        text = f.read()

    repl = init_template(text, replace)

    with open(out_path, "w") as f:
        f.write(repl)

    print(f"Wrote file to {out_path}!")

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
                 slurm_path: str, auto_reschedule: bool, reschedule_add: str):
        self.job_id = "UNSCHEDULED"
        self.status = "UNSCHEDULED"
        self.template_path = template_path
        self.param = param
        self.slurm_path = slurm_path
        self.timeouts = 0
        self.auto_reschedule = auto_reschedule
        self.reschedule_add = reschedule_add

    def print_attrs(self, param = False):
        """ This is a debug method that prints all of this
        object's instance variables\n
        param: Whether to print the param dict"""
        print(f"Job ID: {self.job_id} | Status: {self.status}")
        print(f"Template Path: {self.template_path}")
        print(f"Slurm Path: {self.slurm_path}")
        print(f"Timeouts: {self.timeouts}")
        print(f"AutoRes: {self.auto_reschedule} | ResAdd: {self.reschedule_add}")
        if param:
            print(f"Param: {self.param}")

    def read_template(self):
        """ Reads all template parameters (enclosed in "{}") from
        this Job's template, and returns a list of all template parameters,
        including their enclosing {} characters"""
        print(f"Attempting to read template parameters at {self.template_path}...")
        regex = r"(\{.*?\})"

        with open(self.template_path, 'r') as f:
            text = f.read()

        params = list(set(re.findall(regex, text)))

        print("Done!")

        return params

    def create_script(self):
        """ Writes a script filling in the template parameters of this
        Job's template_path, writing the script to this Job's slurm_path"""
        print("Attempting to write template...")

        params = self.read_template()

        replacements = {}

        print("Attempting to locate parameters...")

        for p in params:
            if "\\" in p:
                replacements[p] = p.replace("\\", "")
                continue

            # convert template parameters (styled like {MY_PARAM}) to
            # lowercase dict keys (styled like my_param)
            p_target = p.strip("{}").lower()
            # set each template parameter to its corresponding dict parameter
            replacements[p] = self.param[p_target]

        print("Done!")

        init_template_file(self.template_path, self.slurm_path, replacements)

        # with open(self.template_path, "r") as f:
        #     text = f.read()

        # text = init_template(text, replacements)

        # with open(self.slurm_path, "w") as f:
        #     f.write(text)

        # print(f"Wrote file to {self.slurm_path}")

    def schedule(self):
        """ Schedules this job to run """
        print("Attempting to schedule job...")
        command = ["sbatch", "--parsable", self.slurm_path]
        result = subprocess.run(command, capture_output = True, text = True, check = True)

        print("Done!")
    
        # strip text to be safe
        self.job_id = result.stdout.strip()
        print(f"Result: {result.stdout} | Job ID: {self.job_id}")

        return self.job_id

    def check(self):
        """ Checks the current status of a specified Slurm job.
            If the job's status is FAILED, NODE_FAIL, or OUT_OF_MEMORY,
            reports it and ends the program. Otherwise, outputs the job's status."""
        print(f"Attempting to view job {self.job_id}'s status...")
        
        command = ["sacct", "--format=State", "--noheader", "-P", "-j", self.job_id]
        result = subprocess.run(command, capture_output = True, text = True, check = True)
    
        code = result.stdout.splitlines()[0]
        print(f"Job {self.job_id}'s code: {code}")
    
        # automatically exit if smth bad happens
        if code == "FAILED":
            print(f"Slurm job {self.job_id} ended with state FAILED!")
            print("Ending process...")
            sys.exit()
    
        if code == "NODE_FAIL":
            print(f"Slurm job {self.job_id} ended with state NODE_FAIL!")
            print("Ending process...")
            sys.exit()
    
        if code == "OUT_OF_MEMORY":
            print(f"Slurm job {self.job_id} ended with state OUT_OF_MEMORY!")
            print("Ending process...")
            sys.exit()
    
        return code

    def add_reschedule_time(self):
        """ Modifies this Job's time parameter by adding the rescheduling time to itself """
        add = self.reschedule_add
        curr = self.param['time']
        total = add_time_strings(curr, add)
        print(f"Current: {curr} | Addition: {add} | Total: {total}")
        print(f"Setting parameter time config to be {total}...")
        self.param['time'] = total
        print("Done!")
        print("Overwriting Slurm script...")
        self.create_script()
        print("Done!")

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
            print("This job has not been scheduled yet! Returning...")
            return

        finished = False

        while not finished:
            code = self.check()
            if code == "COMPLETED":
                finished = True
            if code == "TIMEOUT":
                print(f"Slurm job {self.job_id} timed out!")
                if self.auto_reschedule:
                    print("Auto reschedule is ON!")
                    print("Attempting to reschedule...")
                    self.timeouts += 1
                    self.add_reschedule_time()
                    self.schedule()
                    self.wait_for_slurm_end()
                else:
                    print("Auto reschedule is OFF!")
                    print("Ending process...")
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
    callback = lambda self: print("No specified callback. Continuing program...")

    def print_attrs(self, param=False):
        print(f"Job IDs: {self.job_ids}")
        print(f"Statuses: {self.statuses}")
        super().print_attrs(param)

    def schedule(self):
        """ Schedules a job for all of the items in the "array" key """
        for i, a in enumerate(self.param['array']):
            print(f"Attempting to schedule job {i}...")
            print(f"Prepping specific template...")
            init_template_file(f"{self.slurm_path.replace('.sh', '')}_no_array.sh", f"{self.slurm_path.replace('.sh', '')}_{i}.sh", {"{ARRAY}": a})
            print("Done!")

            command = ["sbatch", "--parsable", f"{self.slurm_path.replace('.sh', '')}_{i}.sh"]
            result = subprocess.run(command, capture_output = True, text = True, check = True)

            print("Done!")
        
            # strip text to be safe
            self.job_ids.append(result.stdout.strip())
            print(f"Result: {result.stdout} | Job ID: {self.job_id}")

        print(f"Scheduled {len(self.param['array'])} job(s) for all arrays!")

        return self.job_ids

    def create_script(self):
        """ Writes 
        Excludes the parameter "array" """
        print("Attempting to write template...")

        params = self.read_template()
        # remove array
        params.remove("{ARRAY}")

        replacements = {}

        print("Attempting to locate parameters...")

        for p in params:
            if "\\" in p:
                replacements[p] = p.replace("\\", "")
                continue

            # convert template parameters (styled like {MY_PARAM}) to
            # lowercase dict keys (styled like my_param)
            p_target = p.strip("{}").lower()
            # set each template parameter to its corresponding dict parameter
            replacements[p] = self.param[p_target]

        print("Done!")

        init_template_file(self.template_path, f"{self.slurm_path.replace('.sh', '')}_no_array.sh", replacements)

        # with open(self.template_path, "r") as f:
        #     text = f.read()

        # text = init_template(text, replacements)

        # with open(self.slurm_path + "_no_array", "w") as f:
        #     f.write(text)

        # print(f"Wrote file to {self.slurm_path}_no_array")

    def check(self):
        """ Checks the current status of a specified Slurm job.
            If the job's status is FAILED, NODE_FAIL, or OUT_OF_MEMORY,
            reports it and ends the program. Otherwise, outputs the job's status."""
        for i, j in enumerate(self.job_ids):
            print(f"Attempting to view job {j} (branch index {i})'s status...")

            command = ["sacct", "--format=State", "--noheader", "-P", "-j", j]
            result = subprocess.run(command, capture_output = True, text = True, check = True)
        
            code = result.stdout.splitlines()[0]
            print(f"Job {j} (branch index {i})'s code: {code}")

            # make sure to append it instead of setting the
            # value if the index doesnt exist yet
            if 0 <= i < len(self.statuses):
                self.statuses[i] = code
            else:
                self.statuses.append(code)
                if not (0 <= i < len(self.statuses)):
                    print(f"Warning: Code {code} not added to index {i} of statuses (job {j}, branch index {i}).")
            print(f"Added code {code} to statuses!")
        
            # automatically exit if smth bad happens
            if code == "FAILED":
                print(f"Slurm job {j} (branch index {i}) ended with state FAILED!")
                print("Ending process...")
                sys.exit()
        
            if code == "NODE_FAIL":
                print(f"Slurm job {j} (branch index {i}) ended with state NODE_FAIL!")
                print("Ending process...")
                sys.exit()
        
            if code == "OUT_OF_MEMORY":
                print(f"Slurm job {j} (branch index {i}) ended with state OUT_OF_MEMORY!")
                print("Ending process...")
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

    job.add_reschedule_time()

    # schedule and wait
    job.schedule()
    job.wait_for_slurm_end()

def run_python(path: str, args: list):
    command = ["python", path].extend(args)
    result = subprocess.run(command, capture_output = True, text = True, check = True)

    return result.stdout

def run_slurm(path: str):
    command = ["sbatch", "--parsable", path]
    result = subprocess.run(command, capture_output = True, text = True, check = True)

    # strip text to be safe
    return result.stdout.strip()



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
            print(f"DIR AMT reached! (dir_amt: {dir_amt}, groups: {groups})")
            if len(out_str) > 1:
                out_str = out_str.rstrip(",")
            if debug:
                print(out_str + "\n")
            out_strs.append(out_str)
            total_dirs += dir_amt
            dir_amt = 0
            out_str = ""
        if d.is_dir():
            if rev:
                log = d / "log"

                state = run_scft.get_state_cat(str(d), debug = debug)
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

    out_strs.append(out_str.rstrip(","))
    total_dirs += dir_amt

    if len(out_str) > 1:
        out_str = out_str.rstrip(",")

    for string in out_strs:
        print(string)
    print(f"Final directory amount: {dir_amt}\nTotal directory amount: {total_dirs}")

    return out_strs

def load_params(paths: list[str]):
    """ Attempts to load JSON parameters from all file paths in paths.
    This can be used to easily change small amounts of JSON parameters while
    keeping the original defaults intact\n
    NOTE: Any duplicate parameters in later files will automatically override
    existing duplicates from earlier files\n
    paths: A list of all paths to read. This program uses sys.argv[1:] by default"""
    # sys.argv[1:]
    if len(paths) != 0:
        print(f"{len(paths)} parameter files detected.")
        params = []

        for p in paths:
            print(f"Attempting to read input file at {p} for custom parameters.")
            with open(p, "r") as f:
                params.append(json.load(f))

        param = params[0]

        for p in params:
            param | p

        return param

    else:
        # end program if nothing is inputted
        print("No parameter file detected.")
        print("Ending program...")
        sys.exit()

def main():
    # load JSON parameters
    # using sys.argv for now

    logging.basicConfig(level = logging.INFO, filename = "test.log", format='%(asctime)s [%(levelname)s] %(message)s')

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

    # make run directory if it doesnt exist already
    if not run_path.exists():
        run_path.mkdir(parents = True, exist_ok = True)

    # copy 
    shutil.copy(param['data_path'], str(run_path / "data.pt"))

    train_job = Job(co_gans_path / "CO_GANs_SCFT/running/auto_running/train_template.sh",
                    param['train']['slurm'] | param['train'] | main_param, main_paths['run_path'] / "train.sh",
                    True, param['train']['slurm']['time_inc'])

    train_job.create_script()

    # make train.sh script
    make_train_script(train_param = param['train'], main_param = main_param)

    # schedule train script and wait for it to end
    job_id = run_slurm(str(run_path / "train.sh"))
    wait_for_slurm_end(job_id = job_id)

    # find latest model file
    time_sorted_models = sorted([f for f in (run_path / "model").iterdir() if f.is_file()], key = lambda x: x.stat().st_mtime)
    target_model = ""

    for f in time_sorted_models:
        if f.name.startswith("Gweights"):
            print(f"Last modified Gweights file: {f.name}")
            target_model = f.name
            break

    if target_model == "":
        print("No model found!")
        print("Ending program...")
        sys.exit()

    print(f"Found model {target_model}!")
    make_gen_script(param['gen'], main_param, target_model)
    print(f"Attempting to generate guesses...")

    # schedule generate script and wait for it to end
    job_id = run_slurm(str(run_path / "generate.sh"))
    wait_for_slurm_end(job_id = job_id)

    # move data.pt and model if enabled
    if main_param['move']:
        print(f"Making directories for move path at {move_path}")
        move_path.mkdir(parents = True, exist_ok = True)
        print(f"Moving data.pt ({run_path / 'data.pt'}) to {move_path}")
        shutil.move(run_path / "data.pt", move_path)
        print(f"Moving model ({run_path / 'model'}) to {move_path}")
        shutil.move(run_path / "model", move_path)

    # initialize SCFT step 1 directories
    # NOTE: need to make scft example param file (NOT DONE)
    run_python(co_gans_path / "CO_GANs_SCFT/running/scft_example.py", ["-p", (run_path / "example_param.json"), "-s", "PREP_SCFT_1"])

    # move gan_guesses if enabled
    if main_param['move']:
        print(f"Moving gan_guesses ({run_path / 'gan_guesses'}) to {move_path}")
        shutil.move(run_path / "gan_guesses", move_path)


    # make scft_multi.sh script
    make_scft_1_script(param['scft_1'], main_param)

    # schedule generate script and wait for it to end
    job_id = run_slurm(str(run_path / "scft_multi.sh"))
    wait_for_slurm_end(job_id = job_id)

    # find ones that didn't finish
    unfinished = scft_array_timeout_check("scft_1")

    # for sec in unfinished:
        
# print("{MY_PARAMETER}".strip("{}").lower())

# main()
