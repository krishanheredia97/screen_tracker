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
                break # Exit loop if state is no longer active work or refs are gone

            active_title_from_os = self._get_active_window_title() # This might be None for "Window Monitor"
            now = datetime.datetime.now()

            # If the active window is our GUI ("Window Monitor", which returns None),
            # effectively ignore it and continue. The current_window_title and start_time remain unchanged.
            if active_title_from_os is None:
                time.sleep(1)
                continue

            # If we are here, active_title_from_os is not our GUI.
            # It could be a trackable window, or "Unknown Window", "Error getting active window."

            if active_title_from_os != self.current_window_title:
                # A change has occurred (or it's the first valid window).
                
                # Log previous window's activity if it was a valid, trackable window.
                if self.current_window_title and \
                   self.current_window_title not in ["Unknown Window", "Error getting active window."] and \
                   self.data_logger_ref and self.state_manager_ref: # Ensure refs are valid
                    self.data_logger_ref.log_window_activity(
                        self.current_window_start_time,
                        now, # End time is current time
                        self.current_window_title,
                        STATE_ACTIVE_WORK, # Assuming this loop only runs for active work
                        self.state_manager_ref.get_note()
                    )
                
                # Now, set the new window as current.
                # If active_title_from_os is "Unknown Window" or "Error getting active window.",
                # it will become the current_window_title. These are not logged when they *start*,
                # only when a *trackable* window *ends*.
                self.current_window_title = active_title_from_os
                self.current_window_start_time = now 
            
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
            if self.thread and self.thread.is_alive(): # Check if alive before join
                self.thread.join(timeout=2)

            # Log the last active window before stopping, if it was a valid one.
            # This is the single point of logging for the final segment of a monitored window.
            if self.current_window_title and \
               self.current_window_start_time and \
               self.current_window_title not in ["Unknown Window", "Error getting active window."] and \
               self.data_logger_ref and self.state_manager_ref:
                
                # Check if the state manager confirms we were in STATE_ACTIVE_WORK.
                # This ensures logging only happens if monitoring is stopped during/from an active work session.
                if self.state_manager_ref.get_current_state() == STATE_ACTIVE_WORK:
                    log_end_time = datetime.datetime.now()
                    duration = (log_end_time - self.current_window_start_time).total_seconds()
                    
                    if duration > 0.1: # Minimum duration to log
                        self.data_logger_ref.log_window_activity(
                            self.current_window_start_time,
                            log_end_time,
                            self.current_window_title,
                            STATE_ACTIVE_WORK, # Logged as part of active work
                            self.state_manager_ref.get_note()
                        )
            
            self.current_window_title = None
            self.current_window_start_time = None
            # Per original file comments, refs are not cleared here to allow for multiple stop/start cycles.
            # self.state_manager_ref = None 
            # self.data_logger_ref = None
            print("Window monitoring stopped.")
