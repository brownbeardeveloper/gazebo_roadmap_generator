#!/usr/bin/env python3
from pathlib import Path

from lxml import etree as ET

# Gazebo uses SI units. A 1 m grid cell keeps maps compact for a
# 0.60 m x 0.30 m RC car while leaving realistic driving clearance.
TILE_SIZE = 1.0
WALL_HEIGHT = 0.4
WALL_OFFSET = TILE_SIZE / 2
WALL_CELL = 3
WALL_COLOR = "0.65 0.65 0.65 1"
SDF_VERSION = "1.10"
DEFAULT_WORLD_PATH = "road.world"
DEFAULT_MAPS_MODEL_DIR = Path(__file__).resolve().parent / "maps"


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


def ensure_maps_model(model_dir=DEFAULT_MAPS_MODEL_DIR):
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    model_sdf = model_dir / "model.sdf"
    if not model_sdf.exists():
        sdf = ET.Element("sdf", version=SDF_VERSION)
        model = ET.SubElement(sdf, "model", name="maps")
        static = ET.SubElement(model, "static")
        static.text = "true"
        link = ET.SubElement(model, "link", name="link")

        for geometry_parent, geometry_name in (("collision", "collision"), ("visual", "visual")):
            element = ET.SubElement(link, geometry_parent, name=geometry_name)
            geometry = ET.SubElement(element, "geometry")
            box = ET.SubElement(geometry, "box")
            size = ET.SubElement(box, "size")
            size.text = "{} {} {}".format(TILE_SIZE, TILE_SIZE, WALL_HEIGHT)

            if geometry_parent == "visual":
                cast_shadows = ET.SubElement(element, "cast_shadows")
                cast_shadows.text = "false"
                material = ET.SubElement(element, "material")
                ambient = ET.SubElement(material, "ambient")
                ambient.text = WALL_COLOR
                diffuse = ET.SubElement(material, "diffuse")
                diffuse.text = WALL_COLOR
                specular = ET.SubElement(material, "specular")
                specular.text = "0.05 0.05 0.05 1"

        ET.ElementTree(sdf).write(str(model_sdf), pretty_print=True, xml_declaration=True)

    model_config = model_dir / "model.config"
    if not model_config.exists():
        model = ET.Element("model")
        name = ET.SubElement(model, "name")
        name.text = "maps"
        version = ET.SubElement(model, "version")
        version.text = "1.0"
        sdf = ET.SubElement(model, "sdf", version=SDF_VERSION)
        sdf.text = "model.sdf"
        author = ET.SubElement(model, "author")
        author_name = ET.SubElement(author, "name")
        author_name.text = "Gazebo Roadmap Generator"
        description = ET.SubElement(model, "description")
        description.text = "Static wall block for saved and generated road maps."

        ET.ElementTree(model).write(str(model_config), pretty_print=True, xml_declaration=True)

    return model_dir


def add_box_model(world, name_prefix, pose, size, color=WALL_COLOR):
    instance_count = sum(
        1 for model in world.findall("model")
        if model.get("name", "").startswith("{}_".format(name_prefix))
    )

    model = ET.SubElement(world, "model", name="{}_{}".format(name_prefix, instance_count))
    static = ET.SubElement(model, "static")
    static.text = "true"
    pose_element = ET.SubElement(model, "pose")
    pose_element.text = " ".join(str(i) for i in pose)

    link = ET.SubElement(model, "link", name="link")

    for geometry_parent, geometry_name in (("collision", "collision"), ("visual", "visual")):
        element = ET.SubElement(link, geometry_parent, name=geometry_name)
        geometry = ET.SubElement(element, "geometry")
        box = ET.SubElement(geometry, "box")
        size_element = ET.SubElement(box, "size")
        size_element.text = " ".join(str(i) for i in size)

        if geometry_parent == "visual":
            cast_shadows = ET.SubElement(element, "cast_shadows")
            cast_shadows.text = "false"
            material = ET.SubElement(element, "material")
            ambient = ET.SubElement(material, "ambient")
            ambient.text = color
            diffuse = ET.SubElement(material, "diffuse")
            diffuse.text = color
            specular = ET.SubElement(material, "specular")
            specular.text = "0.05 0.05 0.05 1"


def add_wall_block(world, center_x, center_y, size_x, size_y):
    add_box_model(
        world,
        "wall_block",
        [center_x, center_y, WALL_HEIGHT / 2, 0, 0, 0],
        [size_x, size_y, WALL_HEIGHT],
    )


def include_boundary_walls(world, grid):
    min_x = ((grid.totalRows / 2) * -TILE_SIZE)
    min_y = ((grid.totalColumns / 2) * -TILE_SIZE)
    max_x = min_x + (grid.totalRows * TILE_SIZE)
    max_y = min_y + (grid.totalColumns * TILE_SIZE)

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    size_x = (grid.totalRows * TILE_SIZE) + (2 * TILE_SIZE)
    size_y = grid.totalColumns * TILE_SIZE

    add_wall_block(world, center_x, min_y - WALL_OFFSET, size_x, TILE_SIZE)
    add_wall_block(world, center_x, max_y + WALL_OFFSET, size_x, TILE_SIZE)
    add_wall_block(world, min_x - WALL_OFFSET, center_y, TILE_SIZE, size_y)
    add_wall_block(world, max_x + WALL_OFFSET, center_y, TILE_SIZE, size_y)


def include_grid_walls(world, grid):
    min_x = ((grid.totalRows / 2) * -TILE_SIZE)
    min_y = ((grid.totalColumns / 2) * -TILE_SIZE)

    for row in range(grid.totalRows):
        column = 0
        while column < grid.totalColumns:
            if not is_wall_cell(grid, row, column):
                column += 1
                continue

            start_column = column
            while column < grid.totalColumns and is_wall_cell(grid, row, column):
                column += 1

            run_length = column - start_column
            center_x = min_x + WALL_OFFSET + (row * TILE_SIZE)
            center_y = min_y + (start_column * TILE_SIZE) + (run_length * TILE_SIZE / 2)
            add_wall_block(world, center_x, center_y, TILE_SIZE, run_length * TILE_SIZE)


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
    ensure_maps_model()

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

            pos[1] += TILE_SIZE
        pos[0] += TILE_SIZE

    include_grid_walls(world, grid)
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
