# Gazebo Roadmap Generator

Simple Python wizard for building Gazebo Sim road maps from a grid.

## Version 1.2

- Added generated `maps` wall block model support with collision geometry for LIDAR training.
- Added drag-and-paint grid modes: Road, Intersection, Wall, and Erase.
- Painted wall cells are merged into solid wall blocks in `road.world`.
- The `maps` model directory is created automatically when missing.
- Added a clean check mode for ROS 2 Jazzy / Gazebo Sim workflows.

## How It Works

1. Run the wizard.
2. Choose rows, columns, and time of day.
3. Paint the grid.
4. Generate the Gazebo world.

The wizard writes `road.world` and launches it with `gz sim` when Gazebo Sim is available. Local models are resolved through `GZ_SIM_RESOURCE_PATH`.

## Requirements

- Python 3.10+
- ROS 2 Jazzy with Gazebo Sim (`gz`)
- Micromamba

## Run

Create the environment:

```bash
micromamba env create -f environment.yml
```

Run the generator:

```bash
./start_map.sh
```

Use a saved map:

```bash
./start_map.sh example.yaml
```

Run the playable example map with the car:

```bash
./play.sh
```

Keep the terminal focused and use the arrow keys to drive. Press `space` to stop and `q` to quit.

Check generation without launching Gazebo:

```bash
./start_map.sh example.yaml --check
```

Generate only:

```bash
./start_map.sh example.yaml --no-launch --output road.world
```
