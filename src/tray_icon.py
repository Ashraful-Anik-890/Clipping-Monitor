import pystray
from PIL import Image, ImageDraw
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class TrayIcon:
    """System tray icon manager"""
    
    def __init__(self, on_show: Callable, on_start: Callable, on_stop: Callable, on_quit: Callable):
        self.on_show = on_show
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_quit = on_quit
        self.icon = None
        self.is_monitoring = False
    
    def create_icon_image(self) -> Image.Image:
        """Create a simple icon image"""
        # Create a 64x64 image with a clipboard icon
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        
        # Draw a simple clipboard shape
        draw.rectangle([10, 5, 54, 59], outline='black', width=3, fill='lightblue')
        draw.rectangle([20, 0, 44, 10], outline='black', width=3, fill='gray')
        
        # Draw lines representing text
        draw.line([15, 20, 49, 20], fill='black', width=2)
        draw.line([15, 30, 49, 30], fill='black', width=2)
        draw.line([15, 40, 49, 40], fill='black', width=2)
        
        return image
    
    def update_monitoring_state(self, is_monitoring: bool):
        """Update monitoring state"""
        self.is_monitoring = is_monitoring
        if self.icon:
            self.icon.menu = self._create_menu()
    
    def _create_menu(self):
        """Create tray menu"""
        return pystray.Menu(
            pystray.MenuItem("Show Window", self.on_show),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Stop Monitoring" if self.is_monitoring else "Start Monitoring",
                self.on_stop if self.is_monitoring else self.on_start
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.on_quit)
        )
    
    def run(self):
        """Run the tray icon"""
        image = self.create_icon_image()
        self.icon = pystray.Icon(
            "clipboard_monitor",
            image,
            "Clipboard Monitor",
            menu=self._create_menu()
        )
        self.icon.run()
    
    def stop(self):
        """Stop the tray icon"""
        if self.icon:
            self.icon.stop()