#!/usr/bin/env python3
from pathlib import Path

from lxml import etree as ET

TILE_SIZE = 10
WALL_HEIGHT = 1.0
WALL_OFFSET = TILE_SIZE / 2
WALL_CELL = 3
SDF_VERSION = "1.10"
DEFAULT_WORLD_PATH = "road.world"


def include_model(world, model_name, pose):
    model_uri = "model://{}".format(model_name)
    instance_count = sum(
        1 for include in world.findall("include")
        if include.findtext("uri") == model_uri
    )

    include = ET.SubElement(world, "include")
    name = ET.SubElement(include, "name")
    name.text = "{}_{}".format(model_name, instance_count)
    uri = ET.SubElement(include, "uri")
    uri.text = model_uri
    pose_element = ET.SubElement(include, "pose")
    pose_element.text = " ".join(str(i) for i in pose)


def include_boundary_walls(world, grid):
    min_x = ((grid.totalRows / 2) * -TILE_SIZE)
    min_y = ((grid.totalColumns / 2) * -TILE_SIZE)
    max_x = min_x + (grid.totalRows * TILE_SIZE)
    max_y = min_y + (grid.totalColumns * TILE_SIZE)

    z = WALL_HEIGHT / 2

    for row in range(grid.totalRows):
        x = min_x + WALL_OFFSET + (row * TILE_SIZE)
        include_model(world, "maps", [x, min_y, z, 0, 0, 0])
        include_model(world, "maps", [x, max_y, z, 0, 0, 0])

    for column in range(grid.totalColumns):
        y = min_y + WALL_OFFSET + (column * TILE_SIZE)
        include_model(world, "maps", [min_x, y, z, 0, 0, 1.57])
        include_model(world, "maps", [max_x, y, z, 0, 0, 1.57])


def is_wall_cell(grid, row, column):
    if row < 0 or row >= grid.totalRows:
        return False
    if column < 0 or column >= grid.totalColumns:
        return False
    return grid.CompleteGrid[row][column] == WALL_CELL


def wall_yaw(grid, row, column):
    if is_wall_cell(grid, row - 1, column) or is_wall_cell(grid, row + 1, column):
        return 1.57
    return 0


def road_yaw(grid, row, column):
    if grid.totalRows == 1:
        vertical_neighbors = ()
    elif row == 0:
        vertical_neighbors = (grid.CompleteGrid[row + 1][column],)
    elif row == grid.totalRows - 1:
        vertical_neighbors = (grid.CompleteGrid[row - 1][column],)
    else:
        vertical_neighbors = (
            grid.CompleteGrid[row - 1][column],
            grid.CompleteGrid[row + 1][column],
        )

    if 1 in vertical_neighbors or 2 in vertical_neighbors:
        return 0
    return 1.57


def add_sun_light(world):
    light = ET.SubElement(world, "light", name="sun", type="directional")
    cast_shadows = ET.SubElement(light, "cast_shadows")
    cast_shadows.text = "true"
    pose = ET.SubElement(light, "pose")
    pose.text = "0 0 10 0 0 0"
    diffuse = ET.SubElement(light, "diffuse")
    diffuse.text = "0.8 0.8 0.8 1"
    specular = ET.SubElement(light, "specular")
    specular.text = "0.2 0.2 0.2 1"

    attenuation = ET.SubElement(light, "attenuation")
    range_element = ET.SubElement(attenuation, "range")
    range_element.text = "1000"
    constant = ET.SubElement(attenuation, "constant")
    constant.text = "0.9"
    linear = ET.SubElement(attenuation, "linear")
    linear.text = "0.01"
    quadratic = ET.SubElement(attenuation, "quadratic")
    quadratic.text = "0.001"

    direction = ET.SubElement(light, "direction")
    direction.text = "-0.5 0.1 -0.9"


def world_generator(grid, settings, output_path=DEFAULT_WORLD_PATH):
    sdf = ET.Element("sdf", version=SDF_VERSION)

    world = ET.SubElement(sdf, "world", name="road_test")

    scene = ET.SubElement(world, "scene")

    ambient = ET.SubElement(scene, "ambient")
    ambient.text = settings.ambient

    # Gazebo Sim expects normalized RGBA values, e.g. "0.47 0.47 0.47 1".

    sky = ET.SubElement(scene, "sky")

    clouds = ET.SubElement(sky, "clouds")

    speed = ET.SubElement(clouds, "speed")
    speed.text = "12"

    time = ET.SubElement(sky, "time")
    time.text = settings.time

    init_x = ((grid.totalRows / 2) * -TILE_SIZE) + WALL_OFFSET
    init_y = ((grid.totalColumns / 2) * -TILE_SIZE) + WALL_OFFSET

    pos = [init_x, init_y, 0, 0, 0, 1.57]
    for row in range(grid.totalRows):
        pos[1] = init_y
        for column in range(grid.totalColumns):
            cell = grid.CompleteGrid[row][column]
            if cell == 1:
                pos[5] = road_yaw(grid, row, column)
                include_model(world, "road_straight", pos)

            elif cell == 2:
                pos[5] = 1.57
                include_model(world, "road_intersection", pos)

            elif cell == WALL_CELL:
                include_model(
                    world,
                    "maps",
                    [pos[0], pos[1], WALL_HEIGHT / 2, 0, 0, wall_yaw(grid, row, column)],
                )

            pos[1] += TILE_SIZE
        pos[0] += TILE_SIZE

    include_boundary_walls(world, grid)
    add_sun_light(world)

    tree = ET.ElementTree(sdf)
    output_path = Path(output_path)
    tree.write(str(output_path), pretty_print=True, xml_declaration=True)
    return output_path


def includeModel(world, model_name, pose):
    include_model(world, model_name, pose)


def includeBoundaryWalls(world, grid):
    include_boundary_walls(world, grid)


def isWallCell(grid, row, column):
    return is_wall_cell(grid, row, column)


def wallYaw(grid, row, column):
    return wall_yaw(grid, row, column)


def addSunLight(world):
    add_sun_light(world)


def worldGenerator(grid, w, output_path=DEFAULT_WORLD_PATH):
    return world_generator(grid, w, output_path)
