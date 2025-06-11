from src.state_manager import StateManager
from src.data_logger import DataLogger
from src.window_monitor import WindowMonitor
from src.gui import SimpleGUI

def main():
    state_manager = StateManager()
    data_logger = DataLogger()
    window_monitor = WindowMonitor()
    
    app = SimpleGUI(state_manager, data_logger, window_monitor)
    app.mainloop()

if __name__ == "__main__":
    main()
