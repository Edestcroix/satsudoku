import itertools
import os
import re
from enum import Enum
from typing import IO, TextIO, Tuple


class Encoding(Enum):
    MINIMAL = 0
    EFFICIENT = 1
    EXTENDED = 2


def encode(sudoku: str, encoding=Encoding.MINIMAL) -> str:
    # parse the sudoku string
    sudoku_list, count = __parse(sudoku)
    return __create_cnf(sudoku_list, count, encoding)


def __getSeparator(sudoku: str) -> str:
    return next((sudoku[i] for i in range(len(sudoku)) if
                 not sudoku[i].isdigit() or sudoku[i] == "0"), "",)


def __parse(sudoku: str) -> Tuple[list, int]:
    separator, count, sudoku_list = "", 0, []

    # strip newlines
    # strip all whitespace, newlines, tabs, etc
    sudoku = re.sub(r"\s+", "", sudoku)
    separator = __getSeparator(sudoku)
    # split sudoku into chunks of 9
    for row, column in itertools.product(range(9), range(9)):
        cell = sudoku[(9*row)+column]
        if cell != separator:
            sudoku_list.append(__enc(row+1, column+1, int(cell)))
            count += 1

    return (sudoku_list, count)


def __enc(row: int, column: int, value: int) -> str:
    # encode the cell as a three digit number
    # first digit is the row, second is the column, third is the value
    # store as int
    # print("value is: " + str(value) + " at: " + str(row), str(column))
    cell = (81 * (row-1)) + (9 * (column-1)) + (value-1) + 1
    return str(cell)


def __create_cnf(sudoku_list: list, count: int, encoding=Encoding.MINIMAL) -> str:
    filename = f"data/sudoku_rules_{encoding.name.lower()}.cnf"

    # if the file doesn't exist, create it
    # and write the sudoku rules to it
    if not os.path.exists(filename):
        with open(filename, "w") as file:
            __fixed_cnf(file, encoding)
    sudoku_rules = open(filename, "r")
    # add the header

    header = sudoku_rules.readline()
    # header format is p cnf <number of variables> <number of clauses>
    # split the header into a list
    header = header.split()
    # get the number of variables and clauses
    num_variables = int(header[2])
    num_clauses = int(header[3]) + count

    cnf = sudoku_rules.read()
    # convert it to CNF
    # create clauses for each cell
    for sudoku in sudoku_list:
        cnf = cnf + sudoku + " 0\n"
    # add the header
    header = f"p cnf {num_variables} {str(num_clauses)}" + "\n"
    cnf = header + cnf
    return cnf


def __fixed_cnf(file, encoding=Encoding.MINIMAL):
    match encoding:
        case Encoding.MINIMAL:
            file.write('p cnf 729 8829\n')
        case Encoding.EFFICIENT:
            file.write('p cnf 729 11745\n')
        case Encoding.EXTENDED:
            file.write('p cnf 729 11988\n')

    __cell_one_number(file)

    __num_once_in_row(file)

    __num_once_in_column(file)

    __num_once_in_box(file)

    if encoding in [Encoding.EFFICIENT, Encoding.EXTENDED]:
        __exactly_one_number(file)
    if encoding == Encoding.EXTENDED:
        __each_number_at_least_once_row(file)
        __each_number_at_least_once_col(file)
        __each_number_at_least_once_box(file)


def __cell_one_number(file: TextIO) -> None:
    for y, x in itertools.product(range(1, 10), range(1, 10)):
        for z in range(1, 10):
            file.write(f"{str(__enc(x, y, z))} ")
        file.write("0\n")


def __num_once_in_row(file: TextIO) -> None:
    for y, z, x in itertools.product(range(1, 10), range(1, 10), range(1, 10)):
        for i in range((x+1), 10):
            file.write(
                f"-{str(__enc(x, y, z))} -{str(__enc(i, y, z))}"
                + " 0\n"
            )


def __num_once_in_column(file: TextIO) -> None:
    for x, z, y in itertools.product(range(1, 10), range(1, 10), range(1, 10)):
        for i in range((y+1), 10):
            file.write(
                f"-{str(__enc(x, y, z))} -{str(__enc(x, i, z))}"
                + " 0\n"
            )


def __num_once_in_box(file: TextIO) -> None:
    for z, i, j, x, y in itertools.product(range(1, 10), range(3), range(3), range(1, 4), range(1, 4)):
        for k in range((y+1), 4):
            file.write(
                f"-{str(__enc(3 * i + x, 3 * j + y, z))} -{str(__enc(3 * i + x, 3 * j + k, z))}"
                + " 0\n"
            )
    for z, i, j, x, y in itertools.product(range(1, 10), range(3), range(3), range(1, 4), range(1, 4)):
        for k, l in itertools.product(range((x+1), 4), range(1, 4)):
            file.write(
                f"-{str(__enc(3 * i + x, 3 * j + y, z))} -{str(__enc(3 * i + k, 3 * j + l, z))}"
                + " 0\n")


def __exactly_one_number(file: TextIO) -> None:
    for i, j, k in itertools.product(range(1, 10), range(1, 10), range(1, 10)):
        for l in range((k+1), 10):
            file.write(
                f"-{str(__enc(i, j, k))} -{str(__enc(i, j, l))}" + " 0\n")


def __each_number_at_least_once_row(file: TextIO) -> None:
    for i, k in itertools.product(range(1, 10), range(1, 10)):
        for j in range(1, 10):
            file.write(f"{str(__enc(i, j, k))} ")
        file.write("0\n")


def __each_number_at_least_once_col(file: TextIO) -> None:
    for j, k in itertools.product(range(1, 10), range(1, 10)):
        for i in range(1, 10):
            file.write(f"{str(__enc(i, j, k))} ")
        file.write("0\n")


def __each_number_at_least_once_box(file: TextIO) -> None:
    for i, j, k in itertools.product(range(3), range(3), range(1, 10)):
        for x, y in itertools.product(range(1, 4), range(1, 4)):
            file.write(f"{str(__enc(3 * i + x, 3 * j + y, k))} ")
        file.write("0\n")
