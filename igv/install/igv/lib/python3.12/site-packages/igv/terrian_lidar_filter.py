#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Imu
import numpy as np
import math

class TerrainAwareLidarFilter(Node):

    def __init__(self):
        super().__init__('terrain_lidar_filter')

        # Tunable parameters (expose via ros2 param or change here)
        self.declare_parameter('base_gradient', 0.05)        # base meters difference
        self.declare_parameter('gradient_scale', 0.02)      # scale * range (distance-adaptive)
        self.declare_parameter('window', 3)                 # sliding half-window size
        self.declare_parameter('min_consecutive', 5)        # beams required to mark region slope
        self.declare_parameter('use_imu', True)
        self.declare_parameter('pitch_disable_deg', 4.0)    # if |pitch| > this, disable filter
        self.declare_parameter('mask_value_eps', 0.01)      # added to range_max when masking
        self.declare_parameter('min_valid_range', 0.01)     # ignore near-zero invalid returns

        self.base_gradient = float(self.get_parameter('base_gradient').value)
        self.gradient_scale = float(self.get_parameter('gradient_scale').value)
        self.window = int(self.get_parameter('window').value)
        self.min_consecutive = int(self.get_parameter('min_consecutive').value)
        self.use_imu = bool(self.get_parameter('use_imu').value)
        self.pitch_disable_deg = float(self.get_parameter('pitch_disable_deg').value)
        self.mask_value_eps = float(self.get_parameter('mask_value_eps').value)
        self.min_valid_range = float(self.get_parameter('min_valid_range').value)

        self.imu_pitch = 0.0  # radians
        if self.use_imu:
            self.create_subscription(Imu, '/imu', self.imu_cb, 20)

        self.create_subscription(LaserScan, '/scan', self.scan_cb, 20)
        self.pub = self.create_publisher(LaserScan, '/scan_filtered', 10)

        self.get_logger().info("Terrain-aware lidar filter started (improved).")

    def imu_cb(self, msg: Imu):
        # convert quaternion to pitch (y axis)
        q = msg.orientation
        # quaternion->euler safe conversion
        qw, qx, qy, qz = q.w, q.x, q.y, q.z
        # roll
        t0 = +2.0 * (qw * qx + qy * qz)
        t1 = +1.0 - 2.0 * (qx * qx + qy * qy)
        # pitch
        t2 = +2.0 * (qw * qy - qz * qx)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch = math.asin(t2)
        self.imu_pitch = pitch

    def scan_cb(self, msg: LaserScan):
        ranges = np.array(msg.ranges, dtype=np.float32)
        n = len(ranges)
        if n == 0:
            return

        # If IMU says we're already pitched beyond threshold, skip filter to avoid masking real obstacles
        if self.use_imu and (math.degrees(abs(self.imu_pitch)) >= self.pitch_disable_deg):
            # pass through unchanged
            self.pub.publish(msg)
            return

        # Precompute angles
        angles = msg.angle_min + np.arange(n) * msg.angle_increment

        # Prepare output
        filtered = np.array(ranges, copy=True)

        # Valid mask
        valid_mask = np.isfinite(ranges) & (ranges > self.min_valid_range) & (ranges <= msg.range_max)

        # compute local gradients using central differences across sliding window
        half = self.window
        # compute per-beam "smoothness" boolean
        smooth = np.zeros(n, dtype=bool)

        for i in range(half, n - half):
            if not valid_mask[i]:
                continue

            # take window of ranges (ignore invalids within window)
            window_inds = np.arange(i - half, i + half + 1)
            wvals = ranges[window_inds]
            wvalid = (np.isfinite(wvals) & (wvals > self.min_valid_range) & (wvals <= msg.range_max))
            if np.sum(wvalid) < (2 * half):  # too many invalids in window
                continue

            # use only valid entries for gradient estimate
            wv = wvals[wvalid]
            # estimate gradient as mean absolute adjacent diff across window
            diffs = np.abs(np.diff(wv))
            if diffs.size == 0:
                continue
            avg_diff = float(np.mean(diffs))

            # distance-adaptive threshold: base + scale * mean_range_in_window
            mean_r = float(np.mean(wv))
            threshold = self.base_gradient + (self.gradient_scale * mean_r)

            # a "smooth" beam means avg gradient is below threshold
            if avg_diff <= threshold:
                smooth[i] = True

        # identify contiguous runs of smooth beams and require min_consecutive length
        i = 0
        masked_count = 0
        while i < n:
            if not smooth[i]:
                i += 1
                continue
            # start of run
            j = i
            while j < n and smooth[j]:
                j += 1
            run_len = j - i
            if run_len >= self.min_consecutive:
                # If run is long enough, mask the run (mark as slope)
                mask_val = float(msg.range_max) + self.mask_value_eps
                filtered[i:j] = mask_val
                masked_count += run_len
            i = j

        # Build a new LaserScan message (preserve metadata)
        new_scan = LaserScan()
        new_scan.header = msg.header
        new_scan.angle_min = msg.angle_min
        new_scan.angle_max = msg.angle_max
        new_scan.angle_increment = msg.angle_increment
        new_scan.time_increment = msg.time_increment
        new_scan.scan_time = msg.scan_time
        new_scan.range_min = msg.range_min
        new_scan.range_max = msg.range_max
        # convert to Python list of floats (safe type)
        new_scan.ranges = [float(x) if np.isfinite(x) else float('inf') for x in filtered.tolist()]
        # preserve intensities if present
        try:
            new_scan.intensities = list(msg.intensities)
        except Exception:
            new_scan.intensities = []

        self.get_logger().debug(f"Filtered {masked_count}/{n} beams as slope (avg_grad_threshold={self.base_gradient:.3f}+scale).")
        self.pub.publish(new_scan)

def main(args=None):
    rclpy.init(args=args)
    node = TerrainAwareLidarFilter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()