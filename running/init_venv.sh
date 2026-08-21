#!/bin/bash
# This script creates a venv within the directory ~/CO_GANs_SCFT, if it exists
# recommended to be run without source, as an error will close an SSH connection
if [[ "$1" == "" ]]; then
    # edit this to install elsewhere
    DIR=~/CO_GANs_SCFT
else
    # if a command line argument is passed in, make that the target directory
    DIR=$1
fi

echo "Target directory: $DIR"

# load python - use 3.10.9 due to GANs_SCFT's old code
# python3/3.10.9_anaconda2023.03_libmamba is a module on MSI
module load python3/3.10.9_anaconda2023.03_libmamba

# exit if the directory doesn't exist
if [ ! -d "$DIR" ]; then
    echo "Directory $DIR does not exist."
    echo "Has the Github repository been cloned?"
    # exit, will close an SSH connection if run with source
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