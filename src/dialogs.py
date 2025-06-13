import tkinter as tk
from tkinter import ttk, font

class WorkStatusDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.break_reason = None
        
        # Configure dialog
        self.title("Work Status")
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)  # Dialog will be on top of the parent window
        self.grab_set()  # Make dialog modal
        
        # Center the dialog on the parent window
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"+{x}+{y}")
        
        # Create widgets
        self._setup_ui()
        
        # Wait for dialog to be closed
        self.wait_window()
    
    def _setup_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Question label
        question_label = ttk.Label(
            main_frame, 
            text="Have you finished work for the day?",
            font=font.Font(size=12, weight='bold')
        )
        question_label.pack(pady=(0, 20))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Configure grid
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        # Yes button
        yes_button = ttk.Button(
            buttons_frame,
            text="Yes, I won't work more today",
            command=self._on_yes_click
        )
        yes_button.grid(row=0, column=0, sticky=tk.W+tk.E, padx=(0, 5))
        
        # No button
        no_button = ttk.Button(
            buttons_frame,
            text="No, I'm taking a break",
            command=self._on_no_click
        )
        no_button.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(5, 0))
        
        # Set focus on the No button as it's likely the more common choice
        no_button.focus_set()
        
        # Bind Enter key to the focused button
        self.bind("<Return>", lambda event: event.widget.invoke() if isinstance(event.widget, ttk.Button) else None)
        
        # Bind Escape key to cancel
        self.bind("<Escape>", lambda event: self._on_cancel())
        
        # Handle window close button
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _on_yes_click(self):
        self.result = "finished"
        self.destroy()
    
    def _on_no_click(self):
        self.result = "break"
        self._show_break_reason_dialog()
    
    def _on_cancel(self):
        self.result = None
        self.destroy()
    
    def _show_break_reason_dialog(self):
        # Hide the current dialog temporarily
        self.withdraw()
        
        # Create and show the break reason dialog
        dialog = BreakReasonDialog(self.parent, self)
        
        # Get the result from the break reason dialog
        self.break_reason = dialog.reason
        
        # If the user canceled the break reason dialog, go back to the work status dialog
        if self.break_reason is None:
            self.deiconify()
            return
            
        # Otherwise, close this dialog too
        self.destroy()


class BreakReasonDialog(tk.Toplevel):
    def __init__(self, parent, previous_dialog=None):
        super().__init__(parent)
        self.parent = parent
        self.previous_dialog = previous_dialog
        self.reason = None
        
        # Configure dialog
        self.title("Break Reason")
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)  # Dialog will be on top of the parent window
        self.grab_set()  # Make dialog modal
        
        # Center the dialog on the parent window
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"+{x}+{y}")
        
        # Create widgets
        self._setup_ui()
        
        # Wait for dialog to be closed
        self.wait_window()
    
    def _setup_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Question label
        question_label = ttk.Label(
            main_frame, 
            text="What's the reason for your break?",
            font=font.Font(size=12, weight='bold')
        )
        question_label.pack(pady=(0, 10))
        
        # Text entry for reason
        self.reason_text = tk.Text(main_frame, height=4, width=40)
        self.reason_text.pack(fill=tk.X, pady=(0, 10))
        self.reason_text.focus_set()
        
        # Add CTRL+BACKSPACE functionality
        self.reason_text.bind("<Control-BackSpace>", self._on_ctrl_backspace)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Configure grid
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        # Cancel button
        cancel_button = ttk.Button(
            buttons_frame,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_button.grid(row=0, column=0, sticky=tk.W+tk.E, padx=(0, 5))
        
        # Submit button
        submit_button = ttk.Button(
            buttons_frame,
            text="Submit",
            command=self._on_submit
        )
        submit_button.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(5, 0))
        
        # Bind Enter key to submit
        self.bind("<Return>", lambda event: self._on_submit() if event.state == 0 else None)
        
        # Bind Escape key to cancel
        self.bind("<Escape>", lambda event: self._on_cancel())
        
        # Handle window close button
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
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
        
        return "break"  # Prevents the default backspace behavior
    
    def _on_submit(self):
        reason_text = self.reason_text.get("1.0", tk.END).strip()
        if reason_text:
            self.reason = reason_text
            self.destroy()
        else:
            # Show error if no reason provided
            tk.messagebox.showerror("Error", "Please enter a reason for your break.")
    
    def _on_cancel(self):
        self.reason = None
        self.destroy()
