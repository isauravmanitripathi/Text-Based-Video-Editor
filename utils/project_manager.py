import os
import shutil
from datetime import datetime
from pathlib import Path
import json

class ProjectManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.projects_dir = Path("projects")
        self.projects_dir.mkdir(exist_ok=True)
        
    def create_project(self, name):
        """
        Create a new project with all necessary directories and files.
        
        Args:
            name (str): Name of the project
            
        Returns:
            tuple: (success (bool), message (str), project_id (int))
        """
        # Sanitize project name
        safe_name = self._sanitize_name(name)
        if not safe_name:
            return False, "Invalid project name", None
            
        try:
            # Create project directory structure
            project_path = self.projects_dir / safe_name
            if project_path.exists():
                return False, "Project already exists", None
                
            # Create project directories
            self._create_project_structure(project_path)
            
            # Create project in database
            success, message, project_id = self.db_manager.create_project(safe_name)
            if not success:
                # Clean up directory if database creation failed
                shutil.rmtree(project_path)
                return False, message, None
                
            return True, "Project created successfully", project_id
            
        except Exception as e:
            # Clean up on error
            if project_path.exists():
                shutil.rmtree(project_path)
            return False, f"Error creating project: {str(e)}", None

    def _create_project_structure(self, project_path):
        """Create the project directory structure."""
        # Create main directories
        (project_path / "sources").mkdir(parents=True)
        (project_path / "output").mkdir(parents=True)
        (project_path / "temp").mkdir(parents=True)
        (project_path / "cache").mkdir(parents=True)
        
        # Create project configuration file
        config = {
            "name": project_path.name,
            "created": datetime.now().isoformat(),
            "settings": {
                "default_output_format": "mp4",
                "video_settings": {
                    "resolution": "1920x1080",
                    "framerate": 30,
                    "codec": "h264"
                },
                "audio_settings": {
                    "sample_rate": 44100,
                    "channels": 2,
                    "codec": "aac"
                }
            }
        }
        
        with open(project_path / "project.json", "w") as f:
            json.dump(config, f, indent=4)
            
    def get_project_size(self, project_id):
        """Calculate total size of project directory."""
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return 0, "Project not found"
            
        project_path = Path(project['project_path'])
        if not project_path.exists():
            return 0, "Project directory not found"
            
        try:
            total_size = sum(f.stat().st_size for f in project_path.rglob('*') if f.is_file())
            return total_size, None
        except Exception as e:
            return 0, f"Error calculating project size: {str(e)}"

    def get_project_file_count(self, project_id):
        """Count files in project directory."""
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return 0, "Project not found"
            
        project_path = Path(project['project_path'])
        if not project_path.exists():
            return 0, "Project directory not found"
            
        try:
            file_count = sum(1 for _ in project_path.rglob('*') if _.is_file())
            return file_count, None
        except Exception as e:
            return 0, f"Error counting files: {str(e)}"

    def export_project(self, project_id, export_path):
        """Export project to a zip file."""
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return False, "Project not found"
            
        project_path = Path(project['project_path'])
        if not project_path.exists():
            return False, "Project directory not found"
            
        try:
            # Create zip file
            zip_path = Path(export_path) / f"{project['name']}_export.zip"
            shutil.make_archive(
                str(zip_path.with_suffix('')),
                'zip',
                project_path
            )
            return True, f"Project exported to {zip_path}"
        except Exception as e:
            return False, f"Error exporting project: {str(e)}"

    def import_project(self, zip_path):
        """Import project from a zip file."""
        try:
            zip_path = Path(zip_path)
            if not zip_path.exists():
                return False, "Import file not found"
                
            # Extract project name from zip file
            project_name = zip_path.stem.replace('_export', '')
            safe_name = self._sanitize_name(project_name)
            
            # Create temporary extraction directory
            temp_dir = self.projects_dir / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Extract zip file
                shutil.unpack_archive(str(zip_path), str(temp_dir), 'zip')
                
                # Validate project structure
                if not self._validate_project_structure(temp_dir):
                    return False, "Invalid project structure"
                
                # Move to projects directory
                target_path = self.projects_dir / safe_name
                if target_path.exists():
                    return False, "Project with this name already exists"
                    
                temp_dir.rename(target_path)
                
                # Create project in database
                success, message, project_id = self.db_manager.create_project(safe_name)
                if not success:
                    shutil.rmtree(target_path)
                    return False, message
                
                return True, "Project imported successfully"
                
            finally:
                # Clean up temp directory if it still exists
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            return False, f"Error importing project: {str(e)}"

    def _validate_project_structure(self, project_path):
        """Validate project directory structure."""
        required_dirs = ['sources', 'output', 'temp']
        required_files = ['project.json']
        
        # Check required directories
        for dir_name in required_dirs:
            if not (project_path / dir_name).is_dir():
                return False
                
        # Check required files
        for file_name in required_files:
            if not (project_path / file_name).is_file():
                return False
                
        return True

    def clean_temp_files(self, project_id):
        """Clean temporary files from project."""
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return False, "Project not found"
            
        try:
            temp_dir = Path(project['project_path']) / "temp"
            cache_dir = Path(project['project_path']) / "cache"
            
            # Clean temp directory
            if temp_dir.exists():
                for item in temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                        
            # Clean cache directory
            if cache_dir.exists():
                for item in cache_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                        
            return True, "Temporary files cleaned successfully"
        except Exception as e:
            return False, f"Error cleaning temporary files: {str(e)}"

    def _sanitize_name(self, name):
        """Sanitize project name for filesystem use."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe_name = ''.join(c for c in name if c not in invalid_chars)
        
        # Remove leading/trailing spaces and dots
        safe_name = safe_name.strip('. ')
        
        # Ensure name is not empty and not too long
        if not safe_name or len(safe_name) > 255:
            return None
            
        return safe_name