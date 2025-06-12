import tkinter as tk
from tkinter import ttk, font
import datetime
from .constants import STATE_INACTIVE, STATE_TRACKING, ALL_TAGS
# StateManager, DataLogger, WindowMonitor will be passed as arguments, no direct import needed here.

class SimpleGUI(tk.Tk):
    def __init__(self, state_manager, data_logger, window_monitor):
        super().__init__()
        self.state_manager = state_manager
        self.data_logger = data_logger
        self.window_monitor = window_monitor

        self.title("Window Monitor")
        self.geometry("600x400") # Increased width and height for better text display
        self.resizable(True, True)
        # self.attributes("-topmost", True) # Optional: always on top

        self.current_state_var = tk.StringVar(value=self.state_manager.get_current_state())
        self.active_work_time_var = tk.StringVar(value="00:00:00")
        self.current_tag_var = tk.StringVar(value="No Tag Selected")
        # Note: self.note_text_widget will be created in _setup_ui

        self._setup_ui()
        self.update_gui() # Initial call to start the GUI update loop
        self.protocol("WM_DELETE_WINDOW", self._on_close) # Handle window close

    def _setup_ui(self):
        # Create a main container frame
        container_frame = ttk.Frame(self, padding="10")
        container_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create left and right frames
        left_frame = ttk.Frame(container_frame, width=400)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_frame.grid_propagate(False)  # Prevent frame from shrinking to fit contents
        
        right_frame = ttk.Frame(container_frame, width=150)
        right_frame.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=(10, 0))
        
        # Configure weights
        container_frame.columnconfigure(0, weight=3)  # Left frame takes more space
        container_frame.columnconfigure(1, weight=1)  # Right frame takes less space
        container_frame.rowconfigure(0, weight=1)
        
        # Configure left frame column weights
        left_frame.columnconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=2)
        
        # Left Frame Contents
        # State Label
        ttk.Label(left_frame, text="Current State:").grid(row=0, column=0, sticky=tk.W, pady=(0,5), padx=(0,10))
        self.state_label = ttk.Label(left_frame, textvariable=self.current_state_var, font=font.Font(weight='bold'))
        self.state_label.grid(row=0, column=1, sticky=tk.W, pady=(0,5))
        
        # Current Tag Label
        ttk.Label(left_frame, text="Current Tag:").grid(row=1, column=0, sticky=tk.W, pady=(0,5), padx=(0,10))
        self.tag_label = ttk.Label(left_frame, textvariable=self.current_tag_var, font=font.Font(weight='bold'))
        self.tag_label.grid(row=1, column=1, sticky=tk.W, pady=(0,5))

        # State Toggle (Tracking/Inactive)
        toggle_frame = ttk.Frame(left_frame)
        toggle_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        toggle_frame.columnconfigure(0, weight=1)
        toggle_frame.columnconfigure(1, weight=1)
        
        self.tracking_button = ttk.Button(toggle_frame, text=STATE_TRACKING, 
                                        command=lambda: self._change_state(STATE_TRACKING))
        self.tracking_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=2)
        
        self.inactive_button = ttk.Button(toggle_frame, text=STATE_INACTIVE, 
                                         command=lambda: self._change_state(STATE_INACTIVE))
        self.inactive_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=2)

        # Timer
        ttk.Label(left_frame, text="Tracking Time:").grid(row=3, column=0, sticky=tk.W, pady=(5,0), padx=(0,10))
        ttk.Label(left_frame, textvariable=self.active_work_time_var).grid(row=3, column=1, sticky=tk.W, pady=(5,0))
        
        # Note Input
        ttk.Label(left_frame, text="Note:").grid(row=4, column=0, sticky=tk.W, pady=(10,0))
        self.note_text_widget = tk.Text(left_frame, height=3, width=30)
        self.note_text_widget.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,5))
        self.note_text_widget.insert(tk.END, self.state_manager.get_note()) # Load initial note

        # Note Buttons
        note_buttons_frame = ttk.Frame(left_frame)
        note_buttons_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        note_buttons_frame.columnconfigure(0, weight=1)
        note_buttons_frame.columnconfigure(1, weight=1)
        
        self.save_note_button = ttk.Button(note_buttons_frame, text="Save Note", command=self._save_note)
        self.save_note_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=2)

        self.clear_note_button = ttk.Button(note_buttons_frame, text="Clear Note", command=self._clear_note)
        self.clear_note_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=2)

        # Status Bar
        self.status_var = tk.StringVar(value="Started in Inactive state.")
        status_bar = ttk.Label(left_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10,0))

        # Right Frame Contents (Tags)
        ttk.Label(right_frame, text="Tags", font=font.Font(weight='bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # Create a canvas with scrollbar for tags
        tag_canvas_frame = ttk.Frame(right_frame)
        tag_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar to the frame
        scrollbar = ttk.Scrollbar(tag_canvas_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas
        self.tag_canvas = tk.Canvas(tag_canvas_frame, yscrollcommand=scrollbar.set)
        self.tag_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=self.tag_canvas.yview)
        
        # Create frame for tags inside canvas
        self.tags_frame = ttk.Frame(self.tag_canvas)
        self.tags_frame_window = self.tag_canvas.create_window((0, 0), window=self.tags_frame, anchor=tk.NW)
        
        # Add tags as buttons
        self.tag_buttons = {}
        for i, tag in enumerate(ALL_TAGS):
            btn = ttk.Button(self.tags_frame, text=tag, command=lambda t=tag: self._select_tag(t))
            btn.pack(fill=tk.X, padx=2, pady=2)
            self.tag_buttons[tag] = btn
            
        # Update canvas scroll region when tags frame changes size
        self.tags_frame.bind("<Configure>", self._on_frame_configure)
        self.tag_canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Apply padding to all children in left_frame (which uses grid)
        for child in left_frame.winfo_children(): 
            if isinstance(child, ttk.Frame) or isinstance(child, tk.Frame):
                continue
            if hasattr(child, 'grid_configure'):
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
            STATE_TRACKING: self.tracking_button,
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
            
        # Update tag buttons
        current_tag = self.state_manager.get_current_tag()
        for tag, button in self.tag_buttons.items():
            if button.winfo_exists():
                button.configure(style="TButton")
                
        if current_tag in self.tag_buttons and self.tag_buttons[current_tag].winfo_exists():
            # Highlight the selected tag button
            self.tag_buttons[current_tag].configure(style="TButton")

    def update_gui(self):
        active_s, _ = self.state_manager.get_session_timers()
        self.active_work_time_var.set(self._format_time(active_s))
        self.current_state_var.set(self.state_manager.get_current_state()) # Ensure state var is current
        
        # Update current tag display
        current_tag = self.state_manager.get_current_tag()
        self.current_tag_var.set(current_tag if current_tag else "No Tag Selected")
        
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
        # For STATE_TRACKING, self.window_monitor.stop_monitoring() (called later) will handle logging.
        
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
        
    def _select_tag(self, tag):
        """Handle tag selection"""
        self.state_manager.set_tag(tag)
        self.current_tag_var.set(tag)
        self.status_var.set(f"Tag set to: {tag}")
        self._update_button_styles()
        
    def _on_frame_configure(self, event):
        """Update the scroll region to encompass the inner frame"""
        self.tag_canvas.configure(scrollregion=self.tag_canvas.bbox("all"))
        
    def _on_canvas_configure(self, event):
        """When the canvas changes size, resize the frame within it"""
        # Update the width of the frame to fit the canvas
        self.tag_canvas.itemconfig(self.tags_frame_window, width=event.width)
