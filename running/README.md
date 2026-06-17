# GANs_SCFT - Easy usage extension


<!-- TABLE OF CONTENTS -->
## Table of Contents
- [A Note on the Purpose of This Fork](#a-note-on-the-purpose-of-this-fork)
<!-- - [Overview](#overview) -->
- [Training Helpers](#training-helpers)
  - [Data Augmentation](#data-augmentation)
  - [Tensor Reshaping](#tensor-reshaping)
- [SCFT Helpers](#scft-helpers)

## A Note on the Purpose of This Fork
This repository is a fork from [GANs_SCFT](https://github.com/kdorfmanUMN/GANs_SCFT), originally authored by [Peng-Yu Chen](https://github.com/pengyuchen) and colleagues. The purpose of this fork is to provide utilities to help users connect the gaps left from GANs_SCFT's code, such as by provided advanced data augmentation helpers and more data compilation helpers. All files specific to this fork are currently located in the directory `running`. See [`README.md`](../README.md) in the main directory for more detailed information on the purpose and utilities of the original repository.

<!-- ## Overview -->

## Training Helpers
The file [`training.py`](./training.py) contains helper functions for GAN training and data preparation.

#### Data Augmentation
One area that warrants the development of additional code to simplify the training proccess is the data preparation process. The main utility provided by GANs_SCFT is [`data_processor.py`](../preprocessing/data_processor.py). This file allows users to randomly upscale, translate, rotate, and downscale once again to create multiple diverse data points from one SCFT initial_guess. It also converts `.rf` initial guesses into `.pt` Pytorch tensors. The exact usage of this file within the paper [Gaming self-consistent field theory: Generative block polymer phase discovery](https://doi.org/10.1073/pnas.2308698120) is somewhat unclear, so the `training.py` helper for this program is currently underdeveloped. [`augment()`](./training.py#L55) currently reads a directory of `.rf` initial guesses, augments each once, and outputs them as `.pt` files to a specified directory.

#### Tensor Reshaping
A second area that is made easier with the use of `training.py` is tensor reshaping. GANs_SCFT's function [`process_files()`](../preprocessing/data_processor.py#L90) in `data_processor.py` presents one issue: the outputted tensor is of size 32,786 (32^3), while GANs_SCFT's training file [`GAN_train.py`](../train/GAN_train.py) requires a Y x 1 x 32 x 32 x 32-sized tensor. Thankfully, Pytorch possesses utility functions that allow for the reshaping of tensors. To simplify the process, the function [`fix_file()`](./training.py#L103) resizes a tensor of size 32,786 to be size 1 x 32 x 32 x 32, then outputs it. Additionally, it has the capability to detect and ignore tensors that are not 32,786-sized. Next, the function [`fix_files()`](./training.py#L144) is very similar to `fix_file()`, but instead runs `fix_file()` for each file in a specified directory. Finally, the function [`combine_tensors()`](./training.py#L182) takes a directory with several 1 x 32 x 32 x 32-sized Pytorch tensors and combines them into a single file, with a Y x 1 x 32 x 32 x 32 tensor (where Y is the amount of tensors combined).
NOTE: This function currently does not do any checking to make sure tensor dimensions are correct, and could potential through an error that way!

## SCFT Helpers
This documentation is currently unfinished! Sorry!