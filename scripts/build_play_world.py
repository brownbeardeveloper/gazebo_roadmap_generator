#!/usr/bin/env python3
import argparse
import copy
import sys
from pathlib import Path
from types import SimpleNamespace

from lxml import etree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from map_file import loadMap, savedGridFromMap
from world_gen import TILE_SIZE, WALL_OFFSET, road_yaw, worldGenerator


DRIVABLE_CELLS = {1, 2}
DEFAULT_CAR_NAME = "roadmap_car"
DEFAULT_SPAWN_Z = 0.0


def settings_from_map(map_data):
    return SimpleNamespace(
        rows=map_data["rows"],
        cols=map_data["columns"],
        time=map_data.get("time", "10:00"),
        ambient=map_data.get("ambient", "0.47 0.47 0.47 1"),
    )


def is_drivable(grid, row, column):
    if row < 0 or row >= grid.totalRows:
        return False
    if column < 0 or column >= grid.totalColumns:
        return False
    return int(grid.CompleteGrid[row][column]) in DRIVABLE_CELLS


def cell_center(grid, row, column):
    x = ((grid.totalRows / 2) * -TILE_SIZE) + WALL_OFFSET + (row * TILE_SIZE)
    y = ((grid.totalColumns / 2) * -TILE_SIZE) + WALL_OFFSET + (column * TILE_SIZE)
    return x, y


def spawn_score(grid, row, column):
    neighbors = (
        is_drivable(grid, row - 1, column),
        is_drivable(grid, row + 1, column),
        is_drivable(grid, row, column - 1),
        is_drivable(grid, row, column + 1),
    )
    boundary_margin = min(
        row,
        column,
        grid.totalRows - row - 1,
        grid.totalColumns - column - 1,
    )
    return (sum(neighbors), boundary_margin, -row, -column)


def choose_spawn_pose(grid):
    candidates = [
        (spawn_score(grid, row, column), row, column)
        for row in range(grid.totalRows)
        for column in range(grid.totalColumns)
        if is_drivable(grid, row, column)
    ]
    if not candidates:
        raise ValueError("Map has no drivable road or intersection cells for the car.")

    _, row, column = max(candidates)
    x, y = cell_center(grid, row, column)
    yaw = road_yaw(grid, row, column)
    return [x, y, DEFAULT_SPAWN_Z, 0, 0, yaw], row, column


def car_model_from_sdf(car_path, car_name, pose):
    tree = ET.parse(str(car_path))
    root = tree.getroot()
    model = root.find("model") if root.tag == "sdf" else root
    if model is None or model.tag != "model":
        raise ValueError(f"{car_path} must contain a top-level SDF <model>.")

    model = copy.deepcopy(model)
    model.set("name", car_name)

    pose_element = model.find("pose")
    if pose_element is None:
        pose_element = ET.Element("pose")
        model.insert(0, pose_element)
    pose_element.text = " ".join(str(value) for value in pose)

    for plugin in model.findall("plugin"):
        if plugin.get("name") != "gz::sim::systems::DiffDrive":
            continue
        replacements = {
            "odom_topic": f"/model/{car_name}/odometry",
            "tf_topic": f"/model/{car_name}/tf",
            "child_frame_id": f"{car_name}/chassis",
        }
        for tag, text in replacements.items():
            element = plugin.find(tag)
            if element is not None:
                element.text = text

    return model


def embed_car(world_path, car_path, map_path, car_name):
    map_data = loadMap(map_path)
    grid = savedGridFromMap(map_data)
    pose, row, column = choose_spawn_pose(grid)

    tree = ET.parse(str(world_path))
    world = tree.find("world")
    if world is None:
        raise ValueError(f"{world_path} does not contain an SDF <world>.")

    for existing_model in world.findall("model"):
        if existing_model.get("name") == car_name:
            world.remove(existing_model)

    world.append(car_model_from_sdf(car_path, car_name, pose))
    tree.write(str(world_path), pretty_print=True, xml_declaration=True)
    return pose, row, column


def build_world(map_path, car_path, output_path, car_name):
    map_data = loadMap(map_path)
    grid = savedGridFromMap(map_data)
    settings = settings_from_map(map_data)
    worldGenerator(grid, settings, output_path)
    return embed_car(output_path, car_path, map_path, car_name)


def build_parser():
    parser = argparse.ArgumentParser(description="Build a playable Gazebo road world.")
    parser.add_argument("--map", default="example.yaml", help="Saved map file to load.")
    parser.add_argument("--car", default="sources/car.sdf", help="SDF model file for the car.")
    parser.add_argument("--output", default="road_play.world", help="World file to write.")
    parser.add_argument("--name", default=DEFAULT_CAR_NAME, help="Car entity name in Gazebo.")
    return parser


def main():
    args = build_parser().parse_args()
    map_path = Path(args.map)
    car_path = Path(args.car)
    output_path = Path(args.output)

    pose, row, column = build_world(map_path, car_path, output_path, args.name)
    print(
        f"Generated {output_path} from {map_path} with {args.name} "
        f"at row {row}, column {column}, pose {' '.join(str(v) for v in pose)}."
    )


if __name__ == "__main__":
    main()
