"""
Offline Bible database for local verse storage.

Provides SQLite-based storage for entire Bible translations,
enabling offline verse lookup without API calls.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from sqlalchemy.exc import IntegrityError

from verse_inserter.models.verse import Verse, VerseReference, TranslationType

# SQLAlchemy Base
Base = declarative_base()


# SQLAlchemy Models
class Translation(Base):
    """Translation database model."""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    abbreviation = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    language = Column(String(50), nullable=False, default="English")
    verse_count = Column(Integer, default=0)
    download_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to verses
    verses = relationship("VerseModel", back_populates="translation", cascade="all, delete-orphan")


class VerseModel(Base):
    """Verse database model."""

    __tablename__ = "verses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    translation_id = Column(Integer, ForeignKey("translations.id"), nullable=False)
    book = Column(String(50), nullable=False)
    chapter = Column(Integer, nullable=False)
    verse = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to translation
    translation = relationship("Translation", back_populates="verses")

    # Composite index for fast lookups
    __table_args__ = (
        Index("idx_verses_lookup", "translation_id", "book", "chapter", "verse"),
    )


@dataclass
class TranslationInfo:
    """Information about a Bible translation."""

    translation: TranslationType
    name: str
    abbreviation: str
    language: str
    verse_count: int
    download_date: Optional[datetime] = None


class OfflineBibleDatabase:
    """
    SQLite database for offline Bible verse storage using SQLAlchemy ORM.

    Features:
    - Store complete Bible translations locally
    - Fast verse lookup without API calls
    - Support multiple translations
    - Efficient indexing for quick searches
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize offline Bible database.

        Args:
            db_path: Path to SQLite database file (defaults to user data dir)
        """
        if db_path is None:
            # Default to user data directory
            from verse_inserter.config.settings import Settings
            settings = Settings()
            db_path = settings.config_dir / "offline_bible.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create SQLAlchemy engine
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,  # Set to True for SQL debugging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize database schema
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Initialize database schema if not exists."""
        Base.metadata.create_all(self.engine)

    def add_translation(
        self,
        translation: TranslationType,
        name: str,
        language: str = "English",
    ) -> int:
        """
        Add a new translation to the database.

        Args:
            translation: Translation type
            name: Full name of translation
            language: Language of translation

        Returns:
            Translation ID
        """
        session: Session = self.SessionLocal()
        try:
            # Check if translation already exists
            existing = session.query(Translation).filter_by(
                abbreviation=translation.name
            ).first()

            if existing:
                return existing.id

            # Create new translation
            new_translation = Translation(
                abbreviation=translation.name,  # Use enum name (e.g., "KJV")
                name=name,
                language=language,
                download_date=datetime.now(timezone.utc),
            )

            session.add(new_translation)
            session.commit()
            session.refresh(new_translation)

            return new_translation.id

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_verse(
        self,
        translation: TranslationType,
        verse: Verse,
    ) -> bool:
        """
        Add a verse to the database.

        Args:
            translation: Translation type
            verse: Verse to add

        Returns:
            True if added successfully
        """
        session: Session = self.SessionLocal()
        try:
            # Get translation
            trans = session.query(Translation).filter_by(
                abbreviation=translation.name
            ).first()

            if not trans:
                return False

            # Check if verse already exists
            existing_verse = session.query(VerseModel).filter_by(
                translation_id=trans.id,
                book=verse.reference.book,
                chapter=verse.reference.chapter,
                verse=verse.reference.start_verse,
            ).first()

            if existing_verse:
                # Update existing verse
                existing_verse.text = verse.text
            else:
                # Add new verse
                new_verse = VerseModel(
                    translation_id=trans.id,
                    book=verse.reference.book,
                    chapter=verse.reference.chapter,
                    verse=verse.reference.start_verse,
                    text=verse.text,
                )
                session.add(new_verse)

            # Update verse count
            trans.verse_count = session.query(VerseModel).filter_by(
                translation_id=trans.id
            ).count()

            session.commit()
            return True

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_verses_bulk(
        self,
        translation: TranslationType,
        verses: List[Verse],
    ) -> int:
        """
        Add multiple verses in bulk (more efficient).

        Args:
            translation: Translation type
            verses: List of verses to add

        Returns:
            Number of verses added
        """
        if not verses:
            return 0

        session: Session = self.SessionLocal()
        try:
            # Get translation
            trans = session.query(Translation).filter_by(
                abbreviation=translation.name
            ).first()

            if not trans:
                return 0

            # Prepare verse models
            verse_models = []
            for v in verses:
                # Check if verse exists
                existing = session.query(VerseModel).filter_by(
                    translation_id=trans.id,
                    book=v.reference.book,
                    chapter=v.reference.chapter,
                    verse=v.reference.start_verse,
                ).first()

                if existing:
                    # Update existing
                    existing.text = v.text
                else:
                    # Add new
                    verse_models.append(VerseModel(
                        translation_id=trans.id,
                        book=v.reference.book,
                        chapter=v.reference.chapter,
                        verse=v.reference.start_verse,
                        text=v.text,
                    ))

            # Bulk insert new verses
            if verse_models:
                session.bulk_save_objects(verse_models)

            # Update verse count
            trans.verse_count = session.query(VerseModel).filter_by(
                translation_id=trans.id
            ).count()

            session.commit()
            return len(verses)

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_verse(
        self,
        reference: VerseReference,
    ) -> Optional[Verse]:
        """
        Get a verse from the database.

        Args:
            reference: Verse reference to lookup

        Returns:
            Verse if found, None otherwise
        """
        session: Session = self.SessionLocal()
        try:
            verse_model = session.query(VerseModel).join(Translation).filter(
                Translation.abbreviation == reference.translation.name,
                VerseModel.book == reference.book,
                VerseModel.chapter == reference.chapter,
                VerseModel.verse == reference.start_verse,
            ).first()

            if verse_model:
                return Verse(
                    reference=reference,
                    text=verse_model.text,
                    translation=reference.translation,
                )

            return None

        finally:
            session.close()

    def get_verse_range(
        self,
        reference: VerseReference,
    ) -> Optional[Verse]:
        """
        Get a verse range from the database.

        Args:
            reference: Verse reference with range (start_verse to end_verse)

        Returns:
            Combined verse text if found
        """
        if reference.end_verse is None:
            return self.get_verse(reference)

        session: Session = self.SessionLocal()
        try:
            verse_models = session.query(VerseModel).join(Translation).filter(
                Translation.abbreviation == reference.translation.name,
                VerseModel.book == reference.book,
                VerseModel.chapter == reference.chapter,
                VerseModel.verse >= reference.start_verse,
                VerseModel.verse <= reference.end_verse,
            ).order_by(VerseModel.verse).all()

            if not verse_models:
                return None

            # Combine verse texts
            combined_text = " ".join(v.text for v in verse_models)

            return Verse(
                reference=reference,
                text=combined_text,
                translation=reference.translation,
            )

        finally:
            session.close()

    def has_translation(self, translation: TranslationType) -> bool:
        """
        Check if translation exists in database.

        Args:
            translation: Translation to check

        Returns:
            True if translation exists
        """
        session: Session = self.SessionLocal()
        try:
            count = session.query(Translation).filter_by(
                abbreviation=translation.name
            ).count()
            return count > 0
        finally:
            session.close()

    def get_translation_info(
        self,
        translation: TranslationType,
    ) -> Optional[TranslationInfo]:
        """
        Get information about a translation.

        Args:
            translation: Translation to query

        Returns:
            TranslationInfo if found
        """
        session: Session = self.SessionLocal()
        try:
            trans = session.query(Translation).filter_by(
                abbreviation=translation.name
            ).first()

            if trans:
                return TranslationInfo(
                    translation=translation,
                    name=trans.name,
                    abbreviation=trans.abbreviation,
                    language=trans.language,
                    verse_count=trans.verse_count,
                    download_date=trans.download_date,
                )

            return None

        finally:
            session.close()

    def get_all_translations(self) -> List[TranslationInfo]:
        """
        Get all downloaded translations.

        Returns:
            List of translation information
        """
        session: Session = self.SessionLocal()
        try:
            trans_models = session.query(Translation).order_by(
                Translation.download_date.desc()
            ).all()

            translations = []
            for trans in trans_models:
                try:
                    # Use enum member name lookup (e.g., TranslationType["KJV"])
                    trans_type = TranslationType[trans.abbreviation]
                    translations.append(TranslationInfo(
                        translation=trans_type,
                        name=trans.name,
                        abbreviation=trans.abbreviation,
                        language=trans.language,
                        verse_count=trans.verse_count,
                        download_date=trans.download_date,
                    ))
                except KeyError:
                    # Skip unknown translations
                    continue

            return translations

        finally:
            session.close()

    def delete_translation(self, translation: TranslationType) -> bool:
        """
        Delete a translation and all its verses.

        Args:
            translation: Translation to delete

        Returns:
            True if deleted successfully
        """
        session: Session = self.SessionLocal()
        try:
            trans = session.query(Translation).filter_by(
                abbreviation=translation.name
            ).first()

            if not trans:
                return False

            # Delete translation (cascade will delete verses)
            session.delete(trans)
            session.commit()
            return True

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_statistics(self) -> Dict[str, any]:
        """
        Get database statistics.

        Returns:
            Dictionary with statistics
        """
        session: Session = self.SessionLocal()
        try:
            translation_count = session.query(Translation).count()
            verse_count = session.query(VerseModel).count()

            # Get database file size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "translation_count": translation_count,
                "verse_count": verse_count,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "database_path": str(self.db_path),
            }

        finally:
            session.close()

    def clear_all(self) -> None:
        """Clear all data from database (keep schema)."""
        session: Session = self.SessionLocal()
        try:
            session.query(VerseModel).delete()
            session.query(Translation).delete()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close database connections and dispose of engine."""
        if hasattr(self, 'engine') and self.engine:
            self.engine.dispose()
