import math
from enum import Enum

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class State(Enum):
    CRUISE = 'cruise'
    AVOID = 'avoid'


class CollisionAvoidance(Node):

    CRUISE_SPEED = 0.5
    TURN_SPEED = 1.2
    FRONT_HALF_ANGLE = math.radians(30.0)
    TRIGGER_DISTANCE = 0.25
    CLEAR_DISTANCE = 0.45
    CONTROL_PERIOD = 0.05

    def __init__(self):
        super().__init__('collision_avoidance_node')

        self.state = State.CRUISE
        # Sign convention from REP-103: angular.z > 0 turns left.
        self.turn_sign = 1.0
        self.latest_scan: LaserScan | None = None

        self.create_subscription(LaserScan, '/scan', self._on_scan, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(self.CONTROL_PERIOD, self._tick)

        self.get_logger().info('collision_avoidance_node started')

    def _on_scan(self, msg: LaserScan) -> None:
        self.latest_scan = msg

    def _sector_minima(self, scan: LaserScan) -> tuple[float, float, float]:
        front_min = math.inf
        left_min = math.inf
        right_min = math.inf

        r_lo = scan.range_min if scan.range_min > 0.0 else 0.0
        r_hi = scan.range_max if scan.range_max > 0.0 else math.inf

        for i, r in enumerate(scan.ranges):
            if not math.isfinite(r) or r < r_lo or r > r_hi:
                continue

            angle = scan.angle_min + i * scan.angle_increment
            angle = math.atan2(math.sin(angle), math.cos(angle))

            if abs(angle) <= self.FRONT_HALF_ANGLE and r < front_min:
                front_min = r
            if 0.0 < angle <= math.pi / 2.0 and r < left_min:
                left_min = r
            elif -math.pi / 2.0 <= angle < 0.0 and r < right_min:
                right_min = r

        return front_min, left_min, right_min

    def _tick(self) -> None:
        if self.latest_scan is None:
            return

        front_min, left_min, right_min = self._sector_minima(self.latest_scan)

        if self.state is State.CRUISE:
            if front_min < self.TRIGGER_DISTANCE:
                self.turn_sign = 1.0 if left_min >= right_min else -1.0
                self.state = State.AVOID
                self.get_logger().info(
                    f'CRUISE -> AVOID (front={front_min:.2f} m, '
                    f'turn={"left" if self.turn_sign > 0 else "right"})'
                )
        else:
            if front_min > self.CLEAR_DISTANCE:
                self.state = State.CRUISE
                self.get_logger().info(f'AVOID -> CRUISE (front={front_min:.2f} m)')

        twist = Twist()
        if self.state is State.CRUISE:
            twist.linear.x = self.CRUISE_SPEED
        else:
            twist.angular.z = self.TURN_SPEED * self.turn_sign
        self.cmd_pub.publish(twist)


def main() -> None:
    rclpy.init()
    node = CollisionAvoidance()
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
