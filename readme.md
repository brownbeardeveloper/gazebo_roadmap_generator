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
source /opt/ros/$ROS_DISTRO/setup.bash
./play.sh
```

Keep the terminal focused and use the arrow keys to drive. Press `space` to stop and `q` to quit.
`play.sh` starts Gazebo running; if the camera looks frozen, click the orange play button in Gazebo.
When ROS 2 is sourced, the keyboard driver publishes `/cmd_vel` through
`ros_gz_bridge` at 20 Hz.
The bridge configuration is in `config/ros_gz_bridge.yaml`; `/cmd_vel` is
bridged from ROS 2 to Gazebo, and camera/odometry topics are bridged back to ROS 2.

The keyboard driver publishes to Gazebo Transport on `/cmd_vel`, so `gz topic -l`
is the direct way to inspect it. If ROS 2 and `ros_gz_bridge` are sourced,
`play.sh` also starts a bridge so `/cmd_vel` appears in `ros2 topic list`.
The car camera publishes on `/model/roadmap_car/front_camera/image` and
`/model/roadmap_car/front_camera/camera_info`.
Check it directly with `gz topic -l | grep front_camera`, or view the bridged
ROS image with `rqt_image_view` when that package is installed.

Check generation without launching Gazebo:

```bash
./start_map.sh example.yaml --check
```

Generate only:

```bash
./start_map.sh example.yaml --no-launch --output road.world
```
