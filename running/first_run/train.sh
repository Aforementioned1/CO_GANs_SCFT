#!/bin/bash -l
# these batch settings are just for example purposes,
#   and will be further configured once actually running jobs
#SBATCH --time=8:00:00               # Time for job, currently set to 8h
#SBATCH --ntasks=8                   # Number of processor cores to run on, currently set to 8
#SBATCH --mem=10g                    # Amount of memory, currently set to 10GB
#SBATCH --tmp = 10g                  # Amount of temporary storage, currently set to 10GB
#SBATCH --mail-type=ALL              # When to send update emails,
#                                        currently set to ALL (includes BEGIN, END, and FAIL)
#SBATCH --mail-users=blank@umn.edu   # Who to send emails to, currently set to a fake email address

# change to cloned Github directory in home to begin running things
cd ~/CO_GANs_SCFT/train

# load python 3.10.9 (hopefully will work, this project has been tested on 3.11.15)
module load python3/3.10.9_anaconda2023.03_libmamba

python GAN_train.py --dataroot ../running/first_run/data.pt --out_dir_images ../running/first_run/model/images --out_dir_model ../running/first_run/model
