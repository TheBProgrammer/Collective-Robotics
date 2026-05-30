import math
from enum import Enum

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class State(Enum):
    FIND_WALL = 'find_wall'
    FOLLOW = 'follow'
    CORNER_TURN = 'corner_turn'


class WallFollower(Node):

    FORWARD_SPEED = 0.5
    SEARCH_TURN = 0.0
    CORNER_TURN_SPEED = 1.2

    FRONT_HALF_ANGLE = math.radians(30.0)
    SIDE_CENTER_ANGLE = -math.pi / 2.0
    SIDE_HALF_ANGLE = math.radians(30.0)

    TARGET_DISTANCE = 0.25
    WALL_DETECT_DISTANCE = 0.7
    CORNER_TRIGGER = 0.30
    CORNER_CLEAR = 0.6

    KP = 6.0
    KD = 0.5
    MAX_ANGULAR = 1.5

    CONTROL_PERIOD = 0.05

    def __init__(self):
        super().__init__('wall_follower_node')

        self.state = State.FIND_WALL
        self.prev_error = 0.0
        self.latest_scan: LaserScan | None = None

        self.create_subscription(LaserScan, '/scan', self._on_scan, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(self.CONTROL_PERIOD, self._tick)

        self.get_logger().info('wall_follower_node started')

    def _on_scan(self, msg: LaserScan) -> None:
        self.latest_scan = msg

    def _sector_min(self, scan: LaserScan, center: float, half_width: float) -> float:
        r_lo = scan.range_min if scan.range_min > 0.0 else 0.0
        r_hi = scan.range_max if scan.range_max > 0.0 else math.inf

        out = math.inf
        for i, r in enumerate(scan.ranges):
            if not math.isfinite(r) or r < r_lo or r > r_hi:
                continue
            angle = scan.angle_min + i * scan.angle_increment
            delta = math.atan2(math.sin(angle - center), math.cos(angle - center))
            if abs(delta) <= half_width and r < out:
                out = r
        return out

    def _tick(self) -> None:
        if self.latest_scan is None:
            return

        front_min = self._sector_min(self.latest_scan, 0.0, self.FRONT_HALF_ANGLE)
        right_min = self._sector_min(self.latest_scan, self.SIDE_CENTER_ANGLE, self.SIDE_HALF_ANGLE)

        if self.state is State.FIND_WALL:
            if front_min < self.CORNER_TRIGGER:
                self.state = State.CORNER_TURN
                self.get_logger().info(
                    f'FIND_WALL -> CORNER_TURN (front={front_min:.2f})'
                )
            elif right_min < self.WALL_DETECT_DISTANCE:
                self.state = State.FOLLOW
                self.prev_error = 0.0
                self.get_logger().info(
                    f'FIND_WALL -> FOLLOW (front={front_min:.2f}, right={right_min:.2f})'
                )
        elif self.state is State.FOLLOW:
            if front_min < self.CORNER_TRIGGER:
                self.state = State.CORNER_TURN
                self.get_logger().info(f'FOLLOW -> CORNER_TURN (front={front_min:.2f})')
        else:
            if front_min > self.CORNER_CLEAR:
                self.state = State.FOLLOW
                self.prev_error = 0.0
                self.get_logger().info(f'CORNER_TURN -> FOLLOW (front={front_min:.2f})')

        twist = Twist()
        if self.state is State.FIND_WALL:
            twist.linear.x = self.FORWARD_SPEED
            twist.angular.z = self.SEARCH_TURN
        elif self.state is State.FOLLOW:
            # PD on right-side distance.
            # error > 0 (too close) -> +angular.z (left, away from wall);
            # error < 0 (too far)   -> -angular.z (right, toward wall).
            measured = right_min if math.isfinite(right_min) else self.WALL_DETECT_DISTANCE
            error = self.TARGET_DISTANCE - measured
            d_error = (error - self.prev_error) / self.CONTROL_PERIOD
            self.prev_error = error
            cmd = self.KP * error + self.KD * d_error
            twist.linear.x = self.FORWARD_SPEED
            twist.angular.z = max(-self.MAX_ANGULAR, min(self.MAX_ANGULAR, cmd))
        else:
            twist.angular.z = self.CORNER_TURN_SPEED
        self.cmd_pub.publish(twist)


def main() -> None:
    rclpy.init()
    node = WallFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
