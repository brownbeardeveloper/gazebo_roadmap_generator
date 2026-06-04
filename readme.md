# Gazebo Roadmap Generator

Simple Python wizard for building Gazebo Sim road maps from a grid.

## Version 1.2

- Added `maps`, a static wall model with collision geometry for LIDAR training.
- Added drag-and-paint grid modes: Road, Intersection, Wall, and Erase.
- Painted wall cells are exported into `road.world`.
- Added a clean check mode for ROS 2 Jazzy / Gazebo Sim workflows.

## How It Works

1. Run the wizard.
2. Choose rows, columns, and time of day.
3. Paint the grid.
4. Generate the Gazebo world.

The wizard writes `road.world` and launches it with `gz sim` when Gazebo Sim is available. Local models are resolved through `GZ_SIM_RESOURCE_PATH`, so copying into `~/.gazebo/models` is not needed for Jazzy.

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
./start_map.sh test.yaml
```

Check generation without launching Gazebo:

```bash
./start_map.sh test.yaml --check
```

Generate only:

```bash
./start_map.sh test.yaml --no-launch --output road.world
```

Classic Gazebo compatibility only:

```bash
./start_map.sh --install-classic-models
```
