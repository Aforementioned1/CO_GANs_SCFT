#!/bin/bash -l
# NOTE: --output and --error need absolute paths
#SBATCH --job-name=CO_GAN_training_SCFT
#SBATCH --output=~/CO_GANs_SCFT/running/first_run/log/gan_%j.out
#SBATCH --error=~/CO_GANs_SCFT/running/first_run/log/gan_%j.err
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=6g
#SBATCH --gres=gpu:1
#SBATCH --mail-type=ALL
#SBATCH --mail-user=blank@umn.edu
#SBATCH --partition=v100

# unload loaded modules
module purge

# change to cloned Github directory in home to begin running things
cd ~/CO_GANs_SCFT/train

# load python 3.10.9 (hopefully will work, this project has been tested on 3.11.15)
module load python3/3.10.9_anaconda2023.03_libmamba

# make sure to load venv!!!
source ~/CO_GANs_SCFT/.venv/bin/activate

#### NEED TO ADD MAKING model and model/out!!!!!!!!!!!!!

python GAN_train.py --dataroot ../running/first_run/data.pt --out_dir_images ../running/first_run/model/images --out_dir_model ../running/first_run/model

# deactivate venv after to be safe
deactivate