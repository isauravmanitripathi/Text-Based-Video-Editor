from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                             QLabel, QHBoxLayout, QFrame, QSplitter, QFileDialog,
                             QMessageBox, QMenu, QToolBar, QStatusBar, QListWidget,
                             QListWidgetItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
import os
import shutil
from datetime import datetime

class ProjectWindow(QMainWindow):
    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data

        # Initialize project database
        from database.project_db import ProjectDatabase
        self.project_db = ProjectDatabase(project_data['project_path'])

        # Initialize data storage
        self.media_files = []
        self.timeline_items = []
        self.project_settings = {}

        self.init_ui()
        self.load_stylesheet()
        self.load_project_data()

    def load_stylesheet(self):
        """Load the QSS stylesheet."""
        style_path = "windows/project/styles/project_window.qss"
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

    def init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle(f"Project: {self.project_data['name']}")
        self.setMinimumSize(1200, 800)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create header
        self.create_header(main_layout)

        # Create toolbar
        self.create_toolbar()

        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Create media browser
        self.create_media_browser(splitter)

        # Create timeline
        self.create_timeline(splitter)

        # Set initial splitter sizes (30% for media browser, 70% for timeline)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.update_status_bar()

    def create_header(self, parent_layout):
        """Create the header section."""
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)

        # Project title
        title_label = QLabel(self.project_data['name'])
        title_label.setObjectName("projectTitle")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(title_label)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setObjectName("separator")
        header_layout.addWidget(separator)

        # Project info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(5)

        created_date = datetime.fromisoformat(self.project_data['created_at'])
        modified_date = datetime.fromisoformat(self.project_data['modified_at'])

        created_label = QLabel(f"Created: {created_date.strftime('%Y-%m-%d %H:%M')}")
        modified_label = QLabel(f"Last Modified: {modified_date.strftime('%Y-%m-%d %H:%M')}")

        for label in [created_label, modified_label]:
            label.setObjectName("infoLabel")
            info_layout.addWidget(label)

        header_layout.addWidget(info_widget)
        header_layout.addStretch()

        parent_layout.addWidget(header_widget)

    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)

        # Add Media
        add_media_action = toolbar.addAction("Add Media")
        add_media_action.setStatusTip("Add media files to the project")
        add_media_action.triggered.connect(self.add_media)

        toolbar.addSeparator()

        # Save Project
        save_action = toolbar.addAction("Save Project")
        save_action.setStatusTip("Save project changes")
        save_action.triggered.connect(self.save_project)

        # Export
        export_action = toolbar.addAction("Export")
        export_action.setStatusTip("Export project")
        export_action.triggered.connect(self.export_project)

        toolbar.addSeparator()

        # Project Settings
        settings_action = toolbar.addAction("Settings")
        settings_action.setStatusTip("Edit project settings")
        settings_action.triggered.connect(self.show_settings)

    def create_media_browser(self, parent):
        """Create the media browser panel."""
        media_widget = QWidget()
        media_widget.setObjectName("mediaBrowser")
        media_widget.setMinimumWidth(250)

        media_layout = QVBoxLayout(media_widget)
        media_layout.setContentsMargins(10, 10, 10, 10)

        # Media Browser Header
        header = QLabel("Media Files")
        header.setObjectName("sectionHeader")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        media_layout.addWidget(header)

        # Add Media Button
        add_button = QPushButton("Add Media Files")
        add_button.clicked.connect(self.add_media)
        media_layout.addWidget(add_button)

        # Media List
        self.media_list = QListWidget()
        self.media_list.setObjectName("mediaList")
        self.media_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.media_list.customContextMenuRequested.connect(self.show_media_context_menu)
        media_layout.addWidget(self.media_list)

        parent.addWidget(media_widget)

    def create_timeline(self, parent):
        """Create the timeline panel."""
        timeline_widget = QWidget()
        timeline_widget.setObjectName("timeline")
        timeline_layout = QVBoxLayout(timeline_widget)
        timeline_layout.setContentsMargins(10, 10, 10, 10)

        # Timeline Header
        header = QLabel("Timeline")
        header.setObjectName("sectionHeader")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        timeline_layout.addWidget(header)

        # Timeline Controls
        controls_layout = QHBoxLayout()

        play_button = QPushButton("Play")
        play_button.clicked.connect(self.play_timeline)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_timeline)

        controls_layout.addWidget(play_button)
        controls_layout.addWidget(stop_button)
        controls_layout.addStretch()

        timeline_layout.addLayout(controls_layout)

        # Timeline Content Area (placeholder)
        timeline_content = QWidget()
        timeline_content.setObjectName("timelineContent")
        timeline_layout.addWidget(timeline_content, 1)

        parent.addWidget(timeline_widget)

    def load_project_data(self):
        """Load project data from its database."""
        try:
            # Load project settings
            self.project_settings = self.project_db.get_project_settings()

            # Load media files
            self.media_files = self.project_db.get_media_files()
            self.update_media_list()

            # Load timeline items
            self.timeline_items = self.project_db.get_timeline_items()

            self.update_status_bar()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to load project data: {str(e)}"
            )

    def update_media_list(self):
        """Update the media files list."""
        self.media_list.clear()
        for media in self.media_files:
            item = QListWidgetItem(media['file_name'])
            item.setData(Qt.UserRole, media)
            self.media_list.addItem(item)

    def update_status_bar(self):
        """Update the status bar with project information."""
        try:
            media_count = len(self.media_files)
            timeline_count = len(self.timeline_items)
            self.statusBar.showMessage(
                f"Project: {self.project_data['name']} | "
                f"Media Files: {media_count} | "
                f"Timeline Items: {timeline_count}"
            )
        except Exception as e:
            self.statusBar.showMessage(f"Error updating status: {str(e)}")

    def add_media(self):
        """Add media files to the project."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Media Files",
            "",
            "Media Files (*.mp4 *.avi *.mov *.mp3 *.wav *.jpg *.png);;All Files (*)"
        )

        if files:
            added_count = 0
            for file_path in files:
                file_name = os.path.basename(file_path)
                file_type = self.get_file_type(file_path)

                # Copy file to project's sources directory
                destination = os.path.join(
                    self.project_data['project_path'],
                    "sources",
                    file_name
                )
                try:
                    shutil.copy2(file_path, destination)

                    # Add to database
                    success, message, _ = self.project_db.add_media_file(
                        file_name,
                        destination,
                        file_type
                    )

                    if success:
                        added_count += 1
                    else:
                        QMessageBox.warning(self, "Error", message)

                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Failed to add media file: {str(e)}"
                    )

            if added_count > 0:
                self.load_project_data()  # Refresh data
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully added {added_count} media file(s)"
                )

    def show_media_context_menu(self, position):
        """Show context menu for media items."""
        item = self.media_list.itemAt(position)
        if item is None:
            return

        menu = QMenu()
        add_to_timeline = menu.addAction("Add to Timeline")
        preview_action = menu.addAction("Preview")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec_(self.media_list.mapToGlobal(position))

        if action == add_to_timeline:
            self.add_to_timeline(item.data(Qt.UserRole))
        elif action == preview_action:
            self.preview_media(item.data(Qt.UserRole))
        elif action == delete_action:
            self.delete_media(item.data(Qt.UserRole))

    def get_file_type(self, file_path):
        """Determine the type of file based on extension."""
        ext = os.path.splitext(file_path)[1].lower()
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
        audio_extensions = {'.mp3', '.wav', '.aac', '.m4a'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif'}

        if ext in video_extensions:
            return 'video'
        elif ext in audio_extensions:
            return 'audio'
        elif ext in image_extensions:
            return 'image'
        else:
            return 'other'

    def add_to_timeline(self, media_data):
        """Add media to timeline."""
        QMessageBox.information(
            self,
            "Coming Soon",
            "Timeline functionality will be implemented soon!"
        )

    def preview_media(self, media_data):
        """Preview media file."""
        QMessageBox.information(
            self,
            "Coming Soon",
            "Media preview functionality will be implemented soon!"
        )

    def delete_media(self, media_data):
        """Delete media file from project."""
        reply = QMessageBox.question(
            self,
            "Delete Media",
            f"Are you sure you want to delete '{media_data['file_name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Delete file from disk
                if os.path.exists(media_data['file_path']):
                    os.remove(media_data['file_path'])

                # Delete from database
                success, message = self.project_db.delete_media_file(media_data['id'])
                if success:
                    self.load_project_data()  # Refresh data
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Media file '{media_data['file_name']}' deleted successfully!"
                    )
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to delete media file: {str(e)}"
                )

    def play_timeline(self):
        """Play the timeline."""
        QMessageBox.information(
            self,
            "Coming Soon",
            "Timeline playback functionality will be implemented soon!"
        )

    def stop_timeline(self):
        """Stop timeline playback."""
        pass

    def save_project(self):
        """Save project changes."""
        try:
            # Currently, all changes are saved immediately to the database
            # This method will be expanded when we add more features
            self.statusBar.showMessage("Project saved successfully", 3000)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to save project: {str(e)}"
            )

    def export_project(self):
        """Export the project."""
        QMessageBox.information(
            self,
            "Coming Soon",
            "Project export functionality will be implemented soon!"
        )

    def show_settings(self):
        """Show project settings dialog."""
        QMessageBox.information(
            self,
            "Coming Soon",
            "Project settings dialog will be implemented soon!"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        reply = QMessageBox.question(
            self,
            "Close Project",
            "Do you want to save changes before closing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )

        if reply == QMessageBox.Save:
            self.save_project()
            event.accept()
        elif reply == QMessageBox.Discard:
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event):
        """Handle window resize event."""
        super().resizeEvent(event)
        # You can add custom resize handling here if needed
        # For example, adjusting the timeline view

    def moveEvent(self, event):
        """Handle window move event."""
        super().moveEvent(event)
        # You can add custom move handling here if needed
        # For example, saving window position

    def focusInEvent(self, event):
        """Handle window focus event."""
        super().focusInEvent(event)
        # Refresh data when window gets focus
        self.load_project_data()

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop event."""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            added_count = 0
            for file_path in files:
                if os.path.isfile(file_path):
                    file_name = os.path.basename(file_path)
                    file_type = self.get_file_type(file_path)

                    # Copy file to project's sources directory
                    destination = os.path.join(
                        self.project_data['project_path'],
                        "sources",
                        file_name
                    )
                    try:
                        shutil.copy2(file_path, destination)

                        # Add to database
                        success, message, _ = self.project_db.add_media_file(
                            file_name,
                            destination,
                            file_type
                        )

                        if success:
                            added_count += 1
                        else:
                            QMessageBox.warning(self, "Error", message)

                    except Exception as e:
                        QMessageBox.warning(
                            self,
                            "Error",
                            f"Failed to add media file: {str(e)}"
                        )

            if added_count > 0:
                self.load_project_data()  # Refresh data
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully added {added_count} media file(s)"
                )
