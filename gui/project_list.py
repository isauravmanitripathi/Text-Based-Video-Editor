from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QLabel, QMenu, QAction, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime

class ProjectListWidget(QWidget):
    projectSelected = pyqtSignal(dict)  # Signal emitted when project is selected
    projectDeleted = pyqtSignal(int)    # Signal emitted when project is deleted
    
    def __init__(self, project_manager):
        super().__init__()
        self.project_manager = project_manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Projects count label
        self.projects_count_label = QLabel("Projects: 0")
        self.projects_count_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(self.projects_count_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_projects)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Projects table
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(5)
        self.projects_table.setHorizontalHeaderLabels([
            "Project Name",
            "Created",
            "Last Modified",
            "Files",
            "Actions"
        ])
        
        # Set header font and style
        header_font = QFont("Arial", 10, QFont.Bold)
        self.projects_table.horizontalHeader().setFont(header_font)
        
        # Set column stretching
        self.projects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.projects_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.projects_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.projects_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.projects_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # Enable sorting
        self.projects_table.setSortingEnabled(True)
        
        # Enable context menu
        self.projects_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.projects_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Connect double-click signal
        self.projects_table.cellDoubleClicked.connect(self.on_project_double_clicked)
        
        layout.addWidget(self.projects_table)
        
        # Initial load
        self.refresh_projects()
        
    def refresh_projects(self):
        """Refresh the projects list."""
        projects = self.project_manager.get_all_projects()
        self.projects_count_label.setText(f"Projects: {len(projects)}")
        
        self.projects_table.setSortingEnabled(False)  # Disable sorting while updating
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
            
            # Files Count
            files_count = self.project_manager.get_project_files_count(project['id'])
            files_item = QTableWidgetItem(str(files_count))
            files_item.setFlags(files_item.flags() & ~Qt.ItemIsEditable)
            self.projects_table.setItem(row, 3, files_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            
            # Open button
            open_btn = QPushButton("Open")
            open_btn.clicked.connect(
                lambda checked, p=project: self.projectSelected.emit(p)
            )
            actions_layout.addWidget(open_btn)
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("deleteButton")
            delete_btn.clicked.connect(
                lambda checked, pid=project['id']: self.delete_project(pid)
            )
            actions_layout.addWidget(delete_btn)
            
            self.projects_table.setCellWidget(row, 4, actions_widget)
        
        self.projects_table.setSortingEnabled(True)  # Re-enable sorting
        
    def delete_project(self, project_id):
        """Delete a project after confirmation."""
        project = self.project_manager.get_project_by_id(project_id)
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
            if self.project_manager.delete_project(project_id):
                self.refresh_projects()
                self.projectDeleted.emit(project_id)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Project '{project['name']}' deleted successfully!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to delete project '{project['name']}'!"
                )
                
    def show_context_menu(self, position):
        """Show context menu for right-clicked project."""
        menu = QMenu()
        
        # Get the row that was clicked
        row = self.projects_table.rowAt(position.y())
        if row >= 0:
            open_action = menu.addAction("Open Project")
            rename_action = menu.addAction("Rename Project")
            duplicate_action = menu.addAction("Duplicate Project")
            menu.addSeparator()
            delete_action = menu.addAction("Delete Project")
            
            # Show menu and get selected action
            action = menu.exec_(self.projects_table.viewport().mapToGlobal(position))
            
            if action:
                project_name = self.projects_table.item(row, 0).text()
                project = self.project_manager.get_project_by_name(project_name)
                
                if action == open_action:
                    self.projectSelected.emit(project)
                elif action == rename_action:
                    self.rename_project(project)
                elif action == duplicate_action:
                    self.duplicate_project(project)
                elif action == delete_action:
                    self.delete_project(project['id'])
                    
    def on_project_double_clicked(self, row, column):
        """Handle double-click on project row."""
        project_name = self.projects_table.item(row, 0).text()
        project = self.project_manager.get_project_by_name(project_name)
        if project:
            self.projectSelected.emit(project)