#!/usr/bin/env python3
import argparse
import curses
import shutil
import subprocess
import sys
import time


DEFAULT_RATE = 20.0


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def twist_payload(linear, angular):
    return f"linear {{ x: {linear:.3f} }} angular {{ z: {angular:.3f} }}"


def publish_twist_once(topic, linear, angular):
    subprocess.run(
        [
            "gz",
            "topic",
            "-t",
            topic,
            "-m",
            "gz.msgs.Twist",
            "-p",
            twist_payload(linear, angular),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


class Ros2TwistPublisher:
    def __init__(self, topic, rate):
        import rclpy
        from geometry_msgs.msg import Twist

        self.topic = topic
        self.rate = rate
        self.rclpy = rclpy
        self.twist_type = Twist
        self.rclpy.init(args=None)
        self.node = self.rclpy.create_node("gazebo_keyboard_drive")
        self.publisher = self.node.create_publisher(Twist, topic, 10)

    @property
    def name(self):
        return "ros2"

    def publish(self, linear, angular):
        msg = self.twist_type()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.publisher.publish(msg)
        self.rclpy.spin_once(self.node, timeout_sec=0.0)

    def status(self):
        return ""

    def close(self):
        self.publish(0.0, 0.0)
        self.node.destroy_node()
        self.rclpy.shutdown()


class GazeboTwistPublisher:
    def __init__(self, topic, rate):
        self.topic = topic
        self.rate = rate

    @property
    def name(self):
        return "gz"

    def publish(self, linear, angular):
        publish_twist_once(self.topic, linear, angular)

    def status(self):
        return "using slow gz one-shot publisher; source ROS 2 for 20 Hz driving"

    def close(self):
        publish_twist_once(self.topic, 0.0, 0.0)


def create_publisher(args):
    if args.transport in ("auto", "ros2"):
        try:
            return Ros2TwistPublisher(args.topic, args.rate)
        except ImportError:
            if args.transport == "ros2":
                raise

    return GazeboTwistPublisher(args.topic, args.rate)


def safe_addstr(stdscr, row, column, text):
    height, width = stdscr.getmaxyx()
    if row >= height or column >= width:
        return
    stdscr.addstr(row, column, text[: max(0, width - column - 1)])


def draw(stdscr, topic, transport, linear, angular, last_error):
    stdscr.erase()
    safe_addstr(stdscr, 0, 0, "Gazebo keyboard drive")
    safe_addstr(stdscr, 2, 0, f"topic:   {topic}")
    safe_addstr(stdscr, 3, 0, f"transport: {transport}")
    safe_addstr(stdscr, 4, 0, f"linear:  {linear:+.2f} m/s")
    safe_addstr(stdscr, 5, 0, f"angular: {angular:+.2f} rad/s")
    safe_addstr(stdscr, 7, 0, "arrow up/down: throttle")
    safe_addstr(stdscr, 8, 0, "arrow left/right: steering")
    safe_addstr(stdscr, 9, 0, "space: stop    c: center steering    q: quit")
    if last_error:
        safe_addstr(stdscr, 11, 0, last_error)
    stdscr.refresh()


def teleop(stdscr, args):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.nodelay(True)

    linear = 0.0
    angular = 0.0
    last_error = ""
    publisher = create_publisher(args)
    interval = 1.0 / args.rate
    next_publish = 0.0

    try:
        publisher.publish(linear, angular)

        while True:
            key = stdscr.getch()
            if key == curses.KEY_UP:
                linear = clamp(linear + args.linear_step, -args.max_linear, args.max_linear)
            elif key == curses.KEY_DOWN:
                linear = clamp(linear - args.linear_step, -args.max_linear, args.max_linear)
            elif key == curses.KEY_LEFT:
                angular = clamp(angular + args.angular_step, -args.max_angular, args.max_angular)
            elif key == curses.KEY_RIGHT:
                angular = clamp(angular - args.angular_step, -args.max_angular, args.max_angular)
            elif key == ord(" "):
                linear = 0.0
                angular = 0.0
            elif key in (ord("c"), ord("C")):
                angular = 0.0
            elif key in (ord("q"), ord("Q")):
                break

            now = time.monotonic()
            if now >= next_publish:
                publisher.publish(linear, angular)
                next_publish = now + interval

            last_error = publisher.status()
            draw(stdscr, args.topic, publisher.name, linear, angular, last_error)
            time.sleep(0.02)
    finally:
        publisher.close()


def build_parser():
    parser = argparse.ArgumentParser(description="Drive a Gazebo DiffDrive model with arrow keys.")
    parser.add_argument("--topic", default="/cmd_vel", help="Gazebo Twist topic.")
    parser.add_argument("--rate", type=float, default=DEFAULT_RATE, help="Publish rate in Hz.")
    parser.add_argument(
        "--transport",
        choices=("auto", "ros2", "gz"),
        default="auto",
        help="Prefer ROS 2 publishing through ros_gz_bridge, or fall back to gz one-shot publishing.",
    )
    parser.add_argument("--max-linear", type=float, default=0.9, help="Maximum linear speed.")
    parser.add_argument("--max-angular", type=float, default=2.4, help="Maximum turn rate.")
    parser.add_argument("--linear-step", type=float, default=0.15, help="Throttle step per key press.")
    parser.add_argument("--angular-step", type=float, default=0.4, help="Steering step per key press.")
    return parser


def main():
    args = build_parser().parse_args()
    if shutil.which("gz") is None:
        print("gz not found in PATH. Install Gazebo Sim in the VM first.", file=sys.stderr)
        return 1
    curses.wrapper(teleop, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
