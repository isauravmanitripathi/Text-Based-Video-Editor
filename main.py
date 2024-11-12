import sys
from PyQt5.QtWidgets import QApplication
from database.models import DatabaseManager
from gui.main_window import MainWindow
from PyQt5.QtCore import Qt

def setup_application():
    """Setup the main application with proper settings."""
    app = QApplication(sys.argv)
    
    # Enable High DPI support
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Set application information
    app.setApplicationName("Text Video Editor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Your Organization")
    app.setOrganizationDomain("yourorganization.com")
    
    return app

def setup_database():
    """Initialize the database manager."""
    try:
        db_manager = DatabaseManager()
        return db_manager
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        sys.exit(1)

def main():
    # Create and setup application
    app = setup_application()
    
    # Initialize database
    db_manager = setup_database()
    
    try:
        # Create and show main window
        window = MainWindow(db_manager)
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()