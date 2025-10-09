"""
Main application window with modern UI.

Implements the primary user interface using ttkbootstrap for a modern,
professional appearance with comprehensive user controls and real-time feedback.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..models.verse import TranslationType
from ..core.document_processor import DocumentProcessor
from ..core.placeholder_parser import PlaceholderParser
from ..core.cache_manager import CacheManager
from ..api.bible_api_client import BibleAPIClient
from ..config.settings import Settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(ttk.Window):
    """
    Main application window for VerseInserter.
    
    Provides comprehensive user interface with file selection, progress tracking,
    translation selection, and real-time status updates.
    
    Features:
        - Modern ttkbootstrap styling
        - Drag-and-drop file support (future)
        - Real-time progress indication
        - Log viewer integration
        - Settings management
        - About dialog with licensing info
    """
    
    APP_TITLE = "VerseInserter - Automated Scripture Insertion"
    APP_VERSION = "1.0.0"
    WINDOW_SIZE = "900x700"
    
    def __init__(self, settings: Settings):
        """
        Initialize main application window.
        
        Args:
            settings: Application settings instance
        """
        super().__init__(themename="cosmo")  # Modern theme
        
        self.settings = settings
        self.selected_file: Optional[Path] = None
        self.is_processing = False
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.cache_manager = CacheManager()
        self.placeholder_parser = PlaceholderParser()
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self._setup_window()
        self._create_widgets()
        self._setup_bindings()
        
        logger.info("Main window initialized")
    
    def _setup_window(self) -> None:
        """Configure main window properties."""
        self.title(self.APP_TITLE)
        self.geometry(self.WINDOW_SIZE)
        
        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Set minimum size
        self.minsize(800, 600)
        
        # Configure window icon (if available)
        # self.iconbitmap("path/to/icon.ico")
    
    def _create_widgets(self) -> None:
        """Create and layout all UI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Header section
        self._create_header(main_frame)
        
        # File selection section
        self._create_file_section(main_frame)
        
        # Translation selection
        self._create_translation_section(main_frame)
        
        # Progress section
        self._create_progress_section(main_frame)
        
        # Log viewer section
        self._create_log_section(main_frame)
        
        # Control buttons
        self._create_control_buttons(main_frame)
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self, parent: ttk.Frame) -> None:
        """Create application header with branding."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=X, pady=(0, 20))
        
        # App title
        title_label = ttk.Label(
            header_frame,
            text="VerseInserter",
            font=("Segoe UI", 24, "bold"),
            bootstyle=INFO
        )
        title_label.pack(anchor=W)
        
        # Tagline
        tagline_label = ttk.Label(
            header_frame,
            text="Inserting Scripture Seamlessly into Your Words.",
            font=("Segoe UI", 10),
            bootstyle=SECONDARY
        )
        tagline_label.pack(anchor=W)
        
        # Separator
        ttk.Separator(parent, orient=HORIZONTAL).pack(fill=X, pady=10)
    
    def _create_file_section(self, parent: ttk.Frame) -> None:
        """Create file selection section."""
        file_frame = ttk.Labelframe(
            parent,
            text="Document Selection",
            padding=15,
            bootstyle=PRIMARY
        )
        file_frame.pack(fill=X, pady=(0, 15))
        
        # File path display
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            path_frame,
            text="Selected File:",
            font=("Segoe UI", 10, "bold")
        ).pack(side=LEFT, padx=(0, 10))
        
        self.file_path_var = tk.StringVar(value="No file selected")
        self.file_path_label = ttk.Label(
            path_frame,
            textvariable=self.file_path_var,
            font=("Segoe UI", 9),
            bootstyle=SECONDARY
        )
        self.file_path_label.pack(side=LEFT, fill=X, expand=YES)
        
        # Browse button
        self.browse_button = ttk.Button(
            file_frame,
            text="Browse for Document...",
            command=self._browse_file,
            bootstyle=INFO,
            width=25
        )
        self.browse_button.pack(anchor=W)
    
    def _create_translation_section(self, parent: ttk.Frame) -> None:
        """Create Bible translation selection."""
        trans_frame = ttk.Labelframe(
            parent,
            text="Translation Settings",
            padding=15,
            bootstyle=PRIMARY
        )
        trans_frame.pack(fill=X, pady=(0, 15))
        
        # Translation dropdown
        trans_inner = ttk.Frame(trans_frame)
        trans_inner.pack(fill=X)
        
        ttk.Label(
            trans_inner,
            text="Bible Translation:",
            font=("Segoe UI", 10, "bold")
        ).pack(side=LEFT, padx=(0, 15))
        
        # Translation options
        translations = [t.display_name for t in TranslationType]
        self.translation_var = tk.StringVar(value=translations[0])
        
        translation_combo = ttk.Combobox(
            trans_inner,
            textvariable=self.translation_var,
            values=translations,
            state="readonly",
            width=35,
            bootstyle=INFO
        )
        translation_combo.pack(side=LEFT)
    
    def _create_progress_section(self, parent: ttk.Frame) -> None:
        """Create progress tracking section."""
        progress_frame = ttk.Labelframe(
            parent,
            text="Processing Progress",
            padding=15,
            bootstyle=SUCCESS
        )
        progress_frame.pack(fill=X, pady=(0, 15))
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            bootstyle=SUCCESS,
            length=400
        )
        self.progress_bar.pack(fill=X, pady=(0, 10))
        
        # Status message
        self.status_var = tk.StringVar(value="Ready to process")
        status_label = ttk.Label(
            progress_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bootstyle=SECONDARY
        )
        status_label.pack(anchor=W)
        
        # Statistics frame
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=X, pady=(10, 0))
        
        self.stats_labels = {}
        stats_items = [
            ("Placeholders Found:", "found"),
            ("Successfully Replaced:", "replaced"),
            ("Failed:", "failed"),
        ]
        
        for idx, (label_text, key) in enumerate(stats_items):
            frame = ttk.Frame(stats_frame)
            frame.pack(side=LEFT, padx=(0, 20) if idx < len(stats_items)-1 else 0)
            
            ttk.Label(
                frame,
                text=label_text,
                font=("Segoe UI", 9)
            ).pack(side=LEFT, padx=(0, 5))
            
            var = tk.StringVar(value="0")
            self.stats_labels[key] = var
            
            ttk.Label(
                frame,
                textvariable=var,
                font=("Segoe UI", 9, "bold"),
                bootstyle=INFO
            ).pack(side=LEFT)
    
    def _create_log_section(self, parent: ttk.Frame) -> None:
        """Create log viewer section."""
        log_frame = ttk.Labelframe(
            parent,
            text="Activity Log",
            padding=15,
            bootstyle=SECONDARY
        )
        log_frame.pack(fill=BOTH, expand=YES, pady=(0, 15))
        
        # Text widget with scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=BOTH, expand=YES)
        
        scrollbar = ttk.Scrollbar(log_container)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.log_text = tk.Text(
            log_container,
            height=10,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#212529",
            relief=FLAT,
            padx=10,
            pady=10
        )
        self.log_text.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.config(command=self.log_text.yview)
        
        # Make log read-only
        self.log_text.bind("<Key>", lambda e: "break")
    
    def _create_control_buttons(self, parent: ttk.Frame) -> None:
        """Create main control buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X)
        
        # Process button
        self.process_button = ttk.Button(
            button_frame,
            text="Process Document",
            command=self._process_document,
            bootstyle=SUCCESS,
            width=20
        )
        self.process_button.pack(side=LEFT, padx=(0, 10))
        
        # Clear button
        clear_button = ttk.Button(
            button_frame,
            text="Clear Log",
            command=self._clear_log,
            bootstyle=WARNING,
            width=15
        )
        clear_button.pack(side=LEFT, padx=(0, 10))
        
        # Settings button
        settings_button = ttk.Button(
            button_frame,
            text="Settings",
            command=self._show_settings,
            bootstyle=INFO,
            width=15
        )
        settings_button.pack(side=LEFT)
        
        # About button (right side)
        about_button = ttk.Button(
            button_frame,
            text="About",
            command=self._show_about,
            bootstyle=SECONDARY,
            width=15
        )
        about_button.pack(side=RIGHT)
    
    def _create_status_bar(self) -> None:
        """Create bottom status bar."""
        status_frame = ttk.Frame(self, relief=SUNKEN, borderwidth=1)
        status_frame.pack(side=BOTTOM, fill=X)
        
        self.status_bar_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_bar_var,
            font=("Segoe UI", 8),
            padding=5
        )
        status_label.pack(side=LEFT)
        
        # Version info (right side)
        version_label = ttk.Label(
            status_frame,
            text=f"Version {self.APP_VERSION}",
            font=("Segoe UI", 8),
            padding=5,
            bootstyle=SECONDARY
        )
        version_label.pack(side=RIGHT)
    
    def _setup_bindings(self) -> None:
        """Setup keyboard shortcuts and event bindings."""
        self.bind("<Control-o>", lambda e: self._browse_file())
        self.bind("<Control-p>", lambda e: self._process_document())
        self.bind("<F1>", lambda e: self._show_about())
    
    def _browse_file(self) -> None:
        """Open file browser dialog."""
        filename = filedialog.askopenfilename(
            title="Select Word Document",
            filetypes=[
                ("Word Documents", "*.docx"),
                ("All Files", "*.*")
            ],
            initialdir=Path.home() / "Documents"
        )
        
        if filename:
            self.selected_file = Path(filename)
            self.file_path_var.set(str(self.selected_file))
            self._log_message(f"Selected file: {self.selected_file.name}")
            self.status_bar_var.set(f"File loaded: {self.selected_file.name}")
    
    def _process_document(self) -> None:
        """Main document processing workflow."""
        if not self.selected_file:
            messagebox.showwarning(
                "No File Selected",
                "Please select a Word document first."
            )
            return
        
        if self.is_processing:
            messagebox.showinfo(
                "Processing in Progress",
                "A document is already being processed."
            )
            return
        
        # Validate API key
        if not self.settings.api_key:
            messagebox.showerror(
                "API Key Required",
                "Please configure your API.Bible key in Settings."
            )
            self._show_settings()
            return
        
        # Start processing in background thread
        self.is_processing = True
        self.process_button.config(state=DISABLED)
        self._reset_progress()
        
        self.executor.submit(self._process_document_async)
    
    def _process_document_async(self) -> None:
        """Asynchronous document processing (runs in thread)."""
        try:
            self._log_message("=" * 50)
            self._log_message("Starting document processing...")
            
            # Get selected translation
            trans_name = self.translation_var.get().split("(")[1].strip(")")
            translation = TranslationType[trans_name]
            
            self._update_status("Loading document...")
            
            # Load document
            with self.document_processor.load_document(self.selected_file) as doc:
                # Find placeholders
                self._update_status("Scanning for placeholders...")
                self.document_processor.set_progress_callback(self._progress_callback)
                
                placeholders = self.document_processor.find_all_placeholders(doc)
                
                if not placeholders:
                    self.after(0, lambda: messagebox.showinfo(
                        "No Placeholders",
                        "No scripture placeholders found in document."
                    ))
                    return
                
                self._update_stats("found", len(placeholders))
                self._log_message(f"Found {len(placeholders)} placeholders")
                
                # Fetch verses
                self._update_status("Fetching verses from API...")
                verses = self._fetch_verses_async(placeholders, translation)
                
                # Replace placeholders
                self._update_status("Replacing placeholders...")
                result = self.document_processor.replace_placeholders(doc, verses)
                
                self._update_stats("replaced", result.placeholders_replaced)
                self._update_stats("failed", result.placeholders_failed)
                
                # Save document
                self._update_status("Saving document...")
                output_path = self.document_processor.generate_output_filename(
                    self.selected_file
                )
                self.document_processor.save_document(doc, output_path)
                
                self._log_message(f"Document saved: {output_path}")
                self._log_message(str(result))
                
                # Show success message
                self.after(0, lambda: messagebox.showinfo(
                    "Processing Complete",
                    f"Document processed successfully!\n\n"
                    f"Output: {output_path.name}\n"
                    f"Replaced: {result.placeholders_replaced}/{result.placeholders_found}"
                ))
                
        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            self._log_message(f"ERROR: {e}")
            self.after(0, lambda: messagebox.showerror(
                "Processing Failed",
                f"An error occurred:\n\n{str(e)}"
            ))
            
        finally:
            self.is_processing = False
            self.after(0, lambda: self.process_button.config(state=NORMAL))
            self._update_status("Ready")
    
    def _fetch_verses_async(self, placeholders, translation):
        """Fetch verses using API client."""
        verses_dict = {}
        
        # Create async event loop for API calls
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def fetch_all():
                async with BibleAPIClient(self.settings.api_key) as client:
                    unique_refs = self.placeholder_parser.extract_unique_references(placeholders)
                    
                    for idx, ref in enumerate(unique_refs):
                        # Check cache first
                        cached_verse = self.cache_manager.get(ref)
                        if cached_verse:
                            verses_dict[ref.canonical_reference] = cached_verse
                            self._log_message(f"Cache hit: {ref.canonical_reference}")
                        else:
                            try:
                                verse = await client.fetch_verse(ref)
                                verses_dict[ref.canonical_reference] = verse
                                self.cache_manager.set(ref, verse)
                                self._log_message(f"Fetched: {ref.canonical_reference}")
                            except Exception as e:
                                self._log_message(f"Failed to fetch {ref.canonical_reference}: {e}")
                        
                        # Update progress
                        progress = (idx + 1) / len(unique_refs) * 50 + 50  # 50-100%
                        self.after(0, lambda p=progress: self.progress_var.set(p))
            
            loop.run_until_complete(fetch_all())
            
        finally:
            loop.close()
        
        return verses_dict
    
    def _progress_callback(self, current: int, total: int, message: str) -> None:
        """Progress callback from document processor."""
        progress = (current / total * 50) if total > 0 else 0  # 0-50%
        self.after(0, lambda: self.progress_var.set(progress))
        self.after(0, lambda: self.status_var.set(message))
    
    def _update_status(self, message: str) -> None:
        """Update status message (thread-safe)."""
        self.after(0, lambda: self.status_var.set(message))
        self.after(0, lambda: self._log_message(message))
    
    def _update_stats(self, key: str, value: int) -> None:
        """Update statistics display (thread-safe)."""
        if key in self.stats_labels:
            self.after(0, lambda: self.stats_labels[key].set(str(value)))
    
    def _log_message(self, message: str) -> None:
        """Add message to log viewer."""
        def add_to_log():
            self.log_text.config(state=NORMAL)
            self.log_text.insert(END, f"{message}\n")
            self.log_text.see(END)
            self.log_text.config(state=DISABLED)
        
        self.after(0, add_to_log)
    
    def _clear_log(self) -> None:
        """Clear log viewer."""
        self.log_text.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.log_text.config(state=DISABLED)
        self._log_message("Log cleared")
    
    def _reset_progress(self) -> None:
        """Reset progress indicators."""
        self.progress_var.set(0)
        self.status_var.set("Processing...")
        for key in self.stats_labels:
            self.stats_labels[key].set("0")
    
    def _show_settings(self) -> None:
        """Show settings dialog."""
        # TODO: Implement settings dialog
        messagebox.showinfo("Settings", "Settings dialog coming soon!")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        about_text = f"""
{self.APP_TITLE}
Version {self.APP_VERSION}

Developed by: Kasim Lyee
Email: lyee@codewithlyee.com
Phone: +256701521269
Website: www.portfolio.codewithlyee.com

Organization: Softlite Inc.
License: Proprietary - All Rights Reserved

© 2025 Softlite Inc. All rights reserved.

"Inserting Scripture Seamlessly into Your Words."
        """
        
        messagebox.showinfo("About VerseInserter", about_text.strip())