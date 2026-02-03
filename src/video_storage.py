"""
Video Storage and Indexing Module
Manages video chunks and correlates them with clipboard events
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import threading
import hashlib

logger = logging.getLogger(__name__)


class VideoStorageManager:
    """
    Manages video chunk storage, indexing, and correlation with clipboard events
    
    Features:
    - SQLite-based metadata indexing
    - Chunk-to-event correlation
    - Retention policy enforcement
    - Upload queue management (future-ready)
    """
    
    def __init__(self, storage_dir: Path, retention_days: int = 30):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.video_dir = self.storage_dir / "videos"
        self.video_dir.mkdir(exist_ok=True)
        
        self.db_path = self.storage_dir / "video_index.db"
        self.retention_days = retention_days
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Initialize database
        self._init_database()
        
        logger.info(f"VideoStorageManager initialized: {self.storage_dir}")
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Video chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_chunks (
                    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration_seconds REAL,
                    size_mb REAL,
                    resolution TEXT,
                    fps INTEGER,
                    codec TEXT,
                    checksum TEXT,
                    uploaded BOOLEAN DEFAULT 0,
                    upload_timestamp TEXT,
                    deleted BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Clipboard events table (denormalized copy for correlation)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clipboard_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data_type TEXT,
                    source_application TEXT,
                    destination_window TEXT,
                    content_preview TEXT,
                    file_names TEXT,
                    chunk_id INTEGER,
                    FOREIGN KEY (chunk_id) REFERENCES video_chunks(chunk_id)
                )
            """)
            
            # Upload queue table (future use)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS upload_queue (
                    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id INTEGER NOT NULL,
                    priority INTEGER DEFAULT 5,
                    retry_count INTEGER DEFAULT 0,
                    last_retry TEXT,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chunk_id) REFERENCES video_chunks(chunk_id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_time ON video_chunks(start_time, end_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON clipboard_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_chunk ON clipboard_events(chunk_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_upload_status ON upload_queue(status)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def register_chunk(self, metadata: Dict[str, Any]) -> int:
        """Register a new video chunk in the database"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Calculate file checksum for integrity
                    checksum = self._calculate_checksum(Path(metadata['filepath']))
                    
                    cursor.execute("""
                        INSERT INTO video_chunks 
                        (filepath, filename, start_time, end_time, duration_seconds, 
                         size_mb, resolution, fps, codec, checksum)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metadata['filepath'],
                        Path(metadata['filepath']).name,
                        metadata['start_time'],
                        metadata['end_time'],
                        metadata['duration_seconds'],
                        metadata['size_mb'],
                        metadata['resolution'],
                        metadata['fps'],
                        metadata['codec'],
                        checksum
                    ))
                    
                    chunk_id = cursor.lastrowid
                    conn.commit()
                    
                    logger.info(f"Registered chunk {chunk_id}: {metadata['filepath']}")
                    return chunk_id
                    
            except Exception as e:
                logger.error(f"Error registering chunk: {e}", exc_info=True)
                return -1
    
    def register_clipboard_event(self, event: Dict[str, Any]):
        """Register clipboard event and correlate with active chunk"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Find the active chunk at this timestamp
                    event_time = event.get('timestamp', datetime.now().isoformat())
                    chunk_id = self._find_chunk_for_timestamp(event_time)
                    
                    # Serialize file names if present
                    file_names = json.dumps(event.get('file_names', [])) if 'file_names' in event else None
                    
                    cursor.execute("""
                        INSERT INTO clipboard_events
                        (timestamp, event_type, data_type, source_application, 
                         destination_window, content_preview, file_names, chunk_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event_time,
                        event['event_type'],
                        event.get('data_type'),
                        event.get('source_application'),
                        event.get('destination_window'),
                        str(event.get('content_preview', ''))[:500],  # Truncate
                        file_names,
                        chunk_id
                    ))
                    
                    conn.commit()
                    logger.debug(f"Registered clipboard event, correlated with chunk {chunk_id}")
                    
            except Exception as e:
                logger.error(f"Error registering clipboard event: {e}", exc_info=True)
    
    def _find_chunk_for_timestamp(self, timestamp: str) -> Optional[int]:
        """Find chunk ID that contains the given timestamp"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT chunk_id FROM video_chunks
                    WHERE start_time <= ? AND end_time >= ?
                    AND deleted = 0
                    ORDER BY chunk_id DESC
                    LIMIT 1
                """, (timestamp, timestamp))
                
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error finding chunk for timestamp: {e}")
            return None
    
    def get_chunk_events(self, chunk_id: int) -> List[Dict[str, Any]]:
        """Get all clipboard events associated with a chunk"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM clipboard_events
                WHERE chunk_id = ?
                ORDER BY timestamp
            """, (chunk_id,))
            
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                if event['file_names']:
                    event['file_names'] = json.loads(event['file_names'])
                events.append(event)
            
            return events
    
    def get_chunks_in_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get all chunks within a time range"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM video_chunks
                WHERE start_time >= ? AND end_time <= ?
                AND deleted = 0
                ORDER BY start_time
            """, (start_time.isoformat(), end_time.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_chunks(self):
        """Delete chunks older than retention period"""
        with self.lock:
            try:
                cutoff_date = datetime.now() - timedelta(days=self.retention_days)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Find old chunks
                    cursor.execute("""
                        SELECT chunk_id, filepath FROM video_chunks
                        WHERE end_time < ? AND deleted = 0
                    """, (cutoff_date.isoformat(),))
                    
                    old_chunks = cursor.fetchall()
                    
                    for chunk_id, filepath in old_chunks:
                        # Delete physical file
                        try:
                            Path(filepath).unlink(missing_ok=True)
                            logger.info(f"Deleted old chunk file: {filepath}")
                        except Exception as e:
                            logger.error(f"Error deleting file {filepath}: {e}")
                        
                        # Mark as deleted in database
                        cursor.execute("""
                            UPDATE video_chunks
                            SET deleted = 1
                            WHERE chunk_id = ?
                        """, (chunk_id,))
                    
                    conn.commit()
                    logger.info(f"Cleaned up {len(old_chunks)} old chunks")
                    
            except Exception as e:
                logger.error(f"Error during cleanup: {e}", exc_info=True)
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of file"""
        try:
            if not filepath.exists():
                return ""
            
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return ""
    
    def export_metadata(self, output_path: Path):
        """Export all metadata to JSON file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all chunks
                cursor.execute("SELECT * FROM video_chunks WHERE deleted = 0")
                chunks = [dict(row) for row in cursor.fetchall()]
                
                # Get all events
                cursor.execute("SELECT * FROM clipboard_events")
                events = [dict(row) for row in cursor.fetchall()]
                
                # Create export structure
                export_data = {
                    "export_time": datetime.now().isoformat(),
                    "total_chunks": len(chunks),
                    "total_events": len(events),
                    "chunks": chunks,
                    "events": events
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Exported metadata to {output_path}")
                
        except Exception as e:
            logger.error(f"Error exporting metadata: {e}", exc_info=True)
            raise
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count chunks
            cursor.execute("SELECT COUNT(*) FROM video_chunks WHERE deleted = 0")
            total_chunks = cursor.fetchone()[0]
            
            # Calculate total size
            cursor.execute("SELECT SUM(size_mb) FROM video_chunks WHERE deleted = 0")
            total_size_mb = cursor.fetchone()[0] or 0
            
            # Count events
            cursor.execute("SELECT COUNT(*) FROM clipboard_events")
            total_events = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute("""
                SELECT MIN(start_time), MAX(end_time) 
                FROM video_chunks WHERE deleted = 0
            """)
            date_range = cursor.fetchone()
            
            return {
                "total_chunks": total_chunks,
                "total_size_mb": round(total_size_mb, 2),
                "total_events": total_events,
                "earliest_chunk": date_range[0],
                "latest_chunk": date_range[1],
                "video_directory": str(self.video_dir),
                "database_path": str(self.db_path)
            }


class UploadQueueManager:
    """
    Future-ready upload queue manager (stub for now)
    
    Will handle:
    - Prioritized upload queue
    - Retry logic with exponential backoff
    - Network connectivity checks
    - Bandwidth throttling
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        logger.info("UploadQueueManager initialized (stub mode)")
    
    def enqueue_chunk(self, chunk_id: int, priority: int = 5):
        """Add chunk to upload queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO upload_queue (chunk_id, priority, status)
                    VALUES (?, ?, 'pending')
                """, (chunk_id, priority))
                conn.commit()
                logger.info(f"Chunk {chunk_id} added to upload queue")
        except Exception as e:
            logger.error(f"Error enqueueing chunk: {e}")
    
    def get_pending_uploads(self) -> List[int]:
        """Get list of pending chunk IDs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chunk_id FROM upload_queue
                WHERE status = 'pending'
                ORDER BY priority DESC, added_at ASC
            """)
            return [row[0] for row in cursor.fetchall()]
    
    def mark_uploaded(self, chunk_id: int):
        """Mark chunk as successfully uploaded"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update upload queue
                cursor.execute("""
                    UPDATE upload_queue
                    SET status = 'completed'
                    WHERE chunk_id = ?
                """, (chunk_id,))
                
                # Update video_chunks table
                cursor.execute("""
                    UPDATE video_chunks
                    SET uploaded = 1, upload_timestamp = ?
                    WHERE chunk_id = ?
                """, (datetime.now().isoformat(), chunk_id))
                
                conn.commit()
                logger.info(f"Chunk {chunk_id} marked as uploaded")
        except Exception as e:
            logger.error(f"Error marking chunk as uploaded: {e}")
