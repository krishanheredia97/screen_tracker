import os
import csv
import threading
import datetime # Added for type hinting if used, or if any datetime ops are needed directly
from .constants import LOG_FILE, UNIQUE_WINDOWS_FILE, DATETIME_FORMAT, STATE_TRACKING

class DataLogger:
    def __init__(self):
        self.log_file = LOG_FILE
        self.unique_windows_file = UNIQUE_WINDOWS_FILE
        self._initialize_log_file()
        self.lock = threading.Lock()
        self.unique_window_titles = self._load_unique_windows()

    def _initialize_log_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["datetime_start", "datetime_end", "duration_seconds", "window_title", "tag", "note", "work_status", "break_reason"])

    def _load_unique_windows(self):
        titles = set()
        if os.path.exists(self.unique_windows_file):
            with open(self.unique_windows_file, 'r', encoding='utf-8') as f:
                for line in f:
                    titles.add(line.strip())
        return titles

    def log_window_activity(self, start_time, end_time, window_title, tag, note_text="", work_status=None, break_reason=None):
        with self.lock:
            duration = (end_time - start_time).total_seconds()
            if duration < 0: duration = 0 # Should not happen, but as a safeguard
            
            start_str = start_time.strftime(DATETIME_FORMAT)
            end_str = end_time.strftime(DATETIME_FORMAT)
            
            print(f"Logging: {start_str}, {end_str}, {duration:.0f}, {window_title}, Tag: {tag}, Note: {note_text}")
            if work_status:
                print(f"Work status: {work_status}, Break reason: {break_reason if break_reason else 'N/A'}")
                
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([start_str, end_str, f"{duration:.0f}", window_title, tag, note_text, work_status or "", break_reason or ""])
                f.flush()
            
            if tag and window_title and window_title != "Unknown Window" and window_title != "Error getting active window." and window_title not in self.unique_window_titles:
                self.unique_window_titles.add(window_title)
                with open(self.unique_windows_file, 'a', encoding='utf-8') as uf:
                    uf.write(window_title + '\n')
                    uf.flush()
