import sqlite3
from datetime import datetime
import os
import json
import shutil

class DatabaseManager:
    def __init__(self, db_file="database/database.db"):
        self.db_file = db_file
        self.ensure_database_exists()

    def _row_to_dict(self, row):
        """Convert SQLite Row object to dictionary."""
        if row is None:
            return None
        return {key: row[key] for key in row.keys()}

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
            
        try:
            os.makedirs(project_path, exist_ok=True)
            
            # Create project directory structure
            os.makedirs(os.path.join(project_path, "sources"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "output"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "temp"), exist_ok=True)
            
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
                    # Clean up created directories if database insert fails
                    shutil.rmtree(project_path, ignore_errors=True)
                    return False, "A project with this name already exists", None
                
        except Exception as e:
            # Clean up if anything goes wrong
            shutil.rmtree(project_path, ignore_errors=True)
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
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

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
            row = cursor.fetchone()
            return self._row_to_dict(row)

    def get_project_by_name(self, name):
        """Get a project by its name."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    p.*,
                    COUNT(pf.id) as file_count
                FROM projects p
                LEFT JOIN project_files pf ON p.id = pf.project_id
                WHERE p.name = ?
                GROUP BY p.id
            ''', (name,))
            row = cursor.fetchone()
            return self._row_to_dict(row)

    def rename_project(self, project_id, new_name, new_path):
        """Rename a project and update its path."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE projects
                    SET name = ?, 
                        project_path = ?,
                        modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_name, new_path, project_id))
                conn.commit()
                return True, "Project renamed successfully"
            except sqlite3.IntegrityError:
                return False, "A project with this name already exists"
            except Exception as e:
                return False, f"Error renaming project: {str(e)}"

    def delete_project(self, project_id):
        """Delete a project and all its associated files."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                # Get project info before deletion
                cursor.execute('SELECT name, project_path FROM projects WHERE id = ?', (project_id,))
                project = cursor.fetchone()
                
                if not project:
                    return False, "Project not found"
                
                # Delete from database (cascade will handle project_files)
                cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
                conn.commit()
                
                # Delete project directory and all contents
                project_path = project[1]
                if os.path.exists(project_path):
                    shutil.rmtree(project_path, ignore_errors=True)
                
                return True, f"Project '{project[0]}' deleted successfully"
            except Exception as e:
                return False, f"Error deleting project: {str(e)}"

    def add_file_to_project(self, project_id, file_name, file_type, metadata=None):
        """
        Add a file to a project.
        
        Args:
            project_id (int): Project ID
            file_name (str): Name of the file
            file_type (str): Type of file (video, audio, image, etc.)
            metadata (dict, optional): Additional file metadata
            
        Returns:
            tuple: (success (bool), message (str), file_id (int))
        """
        if metadata is None:
            metadata = {}
            
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                # Get project path
                cursor.execute('SELECT project_path FROM projects WHERE id = ?', (project_id,))
                project = cursor.fetchone()
                
                if not project:
                    return False, "Project not found", None
                
                # Construct file path
                file_path = os.path.join(project[0], "sources", file_name)
                
                # Add file to database
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
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

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
                    MIN(created_at) as oldest_file,
                    MAX(modified_at) as newest_file
                FROM project_files
                WHERE project_id = ?
            ''', (project_id,))
            return self._row_to_dict(cursor.fetchone())

    def update_project_settings(self, project_id, settings):
        """Update project settings."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE projects
                    SET settings = ?,
                        modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(settings), project_id))
                conn.commit()
                return True, "Settings updated successfully"
            except Exception as e:
                return False, f"Error updating settings: {str(e)}"

    def get_project_settings(self, project_id):
        """Get project settings."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT settings FROM projects WHERE id = ?', (project_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None