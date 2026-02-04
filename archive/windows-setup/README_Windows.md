# TVArgenta Windows Development Setup

This guide helps you set up TVArgenta for development and testing on Windows.

## Prerequisites

- Windows 10/11
- Python 3.8 or higher (download from https://python.org)
- Git (for cloning the repository)

## Quick Setup

1. Clone the repository:
   ```cmd
   git clone https://github.com/jcarr71/tvargenta-release.git
   cd tvargenta-release
   ```

2. Run the setup script:
   ```cmd
   setup_windows.bat
   ```

This will:
- Create a Python virtual environment
- Install all required dependencies
- Set up necessary directories and config files

## Manual Setup (Alternative)

If the batch file doesn't work:

1. Create virtual environment:
   ```cmd
   python -m venv venv
   ```

2. Activate it:
   ```cmd
   call venv\Scripts\activate.bat
   ```

3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

4. Create directories:
   ```cmd
   mkdir content\videos\system content\mods content\patches content\backups logs tmp
   ```

## Running the Application

1. Activate the virtual environment:
   ```cmd
   call venv\Scripts\activate.bat
   ```

2. Run the Flask application:
   ```cmd
   python app.py
   ```

3. Open your browser and go to: http://localhost:5000

## Windows-Specific Notes

- The application uses cross-platform file locking (msvcrt on Windows, fcntl on Unix)
- Some features may not work on Windows:
  - Hardware-specific features (RPi.GPIO, NFC reader, HiFiBerry audio)
  - Systemd services (replaced with background threads)
  - ALSA audio configuration

## Development Features Available on Windows

- Web interface for channel management
- Video upload and metadata editing
- Scheduler testing
- Patch system testing
- Most core Flask routes and templates

## Testing

Run the scheduler tests:
```cmd
python test_scheduler.py
```

## Troubleshooting

- If you get import errors, make sure the virtual environment is activated
- Some dependencies might require additional system packages (like ffmpeg)
- For video processing, ensure ffmpeg is installed and in PATH

## Differences from Raspberry Pi Deployment

- No systemd services (runs as threads)
- No hardware GPIO/NFC support
- No ALSA audio configuration
- Uses Windows file paths and permissions
- Chromium kiosk mode not available (use regular browser)