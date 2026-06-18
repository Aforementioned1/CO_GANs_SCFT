# GANs_SCFT - Easy usage extension

<!-- TABLE OF CONTENTS -->
## Table of Contents
- [A Note on the Purpose of This Fork](#a-note-on-the-purpose-of-this-fork)<!-- - [Overview](#overview) -->
- [Training Helpers](#training-helpers)
  - [Data Augmentation](#data-augmentation)
  - [Tensor Reshaping](#tensor-reshaping)
- [SCFT Helpers](#scft-helpers)
  - [File Preparation](#file-preparation)
- [Shell Script Helpers](#shell-script-helpers)
  - [Virtual Environment Initializer](#virtual-environment-initializer)
  - [Slurm Scheduler Scripts](#slurm-scheduler-scripts)

## A Note on the Purpose of This Fork
This repository is a fork from [GANs_SCFT](https://github.com/kdorfmanUMN/GANs_SCFT), originally authored by [Peng-Yu Chen](https://github.com/pengyuchen) and colleagues. The purpose of this fork is to provide utilities to help users connect the gaps left from GANs_SCFT's code, such as by provided advanced data augmentation helpers and more data compilation helpers. All Python files that provide utilities from this fork are currently located in the directory [`running`](./running). Additional Shellscript helper files are located in [`scripts`](./scripts). Finally, some examples of real file usages will later be located in [`usage`](./usage). See [`README.md`](../README.md) in the main directory for more detailed information on the purpose and utilities of the original repository.

<!-- ## Overview -->

## Training Helpers
The file [`training.py`](./training.py) contains helper functions for GAN training and data preparation.

#### Data Augmentation
One area that warrants the development of additional code to simplify the training proccess is the data preparation process. The main utility provided by GANs_SCFT is [`data_processor.py`](../preprocessing/data_processor.py). This file allows users to randomly upscale, translate, rotate, and downscale once again to create multiple diverse data points from one SCFT initial_guess. It also converts `.rf` initial guesses into `.pt` Pytorch tensors. The exact usage of this file within the paper [Gaming self-consistent field theory: Generative block polymer phase discovery](https://doi.org/10.1073/pnas.2308698120) is somewhat unclear, so the `training.py` helper for this program is currently underdeveloped. [`augment()`](./training.py#L55) currently reads a directory of `.rf` initial guesses, augments each once, and outputs them as `.pt` files to a specified directory.

#### Tensor Reshaping
A second area that is made easier with the use of `training.py` is tensor reshaping. GANs_SCFT's function [`process_files()`](../preprocessing/data_processor.py#L90) in `data_processor.py` presents one issue: the outputted tensor is of size 32,786 (32^3), while GANs_SCFT's training file [`GAN_train.py`](../train/GAN_train.py) requires a Y x 1 x 32 x 32 x 32-sized tensor. Thankfully, Pytorch possesses utility functions that allow for the reshaping of tensors. To simplify the process, the function [`fix_file()`](./training.py#L103) resizes a tensor of size 32,786 to be size 1 x 32 x 32 x 32, then outputs it. Additionally, it has the capability to detect and ignore tensors that are not 32,786-sized. Next, the function [`fix_files()`](./training.py#L144) is very similar to `fix_file()`, but instead runs `fix_file()` for each file in a specified directory. Finally, the function [`combine_tensors()`](./training.py#L182) takes a directory with several 1 x 32 x 32 x 32-sized Pytorch tensors and combines them into a single file, with a Y x 1 x 32 x 32 x 32 tensor (where Y is the amount of tensors combined).
NOTE: This function currently does not do any checking to make sure tensor dimensions are correct, and could potential through an error that way!

## SCFT Helpers
The file [`training.py`](./training.py) contains helper functions for preparing data from the GAN to be run through PSCF, running PSCF, and collecting/analyzing the results of PSCF.

#### File Preparation
After generating guesses with GANs_SCFT's program [`../postprocessing/generate_guess.py`](../postprocessing/generate_guess.py), files are outputted in the format `guess_x.rf`, where x represents the GAN's guess number (ex `guess_1.rf` or `guess_2.rf`). This is slightly problematic, as it is preferable to structure files each in their individual directory, as they are in both [PSCF's examples](https://github.com/dmorse/pscfpp/tree/master/examples) and GANs_SCFT's [Data Repository for U of M (DRUM) files](https://conservancy.umn.edu/items/ba70d027-ba90-4497-9260-8800022654ff). A sample file tree is depicted below:
.
├── 1
│   ├── out
│   │   ├── c.rf
│   │   ├── data
│   │   └── w.bf
│   ├── c.bf
│   ├── command
│   ├── log
│   ├── param
│   ├── rgrid.rf
│   ├── run
│   ├── w.bf
1: The guess number (in this example, 1)
out: Stores data outputted from PSCF
c.bf, w.bf, and log: Created during the process of running PSCF
command, param, and run: Files that are required for PSCF but can be used across various PSCF calculations
rgrid.rf: A PSCF initial guess

This stucture makes running PSCF considerably easier, as one must only run `./run` (or `source ./run` if they lack the execute permission) in order to execute a PSCF calculation. All output and intermediate files are saved locally, so it is clear which files are associated with which initial guess.
This documentation is currently unfinished! Sorry!

## Shell Script Helpers
The directory [`../scripts`](../scripts) contains some helpful Shell Script files. This section is currently underdeveloped, but will later include all scripts used for this project.

#### Virtual Environment Initializer
The file [`../scripts/init_venv.sh`](../scripts/init_venv.sh) contains a Shell Script program that automatically creates a virtual environment (venv) and installs all Python libraries required by this repository. By default, it attempts to search for the directory ~/CO_GANs_SCFT, but this can be altered by entering a command line argument. The program will print an error message and exit if the target directory does not exist. It is recommended to run the file via `./init_venv.sh` rather than using `source ./init_venv.sh`, as the terminal (or SSH connection) will be closed if the program exits this way. Also, this program attempts to load the module `python3/3.10.9_anaconda2023.03_libmamba` with the command `module load`, which is available on the Minnesota Supercomputing Institute (MSI), but may not be available on other computers or shared computing networks. Importantly, GANs_SCFT uses Python code from 2023, so using newer versions of Python (greater than or equal to 3.12)will cause an error. Therefore, the script uses Python 3.10.9.

#### Slurm Scheduler Scripts
MSI uses Slurm to schedule jobs. This fork provides some files that can run Slurm scripts. [`../scripts/batch.sh`](../scripts/batch.sh) contains the basic structure for a Slurm `sbatch` command, which can schedule a job. Note: This file currently only holds placeholder values for the partition and script name, so it will not run correctly!

This rest of this documentation is currently unfinished! Sorry!