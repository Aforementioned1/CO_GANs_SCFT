#!/bin/bash -l
#SBATCH --job-name={SLURM_NAME}_{NAME}
#SBATCH --output={LOG_PATH}/{NAME}/log/gen_%j.out
#SBATCH --error={LOG_PATH}/{NAME}/log/gen_%j.err
#SBATCH --time={TIME}
#SBATCH --ntasks={TASKS}
#SBATCH --cpus-per-task={CPUS}
#SBATCH --mem={MEM}
#SBATCH --mail-type={MAIL_TYPE}
#SBATCH --mail-user={MAIL_USER}

# make sure to load venv!!!
source {CO_GANS_PATH}/CO_GANs_SCFT/.venv/bin/activate

cd {CO_GANS_PATH}/CO_GANs_SCFT/postprocessing

# generate guesses (could maybe be done outside of a job)
python generate_guess.py --weight_path {ABS_PATH}/{NAME}/model/{GWEIGHTS} --out_dir {ABS_PATH}/{NAME}/gan_guesses --num_images 5000

# deactivate venv after to be safe
deactivate