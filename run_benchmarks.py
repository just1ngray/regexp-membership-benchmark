"""Run the benchmarks for each generated regular expression.
1. Find a regular expression
2. Generate accepting words
3. Delete characters from accepting words to make rejecting words
4. Measure the time it takes each method to accept & reject each word
5. Output the results to an output file for later analysis

$ python run_benchmarks.py data
"""

from time import sleep, strftime
import os
import shutil
from multiprocessing import Process
from utils import *
from methods import *
from converters import RegExpConverter


def benchmark_regexp(regexp: str, datadir: str):
    # logging
    logfilename = f"tmp/{os.getpid()}.log"
    logfile = open(logfilename, "w")
    def writelog(*args, sep=" ", end="\n"):
        logfile.write(sep.join(str(arg) for arg in args) + end)
        logfile.flush()
    print("\t", regexp)
    writelog(strftime("%H:%M:%S") + ": REGEXP:", regexp, "\n========")

    # prepare the tests
    tree = RegExpConverter.str_to_regexp(regexp, sigma=config().gen.alphabet)
    writelog(strftime("%H:%M:%S") + ": Generating accepting words ... ")
    accepted = list(pairwise_language_generation(RegExpConverter.str_to_sre(regexp),
                                                max_timeout=config().max_pict_seconds))
    writelog(strftime("%H:%M:%S") + ": Done " + str(len(accepted)))
    writelog(strftime("%H:%M:%S") + ": Generating rejecting words ... ")
    rejected = list(find_rejected_words(tree.nfaPDDAG().evalWordP, accepted))
    writelog(strftime("%H:%M:%S") + ": Done " + str(len(rejected)) + "\n")

    nwords = len(accepted) + len(rejected)
    entry = OutputFileEntry(
        regexp=regexp,
        length=len(regexp.replace(Epsilon, "@").replace(EmptySet, "@")),
        nwords_acc=len(accepted),
        nwords_rej=len(rejected),
        avg_word_length=(sum(map(lambda w: len(w), accepted)) + sum(map(lambda w: len(w), rejected))) / nwords
        # all the times are default set to 0.0
    )

    # perform the tests
    for words, expected in [(accepted, True), (rejected, False)]:
        while len(words) > 0:
            w = words.pop()
            position = logfile.tell()
            output = f"{strftime('%H:%M:%S')}: '{w}'"
            writelog(output, end="")

            # words are popped, but list maintains capacity until we delete manually
            if len(words) % 100 == 0:
                del words[:len(words)]

            for method in METHODS:
                res, cpu_time = method(tree, w)
                assert res is expected, f"{regexp} using {method.__name__} should{'' if expected else ' not'} "\
                    f"have accepted {w}. Returned {res}"
                entry.add_time(method, cpu_time)

            logfile.seek(position)
            writelog(" "*len(output), end="") # overwrite the word
            logfile.seek(position)
            writelog(".", end="") # mark it as finished

    # write the results
    output_file = os.path.join(datadir, config().files.data_output)
    with open(output_file, "a") as file:
        file.write(entry.to_json() + "\n")

    # cleanup
    logfile.close()
    os.remove(logfilename)
    if os.path.exists(f"tmp/pict_{os.getpid()}.txt"):
        os.remove(f"tmp/pict_{os.getpid()}.txt")


if __name__ == "__main__":
    datadir = get_output_dir()
    regexps_file = os.path.join(datadir, config().files.regexps)
    regexps_todo_file = os.path.join(datadir, config().files.regexps_todo)

    if not os.path.exists(regexps_file):
        print(f"Expecting a file of regular expressions called {regexps_file}")
        print(f"It can be generated using 'python generate_regexps.py {datadir}'")
        exit(1)

    if not os.path.exists(regexps_todo_file):
        print(f"{regexps_todo_file} does not exist. Creating it from {regexps_file}")
        shutil.copy(regexps_file, regexps_todo_file)

    if not os.path.exists("tmp"):
        os.mkdir("tmp")

    DONE_MARKER = "= " # any line starting with this prefix is considered complete
    workers = dict()
    try:
        if not os.path.exists("data"): os.mkdir("data")
        with open(regexps_todo_file, "r+") as file:
            while True:
                linestart = file.tell()
                line = file.readline()

                # if reached the end of file, exit deligator
                if len(line) == 0:
                    break

                # if the line has been marked done, continue to next line
                if line.startswith(DONE_MARKER):
                    continue

                # do not exceed multiprocessing amount
                while len(workers) >= config().multiprocessing:
                    for proc in workers.copy():
                        if not proc.is_alive():
                            workers.pop(proc)
                    sleep(0.2)

                # mark the line as done by overwriting the beginning of the line with DONE_MARKER
                file.seek(linestart)
                file.write(DONE_MARKER)
                file.flush()
                file.readline() # go to the end of the line again

                # call the process
                regexp = line.removesuffix(os.linesep)
                proc = Process(target=benchmark_regexp, args=(regexp, datadir), name=f"Python-{regexp[:16]}")
                proc.start()
                workers[proc] = (linestart, line[:len(DONE_MARKER)])

        # keep the main thread alive until all workers exit
        while len(workers) > 0:
            for proc in workers.copy():
                if not proc.is_alive():
                    workers.pop(proc)
            sleep(0.2)

        print("\n\nDone!")

    except KeyboardInterrupt:
        pass
    finally:
        with open(regexps_todo_file, "r+") as file:
            for proc in workers:
                linestart, repl = workers[proc]
                file.seek(linestart)
                file.write(repl)
                if proc.is_alive():
                    proc.kill()

    shutil.rmtree("tmp")