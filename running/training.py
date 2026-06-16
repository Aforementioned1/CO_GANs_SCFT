""" This file contains functions related to data augmentation and GAN training """

import sys
# import os
import torch
from pathlib import Path

# don't need .env since we decided to fork
# # initialize .env
# from dotenv import load_dotenv
# load_dotenv()

# Make sure that the path to GANs_SCFT's "preprocessing"
# directory gets added so DataProcessor can be imported
# sys.path.append(os.getenv("PATH_TO_PREPROCESSING", "/GANs_SCFT/preprocessing"))
sys.path.append("../preprocessing")
from data_processor import DataProcessor

# sys.path.append("/home/coasr2026/gan_test2/GANs_SCFT/preprocessing")

def make_out_dir(out: Path, debug = False):
    """ Creates an out directory if it does not yet exist.\n
        Returns True if the directory exists or was created
        and returns False if the directory was not created"""
    # if out exists but isn't a directory, you're in trouble
    if out.exists() and not out.is_dir():
        # could be replaced with different crash behavior, such as throwing an error
            if debug:
                print(out, "exists, but is not a directory.")
            return False
    # if out does not exist create a directory at out
    if not out.exists():
        out.mkdir()
        if debug:
            print("A new directory was created at", out)
    # if out exists and is a directory, everything is ok :)
    else:
        if debug:
            print("A directory already exists at", str(out) + ". Nothing changed.")
    return True

def view_tensor(path: str, print_all: bool):
    """ Prints information about the tensor at path.\n
    path: A path to a tensor (.pt) file\n
    print_all: Whether to print all of the tensor's data """
    file_path = Path(path)
    if file_path.exists() and file_path.is_file():
        tensor = torch.load(path)
        print(tensor)
        print(tensor.shape)
        print(tensor.ndim)
    else:
        print(path, "does not exist or is not a file!")

def augment(in_path: str, out_path: str, debug = False):
    """ Uses GANs_SCFT's DataProcessor to process each initial
    guess in the provided directory once.\n
    in_path: A path to a directory with initial guesses
    (.rf files) to read from. Should not end in a trailing /\n
    out_path: A path to a directory to write to. Should not end in a trailing /\n
    debug: Whether to print extra information for debugging\n
    Note: You must set a PATH_TO_PREPROCESSING environment
    variable to be able to import DataProcessor\n
    Note 2: This function needs to be updated to work better!"""

    if (debug):
        print("Debug mode ON for augment")
        print("In path:", in_path)
        print("Out path", out_path)
    folder_path = Path(in_path)
    extension = "*.rf"

    # find all .rf files in path
    files = list(folder_path.glob(extension))

    # init processor here to avoid making a bunch
    processor = DataProcessor()

    # make sure out is a directory and create it if it doesn't exist
    out = Path(out_path)

    passed = make_out_dir(out, debug)
    # return if directory could not be created
    if not passed:
        if debug:
            print("Skipping...")
        return

    for f in files:
        path = str(f.resolve())
        name = f.name
        if debug:
            print("Resolved path:", path)
            print("Name:", name)

        # create out path with .pt file
        out_path_fin = out_path + "/" + name.rstrip(".rf") + ".pt"
        if debug:
            print("Finalized out path:", out_path_fin)

        processor.process_files(path, out_path_fin, [32, 32, 32])
        if debug:
            print("Processed", path, "to", out_path)

def fix_file(in_path: str, out_path: str, debug = False):
    """ Remaps "broken" 32,768-size tensors from DataProcessor into
    1 x 32 x 32 x 32 tensors in preparation for training.\n
    in_path: A path to a .pt file with a 32,768-size tensor.\n
    out_path: A path to a directory to write to. Should not end in a trailing /\n
    debug: Whether to print extra information for debugging\n
    Note 2: This function needs to be updated to be more efficient!"""
    # print debug info
    if debug:
        print("Debug mode ON for fix_file")
        print("In path: " + in_path)
        print("Out path: " + out_path)

    path = Path(in_path)
    if path.is_file():
        # only continue if path is a file
        tensor_og = torch.load(in_path)

        if debug:
            print("Loaded tensor from", in_path)
            print("Original tensor size:", tensor_og.size())

        if not tensor_og.shape == (32768,):
            print("Tensor at", in_path, "failed size verification! Skipping...")
            return
        else:
            print("Tensor at", in_path, "passed size verification!")

        # reshape to 32 x 32 x 32; requires tensor_og to be 32768 length
        tensor_3d = tensor_og.view(32, 32, 32)
        # add extra dimension as required by GANs_SCFT's GAN_train
        tensor_4d = tensor_3d.unsqueeze(0)


        torch.save(tensor_4d, out_path + "/" + path.name)
        if debug:
            print("Wrote tensor to", out_path)
    else:
        if debug:
            print(path, "does not exist or is not a file! Skipping file...")

def fix_files(in_path: str, out_path: str, debug = False):
    """ Remaps all "broken" 32,768-size tensors from DataProcessor
    that are in the directory in_path into 1 x 32 x 32 x 32 tensors
    in preparation for training.\n
    in_path: A path to a directory that stores .pt files with 32,768-size tensors.\n
    out_path: A path to a directory to write to. Should not end in a trailing /\n
    debug: Whether to print extra information for debugging\n """

    # print debug info
    if debug:
        print("Debug mode ON for fix_files")
        print("In path: " + in_path)
        print("Out path: " + out_path)

    dir_path = Path(in_path)

    if dir_path.is_dir():
        # make sure out is a directory and create it if it doesn't exist
        out = Path(out_path)
                
        passed = make_out_dir(out, debug)
        # return if directory could not be created
        if not passed:
            if debug:
                print("Skipping...")
            return
        
        # find all files with a .pt extension in in_path
        extension = "*.pt"

        files = list(dir_path.glob(extension))

        for f in files:
            fix_file(str(f), out_path, debug)
    else:
        if debug:
            print(in_path, "does not exist or is not a directory! Skipping...")

def combine_tensors(in_path: str, out_path: str, debug = False):
    """ Combines all "fixed" 1 x 32 x 32 x 32-size tensors from fix_files (and fix_file)
    that are in the directory in_path into a Y x 1 x 32 x 32 x 32-size tensor (where Y is the amount
    of files present in in_path) in preparation for training.\n
    in_path: A path to a directory that stores .pt files with 1 x 32 x 32 x 32-size tensors.\n
    out_path: A path to write the finalized tensor to\n
    debug: Whether to print extra information for debugging\n
    Note: this program currently accepts malformed tensors!!!"""

    # print debug info
    if debug:
        print("Debug mode ON for combine_tensors")
        print("In path: " + in_path)
        print("Out path: " + out_path)

    dir_path = Path(in_path)

    if dir_path.is_dir():
        # find all files with a .pt extension in in_path
        extension = "*.pt"

        files = list(dir_path.glob(extension))

        # add each tensor to a list in order to stack them
        tensor_list = []

        for f in files:
            tensor = torch.load(str(f))
            if debug:
                print("File:", str(f))
                print("Tensor size", tensor.size())
            tensor_list.append(tensor)

        # if debug:
        #     print("Tensors:", tensor_list)

        final_tensor = torch.stack(tensor_list, dim=0)
        if debug:
            print("Final shape: ", final_tensor.shape)

        # this one's probably overkill
        # out = Path(out_path)
        # if not out.exists() or out.is_file():
        torch.save(final_tensor, out_path)
        print("Wrote tensor to", out_path)
    else:
        if debug:
            print(in_path, "does not exist or is not a directory! Skipping...")

### TODO: ADD PARENT DIRECTORY RESOLUTION FOR OUTPUT PATHS TO BE SAFE
### TODO: ADD SAFEGUARD TO COMBINE_TENSORS TO PREVENT MALFORMED TENSORS FROM BEING INPUTTED



# augment("./initial_guesses", "./initial_guesses_hehe", True)
# fix_files("./initial_guesses_hehe", "./initial_guesses_hoho", True)
combine_tensors("./initial_guesses_hoho", "./initial_guesses_hoho/blabla.pt", True)