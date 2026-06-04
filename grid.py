#!/usr/bin/python3
from tkinter import *
import numpy as np
from world_gen import *
import os

class Cell():

    EMPTY_COLOR_BG = "white"
    EMPTY_COLOR_BORDER = "black"
    COLORS = {
        0: ("white", "black"),
        1: ("dark blue", "dark blue"),
        2: ("blue", "blue"),
        3: ("gray45", "gray45"),
    }

    def __init__(self, master, x, y, size):
        #Constructor of the object called by Cell
        self.master = master
        self.abs = x
        self.ord = y
        self.size= size
        self.fill = 0

    def draw(self):
        #Fill selected cell on grid canvas
        if self.master != None :

            fill, outline = Cell.COLORS.get(int(self.fill), Cell.COLORS[0])

            xmin = self.abs * self.size
            xmax = xmin + self.size
            ymin = self.ord * self.size
            ymax = ymin + self.size

            self.master.create_rectangle(xmin, ymin, xmax, ymax, fill = fill, outline = outline)

    def drawinitial(self):
        if self.master != None :
            if not self.fill:
                fill = Cell.EMPTY_COLOR_BG
                outline = Cell.EMPTY_COLOR_BORDER

            xmin = self.abs * self.size
            xmax = xmin + self.size
            ymin = self.ord * self.size
            ymax = ymin + self.size

            self.master.create_rectangle(xmin, ymin, xmax, ymax, fill = fill, outline = outline)


class CellGrid(Canvas):
    def __init__(self,master, rowNumber, columnNumber, cellSize, *args, **kwargs):
        Canvas.__init__(self, master, width = cellSize * columnNumber , height = cellSize * rowNumber, *args, **kwargs)

        self.cellSize = cellSize
        self.totalRows = rowNumber
        self.totalColumns = columnNumber
        self.CompleteGrid = np.zeros((rowNumber,columnNumber))
        self.paintValue = 1

        self.grid = []
        for row in range(rowNumber):

            line = []
            for column in range(columnNumber):
                line.append(Cell(self, column, row, cellSize))

            self.grid.append(line)

        #memorize the cells that have been modified to avoid many switching of state during mouse motion.
        self.switched = []

        #bind click action
        self.bind("<Button-1>", self.handleMouseClick)
        #bind moving while clicking
        self.bind("<B1-Motion>", self.handleMouseMotion)
        #bind release button action - clear the memory of midified cells.
        self.bind("<ButtonRelease-1>", lambda event: self.switched.clear())
        self.drawinitial()



    def draw(self):
        for row in self.grid:
            for cell in row:
                cell.draw()

    def drawinitial(self):
        for row in self.grid:
            for cell in row:
                cell.drawinitial()

    def _eventCoords(self, event):
        row = int(event.y / self.cellSize)
        column = int(event.x / self.cellSize)
        return row, column

    def _isInsideGrid(self, row, column):
        return 0 <= row < self.totalRows and 0 <= column < self.totalColumns

    def toggleCell(self, row, column):
        if not self._isInsideGrid(row, column):
            return

        cell = self.grid[row][column]
        if cell in self.switched:
            return

        self.setCell(row,column,self.paintValue)
        cell.fill = self.paintValue
        cell.draw()
        #add the cell to the list of cell switched during the click
        self.switched.append(cell)

    def handleMouseClick(self, event):
        row, column = self._eventCoords(event)
        self.toggleCell(row,column)

    def handleMouseMotion(self, event):
        row, column = self._eventCoords(event)
        self.toggleCell(row,column)

    def printgrid(self):
        for row in self.CompleteGrid:
            print(" ".join(str(int(i)) for i in row))

    def setPaintValue(self, value):
        self.paintValue = value

    def setCell(self,row,col,value):
        self.CompleteGrid[row][col] = value


#if __name__ == "__main__" :
def OpenGrid(w):
    app = Tk()

    grid = CellGrid(app,w.rows,w.cols,25)
    grid.pack()
    paint_frame = Frame(app)
    paint_frame.pack()
    Button(paint_frame,text="Road",command=lambda: grid.setPaintValue(1)).pack(side=LEFT)
    Button(paint_frame,text="Intersection",command=lambda: grid.setPaintValue(2)).pack(side=LEFT)
    Button(paint_frame,text="Wall",command=lambda: grid.setPaintValue(3)).pack(side=LEFT)
    Button(paint_frame,text="Erase",command=lambda: grid.setPaintValue(0)).pack(side=LEFT)
    Button(app,text="Generate Roadmap",command=app.destroy).pack()
    app.mainloop()
    grid.printgrid()

    worldGenerator(grid,w)
