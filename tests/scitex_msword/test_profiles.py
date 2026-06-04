#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-05-18 00:00:00
# File: tests/scitex_msword/test_profiles.py

"""Tests for scitex_msword.profiles module."""

import pytest


class TestListProfiles:
    """Tests for list_profiles function."""

    def test_list_profiles_returns_list_type(self):
        """list_profiles should return a list."""
        # Arrange
        from scitex_msword import list_profiles
        # Act
        profiles = list_profiles()
        # Assert
        assert isinstance(profiles, list)

    def test_list_profiles_contains_generic_entry(self):
        """list_profiles should include 'generic' profile."""
        # Arrange
        from scitex_msword import list_profiles
        # Act
        profiles = list_profiles()
        # Assert
        assert "generic" in profiles

    def test_list_profiles_contains_mdpi_ijerph(self):
        """list_profiles should include mdpi-ijerph profile."""
        # Arrange
        from scitex_msword import list_profiles
        # Act
        profiles = list_profiles()
        # Assert
        assert "mdpi-ijerph" in profiles

    def test_list_profiles_contains_resna_2025(self):
        """list_profiles should include resna-2025 profile."""
        # Arrange
        from scitex_msword import list_profiles
        # Act
        profiles = list_profiles()
        # Assert
        assert "resna-2025" in profiles

    def test_list_profiles_contains_iop_double_anonymous(self):
        """list_profiles should include iop-double-anonymous profile."""
        # Arrange
        from scitex_msword import list_profiles
        # Act
        profiles = list_profiles()
        # Assert
        assert "iop-double-anonymous" in profiles

    def test_list_profiles_contains_ieee_profile(self):
        """list_profiles should include ieee profile."""
        # Arrange
        from scitex_msword import list_profiles
        # Act
        profiles = list_profiles()
        # Assert
        assert "ieee" in profiles

    def test_list_profiles_returns_sorted_result(self):
        """list_profiles should return a sorted list."""
        # Arrange
        from scitex_msword import list_profiles
        # Act
        profiles = list_profiles()
        # Assert
        assert profiles == sorted(profiles)


class TestGetProfile:
    """Tests for get_profile function."""

    def test_get_profile_generic_has_correct_name(self):
        """get_profile('generic') should return profile named 'generic'."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("generic")
        # Assert
        assert profile.name == "generic"

    def test_get_profile_generic_has_heading_styles(self):
        """get_profile('generic') should populate heading_styles."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("generic")
        # Assert
        assert profile.heading_styles is not None

    def test_get_profile_none_returns_generic_profile(self):
        """get_profile(None) should return generic profile."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile(None)
        # Assert
        assert profile.name == "generic"

    def test_get_profile_unknown_raises_keyerror_exception(self):
        """get_profile with unknown name should raise KeyError."""
        # Arrange
        from scitex_msword import get_profile
        ctx = pytest.raises(KeyError)
        # Act
        # Assert
        with ctx:
            get_profile("unknown-profile-xyz")

    def test_get_profile_unknown_keyerror_mentions_name(self):
        """KeyError message should mention the requested unknown name."""
        # Arrange
        from scitex_msword import get_profile
        raised: KeyError | None = None
        try:
            get_profile("unknown-profile-xyz")
        except KeyError as exc:
            raised = exc
        # Act
        message = str(raised) if raised is not None else ""
        # Assert
        assert "unknown-profile-xyz" in message

    def test_get_profile_mdpi_ijerph_returns_correct_name(self):
        """get_profile('mdpi-ijerph') should return profile with that name."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("mdpi-ijerph")
        # Assert
        assert profile.name == "mdpi-ijerph"

    def test_get_profile_mdpi_ijerph_uses_single_column(self):
        """MDPI IJERPH profile should be single-column."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("mdpi-ijerph")
        # Assert
        assert profile.columns == 1

    def test_get_profile_resna_2025_returns_correct_name(self):
        """get_profile('resna-2025') should return profile with that name."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("resna-2025")
        # Assert
        assert profile.name == "resna-2025"

    def test_get_profile_resna_2025_uses_two_columns(self):
        """RESNA 2025 profile should be two-column."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("resna-2025")
        # Assert
        assert profile.columns == 2

    def test_get_profile_iop_returns_correct_name(self):
        """get_profile('iop-double-anonymous') should return correct name."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("iop-double-anonymous")
        # Assert
        assert profile.name == "iop-double-anonymous"

    def test_get_profile_iop_sets_double_anonymous_flag(self):
        """IOP profile should set double_anonymous=True."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("iop-double-anonymous")
        # Assert
        assert profile.double_anonymous is True

    def test_get_profile_mdpi_alias_resolves_to_mdpi(self):
        """get_profile('mdpi') alias should resolve to an MDPI profile."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("mdpi")
        # Assert
        assert "mdpi" in profile.name.lower()


class TestBaseWordProfile:
    """Tests for BaseWordProfile dataclass."""

    def test_base_word_profile_stores_provided_name(self):
        """BaseWordProfile should store the provided name attribute."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="test", description="Test profile")
        # Assert
        assert profile.name == "test"

    def test_base_word_profile_default_caption_style(self):
        """BaseWordProfile.caption_style should default to 'Caption'."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="test", description="Test profile")
        # Assert
        assert profile.caption_style == "Caption"

    def test_base_word_profile_default_normal_style(self):
        """BaseWordProfile.normal_style should default to 'Normal'."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="test", description="Test profile")
        # Assert
        assert profile.normal_style == "Normal"

    def test_base_word_profile_default_single_column(self):
        """BaseWordProfile.columns should default to 1."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="test", description="Test profile")
        # Assert
        assert profile.columns == 1

    def test_base_word_profile_default_not_double_anonymous(self):
        """BaseWordProfile.double_anonymous should default to False."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="test", description="Test profile")
        # Assert
        assert profile.double_anonymous is False

    def test_base_word_profile_heading_styles_level_one(self):
        """heading_styles should accept and store level-1 style."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(
            name="custom",
            description="Custom profile",
            heading_styles={1: "Title", 2: "Subtitle", 3: "H3"},
        )
        # Assert
        assert profile.heading_styles[1] == "Title"

    def test_base_word_profile_heading_styles_level_two(self):
        """heading_styles should accept and store level-2 style."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(
            name="custom",
            description="Custom profile",
            heading_styles={1: "Title", 2: "Subtitle", 3: "H3"},
        )
        # Assert
        assert profile.heading_styles[2] == "Subtitle"

    def test_base_word_profile_default_reference_section_titles(self):
        """BaseWordProfile should default reference_section_titles to include 'References'."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="test", description="Test")
        # Assert
        assert "References" in profile.reference_section_titles

    def test_base_word_profile_figure_caption_prefixes_full_word(self):
        """figure_caption_prefixes should include 'Figure' by default."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="test", description="Test")
        # Assert
        assert "Figure" in profile.figure_caption_prefixes

    def test_base_word_profile_figure_caption_prefixes_abbreviation(self):
        """figure_caption_prefixes should include 'Fig.' abbreviation by default."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="test", description="Test")
        # Assert
        assert "Fig." in profile.figure_caption_prefixes


class TestRegisterProfile:
    """Tests for register_profile function."""

    def test_register_profile_appears_in_list_profiles(self):
        """register_profile should add a custom profile visible via list_profiles."""
        # Arrange
        from scitex_msword import BaseWordProfile, list_profiles, register_profile
        custom = BaseWordProfile(
            name="test-custom-journal",
            description="Test custom journal",
            heading_styles={1: "Section", 2: "Subsection"},
        )
        # Act
        register_profile(custom)
        profiles = list_profiles()
        # Assert
        assert "test-custom-journal" in profiles

    def test_register_profile_retrievable_with_correct_name(self):
        """Registered profile should be retrievable via get_profile with correct name."""
        # Arrange
        from scitex_msword import BaseWordProfile, get_profile, register_profile
        custom = BaseWordProfile(
            name="test-retrievable-name",
            description="Test retrievable profile",
            columns=2,
        )
        # Act
        register_profile(custom)
        retrieved = get_profile("test-retrievable-name")
        # Assert
        assert retrieved.name == "test-retrievable-name"

    def test_register_profile_retrievable_preserves_columns(self):
        """Registered profile should preserve its columns attribute."""
        # Arrange
        from scitex_msword import BaseWordProfile, get_profile, register_profile
        custom = BaseWordProfile(
            name="test-retrievable-columns",
            description="Test retrievable profile columns",
            columns=2,
        )
        # Act
        register_profile(custom)
        retrieved = get_profile("test-retrievable-columns")
        # Assert
        assert retrieved.columns == 2


class TestBoost2026Profile:
    """Tests for the boost-2026 profile (BOOST v16 dogfooding)."""

    def test_list_profiles_contains_boost_2026(self):
        """boost-2026 should appear in list_profiles."""
        # Arrange
        from scitex_msword import list_profiles
        # Act
        profiles = list_profiles()
        # Assert
        assert "boost-2026" in profiles

    def test_get_profile_boost_returns_boost_2026(self):
        """The 'boost' alias should resolve to boost-2026."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("boost")
        # Assert
        assert profile.name == "boost-2026"

    def test_boost_2026_uses_full_width_ms_mincho_body_font(self):
        """boost-2026 declares ＭＳ 明朝 (full-width MS Mincho) as the body font.

        The full-width ``ＭＳ`` prefix is what Word's Japanese font
        picker resolves; the half-width ``MS`` form that v0.3.0 shipped
        did not match a known font in Word's font picker (proj-grant
        BOOST v40 dogfood).
        """
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("boost-2026")
        # Assert
        assert profile.body_font == "ＭＳ 明朝"

    def test_boost_2026_uses_full_width_ms_gothic_bold_font(self):
        """boost-2026 declares ＭＳ ゴシック (full-width MS Gothic) as the bold font."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("boost-2026")
        # Assert
        assert profile.bold_font == "ＭＳ ゴシック"

    def test_boost_2026_uses_10_5pt_body_font(self):
        """boost-2026 should declare 10.5pt body font size."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("boost-2026")
        # Assert
        assert profile.body_font_size_pt == 10.5

    def test_boost_2026_uses_light_grey_heading_background(self):
        """boost-2026 should declare D9D9D9 (light grey) heading background."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("boost-2026")
        # Assert
        assert profile.heading_background_hex == "D9D9D9"

    def test_boost_2026_uses_single_line_spacing(self):
        """boost-2026 should declare 1.0 line spacing."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("boost-2026")
        # Assert
        assert profile.line_spacing == 1.0

    def test_boost_2026_includes_japanese_references_title(self):
        """boost-2026 should accept 参考文献 as a reference section title."""
        # Arrange
        from scitex_msword import get_profile
        # Act
        profile = get_profile("boost-2026")
        # Assert
        assert "参考文献" in profile.reference_section_titles


class TestBaseWordProfileLayoutHints:
    """Tests for the new layout hint fields on BaseWordProfile."""

    def test_body_font_defaults_to_none(self):
        """body_font should default to None for non-BOOST profiles."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="t", description="t")
        # Assert
        assert profile.body_font is None

    def test_bold_font_defaults_to_none(self):
        """bold_font should default to None for non-BOOST profiles."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="t", description="t")
        # Assert
        assert profile.bold_font is None

    def test_line_spacing_defaults_to_none(self):
        """line_spacing should default to None for non-BOOST profiles."""
        # Arrange
        from scitex_msword import BaseWordProfile
        # Act
        profile = BaseWordProfile(name="t", description="t")
        # Assert
        assert profile.line_spacing is None


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])
