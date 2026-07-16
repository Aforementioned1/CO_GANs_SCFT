#!/bin/bash -l
#SBATCH --job-name=CO_GAN_training_SCFT
#SBATCH --output=/users/0/mumma026/CO_GANs_SCFT/running/log/gan_%j.out
#SBATCH --error=/users/0/mumma026/CO_GANs_SCFT/running/log/gan_%j.err
#SBATCH --time=01:00:00
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

# load environemnt variables
source ~/CO_GANs_SCFT/running/run_env.sh

# make sure to load venv!!!
source ~/CO_GANs_SCFT/.venv/bin/activate

mkdir -p ../running/$RUN_NAME/model/images

#### NEED TO ADD MAKING model and model/out!!!!!!!!!!!!!

python GAN_train.py --dataroot ../running/$RUN_NAME/data.pt \
    --out_dir_images ../running/$RUN_NAME/model/images \
    --out_dir_model ../running/$RUN_NAME/model \
    --batch_size 256
    --lr 0.0002

# deactivate venv after to be safe
deactivate