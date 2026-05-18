#!/usr/bin/env python3
# Timestamp: 2026-05-18 00:00:00
# File: tests/scitex_msword/test_writer.py

"""Tests for scitex_msword.writer module."""

import tempfile
from pathlib import Path

import pytest

# Skip all tests if python-docx is not available
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("docx", reason="python-docx not installed"),
    reason="python-docx not installed",
)


@pytest.fixture
def generic_writer():
    """Build a WordWriter on the generic profile."""
    from scitex_msword import get_profile
    from scitex_msword.writer import WordWriter

    return WordWriter(profile=get_profile("generic"))


class TestWordWriterInit:
    """Tests for WordWriter initialization."""

    def test_word_writer_init_profile_name_matches_input(self):
        """WordWriter.profile.name should match the supplied profile name."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.writer import WordWriter
        profile = get_profile("generic")
        # Act
        writer = WordWriter(profile=profile)
        # Assert
        assert writer.profile.name == "generic"

    def test_word_writer_init_template_path_defaults_to_none(self):
        """WordWriter.template_path should default to None."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.writer import WordWriter
        profile = get_profile("generic")
        # Act
        writer = WordWriter(profile=profile)
        # Assert
        assert writer.template_path is None

    def test_word_writer_init_template_path_overridable(self):
        """WordWriter.template_path should accept an explicit override."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.writer import WordWriter
        profile = get_profile("generic")
        # Act
        writer = WordWriter(profile=profile, template_path="/some/path.docx")
        # Assert
        assert writer.template_path == "/some/path.docx"


class TestWordWriterWrite:
    """Tests for WordWriter.write method."""

    def test_write_simple_document_file_created(self, generic_writer, tmp_path):
        """write() should create the output file for a simple document."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "paragraph", "text": "This is a test paragraph."},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_output.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()

    def test_write_simple_document_file_non_empty(self, generic_writer, tmp_path):
        """write() should produce a non-empty file for a simple document."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "paragraph", "text": "This is a test paragraph."},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_output.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.stat().st_size > 0

    def test_write_document_with_headings_file_created(self, generic_writer, tmp_path):
        """write() should produce a file when blocks include multiple heading levels."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Section 1"},
                {"type": "heading", "level": 2, "text": "Subsection 1.1"},
                {"type": "paragraph", "text": "Content here."},
                {"type": "heading", "level": 2, "text": "Subsection 1.2"},
                {"type": "paragraph", "text": "More content."},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_headings.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()

    def test_write_document_with_table_file_created(self, generic_writer, tmp_path):
        """write() should produce a file when blocks include a table."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Results"},
                {
                    "type": "table",
                    "rows": [
                        ["Header 1", "Header 2", "Header 3"],
                        ["A", "B", "C"],
                        ["D", "E", "F"],
                    ],
                },
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_table.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()

    def test_write_document_with_captions_file_created(self, generic_writer, tmp_path):
        """write() should produce a file when blocks include figure/table captions."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Figures"},
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "Sample figure caption"},
                {"type": "caption", "caption_type": "table", "number": 1, "caption_text": "Sample table caption"},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_captions.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()

    def test_write_document_with_formatted_runs_file_created(self, generic_writer, tmp_path):
        """write() should produce a file when paragraphs carry formatted runs."""
        # Arrange
        doc = {
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "Mixed formatting",
                    "runs": [
                        {"text": "Normal "},
                        {"text": "bold", "bold": True},
                        {"text": " and "},
                        {"text": "italic", "italic": True},
                        {"text": " text."},
                    ],
                },
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_formatting.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()


class TestWordWriterReferences:
    """Tests for reference writing functionality."""

    def test_write_references_file_created(self, generic_writer, tmp_path):
        """write() should produce a file for documents that include references."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "References"},
                {"type": "reference-paragraph", "ref_number": 1, "ref_text": "Author A. Title A. Journal 2024."},
                {"type": "reference-paragraph", "ref_number": 2, "ref_text": "Author B. Title B. Journal 2023."},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_refs.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()


class TestWordWriterListItems:
    """Tests for list item writing functionality."""

    def test_write_bullet_list_file_created(self, generic_writer, tmp_path):
        """write() should produce a file containing bullet-list items."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Bullet Points"},
                {"type": "list-item", "text": "First item", "list_type": "bullet"},
                {"type": "list-item", "text": "Second item", "list_type": "bullet"},
                {"type": "list-item", "text": "Third item", "list_type": "bullet"},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_bullets.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()

    def test_write_bullet_list_file_non_empty(self, generic_writer, tmp_path):
        """write() bullet-list output should be non-empty on disk."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Bullet Points"},
                {"type": "list-item", "text": "First item", "list_type": "bullet"},
                {"type": "list-item", "text": "Second item", "list_type": "bullet"},
                {"type": "list-item", "text": "Third item", "list_type": "bullet"},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_bullets_nonempty.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.stat().st_size > 0

    def test_write_numbered_list_file_created(self, generic_writer, tmp_path):
        """write() should produce a file containing numbered-list items."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Numbered Steps"},
                {"type": "list-item", "text": "Step one", "list_type": "numbered"},
                {"type": "list-item", "text": "Step two", "list_type": "numbered"},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_numbered.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()


class TestWordWriterDoubleAnonymous:
    """Tests for double-anonymous processing."""

    def test_double_anonymous_profile_file_created(self, tmp_path):
        """write() with IOP double-anonymous profile should produce a file."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.writer import WordWriter
        profile = get_profile("iop-double-anonymous")
        writer = WordWriter(profile=profile)
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "paragraph", "text": "This is text by John Smith."},
            ],
            "metadata": {"author": "John Smith"},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_anon.docx"
        # Act
        writer.write(doc, output_path)
        # Assert
        assert output_path.exists()


class TestWordWriterStyleExists:
    """Tests for _style_exists method."""

    def test_style_exists_returns_true_for_normal(self, generic_writer):
        """_style_exists should return True for the built-in Normal style."""
        # Arrange
        import docx
        doc = docx.Document()
        # Act
        result = generic_writer._style_exists(doc, "Normal")
        # Assert
        assert result is True

    def test_style_exists_returns_false_for_unknown(self, generic_writer):
        """_style_exists should return False for an unknown style name."""
        # Arrange
        import docx
        doc = docx.Document()
        # Act
        result = generic_writer._style_exists(doc, "NonExistentStyleXYZ123")
        # Assert
        assert result is False


class TestWordWriterEmptyDocument:
    """Tests for handling empty documents."""

    def test_write_empty_blocks_file_created(self, generic_writer, tmp_path):
        """write() should produce a file even when blocks is empty."""
        # Arrange
        doc = {"blocks": [], "metadata": {}, "images": [], "references": []}
        output_path = tmp_path / "test_empty.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()

    def test_write_blocks_with_empty_text_file_created(self, generic_writer, tmp_path):
        """write() should produce a file when some blocks have empty text."""
        # Arrange
        doc = {
            "blocks": [
                {"type": "paragraph", "text": ""},
                {"type": "heading", "level": 1, "text": ""},
                {"type": "paragraph", "text": "Actual content"},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_empty_text.docx"
        # Act
        generic_writer.write(doc, output_path)
        # Assert
        assert output_path.exists()


class TestWordWriterProfileSettings:
    """Tests for profile-specific writer settings."""

    def test_resna_profile_uses_two_columns(self):
        """RESNA 2025 profile should declare two columns."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("resna-2025")
        # Assert
        assert profile.columns == 2

    def test_write_with_resna_profile_file_created(self, tmp_path):
        """write() with RESNA profile should produce a file."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.writer import WordWriter
        profile = get_profile("resna-2025")
        writer = WordWriter(profile=profile)
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "INTRODUCTION"},
                {"type": "paragraph", "text": "Some text."},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_resna.docx"
        # Act
        writer.write(doc, output_path)
        # Assert
        assert output_path.exists()

    def test_ieee_profile_uses_two_columns(self):
        """IEEE profile should declare two columns."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("ieee")
        # Assert
        assert profile.columns == 2

    def test_write_with_ieee_profile_file_created(self, tmp_path):
        """write() with IEEE profile should produce a file."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.writer import WordWriter
        profile = get_profile("ieee")
        writer = WordWriter(profile=profile)
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "paragraph", "text": "Paper content."},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_ieee.docx"
        # Act
        writer.write(doc, output_path)
        # Assert
        assert output_path.exists()

    def test_springer_profile_uses_single_column(self):
        """Springer profile should declare one column."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("springer")
        # Assert
        assert profile.columns == 1

    def test_write_with_springer_profile_file_created(self, tmp_path):
        """write() with Springer profile should produce a file."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.writer import WordWriter
        profile = get_profile("springer")
        writer = WordWriter(profile=profile)
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "paragraph", "text": "Content here."},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_springer.docx"
        # Act
        writer.write(doc, output_path)
        # Assert
        assert output_path.exists()


class TestWordWriterPreExportHooks:
    """Tests for pre-export hooks."""

    def test_pre_export_hooks_called_once(self, tmp_path):
        """Pre-export hook should be invoked exactly once during write()."""
        # Arrange
        from scitex_msword import BaseWordProfile
        from scitex_msword.writer import WordWriter
        hook_called = []

        def my_hook(doc):
            hook_called.append(True)
            return doc

        profile = BaseWordProfile(
            name="test-hooks",
            description="Test",
            pre_export_hooks=[my_hook],
        )
        writer = WordWriter(profile=profile)
        doc = {
            "blocks": [{"type": "paragraph", "text": "Test"}],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_hooks.docx"
        # Act
        writer.write(doc, output_path)
        # Assert
        assert len(hook_called) == 1

    def test_pre_export_hooks_can_modify_doc(self, tmp_path):
        """Pre-export hook should be free to mutate doc, write() still succeeds."""
        # Arrange
        from scitex_msword import BaseWordProfile
        from scitex_msword.writer import WordWriter

        def add_footer(doc):
            doc["blocks"].append({"type": "paragraph", "text": "Generated by SciTeX"})
            return doc

        profile = BaseWordProfile(
            name="test-modify",
            description="Test",
            pre_export_hooks=[add_footer],
        )
        writer = WordWriter(profile=profile)
        doc = {
            "blocks": [{"type": "paragraph", "text": "Content"}],
            "metadata": {},
            "images": [],
            "references": [],
        }
        output_path = tmp_path / "test_modify.docx"
        # Act
        writer.write(doc, output_path)
        # Assert
        assert output_path.exists()


class TestWordWriterRoundTrip:
    """Tests for round-trip read/write functionality."""

    @pytest.fixture
    def sample_docs_path(self):
        """Path to sample documents."""
        return (
            Path(__file__).parent.parent.parent.parent.parent
            / "docs"
            / "MSWORD_MANUSCTIPS"
        )

    def _do_round_trip(self, sample_docs_path, tmp_path):
        """Helper: perform a read-modify-write round-trip on the RESNA template."""
        from scitex_msword import get_profile
        from scitex_msword.reader import WordReader
        from scitex_msword.writer import WordWriter

        docx_path = sample_docs_path / "RESNA 2025 Scientific Paper Template.docx"
        if not docx_path.exists():
            pytest.skip(f"Sample file not found: {docx_path}")

        profile = get_profile("generic")
        reader = WordReader(profile=profile, extract_images=False)
        doc = reader.read(docx_path)
        doc["blocks"].append({"type": "paragraph", "text": "Added by test"})

        writer = WordWriter(profile=profile)
        output_path = tmp_path / "modified.docx"
        writer.write(doc, output_path)
        return output_path

    def test_read_modify_write_file_created(self, sample_docs_path, tmp_path):
        """Round-trip read-modify-write should produce a file."""
        # Arrange
        # (fixture supplies docs and tmp paths)
        # Act
        output_path = self._do_round_trip(sample_docs_path, tmp_path)
        # Assert
        assert output_path.exists()

    def test_read_modify_write_file_non_empty(self, sample_docs_path, tmp_path):
        """Round-trip read-modify-write should produce a non-empty file."""
        # Arrange
        # (fixture supplies docs and tmp paths)
        # Act
        output_path = self._do_round_trip(sample_docs_path, tmp_path)
        # Assert
        assert output_path.stat().st_size > 0


class TestWordWriterComplexDocument:
    """Tests for complex document structures."""

    @pytest.fixture
    def complete_manuscript(self):
        """A complete-looking manuscript document for write() tests."""
        return {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Abstract"},
                {"type": "paragraph", "text": "This is the abstract."},
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "paragraph", "text": "Background information."},
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 2, "text": "Study Design"},
                {"type": "paragraph", "text": "We conducted..."},
                {"type": "heading", "level": 2, "text": "Data Analysis"},
                {"type": "paragraph", "text": "Statistics were..."},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "paragraph", "text": "We found that..."},
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "Results overview"},
                {"type": "caption", "caption_type": "table", "number": 1, "caption_text": "Summary statistics"},
                {
                    "type": "table",
                    "rows": [
                        ["Variable", "Mean", "SD"],
                        ["Age", "45.2", "12.3"],
                        ["BMI", "25.1", "4.5"],
                    ],
                },
                {"type": "heading", "level": 1, "text": "Discussion"},
                {"type": "paragraph", "text": "Our findings suggest..."},
                {"type": "heading", "level": 1, "text": "Conclusions"},
                {"type": "paragraph", "text": "In conclusion..."},
                {"type": "heading", "level": 1, "text": "References"},
                {"type": "reference-paragraph", "ref_number": 1, "ref_text": "Author A. Title. Journal 2024."},
                {"type": "reference-paragraph", "ref_number": 2, "ref_text": "Author B. Title. Journal 2023."},
            ],
            "metadata": {},
            "images": [],
            "references": [],
        }

    def test_write_complete_manuscript_file_created(self, generic_writer, complete_manuscript, tmp_path):
        """write() of a complete manuscript should produce a file."""
        # Arrange
        output_path = tmp_path / "test_complete.docx"
        # Act
        generic_writer.write(complete_manuscript, output_path)
        # Assert
        assert output_path.exists()

    def test_write_complete_manuscript_file_above_size_threshold(
        self, generic_writer, complete_manuscript, tmp_path
    ):
        """write() of a complete manuscript should yield a file above ~5kB."""
        # Arrange
        output_path = tmp_path / "test_complete_size.docx"
        # Act
        generic_writer.write(complete_manuscript, output_path)
        # Assert
        assert output_path.stat().st_size > 5000


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])
