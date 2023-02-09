import os
import re
import subprocess
from dataclasses import dataclass

import src.constants as c
import src.convertCNF as Cnf
from src.convertCNF import Encoding
from src.tableMD import create as create_table


@dataclass
class TestData:
    silent: bool
    test_type: str
    enc: Encoding
    puzzle: str
    num_puzzles: int
    puzzle_lines: int
    line_between: bool


class SatSolver():
    def __init__(self, puzzle_count: int, source_dir="") -> None:
        self.__puzzle_count = puzzle_count
        self.__in_dir = source_dir
        self.__work_dir = f"{c.CACHE_DIR}/sat/standard/" \
            if "standard" in self.__in_dir else f"{c.CACHE_DIR}/sat/hard/"
        self.__solver = "minisat"
        self.__table_rows, self.__decisions, self.__d_rates,\
            self.__props, self.__p_rates, self.__times = \
            [], [], [], [], [], []

    def set_source_dir(self, source_dir):
        self.__in_dir = source_dir
        self.__work_dir = f"{c.CACHE_DIR}/sat/standard/" \
            if "standard" in self.__in_dir else f"{c.CACHE_DIR}/sat/hard/"

    def set_puzzle_count(self, puzzle_count: int):
        self.__puzzle_count = puzzle_count

    def solve(self):
        # iterate through CNF output and call minisat on each
        os.system(f"mkdir -p {self.__work_dir}")

        for i in range(self.__puzzle_count):
            self.__solvePuzzle(i)

        results = (self.__computeAverages(), self.__table_rows.copy())
        self.__clear()
        return results

    def __clear(self):
        self.__table_rows, self.__decisions, self.__d_rates,\
            self.__props, self.__p_rates, self.__times = \
            [], [], [], [], [], []

    def __getData(self, data):
        decision, _, decision_rate = re.findall(
            r"[-+]?\d*\.\d+|\d+", data[0])[:3]
        self.__decisions.append(decision)
        self.__d_rates.append(decision_rate)
        decision_rate = f"{decision_rate} decisions/sec"

        props_data = tuple(re.findall(r"[-+]?\d*\.\d+|\d+", data[1])[:2])
        prop, p_rate = props_data
        self.__props.append(prop)
        self.__p_rates.append(p_rate)
        p_rate = f"{p_rate} props/sec"

        cpu = data[2].split(":")
        self.__times.append(cpu[1].strip().replace(" s", ""))

        return [decision.strip(), decision_rate.strip(),
                prop.strip(), p_rate, cpu[1].strip()]

    def __solvePuzzle(self, i):
        filename = f"{self.__in_dir}/sudoku_{str(i + 1).zfill(2)}.cnf"
        outfile = f"{self.__work_dir}/sudoku_{str(i + 1).zfill(2)}.out"
        minisat = f"{self.__solver} {filename} {outfile}"

        # get output from minisat
        output = subprocess.Popen(minisat, shell=True,
                                  stdout=subprocess.PIPE).communicate()[0]

        output = output.decode("utf-8").split("\n")

        def want_line(
            l): return "CPU time" in l or "propagations" in l or "decisions" in l

        data = tuple(line for line in output if want_line(line))

        self.__table_rows.append(self.__getData(data))

    def __computeAverages(self):
        lists = [self.__decisions, self.__d_rates,
                 self.__props, self.__p_rates]

        def avg(x): return round(sum(float(x)
                                     for x in x) / len(x), c.ROUND_AVG)
        av_time = round(sum(float(x) for x in self.__times) /
                        len(self.__times), c.ROUND_AVG+2)
        av_dec, av_d_rate, av_prop, av_rate = [
            avg(test_results) for test_results in lists]
        self.__table_rows.append([av_dec, f"{av_d_rate} decisions/sec", av_prop,
                                  f"{av_rate} props/sec", f"{av_time} s"])
        return (av_dec, av_d_rate, av_prop, av_rate, av_time)


class Tester():
    def __init__(self, test_info: TestData, solver: SatSolver):
        self.__p = test_info
        self.solver = solver

    def update_params(self, test_info: TestData):
        self.__p = test_info
        self.solver.set_puzzle_count(test_info.num_puzzles)

    def update_encoding(self, enc: Encoding):
        self.__p.enc = enc

    def test(self, out_dir: str):
        enc = self.__p.enc
        working_dir = f"{c.CACHE_DIR}/{enc.name.lower()}/{self.__p.test_type.lower()}"
        mkdir = f"mkdir -p {working_dir}"
        os.system(mkdir)
        with open(self.__p.puzzle, "r") as f:
            for i in range(self.__p.num_puzzles):
                if self.__p.line_between:
                    f.readline()
                puzzle = "".join(f.readline()
                                 for _ in range(self.__p.puzzle_lines))
                cnf = Cnf.convert(puzzle, enc)
                out_file = f"{working_dir}/sudoku_{str(i+1).zfill(2)}.cnf"
                with open(out_file, "w") as out:
                    out.write(cnf)

        self.solver.set_source_dir(working_dir)
        averages, table_rows = self.solver.solve()

        self.__outputResults(table_rows, out_dir)
        return (enc.name.lower(), ) + averages

    def __header(self):
        match self.__p.enc:
            case Encoding.EFFICIENT: enc = "Efficient"
            case Encoding.EXTENDED: enc = "Extended"
            case _: enc = "Minimal"
        return f"{self.__p.test_type} Test ({self.__p.enc} Encoding)"


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
            table = create_table(self.__header(), table_rows, cols,
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
