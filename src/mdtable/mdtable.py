from typing import List, Tuple, TypeVar

RawTable = List[TypeVar('Row', List, Tuple)]
Table = str


class TableMaker:
    def __init__(self, sep_every=3, sep_func=None, new_line=True):
        self.sep_every = sep_every
        self.sep_func = sep_func
        self.new_line = new_line
        self.sep = sep_func is not None

    def update_params(self, sep_every=None, sep_func=None, new_line=None, sep=None):
        if sep_every is not None:
            self.sep_every = sep_every
        if sep_func is not None:
            self.sep_func = sep_func
        if new_line is not None:
            self.new_line = new_line
        if sep is not None:
            self.sep = sep

    # if the class was initialized without a separator function,
    # col_titles will be ignored.
    def table(self, title, rows: RawTable, col_titles=None) -> Table:
        # find the longest string in each column
        col_widths = (
            [max(len(str(x)) for x in col)
             for col in zip(*rows + [col_titles])]
            if col_titles is not None
            else [max(len(str(x)) for x in col) for col in zip(*rows)]
        )
        out = f"# {title}\n"
        sep_count = 0
        sep_line = "|-" + "-|-".join("-" * n for n in col_widths) + "-|" + "\n"

        for i, row in enumerate(rows):
            if self.sep and i % self.sep_every == 0:
                sep_count += 1
                out += self.__table_sep(sep_count, self.sep_func,
                                        sep_line, col_widths, col_titles)
            elif not self.sep and i == 1:
                out += sep_line

            out += "| " + " | ".join((str(x).ljust(col_widths[j])
                                      for j, x in enumerate(row))) + " |\n"

        if self.new_line:
            out += "\n"
        return Table(out)

    def __table_sep(self, sep_count, sep_func, sep_line, col_widths, col_titles):
        out = ""
        # when a separator of some kind is defined
        # (either a header or a function)
        # print the separator at the interval specified by sep_every
        if sep_func != None:
            # the header is generated by the function
            # passed as an argument to sep_func
            # (this is so that the header can be dynamic)
            head = sep_func(sep_count)

            sep_header = (
                f"## {head.ljust(sum(col_widths) + 3 * (len(col_widths) - 1))}"
                + "\n\n"
            )
            out += "\n"+sep_header if sep_count > 1 else sep_header
        # if there are no column titles, and no separator function
        # a separator line needs to be printed
        if sep_func is None:
            out += sep_line

        out += "| " + " | ".join((str(x).ljust(col_widths[j])
                                  for j, x in enumerate(col_titles))) + " |\n"
        out += sep_line
        return out
