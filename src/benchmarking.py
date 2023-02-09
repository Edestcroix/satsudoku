import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import List, Tuple

import src.convertCNF as Cnf
from src.convertCNF import Encoding
from src.tableMD import RawTable
from src.tableMD import create as create_table

TestResult = Tuple[str, str, str, str, str, str]
Averages = Tuple[str, str, str, str, str]

CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r") as f:
    CONFIG = json.load(f)

@dataclass
class TestData:
    silent: bool
    test_type: str
    enc: Encoding
    puzzle: str
    num_puzzles: int
    puzzle_lines: int
    lines_between: int


class SatSolver():
    __DECISIONS, __DECISION_RATE, __PROPS, __PROP_RATE, __TIME = range(5)

    def __init__(self, pc: int, test: str, enc=Encoding.MINIMAL) -> None:
        self.__puzzle_count: int = pc
        self.__in_dir: str = f"{CONFIG['cacheDir']}{enc.name.lower()}/{test.lower()}"
        self.__work_dir: str = f"{CONFIG['cacheDir']}sat/{test.lower()}/"
        self.__table_rows: RawTable = []
        self.params = {
            self.__DECISIONS: [],
            self.__DECISION_RATE: [],
            self.__PROPS: [],
            self.__PROP_RATE: [],
            self.__TIME: []
        }

    # Update the testing environment with the proper directories
    # when a new test is set or a new encoding is set
    def update_testing(self, test=None, enc=None, pc=None):
        if test:
            self.__work_dir = f"{CONFIG['cacheDir']}sat/{test.lower()}/"
        if enc:
            test = test or self.__work_dir.split("/")[-2]
            self.__in_dir = f"{CONFIG['cacheDir']}{enc.name.lower()}/{test.lower()}"
        if pc:
            self.__puzzle_count = pc

    def solve(self):
        # iterate through CNF output and call minisat on each
        os.system(f"mkdir -p {self.__work_dir}")

        for i in range(self.__puzzle_count):
            self.__solvePuzzle(i)

        results = (self.__computeAverages(), self.__table_rows.copy())
        self.__clear()
        return results

    def __clear(self) -> None:
        self.__table_rows: RawTable = []
        for key in self.params:
            self.params[key] = []

    def __getData(self, data):
        decision, _, decision_rate = re.findall(
            r"[-+]?\d*\.\d+|\d+", data[0])[:3]
        self.params[self.__DECISIONS].append(decision)
        self.params[self.__DECISION_RATE].append(decision_rate)
        decision_rate = f"{decision_rate} decisions/sec"

        props_data = tuple(re.findall(r"[-+]?\d*\.\d+|\d+", data[1])[:2])
        prop, p_rate = props_data
        self.params[self.__PROPS].append(prop)
        self.params[self.__PROP_RATE].append(p_rate)
        p_rate = f"{p_rate} props/sec"

        cpu = data[2].split(":")
        self.params[self.__TIME].append(cpu[1].strip().replace(" s", ""))

        return (decision.strip(), decision_rate.strip(),
                prop.strip(), p_rate, cpu[1].strip())

    def __solvePuzzle(self, i):
        filename = f"{self.__in_dir}/sudoku_{str(i + 1).zfill(2)}.cnf"
        outfile = f"{self.__work_dir}/sudoku_{str(i + 1).zfill(2)}.out"
        minisat = f"minisat {filename} {outfile}"

        # get output from minisat
        output = subprocess.Popen(minisat, shell=True,
                                  stdout=subprocess.PIPE).communicate()[0]

        output = output.decode("utf-8").split("\n")

        def want_line(
            l): return "CPU time" in l or "propagations" in l or "decisions" in l

        data = tuple(line for line in output if want_line(line))

        self.__table_rows.append(self.__getData(data))

    def __computeAverages(self) -> Averages:
        def av(x: List[str], r: int) -> str: return str(round(sum(float(x)
                                                                  for x in x) / len(x), r))
        lists: List[list] = list(self.params.values())
        times: list = self.params[self.__TIME]
        av_time: str = av(times, CONFIG['round']+2)
        averages: list = [av(test_results, CONFIG['round'])
                          for test_results in lists[:-1]] + [av_time]
        averages[self.__DECISION_RATE] = f"{averages[self.__DECISION_RATE]} decisions/sec"
        averages[self.__PROP_RATE] = f"{averages[self.__PROP_RATE]} props/sec"
        averages[self.__TIME] = f"{av_time} s"
        self.__table_rows.append(tuple(averages))

        return tuple(averages)


class Tester():
    def __init__(self, test_info: TestData, solver: SatSolver):
        self.__p: TestData = test_info
        self.solver: SatSolver = solver

    def update_params(self, test_info: TestData):
        self.__p = test_info
        self.solver.update_testing(
            test=test_info.test_type, enc=test_info.enc, pc=test_info.num_puzzles)

    def update_encoding(self, enc: Encoding):
        self.__p.enc = enc
        self.solver.update_testing(enc=enc)

    def test(self, out_dir: str) -> TestResult:
        enc = self.__p.enc
        working_dir = f"{CONFIG['cacheDir']}{enc.name.lower()}/{self.__p.test_type.lower()}"
        mkdir = f"mkdir -p {working_dir}"
        os.system(mkdir)
        with open(self.__p.puzzle, "r") as f:
            for i in range(self.__p.num_puzzles):
                for _ in range(self.__p.lines_between):
                    f.readline()
                puzzle = "".join(f.readline()
                                 for _ in range(self.__p.puzzle_lines))
                cnf = Cnf.convert(puzzle, enc)
                out_file = f"{working_dir}/sudoku_{str(i+1).zfill(2)}.cnf"
                with open(out_file, "w") as out:
                    out.write(cnf)

        averages, table_rows = self.solver.solve()

        self.__outputResults(table_rows, out_dir)
        return (enc.name.capitalize(), ) + averages

    def __outputResults(self, table_rows, out_dir):
        # add a header to the table, the number of puzzles
        # is specified by c, which will be the number of result tables.
        # after this, one more table will be added for the averages,
        # so once i passes c, the header will be changed to "Averages".
        def header_func(i):
            return f"Test {str(i).zfill(2)}" if i <= self.__p.num_puzzles else "Averages"

        if table_rows != []:
            cols = ("Decisions", "Decision Rate", "Propagations",
                    "Propagation Rate", "CPU Time")
            title = f"{self.__p.test_type} Test ({self.__p.enc.name.capitalize()} Encoding)"
            table = create_table(title, table_rows, cols,
                                 sep_every=1, new_line=False, sep_func=header_func)

            self.__print(table)

            if out_dir != "":
                out_dir = out_dir \
                    if out_dir[-4:] == ".txt" or out_dir[-3:] == ".md"\
                    else f"{out_dir}test_results.md"

                with open(out_dir, "w") as outfile:
                    outfile.write(table)

    def __print(self, str):
        None if self.__p.silent else print(str)
