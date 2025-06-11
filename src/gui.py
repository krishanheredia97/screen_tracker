import tkinter as tk
from tkinter import ttk, font
import datetime
from .constants import STATE_INACTIVE, STATE_ACTIVE_WORK, STATE_PACING
# StateManager, DataLogger, WindowMonitor will be passed as arguments, no direct import needed here.

class SimpleGUI(tk.Tk):
    def __init__(self, state_manager, data_logger, window_monitor):
        super().__init__()
        self.state_manager = state_manager
        self.data_logger = data_logger
        self.window_monitor = window_monitor

        self.title("Window Monitor")
        self.geometry("350x300") # Increased height for note field
        self.resizable(False, False)
        # self.attributes("-topmost", True) # Optional: always on top

        self.current_state_var = tk.StringVar(value=self.state_manager.get_current_state())
        self.active_work_time_var = tk.StringVar(value="00:00:00")
        self.pacing_time_var = tk.StringVar(value="00:00:00")
        # Note: self.note_text_widget will be created in _setup_ui

        self._setup_ui()
        self.update_gui() # Initial call to start the GUI update loop
        self.protocol("WM_DELETE_WINDOW", self._on_close) # Handle window close

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # State Label
        ttk.Label(main_frame, text="Current State:").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        self.state_label = ttk.Label(main_frame, textvariable=self.current_state_var, font=font.Font(weight='bold'))
        self.state_label.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=(0,5))

        # State Buttons
        self.active_button = ttk.Button(main_frame, text=STATE_ACTIVE_WORK, command=lambda: self._change_state(STATE_ACTIVE_WORK))
        self.active_button.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=2, pady=5)

        self.pacing_button = ttk.Button(main_frame, text=STATE_PACING, command=lambda: self._change_state(STATE_PACING))
        self.pacing_button.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=2, pady=5)

        self.inactive_button = ttk.Button(main_frame, text=STATE_INACTIVE, command=lambda: self._change_state(STATE_INACTIVE))
        self.inactive_button.grid(row=1, column=2, sticky=(tk.W, tk.E), padx=2, pady=5)

        # Timers
        ttk.Label(main_frame, text="Active Work Time:").grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5,0))
        ttk.Label(main_frame, textvariable=self.active_work_time_var).grid(row=2, column=2, sticky=tk.E, pady=(5,0))

        ttk.Label(main_frame, text="Pacing Time:").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5,0))
        ttk.Label(main_frame, textvariable=self.pacing_time_var).grid(row=3, column=2, sticky=tk.E, pady=(5,0))
        
        # Note Input
        ttk.Label(main_frame, text="Note:").grid(row=4, column=0, sticky=tk.W, pady=(10,0))
        self.note_text_widget = tk.Text(main_frame, height=3, width=30)
        self.note_text_widget.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0,5))
        self.note_text_widget.insert(tk.END, self.state_manager.get_note()) # Load initial note

        # Note Buttons
        self.save_note_button = ttk.Button(main_frame, text="Save Note", command=self._save_note)
        self.save_note_button.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=2, pady=2)

        self.clear_note_button = ttk.Button(main_frame, text="Clear Note", command=self._clear_note)
        self.clear_note_button.grid(row=6, column=2, sticky=(tk.W, tk.E), padx=2, pady=2)

        # Status Bar (Optional - for messages)
        self.status_var = tk.StringVar(value="Started in Inactive state.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10,0))

        for child in main_frame.winfo_children(): 
            child.grid_configure(padx=5, pady=3)

    def _format_time(self, seconds):
        secs = int(seconds % 60)
        mins = int((seconds // 60) % 60)
        hours = int(seconds // 3600)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    def _change_state(self, new_state):
        print(f"Button clicked: Change to {new_state}")
        self.state_manager.set_state(new_state, self.data_logger, self.window_monitor)
        self.current_state_var.set(self.state_manager.get_current_state())
        self.status_var.set(f"State changed to {new_state}.")
        self._update_button_styles()

    def _update_button_styles(self):
        current_state = self.state_manager.get_current_state()
        buttons = {
            STATE_ACTIVE_WORK: self.active_button,
            STATE_PACING: self.pacing_button,
            STATE_INACTIVE: self.inactive_button
        }
        # Reset styles
        for btn_state, button in buttons.items():
            if button.winfo_exists(): # Check if widget exists
                # Using a generic style name for reset, specific for highlight
                # Default TButton style should be fine for reset
                button.configure(style="TButton") 

        # Highlight active button
        if current_state in buttons and buttons[current_state].winfo_exists():
            active_style_name = f"Active.{current_state.replace(' ', '')}.TButton"
            s = ttk.Style()
            # Configure style for the active button - e.g., different background or relief
            # Note: ttk styling can be complex. For simplicity, we might rely on default button states
            # or use a simpler visual cue if full style customization is problematic across themes.
            # For now, let's assume a style 'Active.TButton' could be defined or we use relief.
            # s.configure(active_style_name, relief=tk.SUNKEN, background="#a0e0a0") # Example
            # buttons[current_state].configure(relief=tk.SUNKEN) # Simpler highlight - REMOVED TO FIX TCLERROR
            # self.state_label.config(text=current_state) # current_state_var handles this via textvariable

    def update_gui(self):
        active_s, pacing_s = self.state_manager.get_session_timers()
        self.active_work_time_var.set(self._format_time(active_s))
        self.pacing_time_var.set(self._format_time(pacing_s))
        self.current_state_var.set(self.state_manager.get_current_state()) # Ensure state var is current
        self._update_button_styles()

        # Only update the note widget if it doesn't have focus (user isn't typing in it)
        # This prevents the text from being reset while the user is typing
        if not self.note_text_widget.focus_get() == self.note_text_widget:
            # Get the current note from the state manager
            state_manager_note = self.state_manager.get_note()
            # Get the current text from the widget, strip newlines and whitespace
            current_gui_note = self.note_text_widget.get("1.0", tk.END).strip()
            # Only update if they're different and the widget doesn't have focus
            if current_gui_note != state_manager_note:
                self.note_text_widget.delete("1.0", tk.END)
                self.note_text_widget.insert(tk.END, state_manager_note)

        self.after(1000, self.update_gui) # Update every second

    def _on_close(self):
        print("Closing application...")
        # Ensure current activity is logged before closing
        # For STATE_ACTIVE_WORK, self.window_monitor.stop_monitoring() (called later) will handle logging.
        if self.state_manager.get_current_state() == STATE_PACING:
             self.data_logger.log_window_activity(
                self.state_manager.last_state_change_time,
                datetime.datetime.now(),
                "N/A",
                STATE_PACING,
                self.state_manager.get_note()
            )
        
        if self.window_monitor.monitoring_active:
            self.window_monitor.stop_monitoring() # Ensure monitor thread is stopped
        self.destroy()

    def _save_note(self):
        note_content = self.note_text_widget.get("1.0", tk.END).strip()
        self.state_manager.set_note(note_content)
        self.status_var.set(f"Note saved.")

    def _clear_note(self):
        self.note_text_widget.delete("1.0", tk.END)
        self.state_manager.set_note("")
        self.status_var.set("Note cleared.")
