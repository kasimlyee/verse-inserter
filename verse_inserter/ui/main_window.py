from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import ttkbootstrap as ttk  # type: ignore
except ImportError:
    import tkinter.ttk as ttk  # type: ignore

from ..api.bible_api_client import BibleAPIClient
from ..config.settings import Settings
from ..core.cache_manager import CacheManager
from ..core.document_processor import DocumentProcessor
from ..core.placeholder_parser import PlaceholderParser
from ..models.verse import TranslationType
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(ttk.Window if hasattr(ttk, "Window") else tk.Tk):
    """Main application window for VerseInserter."""

    APP_TITLE = "VerseInserter - Automated Scripture Insertion"
    APP_VERSION = "1.0.0"
    WINDOW_SIZE = "900x700"

    def __init__(self, settings: Settings) -> None:
        if hasattr(ttk, "Window"):
            # If ttkbootstrap is present, prefer themed window
            try:
                super().__init__(themename="cosmo")
            except Exception as e:
                logger.warning(f"ttkbootstrap theme failed: {e}, using default")
                super().__init__()
        else:
            super().__init__()

        self.settings = settings
        self.selected_file: Optional[Path] = None
        self.is_processing = False

        # Core components
        self.document_processor = DocumentProcessor()
        self.cache_manager = CacheManager()
        self.placeholder_parser = PlaceholderParser()

        # Executor for background work
        self.executor = ThreadPoolExecutor(max_workers=4)

        # UI state vars (created in _create_widgets)
        self.file_path_var: tk.StringVar
        self.translation_var: tk.StringVar
        self.progress_var: tk.DoubleVar
        self.status_var: tk.StringVar
        self.status_bar_var: tk.StringVar
        self.stats_labels: Dict[str, tk.StringVar]
        self.log_text: tk.Text

        self._setup_window()
        self._create_widgets()
        self._setup_bindings()

        # Check API key shortly after startup
        self.after(500, self._check_api_key_on_startup)

        logger.info("Main window initialized")

    def _setup_window(self) -> None:
        self.title(self.APP_TITLE)
        self.geometry(self.WINDOW_SIZE)

        # center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.minsize(800, 600)

    def _create_widgets(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=tk.YES)

        # header
        self._create_header(main_frame)

        # control buttons
        self._create_control_buttons(main_frame)

        # file selection
        self._create_file_section(main_frame)

        # translation selection
        self._create_translation_section(main_frame)

        # progress / stats
        self._create_progress_section(main_frame)

        # activity log
        self._create_log_section(main_frame)

        # bottom status bar
        self._create_status_bar()

    def _create_header(self, parent: ttk.Frame) -> None:
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(header_frame, text="VerseInserter", font=("Segoe UI", 24, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Inserting Scripture Seamlessly into Your Words.", font=("Segoe UI", 10)).pack(anchor=tk.W)
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

    def _create_file_section(self, parent: ttk.Frame) -> None:
        file_frame = ttk.LabelFrame(parent, text="📄 Document Selection", padding=15)
        file_frame.pack(fill=tk.X, pady=(0, 15))

        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(path_frame, text="Selected File:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.file_path_var = tk.StringVar(value="No file selected")
        self.file_path_label = ttk.Label(path_frame, textvariable=self.file_path_var, font=("Segoe UI", 9))
        self.file_path_label.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)

        self.browse_button = ttk.Button(file_frame, text="📁 Browse for Document...", command=self._browse_file, width=25)
        self.browse_button.pack(anchor=tk.W)

    def _create_translation_section(self, parent: ttk.Frame) -> None:
        trans_frame = ttk.LabelFrame(parent, text="📖 Translation Settings", padding=15)
        trans_frame.pack(fill=tk.X, pady=(0, 15))

        trans_inner = ttk.Frame(trans_frame)
        trans_inner.pack(fill=tk.X)

        ttk.Label(trans_inner, text="Bible Translation:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 15))

        translations = [t.display_name for t in TranslationType]
        default = translations[0] if translations else "KJV"
        self.translation_var = tk.StringVar(value=default)

        translation_combo = ttk.Combobox(trans_inner, textvariable=self.translation_var, values=translations, state="readonly", width=35)
        translation_combo.pack(side=tk.LEFT)

    def _create_progress_section(self, parent: ttk.Frame) -> None:
        progress_frame = ttk.LabelFrame(parent, text="⏳ Processing Progress", padding=15)
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        self.status_var = tk.StringVar(value="Ready to process")
        ttk.Label(progress_frame, textvariable=self.status_var, font=("Segoe UI", 9)).pack(anchor=tk.W)

        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))

        self.stats_labels = {}
        stats_items = [("Placeholders Found:", "found"), ("Successfully Replaced:", "replaced"), ("Failed:", "failed")]
        for idx, (label_text, key) in enumerate(stats_items):
            frame = ttk.Frame(stats_frame)
            frame.pack(side=tk.LEFT, padx=(0, 20) if idx < len(stats_items) - 1 else 0)
            ttk.Label(frame, text=label_text, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
            var = tk.StringVar(value="0")
            self.stats_labels[key] = var
            ttk.Label(frame, textvariable=var, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

    def _create_log_section(self, parent: ttk.Frame) -> None:
        log_frame = ttk.LabelFrame(parent, text="📋 Activity Log", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=tk.YES, pady=(0, 15))

        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=tk.YES)

        scrollbar = ttk.Scrollbar(log_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_container,
            height=10,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#212529",
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        scrollbar.config(command=self.log_text.yview)

        # make read-only
        self.log_text.bind("<Key>", lambda e: "break")

    def _create_control_buttons(self, parent: ttk.Frame) -> None:
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)

        self.process_button = ttk.Button(left_buttons, text="▶ Start Processing", command=self._process_document, width=20)
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(left_buttons, text="⏹ Stop", command=self._stop_processing, width=12, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        clear_button = ttk.Button(left_buttons, text="🗑 Clear Log", command=self._clear_log, width=12)
        clear_button.pack(side=tk.LEFT)

        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)

        about_button = ttk.Button(right_buttons, text="ℹ About", command=self._show_about, width=12)
        about_button.pack(side=tk.RIGHT, padx=(10, 0))

        settings_button = ttk.Button(right_buttons, text="⚙ Settings", command=self._show_settings, width=12)
        settings_button.pack(side=tk.RIGHT)

        help_button = ttk.Button(right_buttons, text="❓ Help", command=self._show_help, width=12)
        help_button.pack(side=tk.RIGHT, padx=(0, 10))

    def _create_status_bar(self) -> None:
        status_frame = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_bar_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_bar_var, font=("Segoe UI", 8), padding=5).pack(side=tk.LEFT)
        ttk.Label(status_frame, text=f"Version {self.APP_VERSION}", font=("Segoe UI", 8), padding=5).pack(side=tk.RIGHT)

    def _setup_bindings(self) -> None:
        self.bind("<Control-o>", lambda e: self._browse_file())
        self.bind("<Control-p>", lambda e: self._process_document())
        self.bind("<F1>", lambda e: self._show_help())

    def _browse_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select Word Document",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")],
            initialdir=Path.home() / "Documents",
        )
        if filename:
            self.selected_file = Path(filename)
            self.file_path_var.set(str(self.selected_file))
            self._log_message(f"✓ Selected file: {self.selected_file.name}")
            self.status_bar_var.set(f"File loaded: {self.selected_file.name}")

    def _process_document(self) -> None:
        if not self.selected_file:
            messagebox.showwarning("No File Selected", "Please select a Word document first.")
            return

        if self.is_processing:
            messagebox.showinfo("Processing in Progress", "A document is already being processed.")
            return

        if not self.settings.api_key:
            messagebox.showerror("API Key Required", "Please configure your API.Bible key in Settings.")
            self._show_settings()
            return

        self.is_processing = True
        self.process_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self._reset_progress()

        # run heavy work in background
        self.executor.submit(self._process_document_async)

    def _stop_processing(self) -> None:
        if self.is_processing:
            self.is_processing = False
            self.after(0, lambda: self._log_message("⚠ Processing stopped by user"))
            self.after(0, lambda: self.status_var.set("Processing stopped"))

    def _process_document_async(self) -> None:
        try:
            self._log_message("=" * 50)
            self._log_message("▶ Starting document processing...")

            trans_text = self.translation_var.get()
            translation = self._parse_translation(trans_text)
            self._log_message(f"📖 Using translation: {translation.display_name}")

            self._update_status("Loading document...")
            with self.document_processor.load_document(self.selected_file) as doc:
                self._update_status("Scanning for placeholders...")
                self.document_processor.set_progress_callback(self._progress_callback)

                placeholders = self.document_processor.find_all_placeholders(doc, translation=translation)

                if not placeholders:
                    self.after(0, lambda: messagebox.showinfo("No Placeholders", "No scripture placeholders found in document."))
                    return

                self._update_stats("found", len(placeholders))
                self._log_message(f"✓ Found {len(placeholders)} placeholders")

                self._update_status("Fetching verses from API...")
                verses = self._fetch_verses_async(placeholders, translation)

                self._update_status("Replacing placeholders...")
                result = self.document_processor.replace_placeholders(doc, verses)

                self._update_stats("replaced", result.placeholders_replaced)
                self._update_stats("failed", result.placeholders_failed)

                self._update_status("Saving document...")
                output_path = self.document_processor.generate_output_filename(self.selected_file)
                try:
                    self.document_processor.save_document(doc, output_path, overwrite=True)
                except Exception:
                    timestamp = int(time.time())
                    unique_output_path = output_path.parent / f"{output_path.stem}_{timestamp}{output_path.suffix}"
                    self.document_processor.save_document(doc, unique_output_path)
                    output_path = unique_output_path

                self._log_message(f"✅ Document saved: {output_path}")

                self.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Success!",
                        f"Document processed successfully!\n\nOutput: {output_path.name}\nReplaced: {result.placeholders_replaced}/{result.placeholders_found}",
                    ),
                )

        except Exception as exc:
            logger.exception("Processing error")
            self._log_message(f"✗ ERROR: {exc}")
            err = f"An error occurred:\n\n{str(exc)}"
            self.after(0, lambda msg=err: messagebox.showerror("Processing Failed", msg))

        finally:
            self.is_processing = False
            self.after(0, lambda: self.process_button.config(state=tk.NORMAL))
            self.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self._update_status("Ready")

    def _parse_translation(self, trans_text: str) -> TranslationType:
        try:
            return TranslationType.from_display_name(trans_text)
        except Exception:
            try:
                # try to extract code in parentheses
                if "(" in trans_text and ")" in trans_text:
                    code = trans_text.split("(")[1].split(")")[0].strip()
                    if code in TranslationType.__members__:
                        return TranslationType[code]
                clean_name = trans_text.upper().replace(" ", "").replace("(", "").replace(")", "")
                if clean_name in TranslationType.__members__:
                    return TranslationType[clean_name]
            except Exception:
                pass
        logger.warning(f"Could not parse translation: {trans_text}, using KJV")
        return TranslationType.KJV

    def _fetch_verses_async(self, placeholders: Iterable[Any], translation: TranslationType) -> Dict[str, Any]:
        """Fetch verses from API with fallback support."""
        verses_dict: Dict[str, Any] = {}
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
        try:
            async def fetch_all() -> None:
                async with BibleAPIClient(self.settings.api_key) as client:
                    unique_refs = self.placeholder_parser.extract_unique_references(placeholders)
                    total = len(unique_refs) or 1
                    
                    self._log_message(f"📡 Fetching {len(unique_refs)} verses (with fallback)...")
                    
                    for idx, ref in enumerate(unique_refs):
                        if not self.is_processing:
                            break
                        
                        # Check cache first
                        cached = self.cache_manager.get(ref)
                        if cached:
                            verses_dict[ref.canonical_reference] = cached
                            self._log_message(f"💾 Cache hit: {ref.canonical_reference}")
                        else:
                            try:
                                self._log_message(f"⬇️ Fetching: {ref.canonical_reference}")
                                
                                # Use the new method with automatic fallback
                                verse = await client.fetch_verse_with_fallback(ref)
                                
                                if verse and getattr(verse, "text", None):
                                    verses_dict[ref.canonical_reference] = verse
                                    self.cache_manager.set(ref, verse)
                                    
                                    # Indicate if we used fallback
                                    source = "free API" if "fallback" in getattr(verse, "source_api", "") else "API.Bible"
                                    self._log_message(f"✅ Fetched via {source}: {ref.canonical_reference}")
                                else:
                                    self._log_message(f"❌ Both APIs failed for: {ref.canonical_reference}")
                                    
                            except Exception as e:
                                error_msg = f"❌ Complete failure for {ref.canonical_reference}: {str(e)}"
                                self._log_message(error_msg)
                                logger.error(error_msg)
    
                        # Update progress
                        progress = (idx + 1) / total * 50 + 50
                        self.after(0, lambda p=progress: self.progress_var.set(p))
                        self.after(0, lambda i=idx, t=total: self.status_var.set(f"Fetching verses... {i + 1}/{t}"))
    
            loop.run_until_complete(fetch_all())
            
        except Exception as e:
            logger.exception("API fetch error")
            self._log_message(f"❌ API fetch error: {e}")
        finally:
            try:
                loop.close()
            except Exception:
                pass
    
        success_count = len([v for v in verses_dict.values() if v and getattr(v, 'text', None)])
        self._log_message(f"📊 Successfully retrieved {success_count}/{len(unique_refs)} verses")
        return verses_dict

    def _progress_callback(self, current: int, total: int, message: str) -> None:
        progress = (current / total * 50) if total > 0 else 0
        self.after(0, lambda p=progress: self.progress_var.set(p))
        self.after(0, lambda: self.status_var.set(message))

    def _update_status(self, message: str) -> None:
        self.after(0, lambda: self.status_var.set(message))
        self.after(0, lambda: self._log_message(message))

    def _update_stats(self, key: str, value: int) -> None:
        if key in self.stats_labels:
            self.after(0, lambda: self.stats_labels[key].set(str(value)))

    def _log_message(self, message: str) -> None:
        def add_to_log() -> None:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        self.after(0, add_to_log)

    def _clear_log(self) -> None:
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._log_message("🗑 Log cleared")

    def _reset_progress(self) -> None:
        self.progress_var.set(0)
        self.status_var.set("Processing...")
        for key in self.stats_labels:
            self.stats_labels[key].set("0")

    def _show_settings(self) -> None:
        from .widgets.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self, self.settings)
        self.wait_window(dialog)
        if getattr(dialog, "result", None) == "saved":
            logger.info("Settings updated")

    def _show_help(self) -> None:
        help_text = """VerseInserter - Quick Help

HOW TO USE:
1. Click "⚙ Settings" to configure your API key
2. Click "📁 Browse" to select a Word file  
3. Add placeholders: {{John 3:16}}
4. Select Bible translation
5. Click "▶ Start Processing"

PLACEHOLDERS:
• {{John 3:16}}
• {{Psalm 23:1-3}}
• {{1 Corinthians 13:4}}

GET API KEY:
https://scripture.api.bible (free)

SUPPORT:
Email: lyee@codewithlyee.com
Phone: +256701521269
"""
        messagebox.showinfo("Help", help_text)

    def _show_about(self) -> None:
        about_text = f"""VerseInserter v{self.APP_VERSION}\n\nAutomated Scripture Insertion\n\nDeveloper: Kasim Lyee\nEmail: lyee@codewithlyee.com\nPhone: +256701521269\nWebsite: www.portfolio.codewithlyee.com\n\nOrganization: Softlite Inc.\n© 2025 All Rights Reserved\n\n"Inserting Scripture Seamlessly into Your Words."""
        messagebox.showinfo("About", about_text)

    def _check_api_key_on_startup(self) -> None:
        if not self.settings.api_key:
            result = messagebox.askyesno(
                "API Key Required",
                "No API key configured!\n\nGet free key at: https://scripture.api.bible\n\nConfigure now?",
                icon="warning",
            )
            if result:
                self._show_settings()
            else:
                self._log_message("⚠ Warning: No API key. Set it in Settings.")
                self.status_bar_var.set("⚠ API key required")

    def destroy(self) -> None:
        """Ensure executor is shut down on window close."""
        try:
            self.executor.shutdown(wait=False)
        except Exception:
            logger.exception("Error shutting down executor")
        super().destroy()
