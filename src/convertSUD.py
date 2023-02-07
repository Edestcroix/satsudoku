class SATToSudoku:
    def convert(self, cnf: str) -> str:
        # get the sudoku puzzle from the CNF
        sudoku = self.__parse(cnf)
        # format the sudoku puzzle
        sudoku = self.__format(sudoku)
        return sudoku

    def __parse(self, cnf: str) -> list:
        # cnf will be a list of variables, apply to each
        # variable the reverse of 81 * (row-1) + 9 * (column-1) + (value - 1) + 1
        # to get the row, column, and value
        # get the variables from the CNF
        cnf = cnf.replace("\n", "")
        variables = cnf.split()

        sudoku = [[], [], [], [], [], [], [], [], []]
        for i in range(len(variables)):
            variable = int(variables[i])
            if variable > 0:
                # get the row, column, and value
                row = (variable - 1) // 81 + 1
                value = ((variable - 1) % 81) % 9 + 1
                # add the value to the sudoku puzzle
                sudoku[row - 1].append(value)
        return sudoku

    def __format(self, sudoku: list) -> str:
        # format the sudoku puzzle
        # there should be no empty cells because the puzzle is solved
        # add a newline after every 9 cells
        # add a space after every 3 cells
        formatted_sudoku = ""

        for i in range(len(sudoku)):
            for j in range(len(sudoku[i])):
                formatted_sudoku += str(sudoku[i][j])
                if j % 3 == 2:
                    formatted_sudoku += " "
            formatted_sudoku += "\n"
            if i % 3 == 2:
                formatted_sudoku += "\n"
        return formatted_sudoku.strip()
