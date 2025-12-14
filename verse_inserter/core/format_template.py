"""
Custom formatting templates for Bible verses.

Allows users to define their own verse formatting with placeholders.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import re
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path
import json

from verse_inserter.models.verse import Verse, VerseReference


@dataclass
class FormatTemplate:
    """A custom formatting template for verses."""

    name: str
    description: str
    template: str
    is_builtin: bool = False

    def format_verse(self, verse: Verse) -> str:
        """
        Format a verse using this template.

        Available placeholders:
        - {verse_text} - The verse text
        - {reference} - Full reference (e.g., "John 3:16")
        - {book} - Book name (e.g., "John")
        - {chapter} - Chapter number
        - {verse} - Verse number (or range)
        - {translation} - Translation abbreviation (e.g., "NIV")
        - {translation_full} - Full translation name

        Args:
            verse: Verse to format

        Returns:
            Formatted verse text
        """
        ref = verse.reference

        # Prepare replacement values
        verse_range = (
            f"{ref.start_verse}-{ref.end_verse}"
            if ref.end_verse
            else str(ref.start_verse)
        )

        translation_names = {
            "KJV": "King James Version",
            "NIV": "New International Version",
            "ESV": "English Standard Version",
            "NKJV": "New King James Version",
            "NLT": "New Living Translation",
        }

        replacements = {
            "verse_text": verse.text,
            "reference": ref.canonical_reference,
            "book": ref.book,
            "chapter": str(ref.chapter),
            "verse": verse_range,
            "translation": ref.translation.name,
            "translation_full": translation_names.get(
                ref.translation.name,
                ref.translation.name
            ),
        }

        # Replace placeholders
        result = self.template
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", value)

        return result

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "template": self.template,
            "is_builtin": self.is_builtin,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FormatTemplate":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            template=data["template"],
            is_builtin=data.get("is_builtin", False),
        )


class TemplateManager:
    """
    Manages custom formatting templates.

    Features:
    - Built-in templates
    - User-defined templates
    - Template persistence
    - Template validation
    """

    BUILTIN_TEMPLATES = [
        FormatTemplate(
            name="Plain",
            description="Just the verse text",
            template="{verse_text}",
            is_builtin=True,
        ),
        FormatTemplate(
            name="With Reference",
            description="Verse text with reference in parentheses",
            template='"{verse_text}" ({reference})',
            is_builtin=True,
        ),
        FormatTemplate(
            name="With Translation",
            description="Verse text with reference and translation",
            template='"{verse_text}" ({reference}, {translation})',
            is_builtin=True,
        ),
        FormatTemplate(
            name="Blockquote",
            description="Formatted as a blockquote",
            template='> "{verse_text}"\n> \n> — {reference} ({translation})',
            is_builtin=True,
        ),
        FormatTemplate(
            name="Footnote Style",
            description="Reference as superscript footnote",
            template="{verse_text}^[{reference}]",
            is_builtin=True,
        ),
        FormatTemplate(
            name="Academic",
            description="Full academic citation",
            template='"{verse_text}" ({book} {chapter}:{verse}, {translation_full})',
            is_builtin=True,
        ),
        FormatTemplate(
            name="Sermon Notes",
            description="For sermon notes and outlines",
            template="📖 {reference} ({translation})\n{verse_text}",
            is_builtin=True,
        ),
        FormatTemplate(
            name="Social Media",
            description="Optimized for social media posts",
            template='"{verse_text}"\n\n— {reference}',
            is_builtin=True,
        ),
    ]

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize template manager.

        Args:
            config_dir: Directory for storing custom templates
        """
        if config_dir is None:
            from verse_inserter.config.settings import Settings
            settings = Settings()
            config_dir = settings.config_dir

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.templates_file = self.config_dir / "format_templates.json"
        self.custom_templates: List[FormatTemplate] = []

        self._load_templates()

    def _load_templates(self):
        """Load custom templates from file."""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.custom_templates = [
                        FormatTemplate.from_dict(t) for t in data
                    ]
            except Exception:
                self.custom_templates = []
        else:
            self.custom_templates = []

    def _save_templates(self):
        """Save custom templates to file."""
        try:
            data = [t.to_dict() for t in self.custom_templates]
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save templates: {e}")

    def get_all_templates(self) -> List[FormatTemplate]:
        """Get all templates (built-in and custom)."""
        return self.BUILTIN_TEMPLATES + self.custom_templates

    def get_template(self, name: str) -> Optional[FormatTemplate]:
        """Get template by name."""
        for template in self.get_all_templates():
            if template.name == name:
                return template
        return None

    def add_template(self, template: FormatTemplate) -> bool:
        """
        Add a custom template.

        Args:
            template: Template to add

        Returns:
            True if added successfully
        """
        # Check for duplicate names
        if self.get_template(template.name):
            return False

        # Validate template
        if not self._validate_template(template):
            return False

        template.is_builtin = False
        self.custom_templates.append(template)
        self._save_templates()
        return True

    def update_template(self, name: str, template: FormatTemplate) -> bool:
        """
        Update an existing custom template.

        Args:
            name: Original template name
            template: Updated template

        Returns:
            True if updated successfully
        """
        # Can't update builtin templates
        for i, t in enumerate(self.custom_templates):
            if t.name == name:
                if not self._validate_template(template):
                    return False

                template.is_builtin = False
                self.custom_templates[i] = template
                self._save_templates()
                return True

        return False

    def delete_template(self, name: str) -> bool:
        """
        Delete a custom template.

        Args:
            name: Template name to delete

        Returns:
            True if deleted successfully
        """
        # Can't delete builtin templates
        for i, template in enumerate(self.custom_templates):
            if template.name == name:
                del self.custom_templates[i]
                self._save_templates()
                return True

        return False

    def _validate_template(self, template: FormatTemplate) -> bool:
        """
        Validate a template.

        Args:
            template: Template to validate

        Returns:
            True if valid
        """
        if not template.name or not template.template:
            return False

        # Check for valid placeholders
        valid_placeholders = {
            "verse_text", "reference", "book", "chapter",
            "verse", "translation", "translation_full"
        }

        # Find all placeholders in template
        placeholders = set(re.findall(r'\{(\w+)\}', template.template))

        # Check if all placeholders are valid
        invalid = placeholders - valid_placeholders
        if invalid:
            return False

        return True

    def export_templates(self, file_path: Path) -> bool:
        """
        Export custom templates to a file.

        Args:
            file_path: Path to export to

        Returns:
            True if exported successfully
        """
        try:
            data = [t.to_dict() for t in self.custom_templates]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def import_templates(self, file_path: Path) -> int:
        """
        Import templates from a file.

        Args:
            file_path: Path to import from

        Returns:
            Number of templates imported
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported = 0
            for template_data in data:
                template = FormatTemplate.from_dict(template_data)

                # Skip if name already exists
                if not self.get_template(template.name):
                    if self._validate_template(template):
                        template.is_builtin = False
                        self.custom_templates.append(template)
                        imported += 1

            if imported > 0:
                self._save_templates()

            return imported

        except Exception:
            return 0
