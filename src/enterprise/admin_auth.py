"""
Admin Authentication Manager

Secure authentication and authorization for admin console access.

Features:
- Secure password hashing with PBKDF2
- Admin privilege verification
- UAC elevation support
- Session management
- Password reset functionality
"""

import hashlib
import secrets
import json
from pathlib import Path
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

try:
    import win32security
    import win32api
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    logging.warning("Windows modules not available - some features will be limited")

logger = logging.getLogger(__name__)


class AdminAuthManager:
    """
    Secure admin authentication and authorization manager.
    
    Features:
    - PBKDF2 password hashing
    - Encrypted credential storage
    - UAC elevation detection
    - Password reset tokens
    - Session management
    """
    
    # Security parameters
    HASH_ITERATIONS = 100000  # PBKDF2 iterations
    SALT_LENGTH = 32  # bytes
    SESSION_TIMEOUT_MINUTES = 30
    
    def __init__(self, config_dir: Path):
        """
        Initialize admin authentication manager.
        
        Args:
            config_dir: Directory for storing credentials
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.auth_file = self.config_dir / '.admin_credentials'
        self.session_file = self.config_dir / '.admin_session'
        
        # Initialize encryption
        self.cipher = self._init_encryption()
        
        # Initialize admin credentials if not exists
        if not self.auth_file.exists():
            self._create_default_admin()
        
        logger.info("Admin authentication manager initialized")
    
    def _init_encryption(self) -> Fernet:
        """
        Initialize or load encryption key for credentials.
        
        Returns:
            Fernet cipher instance
        """
        key_file = self.config_dir / '.auth_key'
        
        try:
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
                logger.info("Loaded existing auth encryption key")
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                
                # Hide key file on Windows
                if WINDOWS_AVAILABLE:
                    try:
                        win32api.SetFileAttributes(
                            str(key_file),
                            win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM
                        )
                    except Exception as e:
                        logger.warning(f"Could not hide key file: {e}")
                
                logger.info("Generated new auth encryption key")
            
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Error initializing auth encryption: {e}")
            raise
    
    def _create_default_admin(self):
        """Create default admin credentials with random password"""
        # Generate strong random password
        initial_password = secrets.token_urlsafe(16)
        
        # Store encrypted credentials
        self.set_admin_password(initial_password)
        
        # Write initial password to setup file (one-time)
        setup_file = self.config_dir / 'ADMIN_INITIAL_PASSWORD.txt'
        setup_file.write_text(
            f"ENTERPRISE MONITORING AGENT - INITIAL ADMIN PASSWORD\n"
            f"{'='*60}\n\n"
            f"IMPORTANT: Change this password immediately after first login!\n\n"
            f"Initial Password: {initial_password}\n\n"
            f"This file will be deleted after first successful login.\n"
            f"{'='*60}\n"
        )
        
        logger.info("Created default admin credentials")
    
    def _hash_password(self, password: str, salt: bytes = None) -> tuple:
        """
        Hash password using PBKDF2 with SHA-256.
        
        Args:
            password: Plain text password
            salt: Optional salt (generates new if not provided)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(self.SALT_LENGTH)
        
        # Use PBKDF2 with SHA-256
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            self.HASH_ITERATIONS
        )
        
        return hashed, salt
    
    def set_admin_password(self, password: str, username: str = "admin") -> bool:
        """
        Set admin password.
        
        Args:
            password: New password
            username: Admin username
            
        Returns:
            True if successful
        """
        try:
            # Validate password strength
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters")
            
            # Hash password
            hashed, salt = self._hash_password(password)
            
            # Prepare credentials
            credentials = {
                'username': username,
                'password_hash': hashed.hex(),
                'salt': salt.hex(),
                'created_at': datetime.now().isoformat(),
                'last_changed': datetime.now().isoformat(),
                'hash_algorithm': 'pbkdf2_sha256',
                'iterations': self.HASH_ITERATIONS
            }
            
            # Encrypt and save
            encrypted = self.cipher.encrypt(json.dumps(credentials).encode('utf-8'))
            self.auth_file.write_bytes(encrypted)
            
            # Hide credentials file on Windows
            if WINDOWS_AVAILABLE:
                try:
                    win32api.SetFileAttributes(
                        str(self.auth_file),
                        win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM
                    )
                except Exception as e:
                    logger.warning(f"Could not hide credentials file: {e}")
            
            logger.info(f"Admin password set for user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting admin password: {e}")
            return False
    
    def verify_admin_password(self, password: str, username: str = "admin") -> bool:
        """
        Verify admin password.
        
        Args:
            password: Password to verify
            username: Admin username
            
        Returns:
            True if password is correct
        """
        try:
            if not self.auth_file.exists():
                logger.warning("No credentials file found")
                return False
            
            # Decrypt credentials
            encrypted = self.auth_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            credentials = json.loads(decrypted)
            
            # Verify username
            if credentials.get('username') != username:
                logger.warning(f"Invalid username: {username}")
                return False
            
            # Hash input password with stored salt
            salt = bytes.fromhex(credentials['salt'])
            hashed, _ = self._hash_password(password, salt)
            
            # Compare hashes (constant-time comparison)
            stored_hash = credentials['password_hash']
            is_valid = secrets.compare_digest(hashed.hex(), stored_hash)
            
            if is_valid:
                logger.info(f"Successful authentication for user: {username}")
                
                # Delete initial password file after first successful login
                initial_pass_file = self.config_dir / 'ADMIN_INITIAL_PASSWORD.txt'
                if initial_pass_file.exists():
                    try:
                        initial_pass_file.unlink()
                        logger.info("Deleted initial password file")
                    except Exception as e:
                        logger.warning(f"Could not delete initial password file: {e}")
                
                # Create session
                self._create_session(username)
            else:
                logger.warning(f"Failed authentication attempt for user: {username}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def _create_session(self, username: str):
        """
        Create admin session.
        
        Args:
            username: Username for session
        """
        try:
            session = {
                'username': username,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)).isoformat(),
                'session_id': secrets.token_urlsafe(32)
            }
            
            encrypted = self.cipher.encrypt(json.dumps(session).encode('utf-8'))
            self.session_file.write_bytes(encrypted)
            
            logger.info(f"Created session for user: {username}")
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
    
    def verify_session(self) -> bool:
        """
        Verify active admin session.
        
        Returns:
            True if valid session exists
        """
        try:
            if not self.session_file.exists():
                return False
            
            # Decrypt session
            encrypted = self.session_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            session = json.loads(decrypted)
            
            # Check expiration
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now() > expires_at:
                logger.info("Session expired")
                self.session_file.unlink()
                return False
            
            logger.debug("Valid session found")
            return True
            
        except Exception as e:
            logger.debug(f"No valid session: {e}")
            return False
    
    def invalidate_session(self):
        """Invalidate current admin session"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("Session invalidated")
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
    
    def is_user_admin(self) -> bool:
        """
        Check if current user has administrator privileges.
        
        Returns:
            True if user is admin
        """
        if not WINDOWS_AVAILABLE:
            logger.warning("Windows modules not available, cannot check admin status")
            return False
        
        try:
            return win32security.IsUserAnAdmin()
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False
    
    def require_admin_rights(self):
        """
        Require admin rights or raise exception.
        
        Raises:
            PermissionError: If user does not have admin rights
        """
        if not self.is_user_admin():
            raise PermissionError("Administrator privileges required for this operation")
    
    def generate_password_reset_token(self) -> str:
        """
        Generate password reset token.
        
        Returns:
            Reset token string
        """
        token = secrets.token_urlsafe(32)
        
        reset_data = {
            'token': token,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        reset_file = self.config_dir / '.password_reset_token'
        encrypted = self.cipher.encrypt(json.dumps(reset_data).encode('utf-8'))
        reset_file.write_bytes(encrypted)
        
        logger.info("Generated password reset token")
        return token
    
    def verify_reset_token(self, token: str) -> bool:
        """
        Verify password reset token.
        
        Args:
            token: Reset token to verify
            
        Returns:
            True if token is valid
        """
        try:
            reset_file = self.config_dir / '.password_reset_token'
            if not reset_file.exists():
                return False
            
            encrypted = reset_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            reset_data = json.loads(decrypted)
            
            # Check token match
            if not secrets.compare_digest(reset_data['token'], token):
                return False
            
            # Check expiration
            expires_at = datetime.fromisoformat(reset_data['expires_at'])
            if datetime.now() > expires_at:
                reset_file.unlink()
                logger.info("Reset token expired")
                return False
            
            logger.info("Valid reset token")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying reset token: {e}")
            return False
    
    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """
        Reset password using reset token.
        
        Args:
            token: Valid reset token
            new_password: New password
            
        Returns:
            True if successful
        """
        if not self.verify_reset_token(token):
            logger.warning("Invalid or expired reset token")
            return False
        
        # Set new password
        if self.set_admin_password(new_password):
            # Delete reset token
            reset_file = self.config_dir / '.password_reset_token'
            if reset_file.exists():
                reset_file.unlink()
            
            logger.info("Password reset successful")
            return True
        
        return False
    
    def get_credential_info(self) -> Dict:
        """
        Get non-sensitive credential information.
        
        Returns:
            Dictionary with credential metadata
        """
        try:
            if not self.auth_file.exists():
                return {'exists': False}
            
            encrypted = self.auth_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            credentials = json.loads(decrypted)
            
            return {
                'exists': True,
                'username': credentials.get('username'),
                'created_at': credentials.get('created_at'),
                'last_changed': credentials.get('last_changed'),
                'hash_algorithm': credentials.get('hash_algorithm'),
                'iterations': credentials.get('iterations')
            }
            
        except Exception as e:
            logger.error(f"Error getting credential info: {e}")
            return {'exists': False, 'error': str(e)}


# Utility functions for UAC elevation
def is_admin() -> bool:
    """Check if process has admin privileges"""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        return win32security.IsUserAnAdmin()
    except Exception:
        return False


def request_uac_elevation():
    """Request UAC elevation for current process"""
    if not WINDOWS_AVAILABLE:
        logger.error("Windows modules not available")
        return False
    
    import sys
    import ctypes
    
    if is_admin():
        return True
    
    try:
        # Re-run script with admin rights
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            " ".join(sys.argv),
            None,
            1  # SW_SHOWNORMAL
        )
        return True
    except Exception as e:
        logger.error(f"UAC elevation failed: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize auth manager
    config_dir = Path.home() / ".test_monitoring"
    auth_manager = AdminAuthManager(config_dir)
    
    print("\n" + "="*60)
    print("ADMIN AUTHENTICATION MANAGER TEST")
    print("="*60)
    
    # Get initial password
    initial_file = config_dir / 'ADMIN_INITIAL_PASSWORD.txt'
    if initial_file.exists():
        print(f"\nInitial password file exists at: {initial_file}")
        print(initial_file.read_text())
    
    # Test authentication
    password = input("\nEnter password to test: ")
    
    if auth_manager.verify_admin_password(password):
        print("\n✓ Authentication successful!")
        
        # Test password change
        change = input("\nChange password? (y/n): ")
        if change.lower() == 'y':
            new_password = input("Enter new password: ")
            if auth_manager.set_admin_password(new_password):
                print("✓ Password changed successfully!")
    else:
        print("\n✗ Authentication failed!")
    
    # Check admin status
    print(f"\nIs admin: {auth_manager.is_user_admin()}")
    
    # Get credential info
    info = auth_manager.get_credential_info()
    print(f"\nCredential Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")