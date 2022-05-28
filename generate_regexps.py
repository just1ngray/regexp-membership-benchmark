"""Generate the file of regular expressions according to configured values (config.yaml)

$ python generate_regexps.py
"""

import os
import sys
from FAdo.reex import str2regexp
from FAdo.cfg import REStringRGenerator
from utils import config


if __name__ == "__main__":
    if os.path.exists(config().files.regexps):
        print(f"Some regular expressions in {config().files.regexps} have already been generated.",
            "Please rename or delete files appropriately.")
        exit(1)

    print(f"Generating {config().gen.per_length} for each length {config().gen.lengths}")
    print(f"Over the alphabet: {config().gen.alphabet}\n")

    if not os.path.exists("data"): os.mkdir("data")
    with open(config().files.regexps, "w") as handle:
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
                height = str2regexp(regexp).starHeight()
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