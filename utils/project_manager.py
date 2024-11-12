import os
import shutil
from datetime import datetime
from pathlib import Path

class ProjectManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.projects_dir = Path("projects")
        self.projects_dir.mkdir(exist_ok=True)
        
    def create_project(self, name):
        """Create a new project."""
        # Sanitize project name
        safe_name = self._sanitize_name(name)
        if not safe_name:
            return False, "Invalid project name"
            
        try:
            # Create project directory
            project_path = self.projects_dir / safe_name
            if project_path.exists():
                return False, "Project already exists"
                
            project_path.mkdir(parents=True)
            
            # Create project in database
            success = self.db_manager.create_project(safe_name)
            if not success:
                # Clean up directory if database creation failed
                shutil.rmtree(project_path)
                return False, "Failed to create project in database"
                
            # Create initial project structure
            self._create_project_structure(project_path)
            
            return True, "Project created successfully"
            
        except Exception as e:
            # Clean up on error
            if project_path.exists():
                shutil.rmtree(project_path)
            return False, f"Error creating project: {str(e)}"
            
    def _create_project_structure(self, project_path):
        """Create initial project directory structure."""
        # Create standard directories
        (project_path / "sources").mkdir()     # For source video files
        (project_path / "output").mkdir()      # For rendered output
        (project_path / "temp").mkdir()        # For temporary files
        (project_path / "scripts").mkdir()     # For editing scripts
        
        # Create project configuration file
        config = {
            "name": project_path.name,
            "created": datetime.now().isoformat(),
            "settings": {
                "default_output_format": "mp4",
                "default_resolution": "1920x1080",
                "default_fps": 30
            }
        }
        
        with open(project_path / "project.json", "w") as f:
            import json
            json.dump(config, f, indent=4)
            
    def get_project_files_count(self, project_id):
        """Count files in project directory."""
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return 0
            
        project_path = Path(project['project_path'])
        if not project_path.exists():
            return 0
            
        count = 0
        for _, _, files in os.walk(project_path):
            count += len(files)
        return count
        
    def get_project_size(self, project_id):
        """Calculate total size of project directory."""
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return 0
            
        project_path = Path(project['project_path'])
        if not project_path.exists():
            return 0
            
        total_size = 0
        for dirpath, _, filenames in os.walk(project_path):
            for f in filenames:
                fp = Path(dirpath) / f
                total_size += fp.stat().st_size
        return total_size
        
    def rename_project(self, project_id, new_name):
        """Rename a project."""
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return False, "Project not found"
            
        safe_name = self._sanitize_name(new_name)
        if not safe_name:
            return False, "Invalid project name"
            
        try:
            old_path = Path(project['project_path'])
            new_path = old_path.parent / safe_name
            
            if new_path.exists():
                return False, "A project with this name already exists"
                
            # Rename directory
            old_path.rename(new_path)
            
            # Update database
            success = self.db_manager.rename_project(project_id, safe_name, str(new_path))
            if not success:
                # Rollback directory rename if database update failed
                new_path.rename(old_path)
                return False, "Failed to update project in database"
                
            return True, "Project renamed successfully"
            
        except Exception as e:
            return False, f"Error renaming project: {str(e)}"
            
    def duplicate_project(self, project_id, new_name=None):
        """Duplicate a project."""
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return False, "Project not found"
            
        if new_name is None:
            new_name = f"{project['name']}_copy"
            
        safe_name = self._sanitize_name(new_name)
        if not safe_name:
            return False, "Invalid project name"
            
        try:
            src_path = Path(project['project_path'])
            dst_path = self.projects_dir / safe_name
            
            if dst_path.exists():
                return False, "A project with this name already exists"
                
            # Copy project directory
            shutil.copytree(src_path, dst_path)
            
            # Create new project in database
            success = self.db_manager.create_project(safe_name)
            if not success:
                # Clean up directory if database creation failed
                shutil.rmtree(dst_path)
                return False, "Failed to create project in database"
                
            return True, "Project duplicated successfully"
            
        except Exception as e:
            if dst_path.exists():
                shutil.rmtree(dst_path)
            return False, f"Error duplicating project: {str(e)}"
            
    def delete_project(self, project_id):
        """Delete a project."""
        return self.db_manager.delete_project(project_id)
        
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