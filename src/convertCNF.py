from typing import Tuple


class SudokuToCNF():
    def __init__(self) -> None:
        pass

    def convert(self, sudoku: str) -> str:
        # parse the sudoku string
        sudoku_list, count = self.__parse(sudoku)
        # create the CNF
        cnf = self.__create_cnf(sudoku_list, count)
        return cnf

    def __getSeparator(self, sudoku: str) -> str:
        # find first non-number character or zero
        # this is the empty cell separator
        separator = ""
        for i in range(len(sudoku)):
            if not sudoku[i].isdigit() or sudoku[i] == "0":
                separator = sudoku[i]
                break
        return separator

    def __parse(self, sudoku: str) -> Tuple[list, int]:
        separator = ""
        count = 0
        sudoku_list = []

        # strip newlines
        sudoku = sudoku.replace("\n", "")

        separator = self.__getSeparator(sudoku)

        for i in range(1, len(sudoku)):
            row = i // 9 + 1
            column = i % 9 + 1
            if sudoku[i] != separator:

                cell = self.__cell(row, column, int(sudoku[i]))
                count += 1
                sudoku_list.append(cell)
        return (sudoku_list, count)

    def __cell(self, row: int, column: int, value: int) -> str:
        # encode the cell as a three digit number
        # first digit is the row, second is the column, third is the value
        # store as int
        # print("value is: " + str(value) + " at: " + str(row), str(column))
        cell = (81 * (row-1)) + (9 * (column-1)) + (value-1) + 1
        # format as string, pad with zeros
        cell = str(cell)
        return cell

    def __create_cnf(self, sudoku_list: list, count: int) -> str:
        filename = "data/sudoku_rules_out.txt"
        file = open(filename, "w")
        self.__fixed_cnf(file)
        file.close()
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
        for i in range(len(sudoku_list)):
            cnf = cnf + sudoku_list[i] + " 0\n"
        # add the header
        header = "p cnf " + str(num_variables) + " " + str(num_clauses) + "\n"
        cnf = header + cnf
        return cnf

    def __fixed_cnf(self, file):
        file.write('p cnf 729 5529\n')

        self.__cell_one_number(file)
        
        self.__num_once_in_row(file)
        
        self.__num_once_in_column(file)
        
        self.__num_once_in_box(file)

    def __cell_one_number(self, file):
        for y in range(1, 10):
            for x in range(1, 10):
                for z in range(1, 10):
                    file.write(str(self.__cell(x, y, z)) + " ")
                file.write("0\n")

    def __num_once_in_row(self, file):
        for y in range(1, 10):
            for z in range(1, 10):
                for x in range(1, 10):
                    for i in range((x+1), 10):
                        file.write("-" + str(self.__cell(x, y, z)) +
                                   " -" + str(self.__cell(i, y, z)) + " 0\n")

    def __num_once_in_column(self, file):
        for x in range(1, 10):
            for z in range(1, 10):
                for y in range(1, 10):
                    for i in range((y+1), 10):
                        file.write("-" + str(self.__cell(x, y, z)) +
                                   " -" + str(self.__cell(x, i, z)) + " 0\n")

    def __num_once_in_box(self, file):
        for z in range(1, 10):
            for i in range(0, 3):
                for j in range(0, 3):
                    for x in range(1, 4):
                        for y in range(1, 4):
                            for k in range((y+1), 4):
                                file.write("-" + str(self.__cell((3*i+x), (3*j+y), z)) +
                                           " -" + str(self.__cell((3*i+x), (3*j+k), z)) + " 0\n")
        for z in range(1, 10):
            for i in range(0, 3):
                for j in range(0, 3):
                    for x in range(1, 4):
                        for y in range(1, 4):
                            for k in range((x+1), 4):
                                for l in range(1, 4):
                                    file.write("-" + str(self.__cell((3*i+x), (3*j+y), z)) +
                                               " -" + str(self.__cell((3*i+k), (3*j+l), z)) + " 0\n")