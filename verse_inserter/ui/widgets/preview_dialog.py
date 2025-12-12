"""
Preview dialog for verse replacements.

Shows users what placeholders will be replaced with before processing,
allowing selective acceptance or rejection of replacements.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Optional, Set

try:
    import ttkbootstrap as ttk
except ImportError:
    import tkinter.ttk as ttk

from ...models.verse import Verse, Placeholder


class PreviewDialog(tk.Toplevel):
    """
    Dialog for previewing verse replacements before processing.

    Displays a table of placeholders and their replacement verses,
    allowing users to selectively approve or reject individual replacements.
    """

    def __init__(
        self,
        parent: tk.Widget,
        placeholders: List[Placeholder],
        verses: Dict[str, Verse],
        title: str = "Preview Verse Replacements"
    ):
        """
        Initialize preview dialog.

        Args:
            parent: Parent window
            placeholders: List of placeholders found in document
            verses: Dictionary mapping verse references to Verse objects
            title: Dialog window title
        """
        super().__init__(parent)

        self.title(title)
        self.geometry("1000x700")
        self.transient(parent)
        self.grab_set()

        # Data
        self.placeholders = placeholders
        self.verses = verses
        self.selected_replacements: Set[str] = set()  # Track selected items

        # Result
        self.result: Optional[str] = None  # "proceed", "cancel", or None

        # Center window
        self._center_window()

        # Create UI
        self._create_widgets()

        # Select all by default
        self._select_all()

    def _center_window(self) -> None:
        """Center dialog on parent window."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        # Header
        self._create_header()

        # Preview table
        self._create_preview_table()

        # Summary
        self._create_summary()

        # Action buttons
        self._create_buttons()

    def _create_header(self) -> None:
        """Create header section."""
        header_frame = ttk.Frame(self, padding=20)
        header_frame.pack(fill=tk.X)

        ttk.Label(
            header_frame,
            text="📋 Preview Verse Replacements",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor=tk.W)

        ttk.Label(
            header_frame,
            text="Review the verses that will be inserted. Uncheck any you don't want to replace.",
            font=("Segoe UI", 9)
        ).pack(anchor=tk.W, pady=(5, 0))

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20)

    def _create_preview_table(self) -> None:
        """Create scrollable table of replacements."""
        table_frame = ttk.Frame(self, padding=20)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Control buttons
        control_frame = ttk.Frame(table_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            control_frame,
            text="✓ Select All",
            command=self._select_all,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            control_frame,
            text="✗ Deselect All",
            command=self._deselect_all,
            width=15
        ).pack(side=tk.LEFT)

        # Create treeview
        columns = ("reference", "verse_preview", "status")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="tree headings",
            selectmode="extended",
            height=15
        )

        # Configure columns
        self.tree.heading("#0", text="✓")
        self.tree.heading("reference", text="Reference")
        self.tree.heading("verse_preview", text="Verse Preview")
        self.tree.heading("status", text="Status")

        self.tree.column("#0", width=30, stretch=False)
        self.tree.column("reference", width=150, stretch=False)
        self.tree.column("verse_preview", width=600, stretch=True)
        self.tree.column("status", width=100, stretch=False)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Pack tree and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Populate table
        self._populate_table()

        # Bind checkbox toggle
        self.tree.bind("<Button-1>", self._on_item_click)
        self.tree.bind("<space>", self._on_space_press)

    def _populate_table(self) -> None:
        """Populate table with placeholders and verses."""
        for placeholder in self.placeholders:
            ref_key = placeholder.reference.canonical_reference
            verse = self.verses.get(ref_key)

            if verse and verse.text:
                # Truncate long verses for preview
                verse_preview = verse.text
                if len(verse_preview) > 100:
                    verse_preview = verse_preview[:100] + "..."

                status = "✓ Ready"
                status_tag = "ready"
            else:
                verse_preview = "[Verse not available]"
                status = "✗ Missing"
                status_tag = "missing"

            # Insert item
            item_id = self.tree.insert(
                "",
                "end",
                text="☐",
                values=(ref_key, verse_preview, status),
                tags=(status_tag,)
            )

            # Store reference in item
            self.tree.set(item_id, "#0", "☐")

        # Configure tags
        self.tree.tag_configure("ready", foreground="#28a745")
        self.tree.tag_configure("missing", foreground="#dc3545")
        self.tree.tag_configure("selected", foreground="#007bff")

    def _create_summary(self) -> None:
        """Create summary section."""
        summary_frame = ttk.Frame(self, padding=(20, 0, 20, 10))
        summary_frame.pack(fill=tk.X)

        self.summary_var = tk.StringVar()
        self._update_summary()

        ttk.Label(
            summary_frame,
            textvariable=self.summary_var,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W)

    def _create_buttons(self) -> None:
        """Create action buttons."""
        button_frame = ttk.Frame(self, padding=20)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=15
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            button_frame,
            text="▶ Proceed with Selected",
            command=self._on_proceed,
            width=25
        ).pack(side=tk.RIGHT)

    def _on_item_click(self, event) -> None:
        """Handle item click for toggling selection."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "tree":
            item = self.tree.identify_row(event.y)
            if item:
                self._toggle_item(item)

    def _on_space_press(self, event) -> None:
        """Handle space key press for toggling selection."""
        selected_items = self.tree.selection()
        for item in selected_items:
            self._toggle_item(item)

    def _toggle_item(self, item: str) -> None:
        """Toggle selection state of an item."""
        ref = self.tree.item(item, "values")[0]

        if ref in self.selected_replacements:
            self.selected_replacements.remove(ref)
            self.tree.set(item, "#0", "☐")
        else:
            self.selected_replacements.add(ref)
            self.tree.set(item, "#0", "☑")

        self._update_summary()

    def _select_all(self) -> None:
        """Select all items."""
        for item in self.tree.get_children():
            ref = self.tree.item(item, "values")[0]
            verse = self.verses.get(ref)

            # Only select items that have verses available
            if verse and verse.text:
                self.selected_replacements.add(ref)
                self.tree.set(item, "#0", "☑")

        self._update_summary()

    def _deselect_all(self) -> None:
        """Deselect all items."""
        self.selected_replacements.clear()
        for item in self.tree.get_children():
            self.tree.set(item, "#0", "☐")
        self._update_summary()

    def _update_summary(self) -> None:
        """Update summary text."""
        total = len(self.placeholders)
        selected = len(self.selected_replacements)
        available = sum(1 for p in self.placeholders if self.verses.get(p.reference.canonical_reference))

        summary = f"📊 {selected} of {available} verses selected for replacement (Total found: {total})"
        self.summary_var.set(summary)

    def _on_proceed(self) -> None:
        """Handle proceed button click."""
        if not self.selected_replacements:
            messagebox.showwarning(
                "No Selections",
                "Please select at least one verse to replace, or click Cancel.",
                parent=self
            )
            return

        self.result = "proceed"
        self.destroy()

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.result = "cancel"
        self.destroy()

    def get_selected_references(self) -> Set[str]:
        """
        Get set of selected verse references.

        Returns:
            Set of canonical reference strings that user approved
        """
        return self.selected_replacements.copy()
