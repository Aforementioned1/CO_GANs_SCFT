# get env variables
source ../run_env.sh

# copy back
scp -r ../$RUN_NAME/gan_guesses msi:~/CO_GANs_SCFT/running/$RUN_NAME