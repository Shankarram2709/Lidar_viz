#!/usr/bin/python3
import pandas as pd
import os
import glob
import sys
import argparse
from visualizer import Visualizer

if __name__ == '__main__':
    """
    Setup arguements for visualizer
    """
    parser               = argparse.ArgumentParser()
    parser.add_argument('-p','--pickle-files',     dest='pickle_file',        type=str, help='path to pickle file containing input data.',  default=None)
    parser.add_argument('-o','--output-path',    dest='output_path',      type=str, help='path to image/video output files.',  required=True)

    args = parser.parse_args()

    pickle_file_path = args.pickle_file
    output_path = args.output_path
    viz = Visualizer(pickle_file_path,output_path)
    viz.visualize()


