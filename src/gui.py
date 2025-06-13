import tkinter as tk
from tkinter import ttk, font, simpledialog, messagebox
import datetime
from .constants import STATE_INACTIVE, STATE_TRACKING, TAG_PACING
# StateManager, DataLogger, WindowMonitor will be passed as arguments, no direct import needed here.

class SimpleGUI(tk.Tk):
    def __init__(self, state_manager, data_logger, window_monitor):
        super().__init__()
        self.state_manager = state_manager
        self.data_logger = data_logger
        self.window_monitor = window_monitor

        self.style = ttk.Style()
        # Define styles for TFrame based on color names
        self.style.configure("Green.TFrame", background="#90EE90")  # LightGreen
        self.style.configure("Yellow.TFrame", background="#FFFFE0") # LightYellow
        self.style.configure("Gray.TFrame", background="#D3D3D3")   # LightGray
        
        # Store colors for direct use (e.g., for tk.Tk root window or tk.Text)
        self.BG_COLORS = {
            "Green": "#90EE90",
            "Yellow": "#FFFFE0",
            "Gray": "#D3D3D3"
        }

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
        self.container_frame = ttk.Frame(self, padding="10")
        self.container_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create left and right frames
        self.left_frame = ttk.Frame(self.container_frame, width=400)
        self.left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.left_frame.grid_propagate(False)  # Prevent frame from shrinking to fit contents
        
        self.right_frame = ttk.Frame(self.container_frame, width=150)
        self.right_frame.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=(10, 0))
        
        # Configure weights
        self.container_frame.columnconfigure(0, weight=3)  # Left frame takes more space
        self.container_frame.columnconfigure(1, weight=1)  # Right frame takes less space
        self.container_frame.rowconfigure(0, weight=1)
        
        # Configure left frame column weights
        self.left_frame.columnconfigure(0, weight=1)
        self.left_frame.columnconfigure(1, weight=2)
        
        # Left Frame Contents
        # State Label
        ttk.Label(self.left_frame, text="Current State:").grid(row=0, column=0, sticky=tk.W, pady=(0,5), padx=(0,10))
        self.state_label = ttk.Label(self.left_frame, textvariable=self.current_state_var, font=font.Font(weight='bold'))
        self.state_label.grid(row=0, column=1, sticky=tk.W, pady=(0,5))
        
        # Current Tag Label
        ttk.Label(self.left_frame, text="Current Tag:").grid(row=1, column=0, sticky=tk.W, pady=(0,5), padx=(0,10))
        self.tag_label = ttk.Label(self.left_frame, textvariable=self.current_tag_var, font=font.Font(weight='bold'))
        self.tag_label.grid(row=1, column=1, sticky=tk.W, pady=(0,5))

        # State Toggle (Tracking/Inactive)
        toggle_frame = ttk.Frame(self.left_frame)
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
        ttk.Label(self.left_frame, text="Tracking Time:").grid(row=3, column=0, sticky=tk.W, pady=(5,0), padx=(0,10))
        ttk.Label(self.left_frame, textvariable=self.active_work_time_var).grid(row=3, column=1, sticky=tk.W, pady=(5,0))
        
        # Note Input
        ttk.Label(self.left_frame, text="Note:").grid(row=4, column=0, sticky=tk.W, pady=(10,0))
        self.note_text_widget = tk.Text(self.left_frame, height=3, width=30)
        self.note_text_widget.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,5))
        self.note_text_widget.insert(tk.END, self.state_manager.get_note()) # Load initial note
        self.note_text_widget.bind("<Control-BackSpace>", self._on_ctrl_backspace)

        # Note Buttons
        note_buttons_frame = ttk.Frame(self.left_frame)
        note_buttons_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        note_buttons_frame.columnconfigure(0, weight=1)
        note_buttons_frame.columnconfigure(1, weight=1)
        
        self.save_note_button = ttk.Button(note_buttons_frame, text="Save Note", command=self._save_note)
        self.save_note_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=2)

        self.clear_note_button = ttk.Button(note_buttons_frame, text="Clear Note", command=self._clear_note)
        self.clear_note_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=2)

        # Status Bar
        self.status_var = tk.StringVar(value="Started in Inactive state.")
        status_bar = ttk.Label(self.left_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10,0))

        # Right Frame Contents (Tags)
        # Create a frame for the Tags header and + button
        tags_header_frame = ttk.Frame(self.right_frame)
        tags_header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Add Tags label
        ttk.Label(tags_header_frame, text="Tags", font=font.Font(weight='bold')).pack(side=tk.LEFT, anchor=tk.W)
        
        # Add + button for adding new tags
        add_tag_button = ttk.Button(tags_header_frame, text="+", width=3, command=self._add_new_tag)
        add_tag_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Create a canvas with scrollbar for tags
        tag_canvas_frame = ttk.Frame(self.right_frame)
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
        
        # Add tags as buttons with delete options
        self.tag_buttons = {}
        self._refresh_tag_buttons()
            
        # Update canvas scroll region when tags frame changes size
        self.tags_frame.bind("<Configure>", self._on_frame_configure)
        self.tag_canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Apply padding to all children in self.left_frame (which uses grid)
        for child in self.left_frame.winfo_children(): 
            if isinstance(child, ttk.Frame) or isinstance(child, tk.Frame):
                continue
            if hasattr(child, 'grid_configure'):
                child.grid_configure(padx=5, pady=3)
        
        self._update_background_color() # Initial background color set

    def _on_ctrl_backspace(self, event):
        widget = event.widget
        # Get the current cursor position
        insert_index = widget.index(tk.INSERT)

        # Find the start of the word to the left of the cursor
        # We search backwards from the insert position for a space
        line_start = widget.index(f"{insert_index} linestart")
        search_end = widget.index(f"{insert_index} - 1c")

        # If we are at the start of the line, do nothing
        if insert_index == line_start:
            return "break"

        # Search for a space before the cursor
        prev_space_pos = widget.search(r'\s', search_end, backwards=True, regexp=True, stopindex=line_start)

        if prev_space_pos:
            # If a space is found, delete from there to the cursor
            delete_from = widget.index(f"{prev_space_pos} + 1c")
        else:
            # If no space is found, delete from the start of the line
            delete_from = line_start

        widget.delete(delete_from, insert_index)
        
        return "break" # Prevents the default backspace behavior

    def _format_time(self, seconds):
        secs = int(seconds % 60)
        mins = int((seconds // 60) % 60)
        hours = int(seconds // 3600)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    def _change_state(self, new_state):
        print(f"Button clicked: Change to {new_state}")
        
        # If trying to change to tracking state, check if note and tag are selected
        if new_state == STATE_TRACKING:
            current_tag = self.state_manager.get_current_tag()
            current_note = self.state_manager.get_note().strip()
            
            if not current_tag:
                messagebox.showwarning("Tag Required", "You must select a tag before starting tracking.")
                self.status_var.set("Cannot start tracking: No tag selected.")
                return
                
            if not current_note:
                messagebox.showwarning("Note Required", "You must enter a note before starting tracking.")
                self.status_var.set("Cannot start tracking: No note entered.")
                return
        
        # Try to change the state
        result = self.state_manager.set_state(new_state, self.data_logger, self.window_monitor)
        
        # Only update UI if state change was successful
        if result is not False:  # None or True is success
            self.current_state_var.set(self.state_manager.get_current_state())
            self.status_var.set(f"State changed to {new_state}.")
            self._update_button_styles()
            self._update_background_color()

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
        self._update_background_color() # Added call

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
        self._update_background_color() # Added call
        
    def _add_new_tag(self):
        """Open a dialog to add a new tag"""
        new_tag = simpledialog.askstring("Add New Tag", "Enter new tag name:")
        if new_tag and new_tag.strip():
            new_tag = new_tag.strip()
            if self.state_manager.add_tag(new_tag):
                self._refresh_tag_buttons()
                self.status_var.set(f"Added new tag: {new_tag}")
            else:
                self.status_var.set(f"Tag '{new_tag}' already exists")
                
    def _delete_tag(self, tag):
        """Delete a tag after confirmation"""
        if tag == TAG_PACING:
            messagebox.showinfo("Cannot Delete", f"The '{TAG_PACING}' tag cannot be deleted as it is required.")
            return
            
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the tag '{tag}'?")
        if confirm:
            if self.state_manager.remove_tag(tag):
                self._refresh_tag_buttons()
                self.status_var.set(f"Deleted tag: {tag}")
                
    def _refresh_tag_buttons(self):
        """Refresh the tag buttons based on current tags in state manager"""
        # Clear existing buttons
        for widget in self.tags_frame.winfo_children():
            widget.destroy()
        
        # Clear button references
        self.tag_buttons = {}
        
        # Add buttons for each tag
        for tag in self.state_manager.get_tags():
            # Create a frame for each tag to hold the button and delete button
            tag_frame = ttk.Frame(self.tags_frame)
            tag_frame.pack(fill=tk.X, padx=2, pady=2)
            
            # Add the tag button
            btn = ttk.Button(tag_frame, text=tag, command=lambda t=tag: self._select_tag(t))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.tag_buttons[tag] = btn
            
            # Add delete button
            delete_btn = ttk.Button(tag_frame, text="×", width=2, 
                                  command=lambda t=tag: self._delete_tag(t))
            delete_btn.pack(side=tk.RIGHT, padx=(2, 0))
        
        # Update the canvas scroll region
        self._on_frame_configure(None)
        
    def _on_frame_configure(self, event):
        """Update the scroll region to encompass the inner frame"""
        self.tag_canvas.configure(scrollregion=self.tag_canvas.bbox("all"))
        
    def _on_canvas_configure(self, event):
        """When the canvas changes size, resize the frame within it"""
        # Update the width of the frame to fit the canvas
        self.tag_canvas.itemconfig(self.tags_frame_window, width=event.width)

    def _update_background_color(self):
        current_state = self.state_manager.get_current_state()
        current_tag = self.state_manager.get_current_tag()

        target_color_name = "Gray"  # Default color

        if current_tag == "Pacing":
            if current_state == STATE_TRACKING:
                target_color_name = "Yellow"  # Pacing + Tracking = Yellow
            # else: Pacing + Inactive (or other state) = Gray (this is the default)
        elif current_state == STATE_TRACKING: # Not Pacing tag, but Tracking
            target_color_name = "Green"
        # else: Not Pacing tag, and Not Tracking (e.g., Inactive or other state) = Gray (this is the default)
        # Note: If current_state is STATE_INACTIVE and not Pacing, it will correctly be Gray.

        frame_style_name = f"{target_color_name}.TFrame"
        root_bg_color = self.BG_COLORS.get(target_color_name, self.BG_COLORS["Gray"])

        self.configure(background=root_bg_color)
        
        # Configure frames if they exist
        if hasattr(self, 'container_frame') and self.container_frame:
            self.container_frame.configure(style=frame_style_name)
        if hasattr(self, 'left_frame') and self.left_frame:
            self.left_frame.configure(style=frame_style_name)
        if hasattr(self, 'right_frame') and self.right_frame:
            self.right_frame.configure(style=frame_style_name)
        
        # Configure specific tk widgets that need explicit background setting
        if hasattr(self, 'note_text_widget') and self.note_text_widget:
            self.note_text_widget.configure(background=root_bg_color)
        
        if hasattr(self, 'tag_canvas') and self.tag_canvas:  # This is a tk.Canvas
            self.tag_canvas.configure(background=root_bg_color)
        if hasattr(self, 'tags_frame') and self.tags_frame:  # This is a ttk.Frame
            self.tags_frame.configure(style=frame_style_name)
