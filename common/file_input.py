from contextlib import contextmanager
from io import FileIO
from sys import argv
from itertools import islice
from csv import reader as csv_reader

@contextmanager
def open_file():
    if len(argv) < 2:
        print("No input file provided")
        exit(1)
    with open(argv[1], "r") as f:
        yield f

def assert_read(file: FileIO, expected):
    txt = file.read(len(expected))
    if txt != expected:
        raise AssertionError(f"Expected {expected} but got {txt}")

def read_csv(file: FileIO):
    return csv_reader(file, delimiter=",")