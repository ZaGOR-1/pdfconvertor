# Copilot Instructions - Word to PDF Converter

## Project Overview

This is a modern Python desktop application for converting Word documents (DOC, DOCX) to PDF with a graphical user interface, drag & drop support, and batch processing capabilities.

## Architecture & Structure

```
word_to_pdf_converter/
├── main.py                 # Entry point
├── gui/                    # CustomTkinter UI components
│   ├── main_window.py     # Main application window
│   ├── theme_manager.py   # Light/dark theme system
│   └── widgets.py         # Custom UI widgets
├── converter/             # Conversion logic
│   ├── doc_converter.py   # DOC/DOCX → PDF conversion
│   └── file_handler.py    # File operations & validation
├── utils/                 # Shared utilities
│   ├── config.py          # Config manager (Singleton pattern)
│   └── logger.py          # Logging system
└── assets/                # Icons, styles, resources
```

## Key Technologies & Conventions

### GUI Framework: CustomTkinter
- **Always use CustomTkinter** widgets (CTk prefix) instead of standard tkinter
- Modern Material/Fluent Design aesthetic with smooth animations
- Support both light and dark themes via `theme_manager.py`
- Example: `ctk.CTkButton()`, `ctk.CTkFrame()`, `ctk.CTkProgressBar()`

### Conversion Libraries
- **docx2pdf** or **python-docx2pdf** for DOCX files
- **pywin32** (`win32com.client`) for legacy DOC files on Windows
- Always handle conversion in separate threads to avoid blocking UI

### Drag & Drop
- Use **tkinterdnd2** for drag & drop functionality
- Validate file extensions (`.doc`, `.docx`) before accepting drops
- Visual feedback on hover (border color change, opacity effects)

## Code Standards

### Python Conventions
- **PEP 8** compliance mandatory
- **Type hints** required for all function signatures
- **Docstrings** for all classes and public methods (Google style)
- Modular architecture - separate concerns clearly

### Design Patterns
- **MVC/MVP** pattern for GUI architecture
- **Singleton** for `config.py` to maintain single config state
- **Observer** pattern for progress updates during conversion
- **Threading** with `concurrent.futures` for async file processing

### Example Code Pattern
```python
from typing import List, Optional
from pathlib import Path
import customtkinter as ctk

class FileConverter:
    """Handles Word to PDF conversion with progress tracking."""
    
    def convert_batch(self, files: List[Path], output_dir: Optional[Path] = None) -> dict:
        """Convert multiple Word files to PDF.
        
        Args:
            files: List of Word document paths
            output_dir: Optional output directory (defaults to source dir)
            
        Returns:
            Dictionary with 'success', 'failed', and 'errors' keys
        """
        # Implementation with threading and progress callbacks
```

## Critical Workflows

### Development Setup
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Building Executable
```powershell
# Using PyInstaller
pyinstaller --onefile --windowed --icon=assets/icon.ico main.py
```

## Project-Specific Patterns

### Threading & Progress
- **Never block the main thread** during conversion
- Use `threading.Thread` or `concurrent.futures.ThreadPoolExecutor`
- Update progress bars via thread-safe callbacks
- Store progress state in queue or use thread-safe variables

### Error Handling
- Validate file formats before processing (`.doc`, `.docx` only)
- Handle individual file failures without stopping batch
- Log all errors to file via `utils/logger.py`
- Display user-friendly error messages in UI

### Configuration Management
- Save user preferences to `config.json` (theme, last output folder, window size)
- Load config on startup, save on exit and setting changes
- Use Singleton pattern in `utils/config.py`

### File Size Limits
- Support files up to 100 MB
- Implement size validation before adding to conversion queue
- Optimize memory usage for large batches

## UI/UX Guidelines

### Theme System
- Implement light/dark theme toggle
- Persist theme choice in config
- Smooth transitions between themes (fade effects)

### Progress Indication
- Individual progress bar per file in list
- Overall batch progress bar
- Real-time status updates: pending → processing → completed/failed
- Status bar shows current operation and file count

### Animations
- Smooth hover effects on buttons (color/shadow changes)
- Fade in/out for notifications
- Drag & drop visual feedback (border highlights)
- Progress bar animations

## Language & Localization

- Primary UI language: **Ukrainian**
- Secondary: English (optional implementation)
- Use translation keys if implementing i18n
- Button labels: "Додати файли", "Конвертувати", "Очистити список"

## Security & Validation

- Sanitize all file paths using `pathlib.Path`
- Validate file extensions before processing
- Check disk space before conversion
- Limit concurrent conversions to prevent resource exhaustion

## Testing Priorities

1. Test with various Word formats (modern DOCX, legacy DOC)
2. Large files (50-100 MB)
3. Batch processing (50+ files)
4. Edge cases: corrupted files, insufficient permissions, disk space
5. UI responsiveness during heavy operations

## Windows-Specific Considerations

- This is primarily a **Windows application**
- Use `pywin32` for DOC file support (requires MS Word installed)
- Build with PyInstaller for Windows executables
- Test on Windows 10 and Windows 11

## Current Status

Project is in **planning/early development phase**. Reference `roadmap.md` for detailed development stages. Start with:
1. Project structure setup
2. Basic CustomTkinter GUI
3. Drag & drop implementation
4. Core conversion logic
5. Threading and progress tracking
