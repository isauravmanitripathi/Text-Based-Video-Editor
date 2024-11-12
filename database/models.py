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
            conn.commit()

    def create_project(self, name, settings=None):
        """Create a new project with its own database."""
        project_path = f"projects/{name}"
        if settings is None:
            settings = {}
            
        try:
            # Create project directory structure
            os.makedirs(project_path, exist_ok=True)
            os.makedirs(os.path.join(project_path, "sources"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "output"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "temp"), exist_ok=True)
            
            # Create project-specific database
            from database.project_db import ProjectDatabase
            project_db = ProjectDatabase(project_path)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO projects (name, project_path, settings)
                        VALUES (?, ?, ?)
                    ''', (name, project_path, json.dumps(settings)))
                    
                    project_id = cursor.lastrowid
                    conn.commit()
                    return True, "Project created successfully", project_id
                    
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
            cursor.execute('SELECT * FROM projects ORDER BY modified_at DESC')
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_project_by_id(self, project_id):
        """Get a project by its ID."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
            row = cursor.fetchone()
            return self._row_to_dict(row)

    def get_project_by_name(self, name):
        """Get a project by its name."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE name = ?', (name,))
            row = cursor.fetchone()
            return self._row_to_dict(row)

    def rename_project(self, project_id, new_name):
        """Rename a project."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                # Get current project info
                cursor.execute('SELECT project_path FROM projects WHERE id = ?', (project_id,))
                project = cursor.fetchone()
                
                if not project:
                    return False, "Project not found"
                
                old_path = project[0]
                new_path = f"projects/{new_name}"
                
                # Rename directory
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                
                # Update database
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
                # Rollback directory rename if database update fails
                if os.path.exists(new_path):
                    os.rename(new_path, old_path)
                return False, "A project with this name already exists"
                
            except Exception as e:
                return False, f"Error renaming project: {str(e)}"

    def delete_project(self, project_id):
        """Delete a project and its database."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                # Get project info before deletion
                cursor.execute('SELECT name, project_path FROM projects WHERE id = ?', (project_id,))
                project = cursor.fetchone()
                
                if not project:
                    return False, "Project not found"
                
                # Delete from main database
                cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
                conn.commit()
                
                # Delete project directory (including its database)
                project_path = project[1]
                if os.path.exists(project_path):
                    shutil.rmtree(project_path, ignore_errors=True)
                
                return True, f"Project '{project[0]}' deleted successfully"
            except Exception as e:
                return False, f"Error deleting project: {str(e)}"

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