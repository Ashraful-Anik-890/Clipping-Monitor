import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PermissionManager:
    """Manages user consent and permissions"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.permission_file = config_dir / "permissions.json"
        self.permissions = self.load()
    
    def load(self) -> dict:
        """Load permissions from file"""
        try:
            if self.permission_file.exists():
                with open(self.permission_file, 'r', encoding='utf-8') as f:
                    perms = json.load(f)
                    logger.info(f"Loaded permissions: consent_given={perms.get('consent_given', False)}")
                    return perms
        except Exception as e:
            logger.error(f"Error loading permissions: {e}")
        
        # Return default permissions
        default_perms = {
            "consent_given": False,
            "consent_timestamp": None,
            "consent_version": None,
            "user_identifier": None
        }
        logger.info("Using default permissions (no consent)")
        return default_perms
    
    def save(self):
        """Save permissions to file"""
        try:
            with open(self.permission_file, 'w', encoding='utf-8') as f:
                json.dump(self.permissions, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved permissions: consent_given={self.permissions.get('consent_given', False)}")
        except Exception as e:
            logger.error(f"Error saving permissions: {e}")
    
    def request_consent(self, user_identifier: Optional[str] = None) -> bool:
        """Record user consent"""
        self.permissions["consent_given"] = True
        self.permissions["consent_timestamp"] = datetime.now().isoformat()
        self.permissions["consent_version"] = "1.0"
        self.permissions["user_identifier"] = user_identifier or "default_user"
        self.save()
        logger.info("User consent granted and saved")
        return True
    
    def has_consent(self) -> bool:
        """Check if user has given consent"""
        has_consent = self.permissions.get("consent_given", False)
        logger.debug(f"Checking consent: {has_consent}")
        return has_consent
    
    def revoke_consent(self):
        """Revoke user consent"""
        self.permissions["consent_given"] = False
        self.permissions["revocation_timestamp"] = datetime.now().isoformat()
        self.save()
        logger.info("User consent revoked")
    
    def get_consent_info(self) -> dict:
        """Get consent information"""
        return self.permissions.copy()
    
    def reset(self):
        """Reset permissions (for testing)"""
        try:
            if self.permission_file.exists():
                self.permission_file.unlink()
                logger.info("Permissions file deleted")
        except Exception as e:
            logger.error(f"Error resetting permissions: {e}")
        
        self.permissions = self.load()