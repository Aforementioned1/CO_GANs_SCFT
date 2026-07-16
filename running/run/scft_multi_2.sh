#!/bin/bash -l
#SBATCH --job-name=CO_SCFT_array
#SBATCH --output=/users/0/mumma026/CO_GANs_SCFT/running/log/scft_2/scft_%A/%a.out
#SBATCH --error=/users/0/mumma026/CO_GANs_SCFT/running/log/scft_2/scft_%A/%a.err
#SBATCH --array=1-100
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1200m
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mumma026@umn.edu

# Run multiple SCFT step 2 processes with Slurm arrays

echo "--- Running task number: $SLURM_ARRAY_TASK_ID ---"

# change to cloned Github directory in home to begin running things
cd ~/CO_GANs_SCFT/running

# load environemnt variables
source ~/CO_GANs_SCFT/running/run_env.sh

# load python 3.10.9 (hopefully will work, this project has been tested on 3.11.15)
module load python3/3.10.9_anaconda2023.03_libmamba

# load dependencies of PSCF
module load fftw/3.3.6-double-gnu-7.2.0
module load cuda

# make sure to load venv!!!
source ~/CO_GANs_SCFT/.venv/bin/activate

# do scft stuff
python run_one.py $RUN_NAME/scft_2/$SLURM_ARRAY_TASK_ID $RUN_NAME/data/scft_2_timings.csv

# deactivate venv after to be safe
deactivate

echo "--- Task number: $SLURM_ARRAY_TASK_ID finished! ---"