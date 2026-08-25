"""
Configuration management
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager"""
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.config = {}
        self.panelbox = {}
        self.dropdown_options = {}
        self.access = {}
        self.load_all()
    
    def load_all(self):
        """Load all configuration files"""
        self.config = self.load_json('config.json')
        self.panelbox = self.load_json('panelbox.json')
        self.dropdown_options = self.load_json('dropdownoption.json')
        self.access = self.load_json('access.json')
        self.validate_all()
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON file with error handling"""
        file_path = self.config_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {filename}")
            raise FileNotFoundError(f"Configuration file not found: {filename}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            raise ValueError(f"Invalid JSON in {filename}: {e}")
    
    def validate_all(self):
        """Validate all configuration files"""
        self.validate_config()
        self.validate_panelbox()
        self.validate_dropdown_options()
        self.validate_access()
        logger.info("All configuration files validated successfully")
    
    def validate_config(self):
        """Validate config.json"""
        required_fields = ['prefix', 'guild_id', 'database']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required field '{field}' in config.json")
        
        if 'type' not in self.config['database']:
            raise ValueError("Missing 'type' field in database config")
        
        if self.config['database']['type'] not in ['sqlite', 'mongodb']:
            raise ValueError("Database type must be 'sqlite' or 'mongodb'")
    
    def validate_panelbox(self):
        """Validate panelbox.json"""
        required_fields = ['title', 'description', 'color', 'dropdown']
        for field in required_fields:
            if field not in self.panelbox:
                raise ValueError(f"Missing required field '{field}' in panelbox.json")
        
        if 'placeholder' not in self.panelbox['dropdown']:
            raise ValueError("Missing 'placeholder' in dropdown config")
    
    def validate_dropdown_options(self):
        """Validate dropdownoption.json"""
        if 'options' not in self.dropdown_options:
            raise ValueError("Missing 'options' field in dropdownoption.json")
        
        if not self.dropdown_options['options']:
            raise ValueError("No ticket options defined in dropdownoption.json")
        
        seen_ids = set()
        for option in self.dropdown_options['options']:
            if 'id' not in option:
                raise ValueError("Each option must have an 'id' field")
            if option['id'] in seen_ids:
                raise ValueError(f"Duplicate option ID found: {option['id']}")
            seen_ids.add(option['id'])
            
            required = ['name', 'description', 'category_id']
            for field in required:
                if field not in option:
                    raise ValueError(f"Missing required field '{field}' in option {option['id']}")
    
    def validate_access(self):
        """Validate access.json"""
        if 'ticket_admin_role' not in self.access:
            raise ValueError("Missing 'ticket_admin_role' field in access.json")
        
        if 'support_roles' not in self.access:
            self.access['support_roles'] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def get_prefix(self) -> str:
        """Get command prefix"""
        return self.config.get('prefix', '!')
    
    def get_database_type(self) -> str:
        """Get database type"""
        return self.config.get('database', {}).get('type', 'sqlite')
    
    def get_guild_id(self) -> int:
        """Get guild ID"""
        try:
            return int(self.config.get('guild_id', 0))
        except (ValueError, TypeError):
            logger.error("Invalid guild_id in config.json")
            return 0
    
    def get_ticket_options(self) -> List[Dict[str, Any]]:
        """Get ticket options"""
        return self.dropdown_options.get('options', [])
    
    def get_option_by_id(self, option_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket option by ID"""
        for option in self.get_ticket_options():
            if option['id'] == option_id:
                return option
        return None
    
    def get_panelbox(self) -> Dict[str, Any]:
        """Get panelbox config"""
        return self.panelbox
    
    def get_access(self) -> Dict[str, Any]:
        """Get access config"""
        return self.access
    
    def get_ticket_admin_role(self) -> int:
        """Get ticket admin role ID"""
        try:
            return int(self.access.get('ticket_admin_role', 0))
        except (ValueError, TypeError):
            return 0
    
    def get_support_roles_for_option(self, option_id: int) -> List[int]:
        """Get support roles for specific option"""
        roles = []
        support_roles = self.access.get('support_roles', {})
        for role_id, options in support_roles.items():
            if option_id in options:
                try:
                    roles.append(int(role_id))
                except (ValueError, TypeError):
                    continue
        return roles
    
    def get_log_channel(self, log_type: str) -> Optional[int]:
        """Get log channel ID"""
        channel_id = self.config.get('logs', {}).get(log_type)
        if channel_id:
            try:
                return int(channel_id)
            except (ValueError, TypeError):
                return None
        return None
    
    def reload(self):
        """Reload all configuration files"""
        self.load_all()
