import datetime
import json
import os
from .constants import STATE_INACTIVE, STATE_TRACKING, DEFAULT_TAGS, TAG_PACING

class StateManager:
    def __init__(self):
        self.current_state = STATE_INACTIVE
        self.session_start_time = datetime.datetime.now()
        self.active_work_seconds = 0
        self.last_state_change_time = datetime.datetime.now()
        self.current_note = ""
        self.current_tag = None
        # Initialize tags from JSON file or use defaults
        self.tags = self._load_tags()
        # Work status and break reason
        self.work_status = None  # 'finished' or 'break'
        self.break_reason = None

    def set_state(self, new_state, data_logger, window_monitor):
        # If trying to set the same state, do nothing
        if self.current_state == new_state:
            return
            
        # If trying to change to tracking state, check if note and tag are set
        if new_state == STATE_TRACKING:
            if not self.current_tag:
                print("Cannot start tracking without selecting a tag")
                return False
            if not self.current_note.strip():
                print("Cannot start tracking without entering a note")
                return False
            # Set work_status to 'tracking' when starting to track
            self.work_status = "tracking"
            self.break_reason = None

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
        
        return True

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
        if tag in self.tags or tag is None:
            self.current_tag = tag
            print(f"Tag set to: {self.current_tag}")
        else:
            print(f"Invalid tag: {tag}")
            
    def add_tag(self, tag):
        """Add a new tag to the list of available tags"""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            print(f"Added new tag: {tag}")
            self._save_tags()
            return True
        return False
        
    def remove_tag(self, tag):
        """Remove a tag from the list of available tags"""
        if tag == TAG_PACING:
            print(f"Cannot remove the {TAG_PACING} tag as it is required")
            return False
        
        if tag in self.tags:
            self.tags.remove(tag)
            # If the current tag is being removed, reset it
            if self.current_tag == tag:
                self.current_tag = None
            print(f"Removed tag: {tag}")
            self._save_tags()
            return True
        return False
        
    def get_tags(self):
        """Get the list of all available tags"""
        return self.tags.copy()
            
    def get_current_tag(self):
        return self.current_tag

    def set_note(self, note_text):
        self.current_note = note_text
        print(f"Note updated to: {self.current_note}")

    def get_note(self):
        return self.current_note
        
    def set_work_status(self, status, reason=None):
        """Set the work status and break reason"""
        self.work_status = status
        self.break_reason = reason
        print(f"Work status set to: {status}")
        if reason:
            print(f"Break reason: {reason}")
            
    def get_work_status(self):
        """Get the current work status"""
        return self.work_status
        
    def get_break_reason(self):
        """Get the current break reason"""
        return self.break_reason
        
    def _load_tags(self):
        """Load tags from JSON file or use defaults if file doesn't exist"""
        tags_file_path = os.path.join(os.path.dirname(__file__), "schemas", "tags.json")
        try:
            if os.path.exists(tags_file_path):
                with open(tags_file_path, 'r') as f:
                    data = json.load(f)
                    tags = data.get('tags', [])
                    
                    # Ensure Pacing tag is always included
                    if TAG_PACING not in tags:
                        tags.insert(0, TAG_PACING)
                    
                    print(f"Loaded {len(tags)} tags from {tags_file_path}")
                    return tags
        except Exception as e:
            print(f"Error loading tags from {tags_file_path}: {e}")
        
        # If file doesn't exist or there was an error, use default tags
        print(f"Using default tags")
        return DEFAULT_TAGS.copy()
    
    def _save_tags(self):
        """Save tags to JSON file"""
        tags_file_path = os.path.join(os.path.dirname(__file__), "schemas", "tags.json")
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(tags_file_path), exist_ok=True)
            
            # Save tags to file
            with open(tags_file_path, 'w') as f:
                json.dump({'tags': self.tags}, f, indent=4)
            
            print(f"Saved {len(self.tags)} tags to {tags_file_path}")
        except Exception as e:
            print(f"Error saving tags to {tags_file_path}: {e}")
