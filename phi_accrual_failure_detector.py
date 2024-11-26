import math
import time
import logging
from threading import Lock

class HeartbeatHistory:
    def __init__(self, max_sample_size):
        self.max_sample_size = max_sample_size
        self.intervals = []
        self.interval_sum = 0
        self.squared_interval_sum = 0

    def add_interval(self, interval):
        if len(self.intervals) >= self.max_sample_size:
            self.remove_oldest()
        self.intervals.append(interval)
        self.interval_sum += interval
        self.squared_interval_sum += interval * interval

    def remove_oldest(self):
        if self.intervals:
            oldest = self.intervals.pop(0)
            self.interval_sum -= oldest
            self.squared_interval_sum -= oldest * oldest

    def mean(self):
        if not self.intervals:
            raise ValueError("Cannot compute mean of an empty history")
        return self.interval_sum / len(self.intervals)

    def variance(self):
        if not self.intervals:
            raise ValueError("Cannot compute variance of an empty history")
        mean = self.mean()
        return (self.squared_interval_sum / len(self.intervals)) - (mean * mean)

    def std_deviation(self):
        return math.sqrt(self.variance())


class PhiAccrualFailureDetector:
    def __init__(self, threshold, max_sample_size, min_std_deviation, acceptable_heartbeat_pause, first_heartbeat_estimate):
        self.threshold = threshold
        self.max_sample_size = max_sample_size
        self.min_std_deviation = min_std_deviation
        self.acceptable_heartbeat_pause = acceptable_heartbeat_pause
        self.first_heartbeat_estimate = first_heartbeat_estimate
        self.history = HeartbeatHistory(max_sample_size)
        self.last_heartbeat = None
        self.lock = Lock()

        # Initial guess for heartbeats to bootstrap the system
        mean = self.first_heartbeat_estimate
        std_deviation = mean / 4
        self.history.add_interval(mean - std_deviation)
        self.history.add_interval(mean + std_deviation)

    def heartbeat(self):
        with self.lock:
            try:
                current_time = self._current_time()
                if self.last_heartbeat is not None:
                    interval = current_time - self.last_heartbeat
                     #print(f"[DEBUG] Interval between heartbeats: {interval}ms")  # Debug statement
                    if interval >= (self.acceptable_heartbeat_pause / 3 * 2):
                        print(f"[WARNING] Heartbeat interval is growing large: {interval}ms")
                    self.history.add_interval(interval)
                self.last_heartbeat = current_time
                 #print(f"[DEBUG] Heartbeat registered at {current_time}ms")  # Debug statement
            except Exception as e:
                print(f"[ERROR] Exception in heartbeat: {e}")  # Catch any error during heartbeat

    def phi(self):
        with self.lock:
            if self.last_heartbeat is None:
                return 0.0  # No heartbeats yet, so consider it healthy

            current_time = self._current_time()
            time_diff = current_time - self.last_heartbeat

            try:
                mean = self.history.mean()
                std_deviation = max(self.history.std_deviation(), self.min_std_deviation)
                phi_value = self._compute_phi(time_diff, mean + self.acceptable_heartbeat_pause, std_deviation)
                #print(f"[DEBUG] Phi calculation: time_diff={time_diff}, mean={mean}, std_deviation={std_deviation}, phi={phi_value}")
                return phi_value
            except ValueError as e:
                print(f"[ERROR] Exception in phi calculation: {e}")
                return 0.0

    def is_available(self):
        phi_value = self.phi()
        return phi_value < self.threshold

    def _compute_phi(self, time_diff, mean, std_deviation):
        # Ensure std_deviation is not too small to avoid extreme y values
        if std_deviation < 0.001:  # Minimum threshold for std_deviation
            std_deviation = 0.001

        # Calculate y
        y = (time_diff - mean) / std_deviation

        # Log a warning if y is excessively large or small
        if abs(y) > 700:
            logging.warning(f"Warning: y value {y} is too large and may cause overflow.")
        
        # Cap y to a maximum safe value to prevent overflow in math.exp()
        max_y = 700  # Safe upper bound for exponent
        y = min(y, max_y)

        try:
            # Compute e while handling possible overflow
            e = math.exp(-y * (1.5976 + 0.070566 * y * y))
        except OverflowError:
            # Handle the overflow by assigning e a very large value
            e = float('inf')

        # Compute the final result
        if e == float('inf'):
            # When e is infinity, phi should be a very high value (high suspicion)
            return float('inf')
        
        if time_diff > mean:
            # Normal calculation when time_diff is greater than the mean
            return max(-math.log10(e / (1.0 + e)), 0.0)
        else:
            # Alternative calculation for lower time_diff
            phi_value = -math.log10(1.0 - 1.0 / (1.0 + e))
            return max(phi_value, 0.0)

    def _current_time(self):
        # Time in milliseconds
        return int(time.time() * 1000)
