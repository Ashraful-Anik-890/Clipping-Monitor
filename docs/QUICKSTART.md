# Quick Start Implementation Guide

## Step-by-Step Integration

### 1. Install Additional Dependencies

```bash
pip install mss opencv-python numpy
```

### 2. File Integration

Add these new files to your `src/` directory:

```
src/
├── main_enhanced.py          # NEW: Enhanced main controller
├── screen_recorder.py         # NEW: Screen recording module
├── video_storage.py           # NEW: Video indexing and storage
├── startup_manager.py         # NEW: Background execution
├── main.py                    # EXISTING: Keep for backwards compatibility
├── clipboard_monitor.py       # EXISTING: No changes needed
├── storage.py                 # EXISTING: No changes needed
├── config.py                  # EXISTING: No changes needed
├── permissions.py             # EXISTING: No changes needed
├── gui.py                     # EXISTING: No changes needed
├── tray_icon.py              # EXISTING: No changes needed
└── error_handler.py          # EXISTING: No changes needed
```

### 3. Update Configuration

Add to your `Config.DEFAULT_CONFIG` in `config.py`:

```python
DEFAULT_CONFIG = {
    # ... existing config ...
    "enable_screen_recording": True,
    "screen_recording_fps": 10,
    "screen_recording_quality": "medium",  # low, medium, high
    "video_chunk_minutes": 10,
    "video_retention_days": 30,
    "resolution_scale": 0.5,  # 50% of original resolution
}
```

### 4. Test Basic Screen Recording

```python
# test_screen_recording.py
import sys
import logging
from pathlib import Path
from screen_recorder import ScreenRecorder
import time

logging.basicConfig(level=logging.INFO)

def test_callback(event):
    print(f"Event: {event['event_type']}")
    if event['event_type'] == 'video_chunk_complete':
        print(f"  Chunk: {event['metadata']['filepath']}")
        print(f"  Size: {event['metadata']['size_mb']} MB")
        print(f"  Duration: {event['metadata']['duration_seconds']}s")

def main():
    output_dir = Path("test_recordings")
    output_dir.mkdir(exist_ok=True)
    
    print("Starting screen recording test...")
    print("Recording for 65 seconds (will create chunk + rotation)...")
    
    recorder = ScreenRecorder(
        output_dir=output_dir,
        chunk_duration_minutes=1,  # 1 minute for testing
        fps=10,
        resolution_scale=0.5,
        quality="medium",
        callback=test_callback
    )
    
    recorder.start()
    
    # Record for 65 seconds (1 minute + 5 seconds)
    time.sleep(65)
    
    recorder.stop()
    
    # Print statistics
    stats = recorder.get_stats()
    print("\nRecording Statistics:")
    print(f"  Frames captured: {stats['frames_captured']}")
    print(f"  Frames dropped: {stats['frames_dropped']}")
    print(f"  Drop rate: {stats['drop_rate']:.2f}%")
    print(f"  Total chunks: {stats['total_chunks']}")
    
    print(f"\nRecordings saved to: {output_dir}")
    print("Test complete!")

if __name__ == "__main__":
    main()
```

Run the test:
```bash
python test_screen_recording.py
```

### 5. Test Video Indexing

```python
# test_video_indexing.py
import sys
from pathlib import Path
from video_storage import VideoStorageManager
from datetime import datetime

def main():
    storage_dir = Path("test_storage")
    storage_dir.mkdir(exist_ok=True)
    
    print("Initializing VideoStorageManager...")
    video_storage = VideoStorageManager(storage_dir=storage_dir, retention_days=30)
    
    # Register a test chunk
    test_metadata = {
        'filepath': 'test_recordings/screen_chunk_20260202_143022.mp4',
        'start_time': datetime.now().isoformat(),
        'end_time': datetime.now().isoformat(),
        'duration_seconds': 60.0,
        'size_mb': 8.5,
        'resolution': '960x540',
        'fps': 10,
        'codec': 'H264'
    }
    
    chunk_id = video_storage.register_chunk(test_metadata)
    print(f"Registered chunk with ID: {chunk_id}")
    
    # Register a test clipboard event
    test_event = {
        'timestamp': datetime.now().isoformat(),
        'event_type': 'clipboard_copy',
        'data_type': 'text',
        'source_application': 'notepad.exe',
        'content_preview': 'Test clipboard content'
    }
    
    video_storage.register_clipboard_event(test_event)
    print("Registered clipboard event")
    
    # Get storage stats
    stats = video_storage.get_storage_stats()
    print("\nStorage Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Export metadata
    export_path = storage_dir / "metadata_export.json"
    video_storage.export_metadata(export_path)
    print(f"\nMetadata exported to: {export_path}")
    
    print("\nTest complete!")

if __name__ == "__main__":
    main()
```

### 6. Build Enhanced Application

Update your build spec:

```bash
# Copy build_enhanced.spec
pyinstaller build_enhanced.spec
```

Or create a simple build script:

```python
# build.py
import PyInstaller.__main__
import sys

PyInstaller.__main__.run([
    'src/main_enhanced.py',
    '--name=ClipboardMonitor',
    '--onefile',
    '--windowed',  # No console
    '--icon=assets/icon.ico',
    '--hidden-import=cv2',
    '--hidden-import=mss',
    '--hidden-import=numpy',
    '--hidden-import=win32com.client',
    '--exclude-module=matplotlib',
    '--exclude-module=scipy',
    '--exclude-module=pandas',
    '--clean',
])
```

### 7. First Run

```bash
# Test with console visible first
python src/main_enhanced.py

# Test background mode
python src/main_enhanced.py --background

# Install startup (admin required)
python src/main_enhanced.py --install-startup

# Remove startup
python src/main_enhanced.py --remove-startup
```

## Common Issues & Solutions

### Issue 1: Import Errors

**Error**: `ModuleNotFoundError: No module named 'cv2'`

**Solution**:
```bash
pip install opencv-python
```

### Issue 2: MSS Import Error

**Error**: `ModuleNotFoundError: No module named 'mss'`

**Solution**:
```bash
pip install mss
```

### Issue 3: High CPU Usage

**Problem**: CPU usage > 20%

**Solutions**:
1. Lower FPS: Change `screen_recording_fps` from 10 to 5
2. Lower quality: Change `quality` from "medium" to "low"
3. Increase resolution scale: Change from 0.5 to 0.3
4. Check frame drop rate - if high, system may be overloaded

### Issue 4: Large File Sizes

**Problem**: Video files too large

**Solutions**:
1. Lower bitrate: Change quality preset to "low"
2. Reduce resolution: Lower `resolution_scale` to 0.3
3. Reduce FPS: Change to 5fps
4. Shorter chunks: Change `chunk_duration_minutes` to 5

### Issue 5: Task Scheduler Permission

**Error**: "Access denied" when installing startup

**Solution**:
Run as administrator or use registry method:
```python
startup_mgr = StartupManager()
startup_mgr.add_to_registry_run()  # Doesn't require admin
```

### Issue 6: Encoding Errors

**Error**: `VideoWriter failed to open`

**Solution**:
1. Install full OpenCV: `pip install opencv-contrib-python`
2. Try different codec in `_configure_encoding()`:
   ```python
   self.fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Try XVID
   self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # Or MJPG
   ```

## Performance Tuning

### For Low-End Systems (2-4 GB RAM, dual-core)

```python
# config.json
{
    "screen_recording_fps": 5,
    "screen_recording_quality": "low",
    "resolution_scale": 0.3,
    "video_chunk_minutes": 5
}
```

### For High-End Systems (16+ GB RAM, 8+ cores)

```python
# config.json
{
    "screen_recording_fps": 15,
    "screen_recording_quality": "high",
    "resolution_scale": 0.7,
    "video_chunk_minutes": 15
}
```

### For Network Drives / Cloud Storage

```python
# config.json
{
    "log_location": "D:\\ClipboardMonitor\\logs",  # Local SSD
    "video_chunk_minutes": 5,  # Smaller chunks
    "polling_interval_ms": 1000  # Reduce polling for network lag
}
```

## Monitoring Performance

### Add Performance Logging

```python
# In main_enhanced.py, add periodic stats logging

import threading
import time

def log_performance_stats(self):
    """Log performance statistics every 5 minutes"""
    while self.is_monitoring_screen:
        time.sleep(300)  # 5 minutes
        
        # Screen recorder stats
        screen_stats = self.screen_recorder.get_stats()
        logger.info(f"Screen Recording Stats: {screen_stats}")
        
        # Storage stats
        storage_stats = self.video_storage.get_storage_stats()
        logger.info(f"Storage Stats: {storage_stats}")
        
        # System resources
        import psutil
        process = psutil.Process()
        logger.info(f"CPU: {process.cpu_percent()}%, RAM: {process.memory_info().rss / 1024 / 1024:.1f}MB")

# Start monitoring thread
self.perf_thread = threading.Thread(target=self.log_performance_stats, daemon=True)
self.perf_thread.start()
```

## Next Steps

1. **Test thoroughly** on target Windows versions
2. **Profile performance** over 24 hours
3. **Implement upload module** (when ready)
4. **Add settings UI** for screen recording options
5. **Create installer** with Inno Setup
6. **Document for end users**
7. **Set up crash reporting** (optional)

## Security Checklist

- [ ] Encryption key properly hidden
- [ ] No credentials in logs
- [ ] Consent dialog functional
- [ ] Clear data deletion works
- [ ] No network access (until upload ready)
- [ ] Proper file permissions
- [ ] Startup task visible in Task Manager
- [ ] Antivirus compatibility tested

## Production Readiness

Before deploying to production:

1. **Load Testing**: Run for 1 week continuously
2. **Error Handling**: Verify all try-catch blocks
3. **Logging**: Ensure proper log rotation
4. **Resource Limits**: Set max storage limits
5. **Cleanup**: Test retention policy
6. **Recovery**: Test crash recovery
7. **Uninstall**: Verify complete removal
8. **Documentation**: Complete user manual

## Support & Troubleshooting

### Debug Mode

Enable detailed logging:
```python
# In main_enhanced.py
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG
    # ... rest of config
)
```

### View Logs

```
# Windows
C:\Users\<Username>\.clipboard_monitor\app.log

# Check Task Scheduler logs
Event Viewer > Task Scheduler > History
```

### Force Stop All Monitoring

```python
# emergency_stop.py
import win32com.client
import subprocess

# Stop via Task Scheduler
try:
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    root_folder = scheduler.GetFolder('\\')
    task = root_folder.GetTask('ClipboardMonitor_Startup')
    task.Stop(0)
    print("Task stopped")
except:
    pass

# Kill process
subprocess.run(['taskkill', '/F', '/IM', 'ClipboardMonitor.exe'])
print("Process terminated")
```

This guide should get you from your current clipboard monitoring implementation to a full-featured screen recording + clipboard tracking system. Start with the basic tests, verify everything works, then proceed to building and deployment.
