# this script no longer uses Slurm configs, as it can be easily run
# LOCALLY (running on MSI file access will be too slow)

# load environemnt variables
source ~/CO_GANs_SCFT/running/run_env.sh

# make sure to load venv!!!
source ~/CO_GANs_SCFT/.venv/bin/activate

# generate guesses (could maybe be done outside of a job)
python generate_guess.py --weight_path ../running/$RUN_NAME/model/Gweights_45.pt --out_dir ../running/$RUN_NAME/gan_guesses --num_images 5000

# deactivate venv after to be safe
deactivate