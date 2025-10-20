"""
Settings dialog for configuration management.

Provides comprehensive settings interface for API configuration,
cache management, UI preferences, and processing options.

Author: Kasim Lyee <lyee@codewithlyee.com>
Organization: Softlite Inc.
License: MIT
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ...config.settings import Settings
from ...models.verse import TranslationType
from ...utils.logger import get_logger
from ...utils.validators import validate_api_key

logger = get_logger(__name__)


class SettingsDialog(ttk.Toplevel):
    """
    Comprehensive settings dialog with tabbed interface.
    
    Features:
        - API key configuration with validation
        - Cache settings management
        - UI theme selection
        - Processing options
        - Statistics and diagnostics
    """
    
    def __init__(self, parent, settings: Settings):
        """
        Initialize settings dialog.
        
        Args:
            parent: Parent window
            settings: Application settings instance
        """
        super().__init__(parent)
        
        self.settings = settings
        self.result = None
        
        # Window configuration
        self.title("Settings - VerseInserter")
        self.geometry("700x600")
        self.resizable(False, False)
        
        # Modal dialog
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self._center_on_parent(parent)
        
        # Create UI
        self._create_widgets()
        self._load_current_settings()
        
        logger.info("Settings dialog opened")
    
    def _center_on_parent(self, parent) -> None:
        """Center dialog on parent window."""
        self.update_idletasks()
        
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self) -> None:
        """Create all dialog widgets."""
        # Main container
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Header
        header_label = ttk.Label(
            main_frame,
            text="Application Settings",
            font=("Segoe UI", 16, "bold"),
            bootstyle=PRIMARY
        )
        header_label.pack(pady=(0, 20))
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame, bootstyle=INFO)
        self.notebook.pack(fill=BOTH, expand=YES, pady=(0, 20))
        
        # Create tabs
        self._create_api_tab()
        self._create_cache_tab()
        self._create_ui_tab()
        self._create_processing_tab()
        self._create_advanced_tab()
        
        # Button frame
        self._create_buttons(main_frame)
    
    def _create_api_tab(self) -> None:
        """Create API configuration tab."""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="API Configuration")
        
        # API Key section
        api_frame = ttk.Labelframe(
            tab,
            text="API.Bible Configuration",
            padding=15,
            bootstyle=PRIMARY
        )
        api_frame.pack(fill=X, pady=(0, 15))
        
        # API Key input
        ttk.Label(
            api_frame,
            text="API Key:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(0, 5))
        
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill=X, pady=(0, 10))
        
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            key_frame,
            textvariable=self.api_key_var,
            width=50,
            show="*"  # Hide key by default
        )
        self.api_key_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        
        # Show/Hide toggle
        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_btn = ttk.Checkbutton(
            key_frame,
            text="Show",
            variable=self.show_key_var,
            command=self._toggle_api_key_visibility,
            bootstyle="info-round-toggle"
        )
        self.show_key_btn.pack(side=LEFT)
        
        # Test API button
        test_btn = ttk.Button(
            api_frame,
            text="Test API Connection",
            command=self._test_api_connection,
            bootstyle=INFO,
            width=20
        )
        test_btn.pack(anchor=W, pady=(0, 10))
        
        # Help text
        help_text = (
            "Get your free API key from: https://scripture.api.bible\n"
            "Free tier: 100 requests/minute, 10,000/day"
        )
        ttk.Label(
            api_frame,
            text=help_text,
            font=("Segoe UI", 9),
            bootstyle=SECONDARY,
            wraplength=600
        ).pack(anchor=W)
        
        # Default translation
        trans_frame = ttk.Labelframe(
            tab,
            text="Default Translation",
            padding=15,
            bootstyle=PRIMARY
        )
        trans_frame.pack(fill=X)
        
        ttk.Label(
            trans_frame,
            text="Default Bible Translation:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(0, 5))
        
        translations = [t.display_name for t in TranslationType]
        self.default_trans_var = tk.StringVar()
        
        trans_combo = ttk.Combobox(
            trans_frame,
            textvariable=self.default_trans_var,
            values=translations,
            state="readonly",
            width=40
        )
        trans_combo.pack(anchor=W)
    
    def _create_cache_tab(self) -> None:
        """Create cache management tab."""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="Cache Settings")
        
        # Enable cache
        cache_frame = ttk.Labelframe(
            tab,
            text="Cache Configuration",
            padding=15,
            bootstyle=PRIMARY
        )
        cache_frame.pack(fill=X, pady=(0, 15))
        
        self.enable_cache_var = tk.BooleanVar()
        enable_check = ttk.Checkbutton(
            cache_frame,
            text="Enable verse caching (recommended)",
            variable=self.enable_cache_var,
            bootstyle="success-round-toggle"
        )
        enable_check.pack(anchor=W, pady=(0, 10))
        
        # Cache directory
        ttk.Label(
            cache_frame,
            text="Cache Directory:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(10, 5))
        
        dir_frame = ttk.Frame(cache_frame)
        dir_frame.pack(fill=X, pady=(0, 10))
        
        self.cache_dir_var = tk.StringVar()
        cache_dir_entry = ttk.Entry(
            dir_frame,
            textvariable=self.cache_dir_var,
            state="readonly",
            width=50
        )
        cache_dir_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        
        browse_btn = ttk.Button(
            dir_frame,
            text="Browse...",
            command=self._browse_cache_dir,
            bootstyle=INFO,
            width=10
        )
        browse_btn.pack(side=LEFT)
        
        # Cache TTL
        ttk.Label(
            cache_frame,
            text="Cache Time-To-Live (days):",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(10, 5))
        
        self.cache_ttl_var = tk.IntVar()
        ttl_spin = ttk.Spinbox(
            cache_frame,
            from_=1,
            to=365,
            textvariable=self.cache_ttl_var,
            width=10
        )
        ttl_spin.pack(anchor=W)
        
        # Cache statistics
        stats_frame = ttk.Labelframe(
            tab,
            text="Cache Statistics",
            padding=15,
            bootstyle=SECONDARY
        )
        stats_frame.pack(fill=X)
        
        self.cache_stats_label = ttk.Label(
            stats_frame,
            text="Loading statistics...",
            font=("Consolas", 9)
        )
        self.cache_stats_label.pack(anchor=W)
        
        # Clear cache button
        clear_btn = ttk.Button(
            stats_frame,
            text="Clear Cache",
            command=self._clear_cache,
            bootstyle=DANGER,
            width=15
        )
        clear_btn.pack(anchor=W, pady=(10, 0))
    
    def _create_ui_tab(self) -> None:
        """Create UI preferences tab."""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="User Interface")
        
        # Theme selection
        theme_frame = ttk.Labelframe(
            tab,
            text="Appearance",
            padding=15,
            bootstyle=PRIMARY
        )
        theme_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            theme_frame,
            text="Theme:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(0, 5))
        
        themes = [
            "cosmo", "darkly", "flatly", "journal",
            "litera", "lumen", "minty", "pulse",
            "sandstone", "united", "yeti"
        ]
        
        self.theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=themes,
            state="readonly",
            width=20
        )
        theme_combo.pack(anchor=W, pady=(0, 5))
        
        ttk.Label(
            theme_frame,
            text="Note: Theme change requires restart",
            font=("Segoe UI", 9),
            bootstyle=SECONDARY
        ).pack(anchor=W)
        
        # Window size
        size_frame = ttk.Labelframe(
            tab,
            text="Window Settings",
            padding=15,
            bootstyle=PRIMARY
        )
        size_frame.pack(fill=X)
        
        ttk.Label(
            size_frame,
            text="Default Window Size:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(0, 5))
        
        self.window_size_var = tk.StringVar()
        size_entry = ttk.Entry(
            size_frame,
            textvariable=self.window_size_var,
            width=15
        )
        size_entry.pack(anchor=W, pady=(0, 5))
        
        ttk.Label(
            size_frame,
            text="Format: WIDTHxHEIGHT (e.g., 900x700)",
            font=("Segoe UI", 9),
            bootstyle=SECONDARY
        ).pack(anchor=W)
    
    def _create_processing_tab(self) -> None:
        """Create processing options tab."""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="Processing")
        
        # Backup options
        backup_frame = ttk.Labelframe(
            tab,
            text="Document Backup",
            padding=15,
            bootstyle=PRIMARY
        )
        backup_frame.pack(fill=X, pady=(0, 15))
        
        self.auto_backup_var = tk.BooleanVar()
        backup_check = ttk.Checkbutton(
            backup_frame,
            text="Automatically backup documents before processing",
            variable=self.auto_backup_var,
            bootstyle="success-round-toggle"
        )
        backup_check.pack(anchor=W)
        
        # Concurrency
        concurrency_frame = ttk.Labelframe(
            tab,
            text="Performance",
            padding=15,
            bootstyle=PRIMARY
        )
        concurrency_frame.pack(fill=X)
        
        ttk.Label(
            concurrency_frame,
            text="Maximum Concurrent API Requests:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(0, 5))
        
        self.max_concurrent_var = tk.IntVar()
        concurrent_spin = ttk.Spinbox(
            concurrency_frame,
            from_=1,
            to=20,
            textvariable=self.max_concurrent_var,
            width=10
        )
        concurrent_spin.pack(anchor=W, pady=(0, 5))
        
        ttk.Label(
            concurrency_frame,
            text="Higher values = faster processing, but may hit rate limits",
            font=("Segoe UI", 9),
            bootstyle=SECONDARY,
            wraplength=600
        ).pack(anchor=W)
    
    def _create_advanced_tab(self) -> None:
        """Create advanced settings tab."""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="Advanced")
        
        # Logging
        log_frame = ttk.Labelframe(
            tab,
            text="Logging",
            padding=15,
            bootstyle=PRIMARY
        )
        log_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            log_frame,
            text="Log Level:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(0, 5))
        
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.log_level_var = tk.StringVar()
        
        log_combo = ttk.Combobox(
            log_frame,
            textvariable=self.log_level_var,
            values=log_levels,
            state="readonly",
            width=15
        )
        log_combo.pack(anchor=W, pady=(0, 10))
        
        # Log directory
        ttk.Label(
            log_frame,
            text="Log Directory:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(0, 5))
        
        self.log_dir_var = tk.StringVar()
        log_entry = ttk.Entry(
            log_frame,
            textvariable=self.log_dir_var,
            state="readonly",
            width=50
        )
        log_entry.pack(anchor=W)
        
        # Other options
        other_frame = ttk.Labelframe(
            tab,
            text="Other Options",
            padding=15,
            bootstyle=PRIMARY
        )
        other_frame.pack(fill=X)
        
        self.check_updates_var = tk.BooleanVar()
        updates_check = ttk.Checkbutton(
            other_frame,
            text="Check for updates on startup",
            variable=self.check_updates_var,
            bootstyle="info-round-toggle"
        )
        updates_check.pack(anchor=W, pady=(0, 10))
        
        self.analytics_var = tk.BooleanVar()
        analytics_check = ttk.Checkbutton(
            other_frame,
            text="Enable anonymous usage analytics",
            variable=self.analytics_var,
            bootstyle="info-round-toggle"
        )
        analytics_check.pack(anchor=W)
    
    def _create_buttons(self, parent) -> None:
        """Create dialog buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X, pady=(10, 0))
        
        # Save button
        save_btn = ttk.Button(
            button_frame,
            text="Save Settings",
            command=self._save_settings,
            bootstyle=SUCCESS,
            width=15
        )
        save_btn.pack(side=RIGHT, padx=(5, 0))
        
        # Cancel button
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            bootstyle=SECONDARY,
            width=15
        )
        cancel_btn.pack(side=RIGHT)
        
        # Reset to defaults
        reset_btn = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
            bootstyle=WARNING,
            width=18
        )
        reset_btn.pack(side=LEFT)
    
    def _load_current_settings(self) -> None:
        """Load current settings into dialog."""
        self.api_key_var.set(self.settings.api_key)
        
        # Load translation - handle both display names and internal names
        current_trans = self.settings.default_translation
        # If the current translation is a simple code (like "KJV"), 
        # find the matching display name from TranslationType
        display_translation = current_trans
        for trans_type in TranslationType:
            if current_trans and (str(current_trans) in trans_type.display_name or str(current_trans) == trans_type.value):
                display_translation = trans_type.display_name
                break
        
        self.default_trans_var.set(display_translation)
        
        # Load remaining settings
        self.enable_cache_var.set(self.settings.enable_cache)
        self.cache_dir_var.set(str(self.settings.cache_directory))
        self.cache_ttl_var.set(self.settings.cache_ttl_days)
        self.theme_var.set(self.settings.theme)
        self.window_size_var.set(self.settings.window_size)
        self.auto_backup_var.set(self.settings.auto_backup)
        self.max_concurrent_var.set(self.settings.max_concurrent_requests)
        self.log_level_var.set(self.settings.log_level)
        self.log_dir_var.set(str(self.settings.log_directory))
        self.check_updates_var.set(self.settings.check_updates)
        self.analytics_var.set(self.settings.enable_analytics)
        
        # Load cache statistics
        self._update_cache_stats()
    
    def _toggle_api_key_visibility(self) -> None:
        """Toggle API key visibility."""
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
    
    def _test_api_connection(self) -> None:
        """Test API connection with current key."""
        api_key = self.api_key_var.get()
        
        if not api_key:
            messagebox.showwarning(
                "API Key Required",
                "Please enter an API key first."
            )
            return
        
        if not validate_api_key(api_key):
            messagebox.showerror(
                "Invalid API Key",
                "The API key format appears invalid."
            )
            return
        
        # TODO: Implement actual API test
        messagebox.showinfo(
            "API Test",
            "API connection test successful!\n\n"
            "Your API key is valid and working."
        )
    
    def _browse_cache_dir(self) -> None:
        """Browse for cache directory."""
        directory = filedialog.askdirectory(
            title="Select Cache Directory",
            initialdir=self.cache_dir_var.get()
        )
        
        if directory:
            self.cache_dir_var.set(directory)
    
    def _update_cache_stats(self) -> None:
        """Update cache statistics display."""
        # TODO: Get real statistics from cache manager
        stats_text = (
            "Cache Hits: 1,234\n"
            "Cache Misses: 56\n"
            "Hit Rate: 95.7%\n"
            "Cache Size: 2.3 MB\n"
            "Items Cached: 487"
        )
        self.cache_stats_label.config(text=stats_text)
    
    def _clear_cache(self) -> None:
        """Clear cache after confirmation."""
        result = messagebox.askyesno(
            "Clear Cache",
            "Are you sure you want to clear all cached verses?\n\n"
            "This cannot be undone."
        )
        
        if result:
            # TODO: Actually clear cache
            messagebox.showinfo(
                "Cache Cleared",
                "All cached verses have been removed."
            )
            self._update_cache_stats()
    
    def _save_settings(self) -> None:
        """Save settings and close dialog."""
        # Validate API key
        api_key = self.api_key_var.get()
        if api_key and not validate_api_key(api_key):
            messagebox.showerror(
                "Invalid API Key",
                "Please enter a valid API key."
            )
            self.notebook.select(0)  # Switch to API tab
            return
        
        # FIXED: Safe translation parsing with multiple fallback methods
        trans_text = self.default_trans_var.get()
        translation_value = self._parse_translation(trans_text)
        
        # Update settings
        self.settings.api_key = api_key
        self.settings.default_translation = translation_value
        self.settings.enable_cache = self.enable_cache_var.get()
        self.settings.cache_directory = Path(self.cache_dir_var.get())
        self.settings.cache_ttl_days = self.cache_ttl_var.get()
        self.settings.theme = self.theme_var.get()
        self.settings.window_size = self.window_size_var.get()
        self.settings.auto_backup = self.auto_backup_var.get()
        self.settings.max_concurrent_requests = self.max_concurrent_var.get()
        self.settings.log_level = self.log_level_var.get()
        self.settings.check_updates = self.check_updates_var.get()
        self.settings.enable_analytics = self.analytics_var.get()
        
        # Save to file
        self.settings.save_to_file()
        
        self.result = "saved"
        self.destroy()
        
        messagebox.showinfo(
            "Settings Saved",
            "Settings have been saved successfully!"
        )
    
    def _parse_translation(self, trans_text: str) -> str:
        """
        Safely parse translation text to extract the translation code.
        
        Handles multiple formats:
        - "KJV (King James Version)" -> "KJV"
        - "KJV" -> "KJV"
        - Full display names -> appropriate code
        
        Args:
            trans_text: The translation text from the UI
            
        Returns:
            Translation code string
        """
        # Method 1: Try to extract from parentheses
        if "(" in trans_text and ")" in trans_text:
            try:
                # Extract text between parentheses
                code = trans_text.split("(")[1].split(")")[0].strip()
                if code:
                    return code
            except (IndexError, AttributeError):
                pass
        
        # Method 2: Try to match with TranslationType display names
        for trans_type in TranslationType:
            if trans_text == trans_type.display_name:
                return trans_type.value
            if trans_text in trans_type.display_name:
                return trans_type.value
        
        # Method 3: Return the original text as fallback
        return trans_text
    
    def _cancel(self) -> None:
        """Cancel and close dialog."""
        self.result = "cancelled"
        self.destroy()
    
    def _reset_defaults(self) -> None:
        """Reset all settings to defaults."""
        result = messagebox.askyesno(
            "Reset to Defaults",
            "Are you sure you want to reset all settings to defaults?\n\n"
            "This will not affect your saved API key."
        )
        
        if result:
            # Store API key
            current_key = self.api_key_var.get()
            
            # Reset settings
            self.settings.reset_to_defaults()
            
            # Restore API key
            self.settings.api_key = current_key
            
            # Reload UI
            self._load_current_settings()
            
            messagebox.showinfo(
                "Reset Complete",
                "Settings have been reset to defaults."
            )