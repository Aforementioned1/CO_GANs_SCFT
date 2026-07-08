#!/bin/bash -l
# these batch settings are just for example purposes,
#   and will be further configured once actually running jobs
#SBATCH --time=8:00:00               # Time for job, currently set to 8h
#SBATCH --ntasks=8                   # Number of processor cores to run on, currently set to 8
#SBATCH --mem=10g                    # Amount of memory, currently set to 10GB
#SBATCH --tmp = 10g                  # Amount of temporary storage, currently set to 10GB
#SBATCH --mail-type=ALL              # When to send update emails,
#                                        currently set to ALL (includes BEGIN, END, and FAIL)
#SBATCH --mail-user=blank@umn.edu   # Who to send emails to, currently set to a fake email address

# change to cloned Github directory in home to begin running things
cd ~/CO_GANs_SCFT/postprocessing

# load python 3.10.9 (hopefully will work, this project has been tested on 3.11.15)
module load python3/3.10.9_anaconda2023.03_libmamba

# make sure to load venv!!!
source ~/CO_GANs_SCFT/.venv/bin/activate

# generate guesses (could maybe be done outside of a job)
python generate_guess.py --weight_path ../running/first_run/model/Gweights_45.pt --out_dir ../running/first_run/gan_guesses --num_images 5000

# deactivate venv after to be safe
deactivate