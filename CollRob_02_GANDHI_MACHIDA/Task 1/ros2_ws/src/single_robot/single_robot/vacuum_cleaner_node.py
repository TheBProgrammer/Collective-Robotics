import math
from enum import Enum

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class State(Enum):
    SWEEP = 'sweep'
    TURN_A = 'turn_a'
    SHIFT = 'shift'
    TURN_B = 'turn_b'


class VacuumCleaner(Node):

    FORWARD_SPEED = 0.5
    SHIFT_SPEED = 0.5
    TURN_SPEED = 1.2

    FRONT_HALF_ANGLE = math.radians(30.0)
    TRIGGER_DISTANCE = 0.30

    BODY_WIDTH = 0.34
    TURN_ANGLE = math.pi / 2.0
    YAW_TOLERANCE = math.radians(1.0)
    SHIFT_TIMEOUT = 10.0

    KP_YAW = 4.0
    KP_SHIFT = 5.0

    CONTROL_PERIOD = 0.05

    def __init__(self):
        super().__init__('vacuum_cleaner_node')

        self.state = State.SWEEP
        # +1 turns left, -1 turns right. Flips after every U-turn so the
        # lateral shift always advances in the same direction.
        self.turn_direction = 1.0
        self.target_yaw = 0.0
        self.shift_start_x = 0.0
        self.shift_start_y = 0.0
        self.shift_start_time = 0.0

        self.yaw = 0.0
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.have_odom = False
        self.latest_scan: LaserScan | None = None

        self.create_subscription(LaserScan, '/scan', self._on_scan, 10)
        self.create_subscription(Odometry, '/odom', self._on_odom, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(self.CONTROL_PERIOD, self._tick)

        self.get_logger().info('vacuum_cleaner_node started (boustrophedon)')

    def _on_scan(self, msg: LaserScan) -> None:
        self.latest_scan = msg

    def _on_odom(self, msg: Odometry) -> None:
        self.pos_x = msg.pose.pose.position.x
        self.pos_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        self.have_odom = True

    @staticmethod
    def _wrap(angle: float) -> float:
        return math.atan2(math.sin(angle), math.cos(angle))

    def _front_min(self, scan: LaserScan) -> float:
        r_lo = scan.range_min if scan.range_min > 0.0 else 0.0
        r_hi = scan.range_max if scan.range_max > 0.0 else math.inf
        out = math.inf
        for i, r in enumerate(scan.ranges):
            if not math.isfinite(r) or r < r_lo or r > r_hi:
                continue
            angle = self._wrap(scan.angle_min + i * scan.angle_increment)
            if abs(angle) <= self.FRONT_HALF_ANGLE and r < out:
                out = r
        return out

    def _begin_turn(self) -> None:
        self.target_yaw = self._wrap(self.yaw + self.turn_direction * self.TURN_ANGLE)

    def _begin_shift(self) -> None:
        self.shift_start_x = self.pos_x
        self.shift_start_y = self.pos_y
        self.shift_start_time = self.get_clock().now().nanoseconds * 1e-9

    def _tick(self) -> None:
        if self.latest_scan is None or not self.have_odom:
            return

        front_min = self._front_min(self.latest_scan)

        if self.state is State.SWEEP:
            if front_min < self.TRIGGER_DISTANCE:
                self._begin_turn()
                self.state = State.TURN_A
                self.get_logger().info(
                    f'SWEEP -> TURN_A ({"left" if self.turn_direction > 0 else "right"})'
                )

        elif self.state is State.TURN_A:
            if abs(self._wrap(self.target_yaw - self.yaw)) < self.YAW_TOLERANCE:
                self._begin_shift()
                self.state = State.SHIFT
                self.get_logger().info('TURN_A -> SHIFT')

        elif self.state is State.SHIFT:
            d = math.hypot(self.pos_x - self.shift_start_x,
                           self.pos_y - self.shift_start_y)
            elapsed = self.get_clock().now().nanoseconds * 1e-9 - self.shift_start_time
            timed_out = elapsed > self.SHIFT_TIMEOUT
            if d >= self.BODY_WIDTH or front_min < self.TRIGGER_DISTANCE or timed_out:
                self._begin_turn()
                self.state = State.TURN_B
                reason = 'timeout' if timed_out and d < self.BODY_WIDTH and front_min >= self.TRIGGER_DISTANCE else 'ok'
                self.get_logger().info(f'SHIFT -> TURN_B (shifted {d:.2f} m, {reason})')

        else:
            if abs(self._wrap(self.target_yaw - self.yaw)) < self.YAW_TOLERANCE:
                self.turn_direction *= -1.0
                self.state = State.SWEEP
                self.get_logger().info('TURN_B -> SWEEP')

        twist = Twist()
        if self.state is State.SWEEP:
            twist.linear.x = self.FORWARD_SPEED
        elif self.state is State.SHIFT:
            d = math.hypot(self.pos_x - self.shift_start_x,
                           self.pos_y - self.shift_start_y)
            remaining = max(0.0, self.BODY_WIDTH - d)
            twist.linear.x = min(self.SHIFT_SPEED, self.KP_SHIFT * remaining)
        else:
            yaw_err = self._wrap(self.target_yaw - self.yaw)
            twist.angular.z = max(-self.TURN_SPEED,
                                  min(self.TURN_SPEED, self.KP_YAW * yaw_err))
        self.cmd_pub.publish(twist)


def main() -> None:
    rclpy.init()
    node = VacuumCleaner()
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
