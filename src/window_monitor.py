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
                if active_window.title == "Window Monitor": # Title of our GUI
                    return None # Special value to ignore this window
                return active_window.title
            return "Unknown Window" # Consistent name for no active window
        except Exception as e:
            print(f"Error getting active window title: {e}")
            return "Error getting active window."

    def _monitor_loop(self):
        while not self.stop_event.is_set():
            if not self.state_manager_ref or self.state_manager_ref.get_current_state() != STATE_ACTIVE_WORK:
                # self.stop_monitoring() # Called by state_manager if state changes out of ACTIVE_WORK
                break # Exit loop if state is no longer active work or refs are gone

            new_title = self._get_active_window_title() # This might be None for "Window Monitor"
            now = datetime.datetime.now()

            if new_title != self.current_window_title:
                # Log previous window if it was a valid, logged window (not None, not error string)
                if self.current_window_title and self.current_window_title not in ["Unknown Window", "Error getting active window."] and self.data_logger_ref:
                    self.data_logger_ref.log_window_activity(
                        self.current_window_start_time,
                        now,
                        self.current_window_title,
                        STATE_ACTIVE_WORK,
                        self.state_manager_ref.get_note() # Pass current note
                    )
                
                # If the new title is a valid window to log (not None, not error string)
                if new_title and new_title not in ["Unknown Window", "Error getting active window."]:
                    self.current_window_title = new_title
                    self.current_window_start_time = now
                else: # New title is None (Window Monitor) or an error/unknown string
                    # Current logged window has ended (logged above). Mark current as None/error.
                    self.current_window_title = new_title # Sets to None or error string
                    # self.current_window_start_time is not updated, as this state isn't logged with a start time.
            
            time.sleep(1) # Check every second

    def start_monitoring(self, state_manager, data_logger):
        if not self.monitoring_active:
            self.monitoring_active = True
            self.stop_event.clear()
            self.state_manager_ref = state_manager
            self.data_logger_ref = data_logger
            self.current_window_title = self._get_active_window_title() # Might be None
            self.current_window_start_time = datetime.datetime.now() 
            
            print(f"Window monitoring started. Initial window: {self.current_window_title if self.current_window_title is not None else 'Window Monitor (ignored)'}")
            # No immediate log here. The first valid window will be logged on change or when monitoring stops.
            
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop_monitoring(self):
        if self.monitoring_active:
            self.monitoring_active = False
            self.stop_event.set()
            if self.thread:
                self.thread.join(timeout=2) # Wait for thread to finish

            # Log the last active window before stopping, if it was a valid one and in active work state
            if self.current_window_title and self.current_window_title not in ["Unknown Window", "Error getting active window."] and self.data_logger_ref and self.state_manager_ref:
                if self.state_manager_ref.get_current_state() == STATE_ACTIVE_WORK:
                    self.data_logger_ref.log_window_activity(
                        self.current_window_start_time,
                        datetime.datetime.now(), # Current time as end time
                        self.current_window_title,
                        STATE_ACTIVE_WORK,
                        self.state_manager_ref.get_note() # Pass current note
                    )
            
            self.current_window_title = None # Reset for next session
            self.current_window_start_time = None
            # self.state_manager_ref = None # Clearing these might be problematic if stop_monitoring is called multiple times or by state_manager
            # self.data_logger_ref = None # Let's keep them unless explicitly causing issues.
            print("Window monitoring stopped.")
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
