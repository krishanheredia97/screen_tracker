import datetime
from .constants import STATE_INACTIVE, STATE_TRACKING, ALL_TAGS

class StateManager:
    def __init__(self):
        self.current_state = STATE_INACTIVE
        self.session_start_time = datetime.datetime.now()
        self.active_work_seconds = 0
        self.last_state_change_time = datetime.datetime.now()
        self.current_note = ""
        self.current_tag = None

    def set_state(self, new_state, data_logger, window_monitor):
        if self.current_state == new_state:
            return

        now = datetime.datetime.now()
        time_in_current_state = (now - self.last_state_change_time).total_seconds()

        if self.current_state == STATE_TRACKING:
            self.active_work_seconds += time_in_current_state
            # The window_monitor.stop_monitoring() call below will handle logging the last activity.
            window_monitor.stop_monitoring() # Stop window monitor if not in tracking state

        self.current_state = new_state
        self.last_state_change_time = now
        print(f"State changed to: {self.current_state}")

        if self.current_state == STATE_TRACKING:
            window_monitor.start_monitoring(self, data_logger)
        # No specific action for Inactive here, handled by WindowMonitor's active state check

    def get_session_timers(self):
        now = datetime.datetime.now()
        current_duration_in_state = (now - self.last_state_change_time).total_seconds()
        active_display = self.active_work_seconds

        if self.current_state == STATE_TRACKING:
            active_display += current_duration_in_state
        
        return active_display, 0  # Return 0 for pacing time as it's no longer tracked separately

    def get_current_state(self):
        return self.current_state
        
    def set_tag(self, tag):
        if tag in ALL_TAGS or tag is None:
            self.current_tag = tag
            print(f"Tag set to: {self.current_tag}")
        else:
            print(f"Invalid tag: {tag}")
            
    def get_current_tag(self):
        return self.current_tag

    def set_note(self, note_text):
        self.current_note = note_text
        print(f"Note updated to: {self.current_note}")

    def get_note(self):
        return self.current_note
