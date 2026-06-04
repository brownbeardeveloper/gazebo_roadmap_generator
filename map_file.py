#!/usr/bin/python3
import numpy as np


class SavedGrid:
    def __init__(self, rows, columns, grid):
        self.totalRows = rows
        self.totalColumns = columns
        self.CompleteGrid = np.array(grid)

    def printgrid(self):
        for row in self.CompleteGrid:
            print(" ".join(str(int(i)) for i in row))


def _cleanValue(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def loadMap(path):
    values = {}
    grid = []
    in_grid = False

    with open(path) as map_file:
        for raw_line in map_file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if in_grid:
                if not line.startswith("-"):
                    in_grid = False
                else:
                    row = _cleanValue(line[1:].strip())
                    grid.append([int(cell) for cell in row])
                    continue

            if line == "grid:":
                in_grid = True
                continue

            key, value = line.split(":", 1)
            values[key.strip()] = _cleanValue(value)

    rows = int(values["rows"])
    columns = int(values["columns"])

    if len(grid) != rows:
        raise ValueError("Map rows do not match rows setting")

    for row in grid:
        if len(row) != columns:
            raise ValueError("Map row length does not match columns setting")

    values["rows"] = rows
    values["columns"] = columns
    values["grid"] = grid
    return values


def savedGridFromMap(map_data):
    return SavedGrid(map_data["rows"], map_data["columns"], map_data["grid"])
