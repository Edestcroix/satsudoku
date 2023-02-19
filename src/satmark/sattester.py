import os
from dataclasses import dataclass
from typing import Tuple

from mdtable import TableMaker
from satcoder import Encoding, encode

from .conf import Config
from .satsolver import SatSolver

TestResult = Tuple[str, str, str, str, str, str]
Averages = Tuple[str, str, str, str, str]


CONFIG = Config(f"{os.getcwd()}/sat_config.json")


@dataclass
class TestData:
    silent: bool
    test_type: str
    enc: Encoding
    puzzles_dir: str
    num_puzzles: int
    offset: int
    size: int


class Tester:
    def __init__(self, test_info=None, solver=None, silent=False):
        if test_info is None:
            default_set = CONFIG["defaultPuzzleSet"]
            default = CONFIG["puzzleSets"][default_set]
            test_info = TestData(
                silent,
                test_type=default_set,
                enc=Encoding.MINIMAL,
                puzzles_dir=default["file"],
                num_puzzles=default["numPuzzles"],
                size=default["size"],
                offset=default["offset"],
            )
        if solver is None:
            solver = SatSolver(
                pc=test_info.num_puzzles, test=test_info.test_type, enc=test_info.enc
            )
        self.__p: TestData = test_info
        self.solver: SatSolver = solver
        self.__update_working_dir(test_info.enc, test_info.test_type)

    def test_name(self):
        return self.__p.test_type

    def update_params(self, test_info: TestData):
        self.__p = test_info
        self.solver.update_parameters(
            test=test_info.test_type, enc=test_info.enc, pc=test_info.num_puzzles
        )
        self.__update_working_dir(test_info.enc, test_info.test_type)

    def update_encoding(self, enc: Encoding):
        self.__p.enc = enc
        self.solver.update_parameters(enc=enc)
        self.__update_working_dir(enc, self.__p.test_type)

    def test(self, out_dir: str) -> TestResult:
        working_dir = self.__working_dir
        mkdir = f"mkdir -p {working_dir}"
        os.system(mkdir)

        self.__encode_puzzles(working_dir)

        averages, table_rows = self.solver.solve()

        self.__output_results(table_rows, out_dir)
        return (self.__p.enc.name.capitalize(),) + averages

    def __update_working_dir(self, enc: Encoding, test: str):
        self.__working_dir = f"{CONFIG['cacheDir']}{enc.name.lower()}/{test.lower()}"

    def __encode_puzzles(self, working_dir):
        enc = self.__p.enc
        with open(self.__p.puzzles_dir, "r") as f:
            for i in range(self.__p.num_puzzles):
                for _ in range(self.__p.offset):
                    f.readline()
                puzzle = "".join(f.readline() for _ in range(self.__p.size))
                # set write to true, so fixed cnf is cached
                test = self.__p.test_type
                # put fixed cnf in directory name with the test name, this way
                # if the program is mutltiproccessed, each process
                # generates its own cache file and there won't be
                # race conditions where one process reads an unfinished
                # cache file.
                cnf = encode(puzzle, enc, f"{CONFIG['cacheDir']}fixed_cnf/{test}/")

                out_file = f"{working_dir}/sudoku_{str(i+1).zfill(2)}.cnf"
                with open(out_file, "w") as out:
                    out.write(cnf)

    def __output_results(self, table_rows, out_dir):
        # add a header to the table, the number of puzzles
        # is specified by num_puzzles, which will be the number of result tables.
        # after this, one more table will be added for the averages,
        # so once i passes c, the header will be changed to "Averages".
        def header_func(i):
            return (
                f"Test {str(i).zfill(2)}" if i <= self.__p.num_puzzles else "Averages"
            )

        if table_rows != []:
            cols = (
                "Decisions",
                "Decision Rate (dcsns/sec)",
                "Propagations",
                "Propagation Rate (props/sec)",
                "CPU Time (sec)",
            )
            title = (
                f"{self.__p.test_type} Test ({self.__p.enc.name.capitalize()} Encoding)"
            )

            maker = TableMaker(sep_every=1, new_line=False, sep_func=header_func)

            table = maker.table(title, table_rows, cols)

            self.__print(table)

            if out_dir != "":
                out_dir = (
                    out_dir
                    if out_dir[-4:] == ".txt" or out_dir[-3:] == ".md"
                    else f"{out_dir}test_results.md"
                )

                with open(out_dir, "w") as outfile:
                    outfile.write(table)

    def __print(self, str):
        None if self.__p.silent else print(str)
