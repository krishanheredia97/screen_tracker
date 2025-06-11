import datetime
import threading
import time
import pygetwindow as gw
from .constants import STATE_ACTIVE_WORK

class WindowMonitor:
    def __init__(self):
        self.current_window_title = None
        self.current_window_start_time = None
        self.monitoring_active = False
        self.thread = None
        self.stop_event = threading.Event()
        self.state_manager_ref = None
        self.data_logger_ref = None

    def _get_active_window_title(self):
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                return active_window.title
            return "Unknown Window" # Consistent name for no active window
        except Exception as e:
            print(f"Error getting active window title: {e}")
            return "Error getting active window."

    def _monitor_loop(self):
        # self.current_window_title = self._get_active_window_title() # Initial title set in start_monitoring
        # self.current_window_start_time = datetime.datetime.now() # Initial time set in start_monitoring
        # Initial logging of the first window is handled in start_monitoring to avoid duplicate efforts
        # and to ensure data_logger_ref is available.

        while not self.stop_event.is_set():
            if not self.state_manager_ref or self.state_manager_ref.get_current_state() != STATE_ACTIVE_WORK:
                self.stop_monitoring() # Ensure cleanup if state changed
                break

            new_title = self._get_active_window_title()
            now = datetime.datetime.now()

            if new_title != self.current_window_title:
                if self.current_window_title is not None and self.data_logger_ref:
                    # Log previous window before switching
                    self.data_logger_ref.log_window_activity(
                        self.current_window_start_time,
                        now, # End time for the previous window is 'now'
                        self.current_window_title,
                        STATE_ACTIVE_WORK
                    )
                self.current_window_title = new_title
                self.current_window_start_time = now # Start time for the new window is 'now'
                # Log the new window if it's a valid one (optional, could also log only on next change or exit)
                # For consistency, let's log the new window immediately if it's distinct and valid.
                # This was part of the original logic implicitly by how unique windows were added.
                if self.current_window_title and self.current_window_title not in ["Unknown Window", "Error getting active window."] and self.data_logger_ref:
                    if self.current_window_title not in self.data_logger_ref.unique_window_titles:
                        # This part is primarily for adding to unique_windows.txt, actual CSV log is for duration.
                        # The original code had a section for this in start_monitoring and DataLogger.
                        # To keep it simple, DataLogger handles unique_windows.txt additions.
                        # We can call a preliminary log here if desired for immediate unique add.
                        pass # DataLogger handles unique adds during its log_window_activity
            
            time.sleep(1) # Check every second

    def start_monitoring(self, state_manager, data_logger):
        if not self.monitoring_active:
            self.monitoring_active = True
            self.stop_event.clear()
            self.state_manager_ref = state_manager
            self.data_logger_ref = data_logger
            self.current_window_start_time = datetime.datetime.now() # Reset start time
            self.current_window_title = self._get_active_window_title() # Get initial window
            
            print(f"Window monitoring started. Initial window: {self.current_window_title}")
            # Log the first window immediately if it's a valid one and we are in active work state
            if self.current_window_title and self.current_window_title not in ["Unknown Window", "Error getting active window."] and self.data_logger_ref and self.state_manager_ref.get_current_state() == STATE_ACTIVE_WORK:
                # Log to CSV (will also handle unique window addition in DataLogger)
                # Using current_window_start_time for both start and end for an "initial appearance" log
                # This ensures it's captured if the app closes before a window change.
                # However, the original logic in _monitor_loop logged the *first* window when monitoring starts
                # with start and end time being the same. Let's replicate that if it's desired.
                # The original code's _monitor_loop had a section that logged the initial window.
                # Let's ensure DataLogger handles adding to unique_windows.txt if it's a new window.
                # The primary duration log will happen on window change or when monitoring stops.
                # For now, just ensure DataLogger knows about it for unique list purposes if it's new.
                if self.current_window_title not in self.data_logger_ref.unique_window_titles:
                    self.data_logger_ref.log_window_activity(
                        self.current_window_start_time,
                        self.current_window_start_time, # Log as an event / initial sighting
                        self.current_window_title,
                        STATE_ACTIVE_WORK
                    )
            
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop_monitoring(self):
        if self.monitoring_active:
            self.monitoring_active = False
            self.stop_event.set()
            if self.thread and self.thread.is_alive():
                # print("Attempting to join monitor thread...")
                self.thread.join(timeout=2) # Wait for thread to finish
                # if self.thread.is_alive():
                #     print("Monitor thread did not join in time.")
                # else:
                #     print("Monitor thread joined.")
            
            # Log the final window activity before stopping
            if self.current_window_title and self.current_window_start_time and self.data_logger_ref and self.state_manager_ref and self.state_manager_ref.get_current_state() == STATE_ACTIVE_WORK:
                now = datetime.datetime.now()
                if (now - self.current_window_start_time).total_seconds() > 0.1: # Min duration to log to avoid spam on rapid changes
                    self.data_logger_ref.log_window_activity(
                        self.current_window_start_time,
                        now,
                        self.current_window_title,
                        STATE_ACTIVE_WORK
                    )
            # print(f"Window monitoring stopped. Last window: {self.current_window_title}")
            self.current_window_title = None
            self.current_window_start_time = None
            # Don't nullify state_manager_ref and data_logger_ref here if they might be needed by other calls
            # or if stop_monitoring can be called multiple times. The original code did clear them.
            # For now, let's keep original behavior.
            self.state_manager_ref = None 
            self.data_logger_ref = None
            print("Window monitoring stopped.")
