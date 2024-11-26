from time import sleep
from phi_accrual_failure_detector import PhiAccrualFailureDetector

def main():
    # Configuration parameters for the failure detector
    threshold = 8.0
    max_sample_size = 100
    min_std_deviation = 100  # in milliseconds
    acceptable_heartbeat_pause = 200  # in milliseconds
    first_heartbeat_estimate = 500  # in milliseconds

    # Create an instance of the failure detector
    detector = PhiAccrualFailureDetector(
        threshold=threshold,
        max_sample_size=max_sample_size,
        min_std_deviation=min_std_deviation,
        acceptable_heartbeat_pause=acceptable_heartbeat_pause,
        first_heartbeat_estimate=first_heartbeat_estimate
    )

    # Simulate heartbeats
    print("Simulating heartbeats...")

    try:
        for i in range(10):
            print(f"Sending heartbeat {i + 1}")
            detector.heartbeat()  # Simulate a heartbeat
            sleep(0.1)  # 100ms between heartbeats
            phi_value = detector.phi()
            availability = detector.is_available()
            print(f"Heartbeat {i + 1}: phi={phi_value:.2f}, is_available={availability}")

        # Simulate a pause in heartbeats to see failure detection
        print("Simulating a long pause in heartbeats...")
        sleep(1)  # Pause for 1 second
        phi_value = detector.phi()
        availability = detector.is_available()
        print(f"After pause: phi={phi_value:.2f}, is_available={availability}")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
