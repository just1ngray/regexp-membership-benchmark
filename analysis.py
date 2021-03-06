"""Analysis of the regular expression tests

$ python analysis.py data
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


def avg_word_length_per_regexp_length(data: dict[int, list[float]]):
    print("\nlen(re)", "fmean(word length)")
    for regexp_length in sorted(data.keys()):
        print(str(regexp_length).ljust(7), fmean(data[regexp_length]))

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
    datadir = get_output_dir()
    output_file = os.path.join(datadir, config().files.data_output)

    if not os.path.exists(output_file):
        print(f"Missing the output file, {output_file}. "
              f"First you must 'python run_benchmarks {datadir}'")
        exit(1)

    # method => length => [sorted times]
    data = dict((method, dict()) for method in METHODS)
    avg_word_len_per_re_len = dict()

    handle = open(output_file, "r")
    for line in handle.readlines():
        entry = OutputFileEntry.from_json_str(line)
        nwords = entry.nwords_acc + entry.nwords_rej

        lengths = avg_word_len_per_re_len.get(entry.length, list())
        lengths.append(entry.avg_word_length)
        avg_word_len_per_re_len[entry.length] = lengths

        for method in data:
            times = data[method].get(entry.length, list())
            times.append(entry.get_time(method) / nwords) # average time per word
            data[method][entry.length] = times

    handle.close()
    for lengths in data.values():
        for times in lengths.values():
            times.sort()

    ### PERFORM ANALYSIS ON DATA

    text_avg(data)
    avg_word_length_per_regexp_length(avg_word_len_per_re_len)
    display(data)
