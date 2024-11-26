import streamlit as st
import time
import matplotlib.pyplot as plt
import pandas as pd
from phi_accrual_failure_detector import PhiAccrualFailureDetector

# Initialize the failure detector with default parameters
detector = PhiAccrualFailureDetector(threshold=8.0, max_sample_size=100, min_std_deviation=0.1, 
                                     acceptable_heartbeat_pause=1.0, first_heartbeat_estimate=1.0)
heartbeat_data = []

# Initialize the state
heartbeats = []
pause_simulation = False
status_text = st.empty()
heartbeat_data = []

# UI layout
st.title("Phi Accrual Failure Detector Simulator")
st.sidebar.header("Control Panel")

# Sidebar controls
threshold = st.sidebar.slider("Failure Threshold (Phi)", min_value=1.0, max_value=20.0, value=8.0, step=0.1)
pause_duration = st.sidebar.slider("Simulate Pause Duration (seconds)", min_value=0.5, max_value=10.0, value=3.0, step=0.5)
heartbeat_interval = st.sidebar.slider("Heartbeat Interval (seconds)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)

# Update threshold based on user input
detector.threshold = threshold

# Buttons for starting/stopping the simulation
start_button = st.sidebar.button("Start Simulation")
pause_button = st.sidebar.button("Pause Heartbeats")
stop_button = st.sidebar.button("Stop Simulation")

# Main panel for displaying heartbeat details
st.subheader("Heartbeat Simulation")
heartbeat_log = st.empty()
availability_log = st.empty()

def simulate_heartbeats():
    global heartbeats, pause_simulation, is_simulation_running
    heartbeat_count = 0
    is_simulation_running = True

    # Clear heartbeat data only when a new simulation starts
    if start_button:
        heartbeat_data.clear()

    try:
        while is_simulation_running:
            if pause_simulation:
                time.sleep(pause_duration)
                phi_value = detector.phi()
                availability = detector.is_available()
                availability_log.write(f"After pause: phi={phi_value:.2f}, is_available={availability}")
                heartbeat_data.append((time.time(), phi_value, availability))
                pause_simulation = False
                continue

            heartbeat_count += 1
            heartbeats.append(f"Sending heartbeat {heartbeat_count}")
            detector.heartbeat()

            phi_value = detector.phi()
            availability = detector.is_available()
            heartbeats.append(f"Heartbeat {heartbeat_count}: phi={phi_value:.2f}, is_available={availability}")
            heartbeat_data.append((time.time(), phi_value, availability))

            heartbeat_log.text("\n".join(heartbeats[-10:]))
            status_text.text(f"Last Heartbeat: {heartbeat_count} | Phi: {phi_value:.2f} | Available: {availability}")

            time.sleep(heartbeat_interval)
    finally:
        # Capture the last heartbeat data even if the loop breaks
        phi_value = detector.phi()
        availability = detector.is_available()
        heartbeat_data.append((time.time(), phi_value, availability))

def plot_simulation_summary():
    global heartbeat_data

    if not heartbeat_data:
        st.error("No data for plotting. Run the simulation to gather data.")
        return

    times, phi_values, availability_status = zip(*heartbeat_data)

    # Plotting
    fig, ax1 = plt.subplots()

    ax1.set_xlabel('Time')
    ax1.set_ylabel('Phi Value', color='tab:blue')
    ax1.plot(times, phi_values, label='Phi Value', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # Plot the availability status on a secondary y-axis
    ax2 = ax1.twinx()
    ax2.set_ylabel('Availability', color='tab:orange')
    ax2.step(times, availability_status, where='post', label='Availability', color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')

    # Combine legends from both axes
    fig.legend(loc='upper right')
    fig.tight_layout()

    st.pyplot(fig)

if start_button:
    heartbeat_data.clear()
    st.write("Simulating heartbeats...")
    simulate_heartbeats()

if stop_button:
    is_simulation_running = False
    print(heartbeat_data)  # Print the data for inspection
    plot_simulation_summary()