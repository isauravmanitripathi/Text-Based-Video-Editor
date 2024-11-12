from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                           QLabel, QInputDialog, QMessageBox, QHBoxLayout,
                           QScrollArea, QFrame, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QColor
import os
from datetime import datetime

class ProjectCard(QFrame):
    def __init__(self, project, on_delete):
        super().__init__()
        self.project = project  # Now this is a dictionary
        self.on_delete = on_delete
        self.init_ui()
        
    def init_ui(self):
        self.setObjectName("projectCard")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Project name
        name_label = QLabel(self.project['name'])
        name_label.setObjectName("projectName")
        name_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(name_label)
        
        # Project info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # Created date
        created_date = datetime.fromisoformat(self.project['created_at'])
        created_label = QLabel(f"Created: {created_date.strftime('%Y-%m-%d %H:%M')}")
        created_label.setObjectName("projectInfo")
        
        # Modified date
        modified_date = datetime.fromisoformat(self.project['modified_at'])
        modified_label = QLabel(f"Modified: {modified_date.strftime('%Y-%m-%d %H:%M')}")
        modified_label.setObjectName("projectInfo")
        
        # File count
        file_count = self.project.get('file_count', 0)
        files_label = QLabel(f"Files: {file_count}")
        files_label.setObjectName("projectInfo")
        
        info_layout.addWidget(created_label)
        info_layout.addWidget(modified_label)
        info_layout.addWidget(files_label)
        layout.addLayout(info_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open Project")
        open_btn.setObjectName("openButton")
        
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(lambda: self.on_delete(self.project['id']))
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(delete_btn)
        
        layout.addStretch()
        layout.addLayout(button_layout)

class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
        self.load_stylesheet()

    def load_stylesheet(self):
        """Load the QSS stylesheet."""
        style_path = "gui/styles/dark_theme.qss"
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

    def init_ui(self):
        self.setWindowTitle("Text Video Editor")
        self.setMinimumSize(1000, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_layout = QHBoxLayout(header_widget)
        
        # Title
        title_label = QLabel("Text Video Editor")
        title_label.setObjectName("appTitle")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        header_layout.addWidget(title_label)
        
        # Create New Project button
        new_project_btn = QPushButton("New Project")
        new_project_btn.setObjectName("newProjectButton")
        new_project_btn.setMinimumSize(150, 40)
        new_project_btn.setFont(QFont("Arial", 12))
        new_project_btn.clicked.connect(self.create_new_project)
        header_layout.addWidget(new_project_btn, alignment=Qt.AlignRight)
        
        main_layout.addWidget(header_widget)
        
        # Projects section title
        projects_title = QLabel("Your Projects")
        projects_title.setObjectName("sectionTitle")
        projects_title.setFont(QFont("Arial", 18))
        main_layout.addWidget(projects_title)
        
        # Create scroll area for projects
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("projectsScrollArea")
        
        # Container for project cards
        self.projects_container = QWidget()
        self.projects_layout = QGridLayout(self.projects_container)
        self.projects_layout.setSpacing(20)
        self.projects_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(self.projects_container)
        main_layout.addWidget(scroll_area)
        
        # Load projects
        self.load_projects()
        
        # Set up auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_projects)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def create_new_project(self):
        name, ok = QInputDialog.getText(
            self, 
            "Create New Project",
            "Enter project name:"
        )
        
        if ok and name:
            # Validate project name
            if not name.strip():
                QMessageBox.warning(
                    self,
                    "Invalid Name",
                    "Project name cannot be empty!"
                )
                return
                
            success, message, project_id = self.db_manager.create_project(name)
            if success:
                self.load_projects()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Project '{name}' created successfully!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    message
                )

    def load_projects(self):
        # Clear existing projects
        while self.projects_layout.count():
            child = self.projects_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        projects = self.db_manager.get_all_projects()
        
        if not projects:  # If no projects, show a message
            no_projects_label = QLabel("No projects yet. Click 'New Project' to create one!")
            no_projects_label.setObjectName("noProjectsLabel")
            no_projects_label.setAlignment(Qt.AlignCenter)
            self.projects_layout.addWidget(no_projects_label, 0, 0)
            return
        
        # Add project cards to grid
        row = 0
        col = 0
        max_cols = 3  # Number of cards per row
        
        for project in projects:
            card = ProjectCard(project, self.delete_project)
            self.projects_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        # Add stretch to fill empty space
        if projects:
            self.projects_layout.setRowStretch(row + 1, 1)

    def delete_project(self, project_id):
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            QMessageBox.warning(self, "Error", "Project not found!")
            return
            
        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"Are you sure you want to delete the project '{project['name']}'?\n"
            "This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.db_manager.delete_project(project_id)
            if success:
                self.load_projects()
                QMessageBox.information(
                    self,
                    "Success",
                    message
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    message
                )