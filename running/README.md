# GANs_SCFT - Easy usage extension

<!-- TABLE OF CONTENTS -->
## Table of Contents
- [A Note on the Purpose of This Fork](#a-note-on-the-purpose-of-this-fork)<!-- - [Overview](#overview) -->
- [Training Helpers](#training-helpers)
  - [Data Augmentation](#data-augmentation)
  - [Tensor Reshaping](#tensor-reshaping)
- [SCFT Helpers](#scft-helpers)
  - [File Preparation](#file-preparation)
  - [Running PSCF](#running-pscf)
  - [Data Collection](#data-collection)
  - [Data Processing](#data-processing)
  - [Second SCFT Step](#second-scft-step)
- [Shell Script Helpers](#shell-script-helpers)
  - [Virtual Environment Initializer](#virtual-environment-initializer)
  - [Slurm Scheduler Scripts](#slurm-scheduler-scripts)
- [Examples](#examples)
  - [GAN Training Examples](#gan-training-examples)
  - [SCFT Examples](#scft-examples)
  - [JSON Parameters](#json-parameters)

## A Note on the Purpose of This Fork
This repository is a fork from [GANs_SCFT](https://github.com/kdorfmanUMN/GANs_SCFT), originally authored by [Peng-Yu Chen](https://github.com/pengyuchen) and colleagues. The purpose of this fork is to provide utilities to help users connect the gaps left from GANs_SCFT's code, such as by provided advanced data augmentation helpers and more data compilation helpers. All Python files that provide utilities from this fork are currently located in the directory `running`. Additional Shellscript helper files are located in [`scripts`](../scripts). Finally, some examples of real file usages will later be located in [`usage`](../usage). See [`README.md`](../README.md) in the main directory for more detailed information on the purpose and utilities of the original repository.

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
After generating guesses with GANs_SCFT's program [`../postprocessing/generate_guess.py`](../postprocessing/generate_guess.py), files are outputted in the format `guess_x.rf`, where x represents the GAN's guess number (ex `guess_1.rf` or `guess_2.rf`). This is slightly problematic, as it is preferable to structure files each in their individual directory, as they are in both [PSCF's examples](https://github.com/dmorse/pscfpp/tree/master/examples) and GANs_SCFT's [Data Repository for U of M (DRUM) files](https://hdl.handle.net/11299/257550). A sample file tree is depicted below:\
<code>.\
├── 1\
│   ├── out\
│   │   ├── c.rf\
│   │   ├── data\
│   │   └── w.bf\
│   ├── c.bf\
│   ├── command\
│   ├── log\
│   ├── param\
│   ├── rgrid.rf\
│   ├── run\
│   ├── w.bf\
</code>
1: The guess number (in this example, 1)\
out: Stores data outputted from PSCF\
c.bf, w.bf, and log: Created during the process of running PSCF\
command, param, and run: Files that are required for PSCF but can be duplicated and used across various PSCF calculations\
rgrid.rf: A PSCF initial guess

This stucture makes running PSCF considerably easier, as one must only run `./run` (or `source ./run` if they lack the execute permission) in order to execute a PSCF calculation. All output and intermediate files are saved locally, so it is clear which files are associated with which initial guess. To easily prepare a directory of GAN guesses to be run through PSCF, the function [`prepare_files()`](./run_scft.py#L13) has been added.

#### Running PSCF
While GANs_SCFT possesses the ability to generate initial guesses for PSCF, it does not provide a utility to easily run these guesses through PSCF. Additionally, the original repository does not contain any `param`, `command`, or `run` files to be used with this. To solve this issue, the functions [`run()`](./run_scft.py#L279), [`execute_dir()`](./run_scft.py#L323), and [`execute_num()`](./run_scft.py#L432) are included in this repository. `run()` runs a single PSCF calculation, and `execute_dir()` executes `run()` for each subdirectory in a provided input directory, in alphanumeric order. `execute_num()` allows users to specify a range of numerical directory names to execute, opening the possibility to run PSCF in numerical order. Both functions also have the optional ability to run "advanced checking", which searches existing `log` files to see if they either converged or reached the max amount of iterations (currently 2500) and does not rerun the calculation if so. Otherwise, the program will search for the existence of any `log` file at all. This can be problematic in the edge case when a calculation was started but did not converge or reach the maximum amount of iterations before being terminated. These three functions also support timing helpers, which allows users to understand and track how long PSCF calculations will likely take or are taking. `execute_dir()` and `execute_num()` additionally have the ability to output all timing data in CSV format to a specified file path. Finally, the directories [`first`](./first) and [`second`](./second) contain [`param`](./first/param), [`command`](./first/command), and [`run`](./first/run) files (see information on the second SCFT pass [here](#second-scft)). Although minor modifications were made to [`first`'s `command`](./first/command) due to a feature that has likely been removed from PSCF in a newer release and both `run` files were newly created, the other files were obtained from GANs_SCFT's [DRUM files](https://hdl.handle.net/11299/257550), in the DRUM directory `./Data_Generative_SCFT/post_scft`. These resources should enable users to easily execute PSCF for an entire directory of initial guesses.

#### Data Collection
After executing PSCF for many files, a natural next step is to analyze the data outputted. This fork provides utilities to read data from PSCF `log` files and to filter it into a more readable and malleable CSV file. The function [`to_csv()`](./run_scft.py#L552) searches for `log` files in the subdirectories of a given directory (in alphanumeric order), and records each subdirectory's name, whether each has a `log` file present, the number of iterations recorded in the `log` file, whether the initial guess converged, and the Helmholtz free energy value if it did converge. Similarly to [`execute_num()`](./run_scft.py#L432) (see [Running PSCF](#running-pscf) for more information), the function [`to_csv_num()`](./run_scft.py#L641) collects the same data as `to_csv()`, but only reads from directories named in a range of ints, allowing for the creation of CSV files organized in numerical order.

#### Data Processing
This repository also provides various utilities to further analyze collected data. The function [`read_csv_col()`](./run_scft.py#L879) loads a specified CSV column from a specified CSV file into a Python list. It also accepts a lambda as an argument (by default, `lambda text: text`), which allows users to automatically convert datatypes (which default to `str` when being read) into a more useful datatype, such as an `int` or `bool`. The next utility provided with this fork is [`is_close()`](./run_scft.py#L732), which takes two values and an epsilon (tolerance) value and determines whether the two values are close enough with the boolean expression `abs(item_2 - item_1) < epsilon`. This is expanded on with the functions [`find_neighbors()`](./run_scft.py#L750) and [`find_neighbors_list()`](./run_scft.py#L812), which designate "clusters" within a given epsilon value of each other, and return those clusters. `find_neighbors()` returns a dict with the value of each cluster as keys and the number of constituents in the cluster as values. Meanwhile, `find_neighbors_list()` takes an additional list of names, and returns a dict with the value of each cluster as keys and a list of the names of each constituent as values. This can be used to count the number of unique SCFT solutions, as solutions with a free energy that differs by < 10^-5 are usually the same solution. One issue with this method of classification is that a cluster of data which spans a range larger than epsilon will be classified in different ways based on how the data is sorted. Finally, the function [`find_true_names()`](./run_scft.py#L916) takes a list of boolean values and a list of string names (assumed to be of equal length), and returns a list of each name with a corresponding boolean value that is true. This, when combined with `to_csv()` (or `to_csv_num()`) from the previous section and `read_csv_col()` can be used to determine which PSCF initial guesses converged. It is also used to initialize the second step of SCFT (see below for more information)

#### Second SCFT Step
In the paper [Gaming self-consistent field theory: Generative block polymer phase discovery](https://doi.org/10.1073/pnas.2308698120), the authors ran a modified version of SCFT with a lower tolerance after the initial run. This "second step" can be found in the [DRUM](https://hdl.handle.net/11299/257550) directory `./Data_Generative_SCFT/post_scft/scft_step2`. Each initial guess for step 2 uses the outputted `w.bf` file from step 1, and new `param` and `command` files. Any solutions that did not converge during step 1 were completely omitted. Additionally, some changes must be made in order to "fix" `w.bf` files. The changes are:
- crystal_system must be changed from "orthorhombic" to "triclinic" (line 5)
- N_cell_param must be changed from "3" to "6" (line 7)
- The numbers "0.000    0.000    1.5707963" must be appended to cell_param (line 9)
- The number of basis functions must be changed from "32786" to "17000" (line 15)

To reinitialize outputs from the first SCFT step to be run again, the function [`prepare_files_second()`](./run_scft.py#L65) is included in this fork. It initializes new directories for all included subdirectories in a specified directory. The subdirectories to include must be specified, as only solutions that converged during step 1 should be reinitialized. One can easily obtain a list to be used with this function with the function [`find_true_names()`](./run_scft.py#L916) (see the previous section for more information).\
Once these directories have been initialized, the functions [`fix_w_basis()`](./run_scft.py#L138) and [`fix_w_basis_dir()`](./run_scft.py#L186) can be used to automatically apply the aforementioned changes to `w.bf` files. `fix_w_basis()` applies the fix to a single file, and `fix_w_basis_dir()` applies the fix to every (unignored, see note below) subdirectory with a `w.bf` file present. `fix_w_basis_dir()` also optionally appends the name of every directory it fixes to a CSV file, for reuse as a list of ignored names later.\
NOTE: If `fix_w_basis()` is run on the same file twice, it will currently append the new additions twice! `fix_w_basis_dir()` allows for a list of "ignored names" that have already been fixed to be skipped.\
NOTE: `fix_w_basis_dir()` currently does not write a CSV header to the specified file to write ignored names to, so users must prepend a header (such as "names\n") to read it with `read_csv_col()` (see [Data Processing](#data-processing)) or other CSV interpreters. This will be changed in a later version!
Once these helper functions have been run to prepare the second step of SCFT, the same execution functions may be used to run PSCF (see [Running PSCF](#running-pscf)).

## Shell Script Helpers
The directory [`../scripts`](../scripts) contains some helpful Shell Script files. This section is currently underdeveloped, but will later include all scripts used for this project.

#### Virtual Environment Initializer
The file [`../scripts/init_venv.sh`](../scripts/init_venv.sh) contains a Shell Script program that automatically creates a virtual environment (venv) and installs all Python libraries required by this repository. By default, it attempts to search for the directory ~/CO_GANs_SCFT, but this can be altered by entering a command line argument. The program will print an error message and exit if the target directory does not exist. It is recommended to run the file via `./init_venv.sh` rather than using `source ./init_venv.sh`, as the terminal (or SSH connection) will be closed if the program exits this way. Also, this program attempts to load the module `python3/3.10.9_anaconda2023.03_libmamba` with the command `module load`, which is available on the Minnesota Supercomputing Institute (MSI), but may not be available on other computers or shared computing networks. Importantly, GANs_SCFT uses Python code from 2023, so using newer versions of Python (greater than or equal to 3.12)will cause an error. Therefore, the script uses Python 3.10.9.

#### Slurm Scheduler Scripts
MSI uses Slurm to schedule jobs. This fork provides some files that can run Slurm scripts. [`../scripts/batch.sh`](../scripts/batch.sh) contains the basic structure for a Slurm `sbatch` command, which can schedule a job. Note: This file currently only holds placeholder values for the partition and script name, so it will not run correctly!

The rest of this documentation is currently unfinished! Sorry!

## Examples
This section describes the examples provided by this fork. With them, one can easily set up and run a GAN training or SCFT calculation session in mere seconds.

#### GAN Training Examples
There are currently no examples for this part of the process, as it is underdeveloped. Be on the lookout for more information in future commits.

#### SCFT Examples
The file [`scft_example.py`](./scft_example.py) provides critical utilities for the SCFT section of the project. This file performs all steps necessary for the entire two-step SCFT process, by:
- Preparing directories for the files directly outputted from the GAN for initial SCFT calculations (see [File Preparation](#file-preparation))
- Running the first pass of SCFT with the previously prepared files (see [Running PSCF](#running-pscf))
- Writing data from each SCFT trajectory to a CSV file for easy processing (see [Data Collection](#data-collection))
- Reading from the CSV file to find which trajectories converged after the first SCFT pass (see [Data Processing](#data-processing))
- Initializing directories for the second SCFT pass with all converged trajectories (see [Second SCFT Step](#second-scft-step))
- Fixing all w.bf files from the first SCFT pass to agree with the parameter files of the second pass (and skipping any ignored directory names) (see [Second SCFT Step](#second-scft-step))
- Running the second pass of SCFT with the previously prepared files (see [Running PSCF](#running-pscf))
- Writing data from each second-pass SCFT trajectory to a CSV file for easy processing (see [Data Collection](#data-collection))

`scft_example.py` accepts a JSON parameter file as a command line argument. A [sample parameter file](./defaults.json) with default values is provided with this repository. To use it with `scft_example.py`, run the following command:\
`python scft_example.py defaults.json`\
If not file is passed into the program as a command line argument, it will immediately exit. If a parameter file is not properly structured or lacks some necessary keys, the program will likely throw an error (see [JSON's website](https://www.json.org/json-en.html) for some information on how JSON files are structured). Detailed information on all necessary parameters will be provided in a later version of this documentation. Please refer to [`defaults.json`](./defaults.json) to see what parameters must be provided for now.

#### JSON Parameters
The file explained in the previous section, `scft_example.py`, requires the input of a JSON parameter file to specify how the code should operate without needing to actually modify it. A list of each parameter and what it does is given below. While some parameters may seem redundant, this program is intended to give users as much customizability as possible without touching this program's code. Despite this, custom modifications to the code could help repurpose parameters into real use.
- step: The step the current program is on. In `scft_example.py`, this is a value from 0-9, inclusive, where 0 signifies a program that has not started and 9 signifies a program that has completely finished. The JSON parameter file that is inputted will automatically be rewritten with each step to update it. This allows the program to resume execution at the same place that it was halted.
- debug: Whether or not to print each `run_scft.py` method's debug information.
- gan_min: The lowest GAN guess number to use. This will almost always be 0 or 1.
- gan_max: The highest GAN guess number to use. This depends on how high the program should search and how many GAN guesses were generated.
- scft_1: A JSON object with the same parameters as scft_2. Read more below.
- rf_name: The name to rename each GAN initial guess (`.rf`) file to. This should usually be `rgrid.rf`.
- name_col: The CSV column where subdirectory names are stored at. This will always be "name" unless you have modified the code of `run_scft.py`.
- conv_col: The CSV column where subdirectory names are stored at. This will always be "converged" unless you have modified the code of `run_scft.py`.
- scft_2: A JSON object with the same parameters as scft_1. Read more below.
- ignored_path: A path to a CSV file to read ignored directory names from. See [Second SCFT Step](#second-scft-step) for more information.
- ignored_col: The CSV column to read ignored names from in ignored_path (usually "name")
- w_in_name: The name of `w.bf` files to search for in unignored subdirectories in order to fix them for SCFT step 2 (usually "w.bf")
- w_out_name: The name of `w.bf` files to write fixed files to (usually "w.bf", though this will overwrite unfixed files if they are also named "w.bf").
- write_fixed_w_basis: Whether to write the names of the parent directories of every `w.bf` fixed in the program to a CSV file for later use as ignored_path.
- fixed_w_basis_path: Where to append names of the parent directories of every `w.bf` fixed in the program to, with each name separated by a new line (\n) character. See [Second SCFT Step](#second-scft-step) for more information.

The following parameters constitute an "SCFT block":
- The rest of this documentation is currently unfinished! Sorry!

The rest of this documentation is currently unfinished! Sorry!