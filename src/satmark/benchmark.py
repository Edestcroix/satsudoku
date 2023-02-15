import argparse
import os
import shutil
from typing import List

from mdtable import RawTable, Table, TableMaker
from satcoder import Encoding, decode

from .conf import Config
from .satsolver import SatSolver
from .sattester import TestData, Tester, TestResult

# check if minisat is installed somewhere in $PATH
# if not, then the solver will not be able to run
if not shutil.which("minisat"):
    print("Minisat not found in $PATH. Please install minisat.")
    exit()

# load the config file
WORKING_DIR = os.getcwd()
CONFIG_FILE = f"{WORKING_DIR}/sat_config.json"
CONFIG = Config(f"{WORKING_DIR}/sat_config.json")


def main():
    parser = argparse.ArgumentParser(description="Run tests on the sudoku solver")

    args = setup_args(parser)

    if args.clean:
        shutil.rmtree(CONFIG["resultsDir"])
        exit(0)

    # if args.All is true, then flip the values of all the other
    # arguments to their opposite. This way, if -C is specified, the actions of
    # all other arguments are performed, unless they are also specified.
    # (this way, can say do all tests, but don't summarize, instead of
    # having to specify all the other arguments except summarize)
    if args.All:
        params = (
            True,
            not args.summarize,
            not args.keep,
            not args.decode,
            not args.markdown,
        )
    else:
        params = (args.all, args.summarize, args.keep, args.decode, args.markdown)

    if params[1] and not params[0]:
        print("Error: -S must be used with -a")
        exit(1)

    make_dirs()
    run_tests(args, params)


# make the output directories if they don't exist
def make_dirs() -> None:
    if os.path.isdir(CONFIG["cacheDir"]):
        shutil.rmtree(CONFIG["cacheDir"])
    os.mkdir(CONFIG["cacheDir"])
    if not os.path.isdir(CONFIG["resultsDir"]):
        os.mkdir(CONFIG["resultsDir"])


# prepare the arguments for the script
def setup_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
    )
    # add argument flag -t to specify which test to run
    # default is to run all tests
    parser.add_argument(
        "-t", "--test", type=str, default="", help="test to run (standard, hard)"
    )
    parser.add_argument(
        "-e",
        "--enc",
        type=str,
        default="",
        help="encoding to use (minimum, efficient, extended)",
    )
    parser.add_argument("-a", "--all", action="store_true", help="run all tests")
    parser.add_argument(
        "-k",
        "--keep",
        action="store_true",
        help="keep converted CNF files and solver output",
    )
    parser.add_argument(
        "-S", "--summarize", action="store_true", help="summarize results from -a"
    )
    parser.add_argument(
        "-d", "--decode", action="store_true", help="decode solved puzzles"
    )
    parser.add_argument(
        "-A", "--All", action="store_true", help="run all tests with all options"
    )
    parser.add_argument(
        "-c", "--clean", action="store_true", help="clean benchmark directory"
    )
    parser.add_argument(
        "-m",
        "--markdown",
        action="store_true",
        help="output solutions in markdown format",
    )
    return parser.parse_args()


# identify and run tests based on the arguments passed
def run_tests(args: argparse.Namespace, params: tuple) -> None:
    all_tests, summary, keep, decode, markdown = params
    if all_tests:
        # fail if -t or -e specified with -a
        if args.test != "" or args.enc != "":
            print("Error: -a/-C cannot be used with flags other -s")
            return
        test_all(summary, args.silent)
    else:
        run_single_test(args.enc, args.test, args.silent)

    if decode:
        decode_solutions(markdown)
        copy_solution_dir(args.silent)
    if keep:
        copy_working_dir(args.silent)
    else:
        shutil.rmtree(CONFIG["cacheDir"])


def run_single_test(enc: str, test: str, silent: bool) -> None:
    if enc in {"minimal", "efficient", "extended"}:
        encoding = Encoding[enc.upper()]
    elif not enc:
        encoding = Encoding.MINIMAL
    else:
        print("Error: invalid encoding")
        exit(1)

    out = f"{CONFIG['resultsDir']}test_results.md"

    test = test.capitalize() if test else CONFIG["defaultPuzzleSet"]
    if test not in CONFIG["puzzleSets"]:
        print("Error: invalid test")
        exit(1)

    test_data = TestData(silent, test, encoding, *CONFIG.puzzle_values(test))
    solver = SatSolver(test_data.num_puzzles, test, encoding)
    tester = Tester(test_data, solver)
    tester.test(out)


def print_if_not(b: bool, str: str) -> None:
    None if b else print(str)


def copy_solution_dir(silent: bool) -> None:
    out_dir: str = CONFIG["resultsDir"]
    # add trailing slash if not present
    if out_dir[-1] != "/":
        out_dir += "/"
    if os.path.isdir(f"{out_dir}solutions"):
        shutil.rmtree(f"{out_dir}solutions")
    shutil.move(f"{CONFIG['cacheDir']}solutions", out_dir)

    print_if_not(silent, f"Decoded solutions written to {out_dir}solutions")


def copy_working_dir(silent: bool) -> None:
    cache_dir = CONFIG["cacheDir"]
    out_dir = CONFIG["resultsDir"]
    # add trailing slash if not present
    if out_dir[-1] != "/":
        out_dir += "/"

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    if os.path.isdir(f"{cache_dir}fixed_cnf"):
        shutil.rmtree(f"{cache_dir}fixed_cnf")
    if os.path.isdir(f"{out_dir}{cache_dir}"):
        shutil.rmtree(f"{out_dir}{cache_dir}")
    try:
        shutil.move(cache_dir, out_dir)
    except Exception as e:
        print_if_not(
            silent,
            f"Failed to move CNF files and solver output to {out_dir}encodings",
        )
        print_if_not(silent, str(e))
    else:
        if os.path.isdir(f"{out_dir}encodings"):
            shutil.rmtree(f"{out_dir}encodings")
        os.rename(f"{out_dir}{cache_dir}", f"{out_dir}encodings")
        print_if_not(
            silent,
            f"Converted CNF files and solver output saved to {out_dir}encodings",
        )


def summarize(results: RawTable, puzzle_sets) -> None:
    sum_file = f"{CONFIG['resultsDir']}summary.md"
    # header is generated from the keys of the puzzles dict,
    # this allows for easy addition of tests with new puzzles
    # and the summary will automatically update

    def header_func(x):
        return f"Averages ― {puzzle_sets[x-1]} Puzzles"

    cols = [
        "Encoding",
        "Decisions",
        "Decision Rate (dcsns/sec)",
        "Propositions",
        "Proposition Rate (props/sec)",
        "CPU Time (seconds)",
    ]
    with open(sum_file, "w") as f:
        maker = TableMaker(sep_every=3, sep_func=header_func, new_line=False)
        f.write(maker.table("Results Summary", results, cols))


def test_all(summary: bool = False, silent: bool = False) -> None:
    out = CONFIG["resultsDir"]
    msg: str = "Testing {0} puzzles with {1} encoding..."
    print_if_not(silent, f"Running all tests, outputting to {out}")
    print_if_not(silent, "This may take a while...")

    tester = Tester(silent=silent)
    results: List[TestResult] = []
    i: int = 1

    # iterates through all test puzzle files and all encodings
    for test in CONFIG["puzzleSets"]:
        # update tester parameters when switching tests
        tester.update_params(
            TestData(True, test, Encoding.MINIMAL, *CONFIG.puzzle_values(test))
        )
        for enc in Encoding:
            name: str = enc.name.lower()
            t: str = test.lower()
            out_file: str = f"{out}{str(i).zfill(2)}-{t}-{name}.md"

            print_if_not(silent, format(msg.format(t, name)))
            tester.update_encoding(enc)
            results.append(tester.test(out_file))
            i += 1

    print_if_not(silent, "Done!")
    if summary:
        summarize(results, tuple(CONFIG["puzzleSets"].keys()))
        print_if_not(silent, f"Summary saved to {out}summary.md")


def decode_solutions(markdown: bool) -> None:
    # decode solutions from minisat output
    for test in CONFIG["puzzleSets"]:
        test = test.lower()
        in_dir = f"{CONFIG['cacheDir']}sat/{test}/"
        if os.path.exists(in_dir):
            decode_dir(f"solutions/{test}/", in_dir, markdown)


def decode_dir(out_dir: str, in_dir: str, markdown: bool) -> None:
    os.system(f"mkdir -p {CONFIG['cacheDir']}{out_dir}")
    # count how many files are in standard_dir
    count = len(list(os.listdir(in_dir)))
    maker = TableMaker()
    for i in range(count):
        filename = f"{in_dir}sudoku_{str(i + 1).zfill(2)}.out"
        # read file and pass to Sud.convert
        with open(filename, "r") as in_file:
            lines = in_file.readlines()

            sudoku = decode(lines[1])

            outfile = f"{CONFIG['cacheDir']}{out_dir}sudoku_{str(i + 1).zfill(2)}"

            output = (
                sudoku_to_table(sudoku, f"Solution {str(i+1).zfill(2)}", maker)
                if markdown
                else sudoku
            )
            outfile += ".md" if markdown else ".txt"

            with open(outfile, "w") as out:
                out.write(output)


def sudoku_to_table(sudoku: str, title: str, maker: TableMaker) -> Table:
    # convert a sudoku puzzle to a table
    cell_grid = sudoku.replace(" ", "").split("\n")
    cell_grid = [line for line in cell_grid if line != ""]
    cell_grid = [list(line) for line in cell_grid]
    dummy = [""] * 9
    cell_grid = [dummy] + cell_grid
    return maker.table(title, cell_grid)


if __name__ == "__main__":
    # didn't put this in main() because it's only called once,
    # and the values updated by this function should never change
    # again after this
    main()
