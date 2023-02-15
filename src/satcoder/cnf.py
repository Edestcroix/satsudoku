import itertools
import os
import re
from enum import Enum
from typing import Tuple


# sudoku puzzles can be encoded into CNF in 3 different ways,
# each encoding has progressively more clauses, and takes longer
# to solve. The rules set by the efficient and extended encodings
# are implicitly satisfied by the minimal encoding, so the minimal
# is really the most efficient encoding, but the other two are
# included for completeness.
class Encoding(Enum):
    MINIMAL = 0
    EFFICIENT = 1
    EXTENDED = 2


# given a sudoku string,
# returns the CNF encoding of the sudoku as a string
# these string are VERY large, as CNF is a very verbose format
# if cache is not None, the fixed CNF will be written to a file
# in that directory, and reused if it already exists.
def encode(sudoku: str, encoding=Encoding.MINIMAL, cache=None) -> str:
    # parse the sudoku string
    sudoku_list, count = __parse(sudoku)
    return __create_cnf(sudoku_list, count, encoding, cache)


def __getSeparator(sudoku: str) -> str:
    return next(
        (
            sudoku[i]
            for i in range(len(sudoku))
            if not sudoku[i].isdigit() or sudoku[i] == "0"
        ),
        "",
    )


def __parse(sudoku: str) -> Tuple[list, int]:
    separator, count, sudoku_list = "", 0, []

    # strip newlines
    # strip all whitespace, newlines, tabs, etc
    sudoku = re.sub(r"\s+", "", sudoku)
    separator = __getSeparator(sudoku)
    # split sudoku into chunks of 9
    for row, column in itertools.product(range(9), range(9)):
        cell = sudoku[(9 * row) + column]
        if cell != separator:
            sudoku_list.append(__enc(row + 1, column + 1, int(cell)))
            count += 1

    return (sudoku_list, count)


def __enc(row: int, column: int, value: int) -> str:
    # encode the cell as a three digit number
    # first digit is the row, second is the column, third is the value
    # store as int
    # print("value is: " + str(value) + " at: " + str(row), str(column))
    cell = (81 * (row - 1)) + (9 * (column - 1)) + (value - 1) + 1
    return str(cell)


def __create_cnf(
    sudoku_list: list, count: int, encoding=Encoding.MINIMAL, cache_in=None
) -> str:
    filename = f"{cache_in}sudoku_rules_{encoding.name.lower()}.cnf"

    # if cache is true, cache fixed cnf in a file in the cwd so it can be reused
    if cache_in:
        if not os.path.exists(filename):
            mkdir = f"mkdir -p {cache_in}"
            os.system(mkdir)
            with open(filename, "w") as file:
                header, cnf = __fixed_cnf(encoding)
                file.write(header + cnf)

        sudoku_rules = open(filename, "r")
        header = sudoku_rules.readline()

        cnf = sudoku_rules.read()
    else:
        header, cnf = __fixed_cnf(encoding)
        # split on newlines

    # header format is p cnf <number of variables> <number of clauses>
    # split the header into a list
    header = header.split()
    # get the number of variables and clauses
    num_variables = int(header[2])
    num_clauses = int(header[3]) + count
    # create clauses for each cell
    for sudoku in sudoku_list:
        cnf = cnf + sudoku + " 0\n"
    # add the header
    header = f"p cnf {num_variables} {str(num_clauses)}" + "\n"
    cnf = header + cnf
    return cnf


def __fixed_cnf(encoding=Encoding.MINIMAL) -> tuple:
    header = ""
    match encoding:
        case Encoding.MINIMAL:
            header = "p cnf 729 8829\n"
        case Encoding.EFFICIENT:
            header = "p cnf 729 11745\n"
        case Encoding.EXTENDED:
            header = "p cnf 729 11988\n"

    cnf = __cell_one_number()

    cnf += __num_once_in_row()

    cnf += __num_once_in_column()

    cnf += __num_once_in_box()

    if encoding in [Encoding.EFFICIENT, Encoding.EXTENDED]:
        cnf += __at_most_one_number()
    if encoding == Encoding.EXTENDED:
        cnf += __each_number_at_least_once_row()
        cnf += __each_number_at_least_once_col()
        cnf += __each_number_at_least_once_box()

    return header, cnf


# Below Lies The Land Of Nested For Loops
# (seriously, this is a lot of for loops, thank the flying
# spaghetti monster for itertools.product)


def __cell_one_number() -> str:
    cnf = ""
    for i, j in itertools.product(range(1, 10), range(1, 10)):
        for k in range(1, 10):
            cnf += f"{str(__enc(i, j, k))} "
        cnf += "0\n"
    return cnf


def __num_once_in_row() -> str:
    cnf = ""
    for i, k, j in itertools.product(range(1, 10), range(1, 10), range(1, 9)):
        for l in range((j + 1), 10):
            cnf += f"-{str(__enc(i, j, k))} -{str(__enc(i, l, k))}" + " 0\n"
    return cnf


def __num_once_in_column() -> str:
    cnf = ""
    for j, k, i in itertools.product(range(1, 10), range(1, 10), range(1, 9)):
        for l in range((i + 1), 10):
            cnf += f"-{str(__enc(i, j, k))} -{str(__enc(l, j, k))}" + " 0\n"
    return cnf


def __num_once_in_box() -> str:
    cnf = ""
    for k, a, b, u, v in itertools.product(
        range(1, 10), range(3), range(3), range(1, 4), range(1, 3)
    ):
        for w in range((v + 1), 4):
            cnf += (
                f"-{str(__enc(3 * a + u, 3 * b + v, k))} -{str(__enc(3 * a + u, 3 * b + w, k))}"
                + " 0\n"
            )
    for k, a, b, u, v in itertools.product(
        range(1, 10), range(3), range(3), range(1, 3), range(1, 4)
    ):
        for w, t in itertools.product(range((u + 1), 4), range(1, 4)):
            cnf += (
                f"-{str(__enc(3 * a + u, 3 * b + v, k))} -{str(__enc(3 * a + w, 3 * b + t, k))}"
                + " 0\n"
            )
    return cnf


def __at_most_one_number() -> str:
    cnf = ""
    for i, j, k in itertools.product(range(1, 10), range(1, 10), range(1, 9)):
        for l in range((k + 1), 10):
            cnf += f"-{str(__enc(i, j, k))} -{str(__enc(i, j, l))}" + " 0\n"
    return cnf


def __each_number_at_least_once_row() -> str:
    cnf = ""
    for i, k in itertools.product(range(1, 10), range(1, 10)):
        for j in range(1, 10):
            cnf += f"{str(__enc(i, j, k))} "
        cnf += "0\n"
    return cnf


def __each_number_at_least_once_col() -> str:
    cnf = ""
    for j, k in itertools.product(range(1, 10), range(1, 10)):
        for i in range(1, 10):
            cnf += f"{str(__enc(i, j, k))} "
        cnf += "0\n"
    return cnf


def __each_number_at_least_once_box() -> str:
    cnf = ""
    for k, a, b in itertools.product(range(1, 10), range(3), range(3)):
        for u, v in itertools.product(range(1, 4), range(1, 4)):
            cnf += f"{str(__enc(3 * a + u, 3 * b + v, k))} "
        cnf += "0\n"
    return cnf
