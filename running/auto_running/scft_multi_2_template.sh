#!/bin/bash -l
#SBATCH --job-name={SLURM_NAME}_{NAME}
#SBATCH --output={LOG_PATH}/{NAME}/log/scft_2/%A/%a.out
#SBATCH --error={LOG_PATH}/{NAME}/log/scft_2/%A/%a.err
#SBATCH --array={ARRAY}
#SBATCH --time={TIME}
#SBATCH --ntasks={NTASKS}
#SBATCH --cpus-per-task={CPUS}
#SBATCH --mem={MEM}
#SBATCH --mail-type={MAIL_TYPE}
#SBATCH --mail-user={MAIL_USER}

# Run multiple SCFT step 2 processes with Slurm arrays

echo "--- Running task number: $SLURM_ARRAY_TASK_ID ---"

# change to cloned Github directory in home to begin running things
cd {CO_GANS_PATH}/CO_GANs_SCFT/running

# load python 3.10.9 (hopefully will work, this project has been tested on 3.11.15)
module load python3/3.10.9_anaconda2023.03_libmamba

# load dependencies of PSCF
module load fftw/3.3.6-double-gnu-7.2.0
module load cuda

# make sure to load venv!!!
source {CO_GANS_PATH}/CO_GANs_SCFT/.venv/bin/activate

# do scft stuff
python run_one.py {ABS_PATH}/{NAME}/scft_2/$SLURM_ARRAY_TASK_ID {ABS_PATH}/{NAME}/data/scft_2_timings.csv

# deactivate venv after to be safe
deactivate

echo "--- Task number: $SLURM_ARRAY_TASK_ID finished! ---"