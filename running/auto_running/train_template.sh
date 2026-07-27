#!/bin/bash -l
#SBATCH --job-name={TRAIN_NAME}_{NAME}
#SBATCH --output={LOG_PATH}/{NAME}/log/gan_%j.out
#SBATCH --error={LOG_PATH}/{NAME}/log/gan_%j.err
#SBATCH --time={TIME}
#SBATCH --ntasks={TASKS}
#SBATCH --cpus-per-task={CPUS}
#SBATCH --mem={MEM}
#SBATCH --gres={GRES}
#SBATCH --mail-type={MAIL_TYPE}
#SBATCH --mail-user={MAIL_USER}
#SBATCH --partition={PARTITION}

### This is a skeleton script, containing some placeholder values (with "{}")
### To fix these, use auto_run.py

# unload loaded modules
module purge

# change to cloned Github directory in home to begin running things
cd {CO_GANS_PATH}/CO_GANs_SCFT/train

# load python 3.10.9 (hopefully will work, this project has been tested on 3.11.15)
module load python3/3.10.9_anaconda2023.03_libmamba

# make sure to load venv!!!
source {CO_GANS_PATH}/CO_GANs_SCFT/.venv/bin/activate

mkdir -p {ABS_PATH}/{NAME}/model/images

#### NEED TO ADD MAKING model and model/out!!!!!!!!!!!!!

python GAN_train.py --dataroot {ABS_PATH}/{NAME}/data.pt \
    --out_dir_images {ABS_PATH}/{NAME}/model/images \
    --out_dir_model {ABS_PATH}/{NAME}/model \
    --batch_size {BATCH_SIZE} \
    --lr {LEARNING_RATE}

# deactivate venv after to be safe
deactivate