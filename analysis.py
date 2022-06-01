"""Analysis of the regular expression tests

$ python analysis.py
"""
import os
from math import sqrt
from statistics import fmean, stdev
from scipy import stats
import matplotlib.pyplot as plt
from utils import *
from methods import METHODS


def text_avg(data: dict[Callable, dict[int, list[float]]]):
    for method in data:
        print(method.__name__, method.__doc__)
        for length in sorted(data[method].keys()):
            print("\t", str(length).ljust(5), fmean(data[method][length]))


def display(data: dict[Callable, dict[int, list[float]]]):
    fig, ax = plt.subplots()
    lines = {}

    # edit this for a different confidence level
    # CONFIDENCE_LEVEL% confident that our result is within standard error of mean
    CONFIDENCE_LEVEL = 0.95
    alpha = 1 - CONFIDENCE_LEVEL
    z_alpha_by_2 = stats.norm.ppf(1 - alpha/2)

    for method in data:
        lengths = []
        mean_times = []
        std_errs = []
        for length in sorted(data[method].keys()):
            times = data[method][length]
            lengths.append(length)
            mean_times.append(fmean(times))
            std_errs.append(z_alpha_by_2 * stdev(times)/sqrt(len(times)))

        line = ax.errorbar(
            x=lengths,
            y=mean_times,
            label=method.__name__,
            linewidth=1,
            yerr=std_errs,
            capsize=2.0
        )
        lines[method.__name__] = list(line)

    leg = ax.legend(fancybox=True, shadow=True, loc="upper left")
    handles, labels = ax.get_legend_handles_labels()
    handles = [h[0] for h in handles]
    leg = ax.legend(handles, labels, fancybox=True, shadow=True, loc="upper left")
    for text in leg.get_texts():
        text.set_picker(True)

    def on_pick(event):
        visibility = not lines[event.artist._text][0].get_visible()
        for component in lines[event.artist._text]:
            try:
                for drawable in component:
                    drawable.set_visible(visibility)
            except:
                component.set_visible(visibility)

        # BUG: requiring us to call both draw and draw_idle on MacOS
        # https://github.com/matplotlib/matplotlib/issues/22760
        fig.canvas.draw()
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("pick_event", on_pick)
    ax.set_title("Comparing average membership time for each method")
    ax.set_xlim(xmin=0.0)
    ax.set_xlabel("Length of the regular expression")
    ax.set_ylim(ymin=0.0)
    ax.set_ylabel("Mean time in seconds to decide membership\n"
                 f"(error bars define {CONFIDENCE_LEVEL * 100}% confidence interval)")
    plt.show()


if __name__ == "__main__":
    if not os.path.exists(config().files.data_output):
        print(f"Missing the output file, {config().files.data_output}. "
               "First you must 'python run_benchmarks'")
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
    display(data)
