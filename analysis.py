"""Analysis of the regular expression tests

$ python analysis.py
"""
import os
from utils import *
from methods import METHODS


def text_avg(data: dict[Callable, dict[int, list[float]]]):
    for method in data:
        print(method.__name__, method.__doc__)
        for length in sorted(data[method].keys()):
            t = sum(data[method][length]) / len(data[method][length])
            print("\t", str(length).ljust(5), t)


if __name__ == "__main__":
    if not os.path.exists(config().files.data_output):
        print(f"Missing the output file, {config().files.data_output}")
        exit(1)

    # method => length => [sorted times]
    data = dict((method, dict()) for method in METHODS)

    handle = open(config().files.data_output, "r")
    for line in handle.readlines():
        entry = OutputFileEntry.from_json_str(line)
        for method in data:
            times = data[method].get(entry.length, list())
            times.append(entry.get_time(method))
            data[method][entry.length] = times

    handle.close()
    for lengths in data.values():
        for times in lengths.values():
            times.sort()

    ### PERFORM ANALYSIS ON DATA

    text_avg(data)