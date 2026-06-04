#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tkinter import *

from grid import *
from lxml import etree as ET
from map_file import loadMap, savedGridFromMap
from world_gen import DEFAULT_WORLD_PATH, worldGenerator


PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_DIRS = ("road_straight", "road_intersection", "maps")


class WorldSettings:
    def __init__(self):
        self.ambient = "0.47 0.47 0.47 1"
        self.time = "10:00"
        self.rows = 10
        self.cols = 10

    def worldScene(self):
        if self.time == "":
            self.time = "10:00"
        hour = int(self.time[0:2])

        if hour < 6 or hour >= 21:
            self.ambient = "0.08 0.16 0.20 1"
        elif 6 <= hour < 7:
            self.ambient = "0.47 0.31 0.24 1"
        elif 7 <= hour < 8:
            self.ambient = "0.47 0.27 0.31 1"
        elif 19 < hour < 20:
            self.ambient = "0.47 0.27 0.31 1"
        elif 20 <= hour < 21:
            self.ambient = "0.47 0.31 0.24 1"

    def apply_entries(self, row_entry, col_entry, time_entry, window):
        self.rows = int(row_entry.get())
        self.cols = int(col_entry.get())
        self.time = time_entry.get()
        self.worldScene()
        window.destroy()

    def getEntry(self):
        self.apply_entries(row_entry, col_entry, time_entry, root)


worldSettings = WorldSettings


def build_parser():
    parser = argparse.ArgumentParser(description="Generate a Gazebo Sim road world.")
    parser.add_argument("map", nargs="?", help="Saved map YAML-like file to load.")
    parser.add_argument("-o", "--output", default=DEFAULT_WORLD_PATH, help="World file to write.")
    parser.add_argument("--check", action="store_true", help="Generate and validate the world without launching Gazebo.")
    parser.add_argument("--no-launch", action="store_true", help="Generate only; do not launch Gazebo.")
    parser.add_argument("--verbose", action="store_true", help="Print the loaded grid before generating.")
    parser.add_argument(
        "--install-classic-models",
        action="store_true",
        help="Copy models into ~/.gazebo/models for Classic Gazebo compatibility.",
    )
    return parser


def gazebo_env():
    env = os.environ.copy()
    resource_paths = [str(PROJECT_ROOT)]
    existing_path = env.get("GZ_SIM_RESOURCE_PATH")
    if existing_path:
        resource_paths.append(existing_path)
    env["GZ_SIM_RESOURCE_PATH"] = os.pathsep.join(resource_paths)
    return env


def install_classic_models():
    model_root = Path.home() / ".gazebo" / "models"
    model_root.mkdir(parents=True, exist_ok=True)
    for model_dir in MODEL_DIRS:
        source = PROJECT_ROOT / model_dir
        target = model_root / model_dir
        if not target.exists():
            shutil.copytree(source, target)


def validate_world(path):
    tree = ET.parse(str(path))
    root_element = tree.getroot()
    if root_element.tag != "sdf":
        raise ValueError("Generated file is not an SDF document")

    includes = tree.findall(".//include")
    model_names = {model_dir.name for model_dir in PROJECT_ROOT.iterdir() if model_dir.is_dir()}
    missing_models = sorted(
        {
            uri.removeprefix("model://")
            for uri in (include.findtext("uri", "") for include in includes)
            if uri.startswith("model://") and uri.removeprefix("model://") not in model_names
        }
    )
    if missing_models:
        raise ValueError(f"Missing local model directories: {', '.join(missing_models)}")

    missing_names = [include.findtext("uri") for include in includes if include.find("name") is None]
    if missing_names:
        raise ValueError("Every include must have a unique name")

    return len(includes)


def launch_gazebo(world_path):
    gz = shutil.which("gz")
    if gz is None:
        print(f"Gazebo Sim not found in PATH. Generated {world_path}.")
        return

    subprocess.run([gz, "sim", str(world_path)], env=gazebo_env(), check=False)


def settings_from_map(map_data):
    settings = WorldSettings()
    settings.rows = map_data["rows"]
    settings.cols = map_data["columns"]
    settings.time = map_data.get("time", settings.time)
    settings.ambient = map_data.get("ambient", settings.ambient)
    return settings


def generate_from_map(map_path, output_path, verbose=False):
    map_data = loadMap(map_path)
    settings = settings_from_map(map_data)
    grid = savedGridFromMap(map_data)
    print(
        f"Loaded {map_path}: {settings.rows} rows, {settings.cols} columns, "
        f"time {settings.time}, ambient {settings.ambient}."
    )
    if verbose:
        grid.printgrid()
    return worldGenerator(grid, settings, output_path)


def generate_from_gui(output_path):
    root = Tk()
    root.title('Road Generator')


    #FRAME 1
    row_frame = Frame(master=root,width=200,height=5)

    rowLabelText=StringVar()
    rowLabelText.set("\t           Number of Rows: ")
    row_label=Label(row_frame, textvariable=rowLabelText)
    row_label.pack(side=LEFT,padx=10,pady=5)

    row_entry = Entry(row_frame)
    row_entry.pack(side=LEFT,padx=10,pady=5)
    row_entry.focus_set()

    row_frame.pack()

    #FRAME 2
    col_frame = Frame(master=root,width=100,height=50)

    colLabelText=StringVar()
    colLabelText.set("\t            Number of Cols: ")
    col_label=Label(col_frame, textvariable=colLabelText)
    col_label.pack(side=LEFT,padx=10,pady=5)

    col_entry = Entry(col_frame)
    col_entry.pack(side=LEFT,padx=10,pady=5)

    col_frame.pack()

    time_frame = Frame(master=root,width=100,height=50)

    timeLabelText=StringVar()
    timeLabelText.set("Enter time of day[24 hrs](hh:mm):")
    time_label=Label(time_frame, textvariable=timeLabelText)
    time_label.pack(side=LEFT,padx=10,pady=5)

    time_entry = Entry(time_frame)
    time_entry.pack(side=LEFT,padx=10,pady=5)

    time_frame.pack()

    w = WorldSettings()

    #Submit Buttom
    Button(
        root,
        text='Submit',
        command=lambda: w.apply_entries(row_entry, col_entry, time_entry, root),
    ).pack(pady=5)
    root.mainloop()

    print(w.rows,w.cols,w.time,w.ambient)

    OpenGrid(w)
    if output_path != DEFAULT_WORLD_PATH:
        Path(DEFAULT_WORLD_PATH).replace(output_path)
    return Path(output_path)


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.install_classic_models:
        install_classic_models()

    if args.map:
        world_path = generate_from_map(args.map, args.output, args.verbose)
    else:
        world_path = generate_from_gui(args.output)

    include_count = validate_world(world_path)
    print(f"Generated {world_path} with {include_count} model includes.")

    if args.check or args.no_launch:
        return 0

    launch_gazebo(world_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
