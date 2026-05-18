#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-05-18 00:00:00
# File: tests/scitex_msword/test_reader.py

"""Tests for scitex_msword.reader module."""

from pathlib import Path

import pytest

# Skip all tests if python-docx is not available
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("docx", reason="python-docx not installed"),
    reason="python-docx not installed",
)


@pytest.fixture
def generic_reader():
    """Build a WordReader on the generic profile."""
    from scitex_msword import get_profile
    from scitex_msword.reader import WordReader

    return WordReader(profile=get_profile("generic"))


@pytest.fixture
def iop_reader():
    """Build a WordReader on the IOP double-anonymous profile."""
    from scitex_msword import get_profile
    from scitex_msword.reader import WordReader

    return WordReader(profile=get_profile("iop-double-anonymous"))


class TestWordReaderInit:
    """Tests for WordReader initialization."""

    def test_word_reader_init_profile_name_is_generic(self):
        """WordReader profile attribute should match supplied profile name."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.reader import WordReader
        profile = get_profile("generic")
        # Act
        reader = WordReader(profile=profile)
        # Assert
        assert reader.profile.name == "generic"

    def test_word_reader_init_extract_images_defaults_true(self):
        """WordReader.extract_images should default to True."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.reader import WordReader
        profile = get_profile("generic")
        # Act
        reader = WordReader(profile=profile)
        # Assert
        assert reader.extract_images is True

    def test_word_reader_init_extract_images_false_when_overridden(self):
        """WordReader should accept extract_images=False override."""
        # Arrange
        from scitex_msword import get_profile
        from scitex_msword.reader import WordReader
        profile = get_profile("generic")
        # Act
        reader = WordReader(profile=profile, extract_images=False)
        # Assert
        assert reader.extract_images is False


class TestWordReaderCaptionParsing:
    """Tests for caption parsing functionality."""

    def test_parse_figure_caption_sets_caption_type(self, generic_reader):
        """_parse_caption should mark 'Figure N.' as figure type."""
        # Arrange
        text = "Figure 1. Test caption text"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_type"] == "figure"

    def test_parse_figure_caption_extracts_number(self, generic_reader):
        """_parse_caption should extract figure number."""
        # Arrange
        text = "Figure 1. Test caption text"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["number"] == 1

    def test_parse_figure_caption_extracts_text(self, generic_reader):
        """_parse_caption should extract figure caption text."""
        # Arrange
        text = "Figure 1. Test caption text"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_text"] == "Test caption text"

    def test_parse_figure_caption_with_colon_sets_caption_type(self, generic_reader):
        """_parse_caption should treat 'Figure N:' as figure type."""
        # Arrange
        text = "Figure 2: Another caption"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_type"] == "figure"

    def test_parse_figure_caption_with_colon_extracts_number(self, generic_reader):
        """_parse_caption should extract number when separator is a colon."""
        # Arrange
        text = "Figure 2: Another caption"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["number"] == 2

    def test_parse_figure_caption_with_colon_extracts_text(self, generic_reader):
        """_parse_caption should extract text when separator is a colon."""
        # Arrange
        text = "Figure 2: Another caption"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_text"] == "Another caption"

    def test_parse_fig_abbreviation_sets_caption_type(self, generic_reader):
        """_parse_caption should treat 'Fig. N' as figure type."""
        # Arrange
        text = "Fig. 3 Some caption"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_type"] == "figure"

    def test_parse_fig_abbreviation_extracts_number(self, generic_reader):
        """_parse_caption should extract number from 'Fig. N'."""
        # Arrange
        text = "Fig. 3 Some caption"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["number"] == 3

    def test_parse_table_caption_sets_caption_type(self, generic_reader):
        """_parse_caption should mark 'Table N.' as table type."""
        # Arrange
        text = "Table 1. Data summary"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_type"] == "table"

    def test_parse_table_caption_extracts_number(self, generic_reader):
        """_parse_caption should extract table number."""
        # Arrange
        text = "Table 1. Data summary"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["number"] == 1

    def test_parse_table_caption_extracts_text(self, generic_reader):
        """_parse_caption should extract table caption text."""
        # Arrange
        text = "Table 1. Data summary"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_text"] == "Data summary"

    def test_parse_unknown_caption_sets_caption_type(self, generic_reader):
        """_parse_caption should mark unrecognised input as unknown."""
        # Arrange
        text = "Some random text"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_type"] == "unknown"

    def test_parse_unknown_caption_preserves_text(self, generic_reader):
        """_parse_caption should preserve unrecognised text verbatim."""
        # Arrange
        text = "Some random text"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_text"] == "Some random text"


class TestWordReaderReferenceParsing:
    """Tests for reference parsing functionality."""

    def test_parse_bracketed_reference_extracts_number(self, generic_reader):
        """_parse_reference_entry should extract number from '[1] ...'."""
        # Arrange
        text = "[1] Author A. Title. Journal 2024."
        # Act
        result = generic_reader._parse_reference_entry(text)
        # Assert
        assert result["ref_number"] == 1

    def test_parse_bracketed_reference_extracts_author_in_text(self, generic_reader):
        """_parse_reference_entry should preserve author name in ref_text."""
        # Arrange
        text = "[1] Author A. Title. Journal 2024."
        # Act
        result = generic_reader._parse_reference_entry(text)
        # Assert
        assert "Author A" in result["ref_text"]

    def test_parse_numbered_reference_extracts_number(self, generic_reader):
        """_parse_reference_entry should extract number from '1. ...' style."""
        # Arrange
        text = "1. Author B. Title. Journal 2023."
        # Act
        result = generic_reader._parse_reference_entry(text)
        # Assert
        assert result["ref_number"] == 1

    def test_parse_numbered_reference_extracts_author_in_text(self, generic_reader):
        """_parse_reference_entry should preserve author for '1. ...' style."""
        # Arrange
        text = "1. Author B. Title. Journal 2023."
        # Act
        result = generic_reader._parse_reference_entry(text)
        # Assert
        assert "Author B" in result["ref_text"]

    def test_parse_parenthetical_reference_extracts_number(self, generic_reader):
        """_parse_reference_entry should extract number from '(N) ...'."""
        # Arrange
        text = "(2) Author C. Title. Journal 2022."
        # Act
        result = generic_reader._parse_reference_entry(text)
        # Assert
        assert result["ref_number"] == 2

    def test_parse_parenthetical_reference_extracts_author_in_text(self, generic_reader):
        """_parse_reference_entry should preserve author for '(N) ...' style."""
        # Arrange
        text = "(2) Author C. Title. Journal 2022."
        # Act
        result = generic_reader._parse_reference_entry(text)
        # Assert
        assert "Author C" in result["ref_text"]

    def test_parse_unnumbered_reference_has_no_number(self, generic_reader):
        """_parse_reference_entry should leave ref_number unset for unnumbered."""
        # Arrange
        text = "Author D. Title. Journal 2021."
        # Act
        result = generic_reader._parse_reference_entry(text)
        # Assert
        assert "ref_number" not in result or result.get("ref_number") is None

    def test_parse_unnumbered_reference_preserves_author(self, generic_reader):
        """_parse_reference_entry should preserve author in unnumbered ref_text."""
        # Arrange
        text = "Author D. Title. Journal 2021."
        # Act
        result = generic_reader._parse_reference_entry(text)
        # Assert
        assert "Author D" in result["ref_text"]


class TestWordReaderHeadingDetection:
    """Tests for heading level detection."""

    def test_heading_level_from_style_heading1_returns_one(self, generic_reader):
        """_heading_level_from_style should return 1 for 'Heading 1'."""
        # Arrange
        style = "Heading 1"
        # Act
        level = generic_reader._heading_level_from_style(style)
        # Assert
        assert level == 1

    def test_heading_level_from_style_heading2_returns_two(self, generic_reader):
        """_heading_level_from_style should return 2 for 'Heading 2'."""
        # Arrange
        style = "Heading 2"
        # Act
        level = generic_reader._heading_level_from_style(style)
        # Assert
        assert level == 2

    def test_heading_level_from_style_normal_returns_none(self, generic_reader):
        """_heading_level_from_style should return None for 'Normal'."""
        # Arrange
        style = "Normal"
        # Act
        level = generic_reader._heading_level_from_style(style)
        # Assert
        assert level is None

    def test_heading_level_from_style_unknown_returns_none(self, generic_reader):
        """_heading_level_from_style should return None for unknown styles."""
        # Arrange
        style = "My Custom Style"
        # Act
        level = generic_reader._heading_level_from_style(style)
        # Assert
        assert level is None


class TestWordReaderCaptionDetection:
    """Tests for caption detection."""

    def test_is_caption_by_style_name(self, generic_reader):
        """_is_caption should return True when style equals caption_style."""
        # Arrange
        style, text = "Caption", "Any text"
        # Act
        result = generic_reader._is_caption(style, text)
        # Assert
        assert result is True

    def test_is_caption_by_figure_prefix_full_word(self, generic_reader):
        """_is_caption should detect 'Figure N. ...' captions."""
        # Arrange
        style, text = "Normal", "Figure 1. Caption"
        # Act
        result = generic_reader._is_caption(style, text)
        # Assert
        assert result is True

    def test_is_caption_by_figure_prefix_abbreviation(self, generic_reader):
        """_is_caption should detect 'Fig. N ...' captions."""
        # Arrange
        style, text = "Normal", "Fig. 2 Caption"
        # Act
        result = generic_reader._is_caption(style, text)
        # Assert
        assert result is True

    def test_is_caption_by_table_prefix_full_word(self, generic_reader):
        """_is_caption should detect 'Table N. ...' captions."""
        # Arrange
        style, text = "Normal", "Table 1. Caption"
        # Act
        result = generic_reader._is_caption(style, text)
        # Assert
        assert result is True

    def test_is_caption_returns_false_for_regular_paragraph(self, generic_reader):
        """_is_caption should return False for normal prose."""
        # Arrange
        style, text = "Normal", "Regular paragraph text"
        # Act
        result = generic_reader._is_caption(style, text)
        # Assert
        assert result is False


class TestWordReaderLooksLikeHeading:
    """Tests for _looks_like_heading method."""

    @pytest.mark.parametrize(
        "section",
        [
            "Introduction",
            "Methods",
            "Results",
            "Discussion",
            "Conclusions",
            "References",
            "Abstract",
        ],
    )
    def test_looks_like_heading_recognises_common_section(self, generic_reader, section):
        """_looks_like_heading should recognise common section names."""
        # Arrange
        text = section
        # Act
        result = generic_reader._looks_like_heading(text)
        # Assert
        assert result is True

    @pytest.mark.parametrize(
        "section",
        [
            "1 Introduction",
            "2.1 Methodology",
            "3.2.1 Detailed Methods",
        ],
    )
    def test_looks_like_heading_recognises_numbered_section(self, generic_reader, section):
        """_looks_like_heading should recognise numbered section headings."""
        # Arrange
        text = section
        # Act
        result = generic_reader._looks_like_heading(text)
        # Assert
        assert result is True

    @pytest.mark.parametrize(
        "section",
        ["INTRODUCTION", "RESULTS AND DISCUSSION"],
    )
    def test_looks_like_heading_recognises_all_caps_section(self, generic_reader, section):
        """_looks_like_heading should recognise all-caps section names."""
        # Arrange
        text = section
        # Act
        result = generic_reader._looks_like_heading(text)
        # Assert
        assert result is True

    @pytest.mark.parametrize("short", ["THE", "IT"])
    def test_looks_like_heading_rejects_short_all_caps(self, generic_reader, short):
        """_looks_like_heading should reject very short all-caps strings."""
        # Arrange
        text = short
        # Act
        result = generic_reader._looks_like_heading(text)
        # Assert
        assert result is False

    @pytest.mark.parametrize(
        "prose",
        [
            "This is a regular paragraph.",
            "The results show significant improvement.",
        ],
    )
    def test_looks_like_heading_rejects_regular_prose(self, generic_reader, prose):
        """_looks_like_heading should reject regular sentence prose."""
        # Arrange
        text = prose
        # Act
        result = generic_reader._looks_like_heading(text)
        # Assert
        assert result is False


class TestWordReaderGetAverageFontSize:
    """Tests for _get_average_font_size method."""

    def test_get_average_font_size_single_run_returns_its_size(self, generic_reader):
        """_get_average_font_size should return the lone run's size."""
        # Arrange
        runs = [{"text": "Hello", "font_size": 12.0}]
        # Act
        result = generic_reader._get_average_font_size(runs)
        # Assert
        assert result == 12.0

    def test_get_average_font_size_multiple_runs_returns_mean(self, generic_reader):
        """_get_average_font_size should average sizes across runs."""
        # Arrange
        runs = [
            {"text": "Hello", "font_size": 10.0},
            {"text": "World", "font_size": 14.0},
        ]
        # Act
        result = generic_reader._get_average_font_size(runs)
        # Assert
        assert result == 12.0

    def test_get_average_font_size_empty_runs_returns_none(self, generic_reader):
        """_get_average_font_size should return None when runs is empty."""
        # Arrange
        runs: list = []
        # Act
        result = generic_reader._get_average_font_size(runs)
        # Assert
        assert result is None

    def test_get_average_font_size_no_font_size_returns_none(self, generic_reader):
        """_get_average_font_size should return None when no run carries font_size."""
        # Arrange
        runs = [{"text": "Hello"}, {"text": "World"}]
        # Act
        result = generic_reader._get_average_font_size(runs)
        # Assert
        assert result is None

    def test_get_average_font_size_partial_font_size_uses_present_only(self, generic_reader):
        """_get_average_font_size should average only runs that carry font_size."""
        # Arrange
        runs = [
            {"text": "Hello", "font_size": 12.0},
            {"text": "World"},  # No font_size
            {"text": "!", "font_size": 14.0},
        ]
        # Act
        result = generic_reader._get_average_font_size(runs)
        # Assert
        assert result == 13.0


class TestWordReaderDetectCaption:
    """Tests for _detect_caption method."""

    def test_detect_caption_by_style_is_not_none(self, generic_reader):
        """_detect_caption should return non-None when style matches caption_style."""
        # Arrange
        style, text = "Caption", "Figure 1. Test"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result is not None

    def test_detect_caption_by_style_returns_figure_type(self, generic_reader):
        """_detect_caption should return figure type for 'Caption' + 'Figure ...'."""
        # Arrange
        style, text = "Caption", "Figure 1. Test"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["caption_type"] == "figure"

    def test_detect_caption_figure_pattern_returns_figure_type(self, generic_reader):
        """_detect_caption should classify 'Figure N. text' as figure."""
        # Arrange
        style, text = "Normal", "Figure 5. A nice diagram"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["caption_type"] == "figure"

    def test_detect_caption_figure_pattern_extracts_number(self, generic_reader):
        """_detect_caption should extract figure number from pattern match."""
        # Arrange
        style, text = "Normal", "Figure 5. A nice diagram"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["number"] == 5

    def test_detect_caption_figure_pattern_extracts_text(self, generic_reader):
        """_detect_caption should extract caption_text from figure pattern."""
        # Arrange
        style, text = "Normal", "Figure 5. A nice diagram"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["caption_text"] == "A nice diagram"

    def test_detect_caption_table_pattern_returns_table_type(self, generic_reader):
        """_detect_caption should classify 'Table N: text' as table."""
        # Arrange
        style, text = "Normal", "Table 3: Summary of results"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["caption_type"] == "table"

    def test_detect_caption_table_pattern_extracts_number(self, generic_reader):
        """_detect_caption should extract table number."""
        # Arrange
        style, text = "Normal", "Table 3: Summary of results"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["number"] == 3

    def test_detect_caption_scheme_returns_scheme_type(self, generic_reader):
        """_detect_caption should classify 'Scheme N. text' as scheme."""
        # Arrange
        style, text = "Normal", "Scheme 1. Chemical reaction pathway"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["caption_type"] == "scheme"

    def test_detect_caption_scheme_extracts_number(self, generic_reader):
        """_detect_caption should extract scheme number."""
        # Arrange
        style, text = "Normal", "Scheme 1. Chemical reaction pathway"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["number"] == 1

    def test_detect_caption_chart_returns_chart_type(self, generic_reader):
        """_detect_caption should classify 'Chart N. text' as chart."""
        # Arrange
        style, text = "Normal", "Chart 2. Pie chart of distribution"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["caption_type"] == "chart"

    def test_detect_caption_chart_extracts_number(self, generic_reader):
        """_detect_caption should extract chart number."""
        # Arrange
        style, text = "Normal", "Chart 2. Pie chart of distribution"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["number"] == 2

    def test_detect_caption_equation_returns_equation_type(self, generic_reader):
        """_detect_caption should classify 'Equation N. text' as equation."""
        # Arrange
        style, text = "Normal", "Equation 1. Newton's second law"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["caption_type"] == "equation"

    def test_detect_caption_equation_extracts_number(self, generic_reader):
        """_detect_caption should extract equation number."""
        # Arrange
        style, text = "Normal", "Equation 1. Newton's second law"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["number"] == 1

    def test_detect_caption_algorithm_returns_algorithm_type(self, generic_reader):
        """_detect_caption should classify 'Algorithm N. text' as algorithm."""
        # Arrange
        style, text = "Normal", "Algorithm 1. Quick sort implementation"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["caption_type"] == "algorithm"

    def test_detect_caption_algorithm_extracts_number(self, generic_reader):
        """_detect_caption should extract algorithm number."""
        # Arrange
        style, text = "Normal", "Algorithm 1. Quick sort implementation"
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result["number"] == 1

    def test_detect_caption_not_caption_returns_none(self, generic_reader):
        """_detect_caption should return None for non-caption prose."""
        # Arrange
        style, text = "Normal", "This is regular text about figures."
        # Act
        result = generic_reader._detect_caption(style, text)
        # Assert
        assert result is None


class TestWordReaderIOPProfile:
    """Tests for IOP profile with custom heading styles."""

    def test_iop_heading_style_ioph1_returns_level_one(self, iop_reader):
        """IOP profile should map 'IOPH1' to heading level 1."""
        # Arrange
        style = "IOPH1"
        # Act
        level = iop_reader._heading_level_from_style(style)
        # Assert
        assert level == 1

    def test_iop_heading_style_ioph2_returns_level_two(self, iop_reader):
        """IOP profile should map 'IOPH2' to heading level 2."""
        # Arrange
        style = "IOPH2"
        # Act
        level = iop_reader._heading_level_from_style(style)
        # Assert
        assert level == 2

    def test_iop_heading_style_ioph3_returns_level_three(self, iop_reader):
        """IOP profile should map 'IOPH3' to heading level 3."""
        # Arrange
        style = "IOPH3"
        # Act
        level = iop_reader._heading_level_from_style(style)
        # Assert
        assert level == 3

    def test_iop_profile_sets_double_anonymous_true(self):
        """IOP profile should set double_anonymous=True."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("iop-double-anonymous")
        # Assert
        assert profile.double_anonymous is True


class TestWordReaderCaptionPatternVariations:
    """Tests for various caption format variations."""

    def test_parse_fig_without_dot_returns_figure_type(self, generic_reader):
        """_parse_caption should accept 'Fig N text' without a trailing dot."""
        # Arrange
        text = "Fig 4 Caption text"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_type"] == "figure"

    def test_parse_fig_without_dot_extracts_number(self, generic_reader):
        """_parse_caption should extract number from 'Fig N text'."""
        # Arrange
        text = "Fig 4 Caption text"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["number"] == 4

    def test_parse_table_with_colon_returns_table_type(self, generic_reader):
        """_parse_caption should accept 'Table N: text'."""
        # Arrange
        text = "Table 2: Data overview"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_type"] == "table"

    def test_parse_table_with_colon_extracts_number(self, generic_reader):
        """_parse_caption should extract number from 'Table N: text'."""
        # Arrange
        text = "Table 2: Data overview"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["number"] == 2

    def test_parse_table_with_colon_extracts_text(self, generic_reader):
        """_parse_caption should extract caption text after colon separator."""
        # Arrange
        text = "Table 2: Data overview"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_text"] == "Data overview"

    def test_parse_caption_uppercase_figure_returns_figure_type(self, generic_reader):
        """_parse_caption should treat 'FIGURE N.' (uppercase) as figure."""
        # Arrange
        text = "FIGURE 1. Test"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_type"] == "figure"

    def test_parse_caption_uppercase_figure_extracts_number(self, generic_reader):
        """_parse_caption should extract number from uppercase 'FIGURE N.'."""
        # Arrange
        text = "FIGURE 1. Test"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["number"] == 1

    def test_parse_caption_lowercase_figure_returns_figure_type(self, generic_reader):
        """_parse_caption should treat lowercase 'figure N.' as figure."""
        # Arrange
        text = "figure 2. test"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["caption_type"] == "figure"

    def test_parse_caption_lowercase_figure_extracts_number(self, generic_reader):
        """_parse_caption should extract number from lowercase 'figure N.'."""
        # Arrange
        text = "figure 2. test"
        # Act
        result = generic_reader._parse_caption(text)
        # Assert
        assert result["number"] == 2


class TestWordReaderIntegration:
    """Integration tests with real DOCX files."""

    @pytest.fixture
    def sample_docs_path(self):
        """Path to sample documents."""
        return (
            Path(__file__).parent.parent.parent.parent.parent
            / "docs"
            / "MSWORD_MANUSCTIPS"
        )

    def _read_iop(self, sample_docs_path):
        """Helper: read IOP template, skipping if file is missing."""
        from scitex_msword import get_profile
        from scitex_msword.reader import WordReader

        docx_path = sample_docs_path / "IOP-SCIENCE-Word-template-Double-anonymous.docx"
        if not docx_path.exists():
            pytest.skip(f"Sample file not found: {docx_path}")
        reader = WordReader(profile=get_profile("iop-double-anonymous"))
        return reader.read(docx_path)

    def _read_resna(self, sample_docs_path):
        """Helper: read RESNA template, skipping if file is missing."""
        from scitex_msword import get_profile
        from scitex_msword.reader import WordReader

        docx_path = sample_docs_path / "RESNA 2025 Scientific Paper Template.docx"
        if not docx_path.exists():
            pytest.skip(f"Sample file not found: {docx_path}")
        reader = WordReader(profile=get_profile("resna-2025"))
        return reader.read(docx_path)

    def _read_resna_with(self, sample_docs_path, *, extract_images):
        """Helper: read RESNA template with generic profile and given flag."""
        from scitex_msword import get_profile
        from scitex_msword.reader import WordReader

        docx_path = sample_docs_path / "RESNA 2025 Scientific Paper Template.docx"
        if not docx_path.exists():
            pytest.skip(f"Sample file not found: {docx_path}")
        reader = WordReader(
            profile=get_profile("generic"), extract_images=extract_images
        )
        return reader.read(docx_path)

    def test_read_iop_template_has_blocks_key(self, sample_docs_path):
        """read(IOP) result should expose a 'blocks' key."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_iop(sample_docs_path)
        # Assert
        assert "blocks" in result

    def test_read_iop_template_has_metadata_key(self, sample_docs_path):
        """read(IOP) result should expose a 'metadata' key."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_iop(sample_docs_path)
        # Assert
        assert "metadata" in result

    def test_read_iop_template_has_images_key(self, sample_docs_path):
        """read(IOP) result should expose an 'images' key."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_iop(sample_docs_path)
        # Assert
        assert "images" in result

    def test_read_iop_template_metadata_profile_is_iop(self, sample_docs_path):
        """read(IOP) metadata should record the IOP profile name."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_iop(sample_docs_path)
        # Assert
        assert result["metadata"]["profile"] == "iop-double-anonymous"

    def test_read_resna_template_has_blocks_key(self, sample_docs_path):
        """read(RESNA) result should expose a 'blocks' key."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_resna(sample_docs_path)
        # Assert
        assert "blocks" in result

    def test_read_resna_template_blocks_non_empty(self, sample_docs_path):
        """read(RESNA) blocks should contain at least one block."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_resna(sample_docs_path)
        # Assert
        assert len(result["blocks"]) > 0

    def test_read_resna_template_metadata_profile_is_resna(self, sample_docs_path):
        """read(RESNA) metadata should record the RESNA profile name."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_resna(sample_docs_path)
        # Assert
        assert result["metadata"]["profile"] == "resna-2025"

    def test_read_extract_images_true_has_images_key(self, sample_docs_path):
        """read(extract_images=True) result should expose an 'images' key."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_resna_with(sample_docs_path, extract_images=True)
        # Assert
        assert "images" in result

    def test_read_extract_images_true_returns_list_type(self, sample_docs_path):
        """read(extract_images=True) images value should be a list."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_resna_with(sample_docs_path, extract_images=True)
        # Assert
        assert isinstance(result["images"], list)

    def test_read_extract_images_false_returns_empty_list(self, sample_docs_path):
        """read(extract_images=False) images should be the empty list."""
        # Arrange
        # (fixture supplies the docs path)
        # Act
        result = self._read_resna_with(sample_docs_path, extract_images=False)
        # Assert
        assert result["images"] == []


class TestWordReaderReferencesParsing:
    """Tests for _parse_references method."""

    @pytest.fixture
    def two_reference_blocks(self):
        """Blocks containing two reference paragraphs."""
        return [
            {"type": "heading", "text": "References"},
            {
                "type": "reference-paragraph",
                "ref_number": 1,
                "ref_text": "Author A. Title. 2024.",
                "text": "[1] Author A. Title. 2024.",
            },
            {
                "type": "reference-paragraph",
                "ref_number": 2,
                "ref_text": "Author B. Title. 2023.",
                "text": "[2] Author B. Title. 2023.",
            },
        ]

    def test_parse_references_returns_two_entries(self, generic_reader, two_reference_blocks):
        """_parse_references should return one entry per reference paragraph."""
        # Arrange
        blocks = two_reference_blocks
        # Act
        refs = generic_reader._parse_references(blocks)
        # Assert
        assert len(refs) == 2

    def test_parse_references_first_entry_number(self, generic_reader, two_reference_blocks):
        """_parse_references first entry should preserve its reference number."""
        # Arrange
        blocks = two_reference_blocks
        # Act
        refs = generic_reader._parse_references(blocks)
        # Assert
        assert refs[0]["number"] == 1

    def test_parse_references_first_entry_text(self, generic_reader, two_reference_blocks):
        """_parse_references first entry should preserve its reference text."""
        # Arrange
        blocks = two_reference_blocks
        # Act
        refs = generic_reader._parse_references(blocks)
        # Assert
        assert refs[0]["text"] == "Author A. Title. 2024."

    def test_parse_references_second_entry_number(self, generic_reader, two_reference_blocks):
        """_parse_references second entry should preserve its reference number."""
        # Arrange
        blocks = two_reference_blocks
        # Act
        refs = generic_reader._parse_references(blocks)
        # Assert
        assert refs[1]["number"] == 2

    def test_parse_references_empty_blocks_returns_empty_list(self, generic_reader):
        """_parse_references should return [] when given no blocks."""
        # Arrange
        blocks: list = []
        # Act
        refs = generic_reader._parse_references(blocks)
        # Assert
        assert refs == []

    def test_parse_references_no_reference_paragraphs_returns_empty(self, generic_reader):
        """_parse_references should return [] when no reference-paragraph blocks present."""
        # Arrange
        blocks = [
            {"type": "heading", "text": "Introduction"},
            {"type": "paragraph", "text": "Some text"},
        ]
        # Act
        refs = generic_reader._parse_references(blocks)
        # Assert
        assert refs == []


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])
