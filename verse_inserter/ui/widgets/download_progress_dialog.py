"""
Download progress dialog for Bible translations.

Shows real-time progress when downloading complete Bible translations.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio

from verse_inserter.core.offline_database import OfflineBibleDatabase
from verse_inserter.core.translation_downloader import (
    TranslationDownloader,
    DownloadProgress,
)
from verse_inserter.api.bible_api_client import BibleAPIClient
from verse_inserter.models.verse import TranslationType


class DownloadProgressDialog(tk.Toplevel):
    """
    Dialog for downloading Bible translations with progress tracking.

    Features:
    - Real-time progress bar
    - Current book/chapter display
    - Verse count tracking
    - Cancellation support
    - Status messages
    """

    def __init__(
        self,
        parent,
        api_client: BibleAPIClient,
        offline_db: OfflineBibleDatabase,
        translation: TranslationType,
        translation_name: str,
    ):
        """
        Initialize download progress dialog.

        Args:
            parent: Parent window
            api_client: Bible API client
            offline_db: Offline database
            translation: Translation to download
            translation_name: Human-readable translation name
        """
        super().__init__(parent)

        self.api_client = api_client
        self.offline_db = offline_db
        self.translation = translation
        self.translation_name = translation_name

        self.downloader: Optional[TranslationDownloader] = None
        self.download_task = None
        self.cancelled = False
        self.completed = False

        self.title(f"Downloading {translation_name}")
        self.geometry("600x400")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Prevent closing during download
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_widgets()
        self._center_window()

        # Start download
        self.after(100, self._start_download)

    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame,
            text=f"Downloading {self.translation_name}",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(0, 10))

        # Info text
        info_text = (
            "This will download the entire Bible translation for offline use.\n"
            "This may take several minutes depending on your internet speed."
        )
        ttk.Label(
            main_frame,
            text=info_text,
            font=("Segoe UI", 9),
            foreground="gray",
            wraplength=550,
        ).pack(pady=(0, 20))

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=15)
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Current status
        self.status_var = tk.StringVar(value="Initializing...")
        ttk.Label(
            progress_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=550,
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # Statistics frame
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X)

        # Current book/chapter
        left_stats = ttk.Frame(stats_frame)
        left_stats.pack(side=tk.LEFT)

        ttk.Label(
            left_stats,
            text="Current:",
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.current_var = tk.StringVar(value="—")
        ttk.Label(
            left_stats,
            textvariable=self.current_var,
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        # Verses downloaded
        right_stats = ttk.Frame(stats_frame)
        right_stats.pack(side=tk.RIGHT)

        ttk.Label(
            right_stats,
            text="Verses:",
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.verses_var = tk.StringVar(value="0")
        ttk.Label(
            right_stats,
            textvariable=self.verses_var,
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        # Detailed log
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Log text area
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_container,
            height=6,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 8),
            bg="#f8f9fa",
            fg="#212529",
            state=tk.DISABLED,
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_download,
        )
        self.cancel_btn.pack(side=tk.RIGHT)

        self.close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=self._close,
            state=tk.DISABLED,
        )
        self.close_btn.pack(side=tk.RIGHT, padx=(0, 5))

    def _center_window(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        parent = self.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _log_message(self, message: str):
        """Add message to log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _start_download(self):
        """Start the download process."""
        self._log_message(f"Starting download of {self.translation_name}...")

        # Create downloader
        self.downloader = TranslationDownloader(
            api_client=self.api_client,
            database=self.offline_db,
            progress_callback=self._on_progress,
        )

        # Start download task
        self.download_task = asyncio.create_task(
            self._run_download()
        )

    async def _run_download(self):
        """Run the download asynchronously."""
        try:
            success = await self.downloader.download_translation(
                translation=self.translation
            )

            if success:
                self._on_download_complete()
            elif self.cancelled:
                self._on_download_cancelled()
            else:
                self._on_download_failed("Download failed")

        except Exception as e:
            self._on_download_failed(str(e))

    def _on_progress(self, progress: DownloadProgress):
        """Handle progress update."""
        # Update status
        if progress.status == "downloading":
            status = f"Downloading {progress.current_book} {progress.current_chapter}..."
            self.status_var.set(status)

            # Update current
            current = f"{progress.current_book} {progress.current_chapter}"
            self.current_var.set(current)

            # Update verses
            self.verses_var.set(f"{progress.verses_downloaded:,}")

            # Update progress bar
            self.progress_var.set(progress.progress_percentage)

            # Log every 10 chapters
            if progress.current_chapter % 10 == 0:
                self._log_message(
                    f"  {progress.current_book} {progress.current_chapter} "
                    f"({progress.verses_downloaded:,} verses)"
                )

        elif progress.status == "completed":
            self.status_var.set("Download complete!")
            self.progress_var.set(100)
            self.verses_var.set(f"{progress.verses_downloaded:,}")

        elif progress.status == "failed":
            self.status_var.set(f"Failed: {progress.error_message}")

        elif progress.status == "cancelled":
            self.status_var.set("Download cancelled")

    def _on_download_complete(self):
        """Handle download completion."""
        self.completed = True
        self._log_message("✓ Download completed successfully!")

        self.cancel_btn.config(state=tk.DISABLED)
        self.close_btn.config(state=tk.NORMAL)

        messagebox.showinfo(
            "Download Complete",
            f"{self.translation_name} has been downloaded successfully!\n\n"
            f"You can now use this translation offline.",
            parent=self,
        )

    def _on_download_cancelled(self):
        """Handle download cancellation."""
        self._log_message("Download cancelled by user")
        self.cancel_btn.config(state=tk.DISABLED)
        self.close_btn.config(state=tk.NORMAL)

    def _on_download_failed(self, error: str):
        """Handle download failure."""
        self._log_message(f"✗ Download failed: {error}")

        self.cancel_btn.config(state=tk.DISABLED)
        self.close_btn.config(state=tk.NORMAL)

        messagebox.showerror(
            "Download Failed",
            f"Failed to download {self.translation_name}:\n\n{error}",
            parent=self,
        )

    def _cancel_download(self):
        """Cancel the download."""
        if not messagebox.askyesno(
            "Cancel Download",
            "Are you sure you want to cancel the download?",
            parent=self,
        ):
            return

        self.cancelled = True

        if self.downloader:
            self.downloader.cancel()
            self._log_message("Cancelling download...")

        self.status_var.set("Cancelling...")
        self.cancel_btn.config(state=tk.DISABLED)

    def _on_close(self):
        """Handle window close."""
        if not self.completed and not self.cancelled:
            self._cancel_download()
        else:
            self._close()

    def _close(self):
        """Close the dialog."""
        self.grab_release()
        self.destroy()
