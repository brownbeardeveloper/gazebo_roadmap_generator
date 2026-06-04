#!usr/bin/python3
from lxml import etree as ET

TILE_SIZE = 10
WALL_HEIGHT = 1.0
WALL_OFFSET = TILE_SIZE / 2
WALL_CELL = 3


def includeModel(world, model_name, pose):
    include = ET.SubElement(world, "include")
    uri = ET.SubElement(include, "uri")
    uri.text = "model://{}".format(model_name)
    pose_element = ET.SubElement(include, "pose")
    pose_element.text = " ".join(str(i) for i in pose)


def includeBoundaryWalls(world, grid):
    min_x = ((grid.totalRows / 2) * -TILE_SIZE)
    min_y = ((grid.totalColumns / 2) * -TILE_SIZE)
    max_x = min_x + (grid.totalRows * TILE_SIZE)
    max_y = min_y + (grid.totalColumns * TILE_SIZE)

    z = WALL_HEIGHT / 2

    for row in range(grid.totalRows):
        x = min_x + WALL_OFFSET + (row * TILE_SIZE)
        includeModel(world, "maps", [x, min_y, z, 0, 0, 0])
        includeModel(world, "maps", [x, max_y, z, 0, 0, 0])

    for column in range(grid.totalColumns):
        y = min_y + WALL_OFFSET + (column * TILE_SIZE)
        includeModel(world, "maps", [min_x, y, z, 0, 0, 1.57])
        includeModel(world, "maps", [max_x, y, z, 0, 0, 1.57])


def isWallCell(grid, row, column):
    if row < 0 or row >= grid.totalRows:
        return False
    if column < 0 or column >= grid.totalColumns:
        return False
    return grid.CompleteGrid[row][column] == WALL_CELL


def wallYaw(grid, row, column):
    if isWallCell(grid, row - 1, column) or isWallCell(grid, row + 1, column):
        return 1.57
    return 0


def worldGenerator(grid,w):
    sdf = ET.Element("sdf",version="1.4")

    world = ET.SubElement(sdf,"world",name="road test")

    #setting up the scene
    scene = ET.SubElement(world,"scene")

    ambient = ET.SubElement(scene,"ambient")
    ambient.text = w.ambient

    #Day: 120 120 120 255
    #Night: 20 40 50 255
    #Dawm/Dusk: 120 80 60 255
    #AfterDawn/BeforeDusk: 120 70 80 255

    sky = ET.SubElement(scene,"sky")

    clouds = ET.SubElement(sky,"clouds")

    speed = ET.SubElement(clouds,"speed")
    speed.text = "12"

    time = ET.SubElement(sky,"time")
    time.text  = w.time


    #including models

    init_x = ((grid.totalRows/2)*-TILE_SIZE)+WALL_OFFSET
    init_y = ((grid.totalColumns/2)*-TILE_SIZE)+WALL_OFFSET

    pos = [init_x,init_y,0,0,0,1.57]
    for i in range(grid.totalRows):
        pos[1] = init_y
        for j in range(grid.totalColumns):
            pos[5]=1.57
            if(grid.CompleteGrid[i][j]==1):
                if(i==grid.totalRows-1):
                    if(grid.CompleteGrid[i-1][j]==2):
                        pos[5]=0
                    elif(grid.CompleteGrid[i-1][j]==1):
                        pos[5]=0
                elif(i==0):
                    if(grid.CompleteGrid[i+1][j]==2):
                        pos[5]=0
                    elif(grid.CompleteGrid[i+1][j]==1):
                        pos[5]=0
                else:
                    if(grid.CompleteGrid[i-1][j]==2 or grid.CompleteGrid[i+1][j]==2):
                        pos[5]=0
                    elif(grid.CompleteGrid[i-1][j]==1 or grid.CompleteGrid[i+1][j]==1):
                        pos[5]=0

                includeModel(world, "road_straight", pos)

            elif(grid.CompleteGrid[i][j]==2):
                includeModel(world, "road_intersection", pos)

            elif(grid.CompleteGrid[i][j]==WALL_CELL):
                includeModel(world, "maps", [pos[0], pos[1], WALL_HEIGHT / 2, 0, 0, wallYaw(grid, i, j)])

            pos[1]+=TILE_SIZE
        pos[0]+=TILE_SIZE

    includeBoundaryWalls(world, grid)

    include = ET.SubElement(world,"include")
    uri = ET.SubElement(include,"uri")
    uri.text = "model://sun"

    #print ET.tostring(sdf,pretty_print=True,xml_declaration=True)
    tree = ET.ElementTree(sdf)
    tree.write('road.world', pretty_print=True, xml_declaration=True)
