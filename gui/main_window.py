from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                           QLabel, QInputDialog, QMessageBox, QTableWidget,
                           QTableWidgetItem, QHeaderView, QHBoxLayout, QStyle,
                           QStyleFactory)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
import os
from datetime import datetime

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
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("Text Video Editor")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Add some spacing
        layout.addSpacing(20)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Create New Project button
        new_project_btn = QPushButton("Create New Project")
        new_project_btn.setMinimumHeight(40)
        new_project_btn.setFont(QFont("Arial", 12))
        new_project_btn.clicked.connect(self.create_new_project)
        button_layout.addWidget(new_project_btn)
        
        # Add stretch to push button to the left
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addSpacing(20)
        
        # Projects table
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(4)
        self.projects_table.setHorizontalHeaderLabels([
            "Project Name", "Created", "Last Modified", "Actions"
        ])
        
        # Set header font
        header_font = QFont("Arial", 10, QFont.Bold)
        self.projects_table.horizontalHeader().setFont(header_font)
        
        # Set column stretching
        self.projects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.projects_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.projects_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.projects_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Set alternating row colors
        self.projects_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.projects_table)
        
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
        projects = self.db_manager.get_all_projects()
        self.projects_table.setRowCount(len(projects))
        
        for row, project in enumerate(projects):
            # Project Name
            name_item = QTableWidgetItem(project['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.projects_table.setItem(row, 0, name_item)
            
            # Created Date
            created_date = datetime.fromisoformat(project['created_at'])
            created_item = QTableWidgetItem(
                created_date.strftime("%Y-%m-%d %H:%M")
            )
            created_item.setFlags(created_item.flags() & ~Qt.ItemIsEditable)
            self.projects_table.setItem(row, 1, created_item)
            
            # Modified Date
            modified_date = datetime.fromisoformat(project['modified_at'])
            modified_item = QTableWidgetItem(
                modified_date.strftime("%Y-%m-%d %H:%M")
            )
            modified_item.setFlags(modified_item.flags() & ~Qt.ItemIsEditable)
            self.projects_table.setItem(row, 2, modified_item)
            
            # Delete Button
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("deleteButton")  # For specific styling
            delete_btn.clicked.connect(
                lambda checked, pid=project['id']: self.delete_project(pid)
            )
            self.projects_table.setCellWidget(row, 3, delete_btn)

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
                    f"Project '{project['name']}' deleted successfully!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    message
                )