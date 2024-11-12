import sys
from PyQt5.QtWidgets import QApplication
from database.models import DatabaseManager
from gui.main_window import MainWindow

def main():
    # Create application
    app = QApplication(sys.argv)
    
    # Initialize database
    db_manager = DatabaseManager()
    
    # Create and show main window
    window = MainWindow(db_manager)
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()