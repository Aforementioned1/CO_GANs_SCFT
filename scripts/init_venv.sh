#!/bin/bash
# This script creates a venv within the directory ~/CO_GANs_SCFT, if it exists

# edit this to install elsewhere
DIR = "~/CO_GANs_SCFT"

# load python - use 3.10.9 due to GANs_SCFT's old code
module load python3/3.10.9_anaconda2023.03_libmamba

# exit if the directory doesn't exist
if [ ! -d "$DIR" ]; then
    echo "Directory $DIR does not exist."
    echo "Has the Github repository been cloned?"
    exit 1
fi

echo "Directory $DIR exists. Creating virtual environment..."

# assumes this repo has already been cloned
# make sure you are in the right directory!
cd $DIR

# initial venv
python -m venv .venv

# activate venv
source .venv/bin/activate

# install requirements (directory should work out because of the earlier cd command)
pip install -r requirements.txt

# exit venv when done
deactivate