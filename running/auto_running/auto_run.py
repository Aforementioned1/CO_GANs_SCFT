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

JobType = Enum("JobType", "SINGLE ARRAY")

class Job:
    job_id: str
    time_schedule: datetime
    time_end: datetime
    status: str

    def __init__(self, job_id, status):
        self.job_id = job_id
        self.time_schedule = datetime.now()
        self.time_end = datetime(year=999)
        self.status = status

    # def __check__():
        

# class ArrayJob(Job):


def str_to_timedelta(time: str):
    """ Converts a string formatted like "HH:MM:SS" to a
    datetime timedelta object\n
    time: A string formatted like "HH:MM:SS" """
    h, m, s = time.split(":")
    delta = timedelta(hours = int(h), minutes = int(m), seconds = int(s))

    return delta

def timedelta_to_str(delta: timedelta):
    """ Converts a datetime.timedelta object into a string
    formatted like "HH:MM:SS\n
    delta: A timedelta object"""
    h = int(delta.total_seconds() // 3600)
    m = int((delta.total_seconds() % 3600) // 60)
    s = int(delta.total_seconds() % 60)

    return f"{h:02d}:{m:02d}:{s:02d}"

def run_python(path: str, args: list):
    command = ["python", path].extend(args)
    result = subprocess.run(command, capture_output = True, text = True, check = True)

    return result.stdout

def run_slurm(path: str):
    command = ["sbatch", "--parsable", path]
    result = subprocess.run(command, capture_output = True, text = True, check = True)

    # strip text to be safe
    return result.stdout.strip()

def slurm_check(job_id: str):
    """ Checks the current status of a specified Slurm job.
    If the job's status is FAILED, NODE_FAIL, or OUT_OF_MEMORY,
    reports it and ends the program. Otherwise, outputs the job's status.\n
    job_id: The Slurm job to check."""
    command = ["sacct", "--format=State", "--noheader", "-P", "-j", job_id]
    result = subprocess.run(command, capture_output = True, text = True, check = True)

    code = result.stdout.splitlines()[0]

    # automatically exit if smth bad happens
    if code == "FAILED":
        print(f"Slurm job {job_id} ended with state FAILED!")
        print("Ending process...")
        sys.exit()

    if code == "NODE_FAIL":
        print(f"Slurm job {job_id} ended with state NODE_FAIL!")
        print("Ending process...")
        sys.exit()

    if code == "OUT_OF_MEMORY":
        print(f"Slurm job {job_id} ended with state OUT_OF_MEMORY!")
        print("Ending process...")
        sys.exit()

    return code


def wait_for_slurm_end(job_id: str, period = 120.0):
    """ Periodically checks for a Slurm job to finish.
    If the Slurm job's status becomes "FAILED", "TIMEOUT", "NODE_FAIL" or
    "OUT_OF_MEMORY", terminates the program"""
    finished = False

    while not finished:
        code = slurm_check(job_id)
        if code == "COMPLETED":
            finished = True
        if code == "TIMEOUT":
            print(f"Slurm job {job_id} timed out!")
            print("Ending process...")
            sys.exit()

        time.sleep(period)

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

                state = run_scft.get_state_cat(d.absolute(), debug = debug)
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

def load_params(param_path: str):
    if param_path != None:
        print("Parameter file detected.")
        print(f"Attempting to read input file at {param_path} for custom parameters.")
        with open(param_path, "r") as f:
            param = json.load(f)

            # # add the scft_1 and scft_2 JSON objects to their
            # # own variables for easier access later
            # param_scft_1 = param["scft_1"]
            # param_scft_2 = param["scft_2"]

            # # add certain frequently used parameters as variables for easier access later
            # min = param["gan_min"]
            # max = param["gan_max"]
        
        return param

    else:
        # end program if nothing is inputted
        print("No parameter file detected.")
        print("Ending program...")
        sys.exit()

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

def make_train_script(train_param: dict, main_param: dict):
    print("Making train.sh script...")
    slurm_param = train_param['slurm']

    replacements = {
        "{TRAIN_NAME}": slurm_param['name'],
        "{NAME}": main_param['name'],
        "{LOG_PATH}": slurm_param['log_path'],
        "{TIME}": slurm_param['time'],
        "{TASKS}": slurm_param['ntasks'],
        "{CPUS}": slurm_param['cpus_per_task'],
        "{MEM}": slurm_param['mem'],
        "{GRES}": slurm_param['gres'],
        "{MAIL_TYPE}": slurm_param['mail_type'],
        "{MAIL_USER}": slurm_param['mail_user'],
        "{PARTITION}": slurm_param['partition'],
        "{CO_GANS_PATH}": main_param['co_gans_path'],
        "{ABS_PATH}": main_param['abs_path'],
        "{BATCH_SIZE}": train_param['batch_size'],
        "{LEARNING_RATE}": train_param['learning_rate']
    }

    with open((Path(main_param['co_gans_path']) / "CO_GANs_SCFT/running/auto_running/train_template.sh"), "r") as f:
        text = f.read()

    text = init_template(text, replacements)

    with open((Path(main_param['abs_path']) / main_param['name'] / "train.sh"), "w") as f:
        f.write(text)

    print(f"Wrote file to {(Path(main_param['abs_path']) / main_param['name'] / 'train.sh')}")

def make_gen_script(gen_param: dict, main_param: dict, gweights_name: str):
    print("Making generate.sh script...")
    slurm_param = gen_param['slurm']

    replacements = {
        "{GEN_NAME}": slurm_param['name'],
        "{NAME}": main_param['name'],
        "{LOG_PATH}": slurm_param['log_path'],
        "{TIME}": slurm_param['time'],
        "{TASKS}": slurm_param['ntasks'],
        "{CPUS}": slurm_param['cpus_per_task'],
        "{MEM}": slurm_param['mem'],
        "{MAIL_TYPE}": slurm_param['mail_type'],
        "{MAIL_USER}": slurm_param['mail_user'],
        "{CO_GANS_PATH}": main_param['co_gans_path'],
        "{ABS_PATH}": main_param['abs_path'],
        "{GWEIGHTS}": gweights_name
    }

    with open((Path(main_param['co_gans_path']) / "CO_GANs_SCFT/running/auto_running/generate_template.sh"), "r") as f:
        text = f.read()

    text = init_template(text, replacements)

    with open((Path(main_param['abs_path']) / main_param['name'] / "generate.sh"), "w") as f:
        f.write(text)

    print(f"Wrote file to {(Path(main_param['abs_path']) / main_param['name'] / 'generate.sh')}")        

def make_scft_1_script(scft_param: dict, main_param: dict):
    print("Making scft_multi.sh script...")
    slurm_param = scft_param['slurm']

    replacements = {
        "{SCFT_1_NAME}": slurm_param['name'],
        "{NAME}": main_param['name'],
        "{LOG_PATH}": slurm_param['log_path'],
        "{ARRAY}": slurm_param['array'],
        "{TIME}": slurm_param['time'],
        "{TASKS}": slurm_param['ntasks'],
        "{CPUS}": slurm_param['cpus_per_task'],
        "{MEM}": slurm_param['mem'],
        "{MAIL_TYPE}": slurm_param['mail_type'],
        "{MAIL_USER}": slurm_param['mail_user'],
        "{CO_GANS_PATH}": main_param['co_gans_path'],
        "{ABS_PATH}": main_param['abs_path'],
        "{SEC_SIZE}": int(5000 / scft_param['sections'])
    }

    with open((Path(main_param['co_gans_path']) / "CO_GANs_SCFT/running/auto_running/scft_multi_template.sh"), "r") as f:
        text = f.read()

    text = init_template(text, replacements)

    with open((Path(main_param['abs_path']) / main_param['name'] / "scft_multi.sh"), "w") as f:
        f.write(text)

    print(f"Wrote file to {(Path(main_param['abs_path']) / main_param['name'] / 'scft_multi.sh')}") 

def main():
    # load JSON parameters
    # using sys.argv for now
    param = load_params(sys.argv[1])

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
    shutil.copy(param['data_path'], (run_path / "data.pt").absolute())

    # make train.sh script
    make_train_script(train_param = param['train'], main_param = main_param)

    # schedule train script and wait for it to end
    job_id = run_slurm((run_path / "train.sh").absolute())
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
    job_id = run_slurm((run_path / "generate.sh").absolute())
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
    job_id = run_slurm((run_path / "scft_multi.sh").absolute())
    wait_for_slurm_end(job_id = job_id)

    # find ones that didn't finish
    unfinished = scft_array_timeout_check("scft_1")

    # for sec in unfinished:
        

main()