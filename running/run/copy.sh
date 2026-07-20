# get env variables
source ../run_env.sh

# make local directories
mkdir -p ../$RUN_NAME/model

# copy
scp msi:~/CO_GANs_SCFT/running/$RUN_NAME/model/$GWEIGHTS ../$RUN_NAME/model/Gweights.pt