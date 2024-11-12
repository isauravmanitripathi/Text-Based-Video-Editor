import sqlite3
import os
import json
from datetime import datetime

class ProjectDatabase:
    def __init__(self, project_path):
        """Initialize project database."""
        self.project_path = project_path
        self.db_file = os.path.join(project_path, "project.db")
        self.ensure_database_exists()

    def _row_to_dict(self, row):
        """Convert SQLite Row object to dictionary."""
        if row is None:
            return None
        return {key: row[key] for key in row.keys()}

    def ensure_database_exists(self):
        """Create the project database and tables if they don't exist."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()

            # Create media files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    duration REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            ''')

            # Create timeline table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timeline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER,
                    start_time REAL,
                    end_time REAL,
                    track_number INTEGER,
                    position REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (media_id) REFERENCES media_files (id) ON DELETE CASCADE
                )
            ''')

            # Create effects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS effects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timeline_id INTEGER,
                    effect_type TEXT NOT NULL,
                    parameters TEXT DEFAULT '{}',
                    start_time REAL,
                    end_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (timeline_id) REFERENCES timeline (id) ON DELETE CASCADE
                )
            ''')

            # Create project settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Insert default project settings
            default_settings = {
                'resolution': '1920x1080',
                'framerate': '30',
                'audio_sample_rate': '44100',
                'audio_channels': '2'
            }
            
            for key, value in default_settings.items():
                cursor.execute('''
                    INSERT OR IGNORE INTO project_settings (key, value)
                    VALUES (?, ?)
                ''', (key, value))

            conn.commit()

    def add_media_file(self, file_name, file_path, file_type, duration=None, metadata=None):
        """Add a media file to the project."""
        if metadata is None:
            metadata = {}

        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO media_files 
                    (file_name, file_path, file_type, duration, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (file_name, file_path, file_type, duration, json.dumps(metadata)))
                conn.commit()
                return True, "Media file added successfully", cursor.lastrowid
            except Exception as e:
                return False, f"Error adding media file: {str(e)}", None

    def get_media_files(self):
        """Get all media files in the project."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM media_files ORDER BY created_at DESC')
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_media_file_by_id(self, file_id):
        """Get a media file by its ID."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM media_files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            return self._row_to_dict(row)

    def delete_media_file(self, file_id):
        """Delete a media file from the project."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM media_files WHERE id = ?', (file_id,))
                conn.commit()
                return True, "Media file deleted successfully"
            except Exception as e:
                return False, f"Error deleting media file: {str(e)}"

    def update_media_metadata(self, file_id, metadata):
        """Update a media file's metadata."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE media_files
                    SET metadata = ?,
                        modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(metadata), file_id))
                conn.commit()
                return True, "Metadata updated successfully"
            except Exception as e:
                return False, f"Error updating metadata: {str(e)}"

    def add_timeline_item(self, media_id, start_time, end_time, track_number, position):
        """Add an item to the timeline."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO timeline 
                    (media_id, start_time, end_time, track_number, position)
                    VALUES (?, ?, ?, ?, ?)
                ''', (media_id, start_time, end_time, track_number, position))
                conn.commit()
                return True, "Timeline item added successfully", cursor.lastrowid
            except Exception as e:
                return False, f"Error adding timeline item: {str(e)}", None

    def get_timeline_items(self):
        """Get all timeline items with their associated media files."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.*, m.file_name, m.file_type, m.duration
                FROM timeline t
                JOIN media_files m ON t.media_id = m.id
                ORDER BY t.track_number, t.position
            ''')
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def delete_timeline_item(self, item_id):
        """Delete a timeline item."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM timeline WHERE id = ?', (item_id,))
                conn.commit()
                return True, "Timeline item deleted successfully"
            except Exception as e:
                return False, f"Error deleting timeline item: {str(e)}"

    def add_effect(self, timeline_id, effect_type, parameters=None, start_time=None, end_time=None):
        """Add an effect to a timeline item."""
        if parameters is None:
            parameters = {}

        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO effects 
                    (timeline_id, effect_type, parameters, start_time, end_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (timeline_id, effect_type, json.dumps(parameters), start_time, end_time))
                conn.commit()
                return True, "Effect added successfully", cursor.lastrowid
            except Exception as e:
                return False, f"Error adding effect: {str(e)}", None

    def get_effects_for_timeline_item(self, timeline_id):
        """Get all effects for a specific timeline item."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM effects
                WHERE timeline_id = ?
                ORDER BY start_time
            ''', (timeline_id,))
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def delete_effect(self, effect_id):
        """Delete an effect."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM effects WHERE id = ?', (effect_id,))
                conn.commit()
                return True, "Effect deleted successfully"
            except Exception as e:
                return False, f"Error deleting effect: {str(e)}"

    def get_project_settings(self):
        """Get all project settings."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM project_settings')
            rows = cursor.fetchall()
            settings = {}
            for row in rows:
                settings[row['key']] = row['value']
            return settings

    def update_project_setting(self, key, value):
        """Update a project setting."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO project_settings (key, value, modified_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
                conn.commit()
                return True, "Setting updated successfully"
            except Exception as e:
                return False, f"Error updating setting: {str(e)}"