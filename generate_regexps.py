"""Generate the file of regular expressions according to configured values (config.yaml)

$ python generate_regexps.py data
"""

import os
import sys
from FAdo.cfg import REStringRGenerator
from utils import config, get_output_dir
from converters import RegExpConverter


if __name__ == "__main__":
    datadir = get_output_dir()
    regexps_file = os.path.join(datadir, config().files.regexps)

    if os.path.exists(regexps_file):
        print(f"Some regular expressions in {regexps_file} have already been generated.",
            "Please rename or delete files appropriately.")
        exit(1)

    print(f"Generating {config().gen.per_length} for each length {config().gen.lengths}")
    print(f"Over the alphabet: {config().gen.alphabet}\n")

    if not os.path.exists(datadir): os.mkdir(datadir)
    with open(regexps_file, "w") as handle:
        for regexp_length in config().gen.lengths:
            print(str(regexp_length).ljust(6), end="")
            sys.stdout.flush()

            regexp_generator = REStringRGenerator(
                Sigma=config().gen.alphabet,
                size=regexp_length,
                epsilon=config().gen.epsilon,
                empty=config().gen.empty
            )

            interval = max(1, config().gen.per_length // 40)
            n = 0
            while n < config().gen.per_length:
                regexp = regexp_generator.generate()

                # if the star height is too large, the pairwise language generation
                # strategy becomes extremely slow
                height = RegExpConverter.str_to_regexp(regexp).starHeight()
                if height > 2:
                    continue

                handle.write(f"{regexp}\n")
                n += 1
                if n % interval == 0:
                    print(".", end="")
                    sys.stdout.flush()

            handle.flush()
            print(u" \u2713") # check mark

    print("Done!")