"""
Template manager dialog for custom verse formatting.

Provides UI for creating, editing, and managing formatting templates.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from verse_inserter.core.format_template import TemplateManager, FormatTemplate
from verse_inserter.models.verse import Verse, VerseReference, TranslationType


class TemplateManagerDialog(tk.Toplevel):
    """
    Dialog for managing verse formatting templates.

    Features:
    - View all templates (built-in and custom)
    - Create new templates
    - Edit custom templates
    - Delete custom templates
    - Preview templates
    - Import/Export templates
    """

    # Sample verse for previewing
    SAMPLE_VERSE = Verse(
        reference=VerseReference(
            book="John",
            chapter=3,
            start_verse=16,
            translation=TranslationType.NIV,
        ),
        text="For God so loved the world that he gave his one and only Son, "
             "that whoever believes in him shall not perish but have eternal life.",
        translation=TranslationType.NIV,
    )

    def __init__(self, parent):
        """
        Initialize template manager dialog.

        Args:
            parent: Parent window
        """
        super().__init__(parent)

        self.template_manager = TemplateManager()
        self.selected_template: Optional[FormatTemplate] = None

        self.title("Manage Formatting Templates")
        self.geometry("1000x700")
        self.resizable(True, True)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._load_templates()
        self._center_window()

    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="Formatting Templates",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(0, 15))

        # Content frame (horizontal split)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left side - Template list
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        ttk.Label(
            left_frame,
            text="Templates",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=tk.W, pady=(0, 5))

        # Template listbox
        list_container = ttk.Frame(left_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.template_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10),
        )
        self.template_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.template_listbox.yview)

        self.template_listbox.bind('<<ListboxSelect>>', self._on_template_select)

        # Buttons under list
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="➕ New",
            command=self._new_template,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="✏ Edit",
            command=self._edit_template,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="🗑 Delete",
            command=self._delete_template,
        ).pack(side=tk.LEFT)

        # Right side - Template details
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(
            right_frame,
            text="Template Details",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=tk.W, pady=(0, 5))

        # Template info frame
        info_frame = ttk.LabelFrame(right_frame, text="Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # Name
        name_row = ttk.Frame(info_frame)
        name_row.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(name_row, text="Name:", width=12).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Label(
            name_row,
            textvariable=self.name_var,
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        # Description
        desc_row = ttk.Frame(info_frame)
        desc_row.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(desc_row, text="Description:", width=12).pack(side=tk.LEFT)
        self.desc_var = tk.StringVar()
        ttk.Label(
            desc_row,
            textvariable=self.desc_var,
            foreground="gray",
        ).pack(side=tk.LEFT)

        # Template text
        template_frame = ttk.LabelFrame(right_frame, text="Template", padding=10)
        template_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        template_scroll = ttk.Scrollbar(template_frame)
        template_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.template_text = tk.Text(
            template_frame,
            height=5,
            wrap=tk.WORD,
            yscrollcommand=template_scroll.set,
            font=("Consolas", 9),
            state=tk.DISABLED,
        )
        self.template_text.pack(fill=tk.BOTH, expand=True)
        template_scroll.config(command=self.template_text.yview)

        # Preview frame
        preview_frame = ttk.LabelFrame(right_frame, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)

        preview_scroll = ttk.Scrollbar(preview_frame)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.preview_text = tk.Text(
            preview_frame,
            height=5,
            wrap=tk.WORD,
            yscrollcommand=preview_scroll.set,
            font=("Segoe UI", 9),
            bg="#f8f9fa",
            state=tk.DISABLED,
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        preview_scroll.config(command=self.preview_text.yview)

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(
            button_frame,
            text="📥 Import",
            command=self._import_templates,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="📤 Export",
            command=self._export_templates,
        ).pack(side=tk.LEFT)

        ttk.Button(
            button_frame,
            text="Close",
            command=self._close,
        ).pack(side=tk.RIGHT)

    def _center_window(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        parent = self.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _load_templates(self):
        """Load and display templates."""
        self.template_listbox.delete(0, tk.END)

        templates = self.template_manager.get_all_templates()

        for template in templates:
            prefix = "🔒" if template.is_builtin else "✏"
            display_name = f"{prefix} {template.name}"
            self.template_listbox.insert(tk.END, display_name)

    def _on_template_select(self, event):
        """Handle template selection."""
        selection = self.template_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        templates = self.template_manager.get_all_templates()

        if idx < len(templates):
            template = templates[idx]
            self.selected_template = template

            # Update details
            self.name_var.set(template.name)
            self.desc_var.set(template.description)

            # Update template text
            self.template_text.config(state=tk.NORMAL)
            self.template_text.delete(1.0, tk.END)
            self.template_text.insert(1.0, template.template)
            self.template_text.config(state=tk.DISABLED)

            # Update preview
            try:
                preview = template.format_verse(self.SAMPLE_VERSE)
                self.preview_text.config(state=tk.NORMAL)
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, preview)
                self.preview_text.config(state=tk.DISABLED)
            except Exception as e:
                self.preview_text.config(state=tk.NORMAL)
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, f"Error: {e}")
                self.preview_text.config(state=tk.DISABLED)

    def _new_template(self):
        """Create new template."""
        dialog = TemplateEditorDialog(self, None)
        self.wait_window(dialog)

        if hasattr(dialog, 'result') and dialog.result:
            template = dialog.result
            if self.template_manager.add_template(template):
                self._load_templates()
                messagebox.showinfo(
                    "Success",
                    f"Template '{template.name}' created successfully!",
                    parent=self,
                )
            else:
                messagebox.showerror(
                    "Error",
                    "Failed to create template. Name may already exist.",
                    parent=self,
                )

    def _edit_template(self):
        """Edit selected template."""
        if not self.selected_template:
            messagebox.showwarning(
                "No Selection",
                "Please select a template to edit.",
                parent=self,
            )
            return

        if self.selected_template.is_builtin:
            messagebox.showinfo(
                "Built-in Template",
                "Built-in templates cannot be edited.\n\nCreate a new custom template instead.",
                parent=self,
            )
            return

        dialog = TemplateEditorDialog(self, self.selected_template)
        self.wait_window(dialog)

        if hasattr(dialog, 'result') and dialog.result:
            template = dialog.result
            if self.template_manager.update_template(
                self.selected_template.name,
                template
            ):
                self._load_templates()
                messagebox.showinfo(
                    "Success",
                    f"Template '{template.name}' updated successfully!",
                    parent=self,
                )

    def _delete_template(self):
        """Delete selected template."""
        if not self.selected_template:
            messagebox.showwarning(
                "No Selection",
                "Please select a template to delete.",
                parent=self,
            )
            return

        if self.selected_template.is_builtin:
            messagebox.showinfo(
                "Built-in Template",
                "Built-in templates cannot be deleted.",
                parent=self,
            )
            return

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete template '{self.selected_template.name}'?",
            parent=self,
        ):
            return

        if self.template_manager.delete_template(self.selected_template.name):
            self._load_templates()
            self.selected_template = None
            self.name_var.set("")
            self.desc_var.set("")
            self.template_text.config(state=tk.NORMAL)
            self.template_text.delete(1.0, tk.END)
            self.template_text.config(state=tk.DISABLED)

            messagebox.showinfo(
                "Success",
                "Template deleted successfully!",
                parent=self,
            )

    def _import_templates(self):
        """Import templates from file."""
        file_path = filedialog.askopenfilename(
            title="Import Templates",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            parent=self,
        )

        if not file_path:
            return

        count = self.template_manager.import_templates(Path(file_path))

        if count > 0:
            self._load_templates()
            messagebox.showinfo(
                "Success",
                f"Imported {count} template(s) successfully!",
                parent=self,
            )
        else:
            messagebox.showwarning(
                "No Templates",
                "No new templates were imported.",
                parent=self,
            )

    def _export_templates(self):
        """Export custom templates to file."""
        if not self.template_manager.custom_templates:
            messagebox.showinfo(
                "No Templates",
                "No custom templates to export.",
                parent=self,
            )
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Templates",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            parent=self,
        )

        if not file_path:
            return

        if self.template_manager.export_templates(Path(file_path)):
            messagebox.showinfo(
                "Success",
                "Templates exported successfully!",
                parent=self,
            )
        else:
            messagebox.showerror(
                "Error",
                "Failed to export templates.",
                parent=self,
            )

    def _close(self):
        """Close dialog."""
        self.grab_release()
        self.destroy()


class TemplateEditorDialog(tk.Toplevel):
    """Dialog for creating/editing a template."""

    def __init__(self, parent, template: Optional[FormatTemplate] = None):
        """
        Initialize template editor.

        Args:
            parent: Parent window
            template: Template to edit (None for new)
        """
        super().__init__(parent)

        self.template = template
        self.result: Optional[FormatTemplate] = None

        title = "Edit Template" if template else "New Template"
        self.title(title)
        self.geometry("700x600")
        self.resizable(True, True)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._load_template()
        self._center_window()

    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_text = "Edit Template" if self.template else "Create New Template"
        ttk.Label(
            main_frame,
            text=title_text,
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(0, 15))

        # Name
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(name_frame, text="Name:*", width=15).pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame, width=50)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Description
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(desc_frame, text="Description:", width=15).pack(side=tk.LEFT)
        self.desc_entry = ttk.Entry(desc_frame, width=50)
        self.desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Template
        template_label_frame = ttk.Frame(main_frame)
        template_label_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(
            template_label_frame,
            text="Template:*",
            width=15,
        ).pack(side=tk.LEFT)

        ttk.Label(
            template_label_frame,
            text="(Use placeholders like {verse_text}, {reference}, etc.)",
            foreground="gray",
            font=("Segoe UI", 8),
        ).pack(side=tk.LEFT)

        template_container = ttk.Frame(main_frame)
        template_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        template_scroll = ttk.Scrollbar(template_container)
        template_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.template_text = tk.Text(
            template_container,
            height=10,
            wrap=tk.WORD,
            yscrollcommand=template_scroll.set,
            font=("Consolas", 9),
        )
        self.template_text.pack(fill=tk.BOTH, expand=True)
        template_scroll.config(command=self.template_text.yview)

        self.template_text.bind('<KeyRelease>', self._update_preview)

        # Placeholder reference
        ref_frame = ttk.LabelFrame(main_frame, text="Available Placeholders", padding=10)
        ref_frame.pack(fill=tk.X, pady=(0, 10))

        placeholders = [
            "{verse_text}", "{reference}", "{book}", "{chapter}",
            "{verse}", "{translation}", "{translation_full}"
        ]

        ttk.Label(
            ref_frame,
            text="  ".join(placeholders),
            font=("Consolas", 8),
            foreground="blue",
        ).pack()

        # Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.preview_text = tk.Text(
            preview_frame,
            height=4,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            bg="#f8f9fa",
            state=tk.DISABLED,
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Save",
            command=self._save,
            style="Accent.TButton",
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
        ).pack(side=tk.RIGHT)

    def _center_window(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        parent = self.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _load_template(self):
        """Load template data if editing."""
        if self.template:
            self.name_entry.insert(0, self.template.name)
            self.desc_entry.insert(0, self.template.description)
            self.template_text.insert(1.0, self.template.template)
            self._update_preview()

    def _update_preview(self, event=None):
        """Update template preview."""
        template_str = self.template_text.get(1.0, tk.END).strip()

        if not template_str:
            return

        try:
            temp_template = FormatTemplate(
                name="Preview",
                description="",
                template=template_str,
            )

            sample_verse = TemplateManagerDialog.SAMPLE_VERSE
            preview = temp_template.format_verse(sample_verse)

            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, preview)
            self.preview_text.config(state=tk.DISABLED)

        except Exception as e:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"Error: {e}")
            self.preview_text.config(state=tk.DISABLED)

    def _save(self):
        """Save template."""
        name = self.name_entry.get().strip()
        description = self.desc_entry.get().strip()
        template_str = self.template_text.get(1.0, tk.END).strip()

        if not name or not template_str:
            messagebox.showwarning(
                "Missing Information",
                "Please provide both name and template.",
                parent=self,
            )
            return

        # Create template
        self.result = FormatTemplate(
            name=name,
            description=description,
            template=template_str,
        )

        self.grab_release()
        self.destroy()

    def _cancel(self):
        """Cancel editing."""
        self.result = None
        self.grab_release()
        self.destroy()
