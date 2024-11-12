import sqlite3
from datetime import datetime
import os
import json

class DatabaseManager:
    def __init__(self, db_file="database/database.db"):
        self.db_file = db_file
        self.ensure_database_exists()

    def ensure_database_exists(self):
        """Create the database and tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Create projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    project_path TEXT NOT NULL,
                    settings TEXT DEFAULT '{}'
                )
            ''')
            
            # Create project_files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()

    def create_project(self, name, settings=None):
        """
        Create a new project.
        
        Args:
            name (str): Project name
            settings (dict, optional): Project settings
            
        Returns:
            tuple: (success (bool), message (str), project_id (int))
        """
        project_path = f"projects/{name}"
        if settings is None:
            settings = {}
            
        os.makedirs(project_path, exist_ok=True)
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO projects (name, project_path, settings)
                    VALUES (?, ?, ?)
                ''', (name, project_path, json.dumps(settings)))
                conn.commit()
                return True, "Project created successfully", cursor.lastrowid
            except sqlite3.IntegrityError:
                return False, "A project with this name already exists", None
            except Exception as e:
                return False, f"Error creating project: {str(e)}", None

    def get_all_projects(self):
        """Get all projects."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    p.*,
                    COUNT(pf.id) as file_count
                FROM projects p
                LEFT JOIN project_files pf ON p.id = pf.project_id
                GROUP BY p.id
                ORDER BY p.modified_at DESC
            ''')
            return cursor.fetchall()

    def get_project_by_id(self, project_id):
        """Get a project by its ID."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    p.*,
                    COUNT(pf.id) as file_count
                FROM projects p
                LEFT JOIN project_files pf ON p.id = pf.project_id
                WHERE p.id = ?
                GROUP BY p.id
            ''', (project_id,))
            return cursor.fetchone()

    def get_project_by_name(self, name):
        """Get a project by its name."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE name = ?', (name,))
            return cursor.fetchone()

    def rename_project(self, project_id, new_name, new_path):
        """
        Rename a project.
        
        Args:
            project_id (int): Project ID
            new_name (str): New project name
            new_path (str): New project path
            
        Returns:
            tuple: (success (bool), message (str))
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE projects
                    SET name = ?, project_path = ?, modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_name, new_path, project_id))
                conn.commit()
                return True, "Project renamed successfully"
            except sqlite3.IntegrityError:
                return False, "A project with this name already exists"
            except Exception as e:
                return False, f"Error renaming project: {str(e)}"

    def delete_project(self, project_id):
        """Delete a project and all its files."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                # Get project path before deletion
                cursor.execute('SELECT project_path FROM projects WHERE id = ?', (project_id,))
                project = cursor.fetchone()
                
                if project:
                    # Delete from database (cascade will handle project_files)
                    cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
                    conn.commit()
                    
                    # Delete project directory
                    import shutil
                    shutil.rmtree(project[0], ignore_errors=True)
                    return True, "Project deleted successfully"
                return False, "Project not found"
            except Exception as e:
                return False, f"Error deleting project: {str(e)}"

    def update_project_settings(self, project_id, settings):
        """Update project settings."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE projects
                    SET settings = ?, modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(settings), project_id))
                conn.commit()
                return True, "Settings updated successfully"
            except Exception as e:
                return False, f"Error updating settings: {str(e)}"

    def add_project_file(self, project_id, file_name, file_path, file_type, metadata=None):
        """Add a file to a project."""
        if metadata is None:
            metadata = {}
            
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO project_files 
                    (project_id, file_name, file_path, file_type, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (project_id, file_name, file_path, file_type, json.dumps(metadata)))
                
                # Update project modified time
                cursor.execute('''
                    UPDATE projects
                    SET modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (project_id,))
                
                conn.commit()
                return True, "File added successfully", cursor.lastrowid
            except Exception as e:
                return False, f"Error adding file: {str(e)}", None

    def get_project_files(self, project_id):
        """Get all files in a project."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM project_files
                WHERE project_id = ?
                ORDER BY created_at DESC
            ''', (project_id,))
            return cursor.fetchall()

    def delete_project_file(self, file_id):
        """Delete a file from a project."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                # Get file info before deletion
                cursor.execute('''
                    SELECT pf.file_path, p.id
                    FROM project_files pf
                    JOIN projects p ON p.id = pf.project_id
                    WHERE pf.id = ?
                ''', (file_id,))
                file_info = cursor.fetchone()
                
                if file_info:
                    # Delete file record
                    cursor.execute('DELETE FROM project_files WHERE id = ?', (file_id,))
                    
                    # Update project modified time
                    cursor.execute('''
                        UPDATE projects
                        SET modified_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (file_info[1],))
                    
                    conn.commit()
                    
                    # Delete actual file
                    if os.path.exists(file_info[0]):
                        os.remove(file_info[0])
                    return True, "File deleted successfully"
                return False, "File not found"
            except Exception as e:
                return False, f"Error deleting file: {str(e)}"

    def update_file_metadata(self, file_id, metadata):
        """Update file metadata."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE project_files
                    SET metadata = ?, modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(metadata), file_id))
                
                # Update project modified time
                cursor.execute('''
                    UPDATE projects p
                    SET modified_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT project_id 
                        FROM project_files 
                        WHERE id = ?
                    )
                ''', (file_id,))
                
                conn.commit()
                return True, "Metadata updated successfully"
            except Exception as e:
                return False, f"Error updating metadata: {str(e)}"

    def get_project_statistics(self, project_id):
        """Get project statistics."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_files,
                    SUM(CASE WHEN file_type = 'video' THEN 1 ELSE 0 END) as video_files,
                    SUM(CASE WHEN file_type = 'audio' THEN 1 ELSE 0 END) as audio_files,
                    SUM(CASE WHEN file_type = 'image' THEN 1 ELSE 0 END) as image_files,
                    SUM(CASE WHEN file_type = 'other' THEN 1 ELSE 0 END) as other_files,
                    MIN(created_at) as oldest_file,
                    MAX(modified_at) as newest_file
                FROM project_files
                WHERE project_id = ?
            ''', (project_id,))
            return cursor.fetchone()