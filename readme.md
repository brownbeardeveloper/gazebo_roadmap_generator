# Road Generator

Simple Python wizard for building Gazebo road maps from a grid.

## Version 1.1

- Added `maps`, a static wall model with collision geometry for LIDAR training.
- Added drag-and-paint grid modes: Road, Intersection, Wall, and Erase.
- Painted wall cells are exported into `road.world`.

## How It Works

1. Run the wizard.
2. Choose rows, columns, and time of day.
3. Paint the grid.
4. Generate the Gazebo world.

The wizard copies the needed models into `~/.gazebo/models/` and writes `road.world`.

## Requirements

- Python 3.10+
- Gazebo 7+
- uv

## Run

```bash
./start_map.sh
```

Use a saved map:

```bash
./start_map.sh test.yaml
```
