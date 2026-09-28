from __future__ import annotations
import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def setup_application() -> QApplication:
    """Create and configure the QApplication."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("MusicPlayer")
    app.setOrganizationName("MusicPlayer")
    return app
def main() -> int:
    """Main entry point."""
    logger.info("Starting Music Player")

    app = setup_application()

    try:
        # Initialize backend services
        from src.backend.services.library import LibraryServiceImpl
        from src.backend.services.playback import PlaybackServiceImpl
        from src.backend.services.queue import QueueServiceImpl
        from src.backend.services.playlist import PlaylistServiceImpl
        from src.backend.services.settings import SettingsServiceImpl

        logger.info("Initializing backend services...")

        library_service = LibraryServiceImpl()
        playback_service = PlaybackServiceImpl()
        queue_service = QueueServiceImpl()
        playlist_service = PlaylistServiceImpl()
        settings_service = SettingsServiceImpl()
        logger.info("Backend services initialized")

        # Create and show main window
        from src.frontend.main_window import MainWindow
        window = MainWindow(
            library_service=library_service,
            playback_service=playback_service,
            queue_service=queue_service,
            playlist_service=playlist_service,
            settings_service=settings_service,
        )

        window.resize(1400, 900)
        window.show()
        logger.info("Application initialized, entering event loop")
        return app.exec()
    except Exception as e:
        logger.fatal(f"Fatal error starting application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())