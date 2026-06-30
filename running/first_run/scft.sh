#!/bin/bash -l
#SBATCH --job-name=CO_GAN_training_SCFT
#SBATCH --output=~/CO_GANs_SCFT/running/first_run/log/scft_%j.out
#SBATCH --error=~/CO_GANs_SCFT/running/first_run/log/scft_%j.err
#SBATCH --time=1:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8g
#SBATCH --mail-type=ALL
#SBATCH --mail-user=blank@umn.edu

# change to cloned Github directory in home to begin running things
cd ~/CO_GANs_SCFT/running

# load python 3.10.9 (hopefully will work, this project has been tested on 3.11.15)
module load python3/3.10.9_anaconda2023.03_libmamba

# make sure to load venv!!!
source ~/CO_GANs_SCFT/.venv/bin/activate

# do scft stuff
python scft_example.py param.json

# deactivate venv after to be safe
deactivate