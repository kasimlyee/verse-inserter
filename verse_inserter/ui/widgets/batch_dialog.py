"""
Batch processing dialog for multiple documents.

Provides UI for selecting and processing multiple Word documents
with real-time progress tracking and results summary.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List, Optional
import asyncio

from verse_inserter.core.batch_processor import BatchProcessor, BatchProcessingResult


class BatchProcessingDialog(tk.Toplevel):
    """
    Dialog for batch processing multiple Word documents.

    Features:
    - Multi-file selection
    - File list with status indicators
    - Real-time progress tracking
    - Results summary
    - Output directory selection
    """

    def __init__(self, parent, api_client, cache_manager=None):
        """
        Initialize batch processing dialog.

        Args:
            parent: Parent window
            api_client: Bible API client
            cache_manager: Optional cache manager
        """
        super().__init__(parent)

        self.api_client = api_client
        self.cache_manager = cache_manager
        self.file_paths: List[Path] = []
        self.output_dir: Optional[Path] = None
        self.result: Optional[BatchProcessingResult] = None
        self.processing = False

        self.title("Batch Process Documents")
        self.geometry("800x600")
        self.resizable(True, True)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._center_window()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Main container
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Batch Process Multiple Documents",
            font=("Segoe UI", 14, "bold"),
        )
        title_label.pack(pady=(0, 10))

        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Input Files", padding=10)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Buttons frame
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            btn_frame,
            text="📁 Add Files",
            command=self._add_files,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="🗑 Remove Selected",
            command=self._remove_selected,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="🧹 Clear All",
            command=self._clear_all,
        ).pack(side=tk.LEFT)

        # File count label
        self.file_count_label = ttk.Label(
            btn_frame,
            text="0 files selected",
            foreground="gray",
        )
        self.file_count_label.pack(side=tk.RIGHT)

        # File list with scrollbar
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9),
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # Output directory frame
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))

        output_row = ttk.Frame(output_frame)
        output_row.pack(fill=tk.X)

        ttk.Label(output_row, text="Output Directory:").pack(side=tk.LEFT)

        self.output_entry = ttk.Entry(output_row, state="readonly")
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Button(
            output_row,
            text="Browse...",
            command=self._select_output_dir,
        ).pack(side=tk.LEFT)

        ttk.Label(
            output_frame,
            text="(Leave empty to save in same directory as input files)",
            font=("Segoe UI", 8),
            foreground="gray",
        ).pack(anchor=tk.W, pady=(5, 0))

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_label = ttk.Label(
            progress_frame,
            text="Ready to process",
            foreground="gray",
        )
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            maximum=100,
        )
        self.progress_bar.pack(fill=tk.X)

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X)

        self.process_btn = ttk.Button(
            action_frame,
            text="🚀 Start Processing",
            command=self._start_processing,
            style="Accent.TButton",
        )
        self.process_btn.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            action_frame,
            text="Close",
            command=self._close,
        ).pack(side=tk.RIGHT)

        self.results_btn = ttk.Button(
            action_frame,
            text="📊 View Results",
            command=self._show_results,
            state=tk.DISABLED,
        )
        self.results_btn.pack(side=tk.RIGHT, padx=(0, 5))

    def _center_window(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        parent = self.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _add_files(self):
        """Add files to processing list."""
        files = filedialog.askopenfilenames(
            title="Select Word Documents",
            filetypes=[
                ("Word Documents", "*.docx"),
                ("All Files", "*.*"),
            ],
        )

        if files:
            for file in files:
                path = Path(file)
                if path not in self.file_paths:
                    self.file_paths.append(path)
                    self.file_listbox.insert(tk.END, str(path))

            self._update_file_count()

    def _remove_selected(self):
        """Remove selected files from list."""
        selection = self.file_listbox.curselection()
        if not selection:
            return

        # Remove in reverse order to maintain indices
        for idx in reversed(selection):
            self.file_paths.pop(idx)
            self.file_listbox.delete(idx)

        self._update_file_count()

    def _clear_all(self):
        """Clear all files from list."""
        if self.file_paths and messagebox.askyesno(
            "Clear All",
            "Remove all files from the list?",
            parent=self,
        ):
            self.file_paths.clear()
            self.file_listbox.delete(0, tk.END)
            self._update_file_count()

    def _update_file_count(self):
        """Update file count label."""
        count = len(self.file_paths)
        self.file_count_label.config(text=f"{count} file{'s' if count != 1 else ''} selected")

    def _select_output_dir(self):
        """Select output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            parent=self,
        )

        if directory:
            self.output_dir = Path(directory)
            self.output_entry.config(state="normal")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, str(self.output_dir))
            self.output_entry.config(state="readonly")

    def _start_processing(self):
        """Start batch processing."""
        if not self.file_paths:
            messagebox.showwarning(
                "No Files",
                "Please add at least one document to process.",
                parent=self,
            )
            return

        if self.processing:
            return

        # Confirm processing
        if not messagebox.askyesno(
            "Start Processing",
            f"Process {len(self.file_paths)} document(s)?",
            parent=self,
        ):
            return

        self.processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.results_btn.config(state=tk.DISABLED)

        # Run processing in background
        asyncio.create_task(self._run_batch_processing())

    async def _run_batch_processing(self):
        """Run batch processing asynchronously."""
        try:
            processor = BatchProcessor(
                api_client=self.api_client,
                cache_manager=self.cache_manager,
                progress_callback=self._update_progress,
            )

            self.result = await processor.process_batch(
                file_paths=self.file_paths,
                output_dir=self.output_dir,
            )

            self._processing_complete()

        except Exception as e:
            self.processing = False
            self.process_btn.config(state=tk.NORMAL)
            messagebox.showerror(
                "Processing Error",
                f"An error occurred during batch processing:\n\n{str(e)}",
                parent=self,
            )

    def _update_progress(self, message: str, current: int, total: int):
        """Update progress display."""
        self.progress_label.config(text=message)

        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar["value"] = percentage

        self.update_idletasks()

    def _processing_complete(self):
        """Handle processing completion."""
        self.processing = False
        self.process_btn.config(state=tk.NORMAL)
        self.results_btn.config(state=tk.NORMAL)

        if self.result:
            self.progress_label.config(
                text=f"Complete! {self.result.successful}/{self.result.total_files} files processed successfully",
                foreground="green",
            )
            self.progress_bar["value"] = 100

            messagebox.showinfo(
                "Processing Complete",
                f"Batch processing complete!\n\n"
                f"Successful: {self.result.successful}\n"
                f"Failed: {self.result.failed}\n"
                f"Success Rate: {self.result.success_rate:.1f}%",
                parent=self,
            )

    def _show_results(self):
        """Show detailed results dialog."""
        if not self.result:
            return

        results_window = tk.Toplevel(self)
        results_window.title("Batch Processing Results")
        results_window.geometry("900x500")
        results_window.transient(self)

        # Main frame
        main_frame = ttk.Frame(results_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Summary
        summary_frame = ttk.LabelFrame(main_frame, text="Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        summary_text = (
            f"Total Files: {self.result.total_files}  |  "
            f"Successful: {self.result.successful}  |  "
            f"Failed: {self.result.failed}  |  "
            f"Success Rate: {self.result.success_rate:.1f}%\n"
            f"Total Placeholders: {self.result.total_placeholders}  |  "
            f"Total Verses Inserted: {self.result.total_verses_inserted}"
        )
        ttk.Label(summary_frame, text=summary_text).pack()

        # Results table
        table_frame = ttk.LabelFrame(main_frame, text="File Results", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        columns = ("status", "filename", "placeholders", "verses", "output")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        tree.heading("status", text="Status")
        tree.heading("filename", text="Filename")
        tree.heading("placeholders", text="Placeholders")
        tree.heading("verses", text="Verses")
        tree.heading("output", text="Output File")

        tree.column("status", width=80, anchor=tk.CENTER)
        tree.column("filename", width=250)
        tree.column("placeholders", width=100, anchor=tk.CENTER)
        tree.column("verses", width=100, anchor=tk.CENTER)
        tree.column("output", width=300)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate results
        for file_result in self.result.file_results:
            status = "✓ Success" if file_result.success else "✗ Failed"
            filename = file_result.file_path.name
            placeholders = str(file_result.placeholders_found) if file_result.success else "—"
            verses = str(file_result.verses_inserted) if file_result.success else "—"
            output = file_result.output_path.name if file_result.output_path else (
                file_result.error_message or "—"
            )

            tree.insert("", tk.END, values=(status, filename, placeholders, verses, output))

        # Close button
        ttk.Button(
            main_frame,
            text="Close",
            command=results_window.destroy,
        ).pack(pady=(10, 0))

    def _close(self):
        """Close dialog."""
        if self.processing:
            if not messagebox.askyesno(
                "Processing In Progress",
                "Processing is in progress. Are you sure you want to close?",
                parent=self,
            ):
                return

        self.grab_release()
        self.destroy()
