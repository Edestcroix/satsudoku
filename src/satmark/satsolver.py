import json
import os
import re
import subprocess
from typing import List, Tuple
from satcoder import Encoding

TestResult = Tuple[str, str, str, str, str, str]
Averages = Tuple[str, str, str, str, str]

CONFIG_FILE = f"{os.getcwd()}/sat_config.json"

class SatSolver:
    __DECISIONS, __DECISION_RATE, __PROPS, __PROP_RATE, __TIME = range(5)

    def __init__(self, pc: int, test: str, enc=Encoding.MINIMAL) -> None:
    
        with open(CONFIG_FILE, "r") as f:
            self.config = json.load(f)
        self.__puzzle_count: int = pc
        self.__in_dir: str = f"{self.config['cacheDir']}{enc.name.lower()}/{test.lower()}"
        self.__work_dir: str = f"{self.config['cacheDir']}sat/{test.lower()}/"
        self.__table_rows: list = []
        self.params = {
            self.__DECISIONS: [],
            self.__DECISION_RATE: [],
            self.__PROPS: [],
            self.__PROP_RATE: [],
            self.__TIME: []
        }


    # Update the testing environment with new parameters
    def update_parameters(self, test=None, enc=None, pc=None):
        if test:
            self.__work_dir = f"{self.config['cacheDir']}sat/{test.lower()}/"
        if enc:
            test = test or self.__work_dir.split("/")[-2]
            self.__in_dir = f"{self.config['cacheDir']}{enc.name.lower()}/{test.lower()}"
        if pc:
            self.__puzzle_count = pc

    def solve(self):
        # iterate through CNF output and call minisat on each
        os.system(f"mkdir -p {self.__work_dir}")

        for i in range(self.__puzzle_count):
            self.__solve_puzzle(i)

        results = (self.__compute_averages(), self.__table_rows.copy())
        self.__clear()
        return results

    def __clear(self) -> None:
        self.__table_rows = []
        for key in self.params:
            self.params[key] = []

    def __get_data(self, data):
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

    def __solve_puzzle(self, i):
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

        self.__table_rows.append(self.__get_data(data))

    def __compute_averages(self) -> Averages:
        def av(x: List[str], r: int) -> str: return str(round(sum(float(x)
                                                                  for x in x) / len(x), r))
        lists: List[list] = list(self.params.values())
        times: list = self.params[self.__TIME]
        av_time: str = av(times, self.config['round']+2)
        averages: list = [av(test_results, self.config['round'])
                          for test_results in lists[:-1]] + [av_time]
        averages[self.__DECISION_RATE] = f"{averages[self.__DECISION_RATE]} decisions/sec"
        averages[self.__PROP_RATE] = f"{averages[self.__PROP_RATE]} props/sec"
        averages[self.__TIME] = f"{av_time} s"
        self.__table_rows.append(tuple(averages))

        return tuple(averages)

