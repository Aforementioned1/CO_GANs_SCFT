#!/bin/bash -l
#SBATCH --job-name=CO_AUTO_RUN_14
#SBATCH --output=/projects/standard/dorfmank/shared/mumma026_holm0994/trial_14/auto_%j.out
#SBATCH --error=/projects/standard/dorfmank/shared/mumma026_holm0994/trial_14/auto_%j.err
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=200m
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mumma026@umn.edu

### This is a skeleton script, containing some placeholder values (with curly braces)
### To fix these, use auto_run.py

# make sure to load venv!!!
source /users/0/mumma026/CO_GANs_SCFT/.venv/bin/activate

cd /users/0/mumma026/CO_GANs_SCFT/running/auto_running

# generate guesses (could maybe be done outside of a job)
python auto_run.py /projects/standard/dorfmank/shared/mumma026_holm0994/trial_14/log.txt param.json custom.json

# deactivate venv after to be safe
deactivate