import datetime
from .constants import STATE_INACTIVE, STATE_ACTIVE_WORK, STATE_PACING

class StateManager:
    def __init__(self):
        self.current_state = STATE_INACTIVE
        self.session_start_time = datetime.datetime.now()
        self.active_work_seconds = 0
        self.pacing_seconds = 0
        self.last_state_change_time = datetime.datetime.now()
        self.current_note = ""

    def set_state(self, new_state, data_logger, window_monitor):
        if self.current_state == new_state:
            return

        now = datetime.datetime.now()
        time_in_current_state = (now - self.last_state_change_time).total_seconds()

        if self.current_state == STATE_ACTIVE_WORK:
            self.active_work_seconds += time_in_current_state
            # The window_monitor.stop_monitoring() call below will handle logging the last activity.
            window_monitor.stop_monitoring() # Stop window monitor if not in active work
        elif self.current_state == STATE_PACING:
            self.pacing_seconds += time_in_current_state
            # Log pacing block
            data_logger.log_window_activity(
                self.last_state_change_time, 
                now, 
                "N/A", 
                self.current_state,
                self.current_note
            )

        self.current_state = new_state
        self.last_state_change_time = now
        print(f"State changed to: {self.current_state}")

        if self.current_state == STATE_ACTIVE_WORK:
            window_monitor.start_monitoring(self, data_logger)
        # No specific action for Pacing or Inactive here, handled by WindowMonitor's active state check

    def get_session_timers(self):
        now = datetime.datetime.now()
        current_duration_in_state = (now - self.last_state_change_time).total_seconds()
        active_display = self.active_work_seconds
        pacing_display = self.pacing_seconds

        if self.current_state == STATE_ACTIVE_WORK:
            active_display += current_duration_in_state
        elif self.current_state == STATE_PACING:
            pacing_display += current_duration_in_state
        
        return active_display, pacing_display

    def get_current_state(self):
        return self.current_state

    def set_note(self, note_text):
        self.current_note = note_text
        print(f"Note updated to: {self.current_note}")

    def get_note(self):
        return self.current_note
