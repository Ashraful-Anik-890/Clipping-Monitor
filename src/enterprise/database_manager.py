"""
Database Manager

Centralized SQLite database for all monitoring data with encryption support.

Features:
- Encrypted storage for sensitive data
- Structured schema for all event types
- Efficient indexing for fast queries
- Export to JSON and CSV
- Thread-safe operations
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json
from cryptography.fernet import Fernet
import threading
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Centralized database manager for all monitoring data.
    
    Manages:
    - Clipboard events
    - Application usage
    - Browser activity
    - Screen recordings metadata
    """
    
    def __init__(self, db_path: Path, enable_encryption: bool = True):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
            enable_encryption: Whether to encrypt sensitive content
        """
        self.db_path = db_path
        self.enable_encryption = enable_encryption
        self.lock = threading.Lock()
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self.cipher = None
        if enable_encryption:
            self.cipher = self._init_encryption()
        
        # Initialize database schema
        self._init_database()
        
        logger.info(f"Database initialized at {db_path}")
    
    def _init_encryption(self) -> Fernet:
        """
        Initialize or load encryption key.
        
        Returns:
            Fernet cipher instance
        """
        key_file = self.db_path.parent / '.db_encryption_key'
        
        try:
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
                logger.info("Loaded existing encryption key")
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                
                # Hide the key file on Windows
                try:
                    import win32api
                    import win32con
                    win32api.SetFileAttributes(
                        str(key_file),
                        win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM
                    )
                except ImportError:
                    pass
                
                logger.info("Generated new encryption key")
            
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Error initializing encryption: {e}")
            raise
    
    def _init_database(self):
        """Initialize database schema with all required tables"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Clipboard events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clipboard_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data_type TEXT,
                    data_size INTEGER,
                    source_app TEXT,
                    source_window TEXT,
                    destination_app TEXT,
                    destination_window TEXT,
                    content_preview TEXT,
                    metadata TEXT,
                    encrypted_content BLOB,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Application usage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL,
                    process_name TEXT NOT NULL,
                    process_path TEXT,
                    window_title TEXT,
                    pid INTEGER,
                    parent_process TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Browser activity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS browser_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL,
                    browser_name TEXT NOT NULL,
                    browser_process TEXT,
                    tab_title TEXT,
                    url TEXT,
                    pid INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Screen recordings metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS screen_recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL,
                    file_path TEXT,
                    file_size_mb REAL,
                    resolution TEXT,
                    fps INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System events table (for service lifecycle, errors, etc.)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT,
                    message TEXT,
                    details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_clipboard_timestamp 
                ON clipboard_events(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_clipboard_type 
                ON clipboard_events(event_type, data_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_app_usage_time 
                ON app_usage(start_time, end_time)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_app_usage_process 
                ON app_usage(process_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_browser_time 
                ON browser_activity(start_time, end_time)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_browser_name 
                ON browser_activity(browser_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_events_time 
                ON system_events(timestamp)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("Database schema initialized")
    
    def _encrypt_content(self, content: Any) -> bytes:
        """Encrypt content for storage"""
        if not self.cipher:
            return None
        
        try:
            json_data = json.dumps(content, ensure_ascii=False)
            return self.cipher.encrypt(json_data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error encrypting content: {e}")
            return None
    
    def _decrypt_content(self, encrypted_content: bytes) -> Any:
        """Decrypt content from storage"""
        if not self.cipher or not encrypted_content:
            return None
        
        try:
            decrypted_data = self.cipher.decrypt(encrypted_content)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error decrypting content: {e}")
            return None
    
    def log_clipboard_event(self, event: Dict):
        """
        Log clipboard event to database.
        
        Args:
            event: Clipboard event dictionary
        """
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                # Encrypt full content if available
                encrypted_content = None
                if self.enable_encryption and 'content_full' in event:
                    encrypted_content = self._encrypt_content(event['content_full'])
                
                cursor.execute("""
                    INSERT INTO clipboard_events (
                        timestamp, event_type, data_type, data_size,
                        source_app, source_window, destination_app, destination_window,
                        content_preview, metadata, encrypted_content
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.get('timestamp'),
                    event.get('event_type'),
                    event.get('data_type'),
                    event.get('data_size'),
                    event.get('source_application'),
                    event.get('source_window'),
                    event.get('destination_application'),
                    event.get('destination_window'),
                    event.get('content_preview'),
                    json.dumps(event.get('extra_info', {})),
                    encrypted_content
                ))
                
                conn.commit()
                conn.close()
                
                logger.debug(f"Logged clipboard event: {event.get('event_type')}")
                
            except Exception as e:
                logger.error(f"Error logging clipboard event: {e}")
    
    def log_app_usage(self, event: Dict):
        """
        Log application usage event to database.
        
        Args:
            event: Application usage event dictionary
        """
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO app_usage (
                        start_time, end_time, duration_seconds,
                        process_name, process_path, window_title, pid, parent_process
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.get('start_time'),
                    event.get('end_time'),
                    event.get('duration_seconds'),
                    event.get('process_name'),
                    event.get('process_path'),
                    event.get('window_title'),
                    event.get('pid'),
                    event.get('parent_process')
                ))
                
                conn.commit()
                conn.close()
                
                logger.debug(f"Logged app usage: {event.get('process_name')}")
                
            except Exception as e:
                logger.error(f"Error logging app usage: {e}")
    
    def log_browser_activity(self, event: Dict):
        """
        Log browser activity event to database.
        
        Args:
            event: Browser activity event dictionary
        """
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO browser_activity (
                        start_time, end_time, duration_seconds,
                        browser_name, browser_process, tab_title, url, pid
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.get('start_time'),
                    event.get('end_time'),
                    event.get('duration_seconds'),
                    event.get('browser_name'),
                    event.get('browser_process'),
                    event.get('tab_title'),
                    event.get('url'),
                    event.get('pid')
                ))
                
                conn.commit()
                conn.close()
                
                logger.debug(f"Logged browser activity: {event.get('browser_name')}")
                
            except Exception as e:
                logger.error(f"Error logging browser activity: {e}")
    
    def log_system_event(self, event_type: str, severity: str, message: str, details: Dict = None):
        """
        Log system event (service lifecycle, errors, etc.)
        
        Args:
            event_type: Type of system event
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
            message: Event message
            details: Additional details dictionary
        """
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO system_events (
                        timestamp, event_type, severity, message, details
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    event_type,
                    severity,
                    message,
                    json.dumps(details) if details else None
                ))
                
                conn.commit()
                conn.close()
                
                logger.debug(f"Logged system event: {event_type}")
                
            except Exception as e:
                logger.error(f"Error logging system event: {e}")
    
    def get_events(self, table: str, start_date: datetime = None, end_date: datetime = None, 
                   limit: int = 1000) -> List[Dict]:
        """
        Retrieve events from database.
        
        Args:
            table: Table name to query
            start_date: Filter events after this date
            end_date: Filter events before this date
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build query with date filters
                query = f"SELECT * FROM {table}"
                params = []
                
                if start_date or end_date:
                    query += " WHERE "
                    conditions = []
                    
                    if start_date:
                        conditions.append("timestamp >= ?")
                        params.append(start_date.isoformat())
                    
                    if end_date:
                        conditions.append("timestamp <= ?")
                        params.append(end_date.isoformat())
                    
                    query += " AND ".join(conditions)
                
                query += f" ORDER BY id DESC LIMIT {limit}"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to dictionaries
                events = [dict(row) for row in rows]
                
                conn.close()
                
                return events
                
            except Exception as e:
                logger.error(f"Error retrieving events: {e}")
                return []
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                stats = {}
                
                # Count events in each table
                tables = ['clipboard_events', 'app_usage', 'browser_activity', 
                         'screen_recordings', 'system_events']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[f'{table}_count'] = count
                
                # Get database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                size_bytes = cursor.fetchone()[0]
                stats['database_size_mb'] = round(size_bytes / (1024 * 1024), 2)
                
                # Get date range
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM clipboard_events")
                result = cursor.fetchone()
                if result[0]:
                    stats['oldest_event'] = result[0]
                    stats['newest_event'] = result[1]
                
                conn.close()
                
                return stats
                
            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                return {}
    
    def export_to_json(self, output_path: Path, table_name: str = None, 
                       start_date: datetime = None, end_date: datetime = None):
        """
        Export data to JSON file.
        
        Args:
            output_path: Output file path
            table_name: Specific table to export (or all if None)
            start_date: Filter events after this date
            end_date: Filter events before this date
        """
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row
                
                if table_name:
                    tables = [table_name]
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                
                export_data = {
                    'export_date': datetime.now().isoformat(),
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                    'tables': {}
                }
                
                for table in tables:
                    cursor = conn.cursor()
                    
                    # Build query with date filters
                    query = f"SELECT * FROM {table}"
                    params = []
                    
                    if start_date or end_date:
                        query += " WHERE "
                        conditions = []
                        
                        if start_date:
                            conditions.append("timestamp >= ? OR start_time >= ?")
                            params.extend([start_date.isoformat(), start_date.isoformat()])
                        
                        if end_date:
                            conditions.append("timestamp <= ? OR start_time <= ?")
                            params.extend([end_date.isoformat(), end_date.isoformat()])
                        
                        query += " AND ".join(conditions)
                    
                    cursor.execute(query, params)
                    
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    export_data['tables'][table] = [
                        dict(zip(columns, row)) for row in rows
                    ]
                
                conn.close()
                
                # Write to file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(
                    json.dumps(export_data, indent=2, default=str, ensure_ascii=False),
                    encoding='utf-8'
                )
                
                logger.info(f"Exported data to {output_path}")
                
            except Exception as e:
                logger.error(f"Error exporting to JSON: {e}")
                raise
    
    def export_to_csv(self, output_dir: Path, start_date: datetime = None, end_date: datetime = None):
        """
        Export each table to separate CSV files.
        
        Args:
            output_dir: Output directory path
            start_date: Filter events after this date
            end_date: Filter events before this date
        """
        import csv
        
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                output_dir.mkdir(parents=True, exist_ok=True)
                
                for table in tables:
                    # Build query with date filters
                    query = f"SELECT * FROM {table}"
                    params = []
                    
                    if start_date or end_date:
                        query += " WHERE "
                        conditions = []
                        
                        if start_date:
                            conditions.append("(timestamp >= ? OR start_time >= ?)")
                            params.extend([start_date.isoformat(), start_date.isoformat()])
                        
                        if end_date:
                            conditions.append("(timestamp <= ? OR start_time <= ?)")
                            params.extend([end_date.isoformat(), end_date.isoformat()])
                        
                        query += " AND ".join(conditions)
                    
                    cursor.execute(query, params)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    # Write to CSV
                    csv_path = output_dir / f"{table}.csv"
                    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(columns)
                        writer.writerows(rows)
                    
                    logger.info(f"Exported {table} to {csv_path}")
                
                conn.close()
                logger.info(f"All tables exported to {output_dir}")
                
            except Exception as e:
                logger.error(f"Error exporting to CSV: {e}")
                raise
    
    def cleanup_old_data(self, retention_days: int = 90):
        """
        Delete data older than retention period.
        
        Args:
            retention_days: Number of days to retain data
        """
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
                
                tables = ['clipboard_events', 'app_usage', 'browser_activity', 'system_events']
                
                total_deleted = 0
                
                for table in tables:
                    cursor.execute(f"""
                        DELETE FROM {table} 
                        WHERE timestamp < ? OR start_time < ?
                    """, (cutoff_date, cutoff_date))
                    
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    logger.info(f"Deleted {deleted} old records from {table}")
                
                conn.commit()
                
                # Vacuum to reclaim space
                cursor.execute("VACUUM")
                
                conn.close()
                
                logger.info(f"Cleanup complete. Total deleted: {total_deleted} records")
                
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    def optimize_database(self):
        """Optimize database performance"""
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                # Analyze tables for query optimization
                cursor.execute("ANALYZE")
                
                # Vacuum to reclaim space and defragment
                cursor.execute("VACUUM")
                
                # Update statistics
                cursor.execute("PRAGMA optimize")
                
                conn.close()
                
                logger.info("Database optimized")
                
            except Exception as e:
                logger.error(f"Error optimizing database: {e}")
    
    def close(self):
        """Close database connections and cleanup"""
        logger.info("Closing database")