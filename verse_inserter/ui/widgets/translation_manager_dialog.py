"""
Translation management dialog for offline Bible database.

Provides UI for viewing, downloading, and managing Bible translations.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import asyncio

from verse_inserter.core.offline_database import OfflineBibleDatabase, TranslationInfo
from verse_inserter.models.verse import TranslationType
from verse_inserter.api.bible_api_client import BibleAPIClient
from verse_inserter.core.translation_downloader import TranslationDownloader, DownloadProgress


class TranslationManagerDialog(tk.Toplevel):
    """
    Dialog for managing Bible translations.

    Features:
    - View downloaded translations
    - Download new translations
    - Delete translations
    - View translation statistics
    """

    # Available translations for download
    AVAILABLE_TRANSLATIONS = [
        (TranslationType.KJV, "King James Version", "Classic English translation"),
        (TranslationType.NIV, "New International Version", "Modern English translation"),
        (TranslationType.ESV, "English Standard Version", "Literal translation"),
        (TranslationType.NKJV, "New King James Version", "Updated KJV"),
        (TranslationType.NLT, "New Living Translation", "Thought-for-thought translation"),
    ]

    def __init__(self, parent, api_client: BibleAPIClient, offline_db: Optional[OfflineBibleDatabase] = None):
        """
        Initialize translation manager dialog.

        Args:
            parent: Parent window
            api_client: Bible API client for downloading
            offline_db: Offline database (defaults to new instance)
        """
        super().__init__(parent)

        self.api_client = api_client
        self.offline_db = offline_db or OfflineBibleDatabase()

        self.title("Manage Bible Translations")
        self.geometry("900x600")
        self.resizable(True, True)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._load_translations()
        self._center_window()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Main container
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Translation Manager",
            font=("Segoe UI", 16, "bold"),
        )
        title_label.pack(pady=(0, 15))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Downloaded translations tab
        self.downloaded_frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.downloaded_frame, text="📥 Downloaded")
        self._create_downloaded_tab()

        # Available translations tab
        self.available_frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.available_frame, text="📚 Available")
        self._create_available_tab()

        # Statistics tab
        self.stats_frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.stats_frame, text="📊 Statistics")
        self._create_statistics_tab()

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(
            button_frame,
            text="Refresh",
            command=self._refresh,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Close",
            command=self._close,
        ).pack(side=tk.RIGHT)

    def _create_downloaded_tab(self):
        """Create downloaded translations tab."""
        # Info label
        ttk.Label(
            self.downloaded_frame,
            text="Translations downloaded for offline use",
            font=("Segoe UI", 10),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Treeview for downloaded translations
        columns = ("name", "language", "verses", "size", "date")
        self.downloaded_tree = ttk.Treeview(
            self.downloaded_frame,
            columns=columns,
            show="headings",
            height=12,
        )

        self.downloaded_tree.heading("name", text="Translation")
        self.downloaded_tree.heading("language", text="Language")
        self.downloaded_tree.heading("verses", text="Verses")
        self.downloaded_tree.heading("size", text="Storage")
        self.downloaded_tree.heading("date", text="Downloaded")

        self.downloaded_tree.column("name", width=250)
        self.downloaded_tree.column("language", width=100)
        self.downloaded_tree.column("verses", width=100, anchor=tk.CENTER)
        self.downloaded_tree.column("size", width=100, anchor=tk.CENTER)
        self.downloaded_tree.column("date", width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.downloaded_frame,
            orient=tk.VERTICAL,
            command=self.downloaded_tree.yview,
        )
        self.downloaded_tree.configure(yscrollcommand=scrollbar.set)

        self.downloaded_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_frame = ttk.Frame(self.downloaded_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="🗑 Delete Selected",
            command=self._delete_translation,
        ).pack(side=tk.LEFT)

    def _create_available_tab(self):
        """Create available translations tab."""
        # Info label
        ttk.Label(
            self.available_frame,
            text="Available translations for download",
            font=("Segoe UI", 10),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Treeview for available translations
        columns = ("name", "description", "status")
        self.available_tree = ttk.Treeview(
            self.available_frame,
            columns=columns,
            show="headings",
            height=12,
        )

        self.available_tree.heading("name", text="Translation")
        self.available_tree.heading("description", text="Description")
        self.available_tree.heading("status", text="Status")

        self.available_tree.column("name", width=250)
        self.available_tree.column("description", width=400)
        self.available_tree.column("status", width=150, anchor=tk.CENTER)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.available_frame,
            orient=tk.VERTICAL,
            command=self.available_tree.yview,
        )
        self.available_tree.configure(yscrollcommand=scrollbar.set)

        self.available_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_frame = ttk.Frame(self.available_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="⬇ Download Selected",
            command=self._download_translation,
            style="Accent.TButton",
        ).pack(side=tk.LEFT)

    def _create_statistics_tab(self):
        """Create statistics tab."""
        stats_container = ttk.Frame(self.stats_frame)
        stats_container.pack(fill=tk.BOTH, expand=True, pady=20, padx=20)

        # Create stats display
        self.stats_labels = {}

        stats = [
            ("total_translations", "Total Translations:"),
            ("total_verses", "Total Verses:"),
            ("database_size", "Database Size:"),
            ("database_path", "Database Location:"),
        ]

        for key, label_text in stats:
            frame = ttk.Frame(stats_container)
            frame.pack(fill=tk.X, pady=10)

            ttk.Label(
                frame,
                text=label_text,
                font=("Segoe UI", 11, "bold"),
            ).pack(side=tk.LEFT, padx=(0, 10))

            var = tk.StringVar(value="—")
            self.stats_labels[key] = var

            ttk.Label(
                frame,
                textvariable=var,
                font=("Segoe UI", 11),
            ).pack(side=tk.LEFT)

    def _center_window(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        parent = self.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _load_translations(self):
        """Load and display translations."""
        # Load downloaded translations
        self.downloaded_tree.delete(*self.downloaded_tree.get_children())

        downloaded = self.offline_db.get_all_translations()
        for trans_info in downloaded:
            # Format size
            size_mb = trans_info.verse_count * 100 / (1024 * 1024)  # Rough estimate
            size_str = f"{size_mb:.1f} MB"

            # Format date
            date_str = trans_info.download_date.strftime("%Y-%m-%d %H:%M") if trans_info.download_date else "—"

            self.downloaded_tree.insert(
                "",
                tk.END,
                values=(
                    trans_info.name,
                    trans_info.language,
                    f"{trans_info.verse_count:,}",
                    size_str,
                    date_str,
                ),
                tags=(trans_info.abbreviation,),
            )

        # Load available translations
        self.available_tree.delete(*self.available_tree.get_children())

        downloaded_abbrs = {t.abbreviation for t in downloaded}

        for trans_type, name, description in self.AVAILABLE_TRANSLATIONS:
            if trans_type.name in downloaded_abbrs:
                status = "✓ Downloaded"
            else:
                status = "Not Downloaded"

            self.available_tree.insert(
                "",
                tk.END,
                values=(name, description, status),
                tags=(trans_type.name,),
            )

        # Update statistics
        self._update_statistics()

    def _update_statistics(self):
        """Update statistics display."""
        stats = self.offline_db.get_statistics()

        self.stats_labels["total_translations"].set(str(stats["translation_count"]))
        self.stats_labels["total_verses"].set(f"{stats['verse_count']:,}")
        self.stats_labels["database_size"].set(f"{stats['database_size_mb']} MB")
        self.stats_labels["database_path"].set(stats["database_path"])

    def _delete_translation(self):
        """Delete selected translation."""
        selection = self.downloaded_tree.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Please select a translation to delete.",
                parent=self,
            )
            return

        item = self.downloaded_tree.item(selection[0])
        trans_name = item["values"][0]
        trans_abbr = item["tags"][0]

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete {trans_name}?\n\nThis will remove all downloaded verses for this translation.",
            parent=self,
        ):
            return

        try:
            # Get translation type from abbreviation
            trans_type = TranslationType[trans_abbr]

            # Delete from database
            self.offline_db.delete_translation(trans_type)

            messagebox.showinfo(
                "Success",
                f"{trans_name} has been deleted.",
                parent=self,
            )

            self._refresh()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to delete translation:\n\n{str(e)}",
                parent=self,
            )

    def _download_translation(self):
        """Download selected translation."""
        selection = self.available_tree.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Please select a translation to download.",
                parent=self,
            )
            return

        item = self.available_tree.item(selection[0])
        trans_name = item["values"][0]
        trans_abbr = item["tags"][0]
        status = item["values"][2]

        if "Downloaded" in status:
            messagebox.showinfo(
                "Already Downloaded",
                f"{trans_name} is already downloaded.",
                parent=self,
            )
            return

        # Get translation type
        trans_type = TranslationType[trans_abbr]

        # Open download progress dialog
        from .download_progress_dialog import DownloadProgressDialog

        dialog = DownloadProgressDialog(
            parent=self,
            api_client=self.api_client,
            offline_db=self.offline_db,
            translation=trans_type,
            translation_name=trans_name,
        )

        self.wait_window(dialog)

        # Refresh after download
        self._refresh()

    def _refresh(self):
        """Refresh all data."""
        self._load_translations()

    def _close(self):
        """Close dialog."""
        self.grab_release()
        self.destroy()
