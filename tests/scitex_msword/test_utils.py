#!/usr/bin/env python3
# Timestamp: 2026-05-18 00:00:00
# File: tests/scitex_msword/test_utils.py

"""Tests for scitex_msword.utils module."""

import pytest


class TestLinkCaptionsToImages:
    """Tests for link_captions_to_images function."""

    def test_link_captions_to_images_basic_first_caption(self):
        """First figure caption should be linked to first image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {
                    "type": "caption",
                    "caption_type": "figure",
                    "number": 1,
                    "caption_text": "First figure",
                },
                {
                    "type": "caption",
                    "caption_type": "figure",
                    "number": 2,
                    "caption_text": "Second figure",
                },
            ],
            "images": [
                {"hash": "hash_img_1"},
                {"hash": "hash_img_2"},
            ],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert result["blocks"][0]["image_hash"] == "hash_img_1"

    def test_link_captions_to_images_basic_second_caption(self):
        """Second figure caption should be linked to second image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {
                    "type": "caption",
                    "caption_type": "figure",
                    "number": 1,
                    "caption_text": "First figure",
                },
                {
                    "type": "caption",
                    "caption_type": "figure",
                    "number": 2,
                    "caption_text": "Second figure",
                },
            ],
            "images": [
                {"hash": "hash_img_1"},
                {"hash": "hash_img_2"},
            ],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert result["blocks"][1]["image_hash"] == "hash_img_2"

    def test_link_captions_to_images_with_more_images_links_first(self):
        """With more images than captions, the lone caption links to first image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {
                    "type": "caption",
                    "caption_type": "figure",
                    "number": 1,
                    "caption_text": "Only figure",
                },
            ],
            "images": [
                {"hash": "hash_1"},
                {"hash": "hash_2"},
                {"hash": "hash_3"},
            ],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert result["blocks"][0]["image_hash"] == "hash_1"

    def test_link_captions_to_images_with_more_captions_links_first(self):
        """With more captions than images, the first caption gets the only image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "First"},
                {"type": "caption", "caption_type": "figure", "number": 2, "caption_text": "Second"},
                {"type": "caption", "caption_type": "figure", "number": 3, "caption_text": "Third"},
            ],
            "images": [{"hash": "hash_only"}],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert result["blocks"][0]["image_hash"] == "hash_only"

    def test_link_captions_to_images_with_more_captions_skips_second(self):
        """Second caption should receive no image_hash when only one image exists."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "First"},
                {"type": "caption", "caption_type": "figure", "number": 2, "caption_text": "Second"},
                {"type": "caption", "caption_type": "figure", "number": 3, "caption_text": "Third"},
            ],
            "images": [{"hash": "hash_only"}],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert "image_hash" not in result["blocks"][1]

    def test_link_captions_to_images_with_more_captions_skips_third(self):
        """Third caption should receive no image_hash when only one image exists."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "First"},
                {"type": "caption", "caption_type": "figure", "number": 2, "caption_text": "Second"},
                {"type": "caption", "caption_type": "figure", "number": 3, "caption_text": "Third"},
            ],
            "images": [{"hash": "hash_only"}],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert "image_hash" not in result["blocks"][2]

    def test_link_captions_to_images_empty_images_no_link(self):
        """With no images present, no caption should gain image_hash."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 1},
            ],
            "images": [],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert "image_hash" not in result["blocks"][0]

    def test_link_captions_to_images_no_figure_captions_skips_table(self):
        """Table captions should not gain image_hash."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "table", "number": 1},
                {"type": "paragraph", "text": "Some text"},
            ],
            "images": [{"hash": "hash_1"}],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert "image_hash" not in result["blocks"][0]

    def test_link_captions_to_images_mixed_blocks_first_figure(self):
        """In mixed blocks, the first figure caption should link to the first image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Figures"},
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "Fig 1"},
                {"type": "paragraph", "text": "Description"},
                {"type": "caption", "caption_type": "table", "number": 1, "caption_text": "Table 1"},
                {"type": "caption", "caption_type": "figure", "number": 2, "caption_text": "Fig 2"},
            ],
            "images": [
                {"hash": "img_hash_1"},
                {"hash": "img_hash_2"},
            ],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert result["blocks"][1]["image_hash"] == "img_hash_1"

    def test_link_captions_to_images_mixed_blocks_table_unlinked(self):
        """Table captions in mixed blocks should remain unlinked."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Figures"},
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "Fig 1"},
                {"type": "paragraph", "text": "Description"},
                {"type": "caption", "caption_type": "table", "number": 1, "caption_text": "Table 1"},
                {"type": "caption", "caption_type": "figure", "number": 2, "caption_text": "Fig 2"},
            ],
            "images": [
                {"hash": "img_hash_1"},
                {"hash": "img_hash_2"},
            ],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert "image_hash" not in result["blocks"][3]

    def test_link_captions_to_images_mixed_blocks_second_figure(self):
        """The second figure caption in mixed blocks should link to the second image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Figures"},
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "Fig 1"},
                {"type": "paragraph", "text": "Description"},
                {"type": "caption", "caption_type": "table", "number": 1, "caption_text": "Table 1"},
                {"type": "caption", "caption_type": "figure", "number": 2, "caption_text": "Fig 2"},
            ],
            "images": [
                {"hash": "img_hash_1"},
                {"hash": "img_hash_2"},
            ],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert result["blocks"][4]["image_hash"] == "img_hash_2"

    def test_link_captions_to_images_non_sequential_first_block(self):
        """A figure-numbered-2 caption listed first should link by its number."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 2, "caption_text": "Second"},
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "First"},
            ],
            "images": [
                {"hash": "hash_0"},
                {"hash": "hash_1"},
            ],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert result["blocks"][0]["image_hash"] == "hash_1"

    def test_link_captions_to_images_non_sequential_second_block(self):
        """A figure-numbered-1 caption listed second should link by its number."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 2, "caption_text": "Second"},
                {"type": "caption", "caption_type": "figure", "number": 1, "caption_text": "First"},
            ],
            "images": [
                {"hash": "hash_0"},
                {"hash": "hash_1"},
            ],
        }
        # Act
        result = link_captions_to_images(doc)
        # Assert
        assert result["blocks"][1]["image_hash"] == "hash_0"


class TestLinkCaptionsToImagesByProximity:
    """Tests for link_captions_to_images_by_proximity function."""

    def test_link_by_proximity_basic_first_pair(self):
        """First caption should link to nearest preceding image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images_by_proximity
        doc = {
            "blocks": [
                {"type": "image", "image_hash": "img_1"},
                {"type": "caption", "caption_type": "figure", "number": 1},
                {"type": "image", "image_hash": "img_2"},
                {"type": "caption", "caption_type": "figure", "number": 2},
            ],
            "images": [],
        }
        # Act
        result = link_captions_to_images_by_proximity(doc)
        # Assert
        assert result["blocks"][1]["image_hash"] == "img_1"

    def test_link_by_proximity_basic_second_pair(self):
        """Second caption should link to its nearest preceding image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images_by_proximity
        doc = {
            "blocks": [
                {"type": "image", "image_hash": "img_1"},
                {"type": "caption", "caption_type": "figure", "number": 1},
                {"type": "image", "image_hash": "img_2"},
                {"type": "caption", "caption_type": "figure", "number": 2},
            ],
            "images": [],
        }
        # Act
        result = link_captions_to_images_by_proximity(doc)
        # Assert
        assert result["blocks"][3]["image_hash"] == "img_2"

    def test_link_by_proximity_fallback_first_caption(self):
        """When no image blocks exist, fall back to images list for first caption."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images_by_proximity
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 1},
                {"type": "caption", "caption_type": "figure", "number": 2},
            ],
            "images": [
                {"hash": "fallback_1"},
                {"hash": "fallback_2"},
            ],
        }
        # Act
        result = link_captions_to_images_by_proximity(doc)
        # Assert
        assert result["blocks"][0]["image_hash"] == "fallback_1"

    def test_link_by_proximity_fallback_second_caption(self):
        """When no image blocks exist, fall back to images list for second caption."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images_by_proximity
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 1},
                {"type": "caption", "caption_type": "figure", "number": 2},
            ],
            "images": [
                {"hash": "fallback_1"},
                {"hash": "fallback_2"},
            ],
        }
        # Act
        result = link_captions_to_images_by_proximity(doc)
        # Assert
        assert result["blocks"][1]["image_hash"] == "fallback_2"

    def test_link_by_proximity_no_images_at_all(self):
        """With no images anywhere, captions should have no image_hash."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images_by_proximity
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 1},
            ],
            "images": [],
        }
        # Act
        result = link_captions_to_images_by_proximity(doc)
        # Assert
        assert "image_hash" not in result["blocks"][0]

    def test_link_by_proximity_prefers_preceding_image(self):
        """Captions should prefer preceding images over following images."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images_by_proximity
        doc = {
            "blocks": [
                {"type": "image", "image_hash": "before_img"},
                {"type": "paragraph", "text": "text"},
                {"type": "caption", "caption_type": "figure", "number": 1},
                {"type": "paragraph", "text": "more text"},
                {"type": "image", "image_hash": "after_img"},
            ],
            "images": [],
        }
        # Act
        result = link_captions_to_images_by_proximity(doc)
        # Assert
        assert result["blocks"][2]["image_hash"] == "before_img"

    def test_link_by_proximity_uses_following_if_no_preceding(self):
        """When no preceding image exists, use the following image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images_by_proximity
        doc = {
            "blocks": [
                {"type": "caption", "caption_type": "figure", "number": 1},
                {"type": "paragraph", "text": "text"},
                {"type": "image", "image_hash": "only_img"},
            ],
            "images": [],
        }
        # Act
        result = link_captions_to_images_by_proximity(doc)
        # Assert
        assert result["blocks"][0]["image_hash"] == "only_img"

    def test_link_by_proximity_avoids_reusing_images_first(self):
        """First caption claims nearest image; second must not reuse it."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images_by_proximity
        doc = {
            "blocks": [
                {"type": "image", "image_hash": "shared_img"},
                {"type": "caption", "caption_type": "figure", "number": 1},
                {"type": "caption", "caption_type": "figure", "number": 2},
                {"type": "image", "image_hash": "second_img"},
            ],
            "images": [],
        }
        # Act
        result = link_captions_to_images_by_proximity(doc)
        # Assert
        assert result["blocks"][1]["image_hash"] == "shared_img"

    def test_link_by_proximity_avoids_reusing_images_second(self):
        """Second caption should receive the remaining unused image."""
        # Arrange
        from scitex_msword.utils import link_captions_to_images_by_proximity
        doc = {
            "blocks": [
                {"type": "image", "image_hash": "shared_img"},
                {"type": "caption", "caption_type": "figure", "number": 1},
                {"type": "caption", "caption_type": "figure", "number": 2},
                {"type": "image", "image_hash": "second_img"},
            ],
            "images": [],
        }
        # Act
        result = link_captions_to_images_by_proximity(doc)
        # Assert
        assert result["blocks"][2]["image_hash"] == "second_img"


class TestNormalizeSectionHeadings:
    """Tests for normalize_section_headings function."""

    def test_normalize_intro_becomes_introduction(self):
        """Should normalize 'intro' to 'Introduction'."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {"blocks": [{"type": "heading", "level": 1, "text": "intro"}]}
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "Introduction"

    def test_normalize_introduction_stays_introduction(self):
        """Should normalize 'introduction' to 'Introduction'."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {"blocks": [{"type": "heading", "level": 1, "text": "introduction"}]}
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "Introduction"

    def test_normalize_method_becomes_methods(self):
        """Should normalize 'method' to 'Methods'."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {"blocks": [{"type": "heading", "level": 1, "text": "method"}]}
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "Methods"

    def test_normalize_result_becomes_results(self):
        """Should normalize 'result' to 'Results'."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {"blocks": [{"type": "heading", "level": 1, "text": "result"}]}
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "Results"

    def test_normalize_conclusion_becomes_conclusions(self):
        """Should normalize 'conclusion' to 'Conclusions'."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {"blocks": [{"type": "heading", "level": 1, "text": "conclusion"}]}
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "Conclusions"

    def test_normalize_acknowledgement_becomes_acknowledgements(self):
        """Should normalize 'acknowledgement' to 'Acknowledgements'."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {"blocks": [{"type": "heading", "level": 1, "text": "acknowledgement"}]}
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "Acknowledgements"

    def test_normalize_bibliography_becomes_references(self):
        """Should normalize 'bibliography' to 'References'."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {"blocks": [{"type": "heading", "level": 1, "text": "bibliography"}]}
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "References"

    def test_normalize_skips_level2_headings(self):
        """Level 2 headings should not be normalised."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {
            "blocks": [
                {"type": "heading", "level": 2, "text": "intro"},
                {"type": "heading", "level": 3, "text": "method"},
            ]
        }
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "intro"

    def test_normalize_skips_level3_headings(self):
        """Level 3 headings should not be normalised."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {
            "blocks": [
                {"type": "heading", "level": 2, "text": "intro"},
                {"type": "heading", "level": 3, "text": "method"},
            ]
        }
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][1]["text"] == "method"

    def test_normalize_case_insensitive_all_caps(self):
        """All-caps text should normalise to canonical case."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "INTRODUCTION"},
                {"type": "heading", "level": 1, "text": "Methods"},
            ]
        }
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "Introduction"

    def test_normalize_case_insensitive_title_case(self):
        """Title-case text matching a known section should normalise canonically."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "INTRODUCTION"},
                {"type": "heading", "level": 1, "text": "Methods"},
            ]
        }
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][1]["text"] == "Methods"

    def test_normalize_preserves_paragraph_blocks(self):
        """Paragraph blocks should be left untouched."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {
            "blocks": [
                {"type": "paragraph", "text": "intro"},
                {"type": "caption", "text": "method"},
            ]
        }
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "intro"

    def test_normalize_preserves_caption_blocks(self):
        """Caption blocks should be left untouched."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {
            "blocks": [
                {"type": "paragraph", "text": "intro"},
                {"type": "caption", "text": "method"},
            ]
        }
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][1]["text"] == "method"

    def test_normalize_materials_and_methods_to_canonical(self):
        """Should normalize 'materials and methods' to canonical case."""
        # Arrange
        from scitex_msword.utils import normalize_section_headings
        doc = {"blocks": [{"type": "heading", "level": 1, "text": "materials and methods"}]}
        # Act
        result = normalize_section_headings(doc)
        # Assert
        assert result["blocks"][0]["text"] == "Materials and Methods"


class TestValidateDocument:
    """Tests for validate_document function."""

    def test_validate_complete_document_no_warnings(self):
        """A complete document should yield zero warnings."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "heading", "level": 1, "text": "Discussion"},
                {"type": "heading", "level": 1, "text": "References"},
            ],
            "references": [{"number": 1, "text": "Ref 1"}],
            "warnings": [],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert len(result["warnings"]) == 0

    def test_validate_missing_introduction_warns(self):
        """Should warn when Introduction section is missing."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "heading", "level": 1, "text": "Discussion"},
                {"type": "heading", "level": 1, "text": "References"},
            ],
            "references": [{"number": 1, "text": "Ref"}],
            "warnings": [],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert any("Introduction" in w for w in result["warnings"])

    def test_validate_missing_methods_warns(self):
        """Should warn when Methods section is missing."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "heading", "level": 1, "text": "Discussion"},
                {"type": "heading", "level": 1, "text": "References"},
            ],
            "references": [{"number": 1, "text": "Ref"}],
            "warnings": [],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert any("Methods" in w for w in result["warnings"])

    def test_validate_missing_results_warns(self):
        """Should warn when Results section is missing."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 1, "text": "Discussion"},
                {"type": "heading", "level": 1, "text": "References"},
            ],
            "references": [{"number": 1, "text": "Ref"}],
            "warnings": [],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert any("Results" in w for w in result["warnings"])

    def test_validate_missing_discussion_warns(self):
        """Should warn when Discussion section is missing."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "heading", "level": 1, "text": "References"},
            ],
            "references": [{"number": 1, "text": "Ref"}],
            "warnings": [],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert any("Discussion" in w for w in result["warnings"])

    def test_validate_missing_references_section_warns(self):
        """Should warn when References section is missing."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "heading", "level": 1, "text": "Discussion"},
            ],
            "references": [{"number": 1, "text": "Ref"}],
            "warnings": [],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert any("References" in w for w in result["warnings"])

    def test_validate_duplicate_figure_numbers_warns(self):
        """Should warn about duplicate figure numbers."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "heading", "level": 1, "text": "Discussion"},
                {"type": "heading", "level": 1, "text": "References"},
                {"type": "caption", "caption_type": "figure", "number": 1},
                {"type": "caption", "caption_type": "figure", "number": 1},  # Duplicate!
            ],
            "references": [{"number": 1, "text": "Ref"}],
            "warnings": [],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert any("Duplicate figure number: 1" in w for w in result["warnings"])

    def test_validate_no_references_warns(self):
        """Should warn when references list is empty."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "heading", "level": 1, "text": "Discussion"},
                {"type": "heading", "level": 1, "text": "References"},
            ],
            "references": [],
            "warnings": [],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert any("No references found" in w for w in result["warnings"])

    def test_validate_reference_paragraphs_suppress_warning(self):
        """Presence of reference-paragraph blocks should suppress the missing-references warning."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "heading", "level": 1, "text": "Discussion"},
                {"type": "heading", "level": 1, "text": "References"},
                {"type": "reference-paragraph", "ref_number": 1, "text": "Ref 1"},
            ],
            "references": [],
            "warnings": [],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert not any("No references found" in w for w in result["warnings"])

    def test_validate_preserves_existing_warnings(self):
        """Existing warnings on input should be retained on output."""
        # Arrange
        from scitex_msword.utils import validate_document
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Introduction"},
                {"type": "heading", "level": 1, "text": "Methods"},
                {"type": "heading", "level": 1, "text": "Results"},
                {"type": "heading", "level": 1, "text": "Discussion"},
                {"type": "heading", "level": 1, "text": "References"},
            ],
            "references": [{"number": 1, "text": "Ref"}],
            "warnings": ["Existing warning"],
        }
        # Act
        result = validate_document(doc)
        # Assert
        assert "Existing warning" in result["warnings"]


class TestCreatePostImportHook:
    """Tests for create_post_import_hook function."""

    def test_create_hook_single_function_applies_mutation(self):
        """A single-function hook should apply that function's mutation."""
        # Arrange
        from scitex_msword.utils import create_post_import_hook

        def add_marker(doc):
            doc["marker"] = True
            return doc

        hook = create_post_import_hook(add_marker)
        # Act
        result = hook({"blocks": []})
        # Assert
        assert result["marker"] is True

    def test_create_hook_multi_function_applies_first(self):
        """A multi-function hook should apply the first function's mutation."""
        # Arrange
        from scitex_msword.utils import create_post_import_hook

        def add_first(doc):
            doc["first"] = True
            return doc

        def add_second(doc):
            doc["second"] = True
            return doc

        hook = create_post_import_hook(add_first, add_second)
        # Act
        result = hook({"blocks": []})
        # Assert
        assert result["first"] is True

    def test_create_hook_multi_function_applies_second(self):
        """A multi-function hook should apply the second function's mutation."""
        # Arrange
        from scitex_msword.utils import create_post_import_hook

        def add_first(doc):
            doc["first"] = True
            return doc

        def add_second(doc):
            doc["second"] = True
            return doc

        hook = create_post_import_hook(add_first, add_second)
        # Act
        result = hook({"blocks": []})
        # Assert
        assert result["second"] is True

    def test_create_hook_order_preserved_left_to_right(self):
        """Functions should run in the order they are passed."""
        # Arrange
        from scitex_msword.utils import create_post_import_hook

        def append_a(doc):
            doc["order"] = doc.get("order", "") + "A"
            return doc

        def append_b(doc):
            doc["order"] = doc.get("order", "") + "B"
            return doc

        hook = create_post_import_hook(append_a, append_b)
        # Act
        result = hook({"blocks": []})
        # Assert
        assert result["order"] == "AB"

    def test_create_hook_with_real_utils_normalizes_first(self):
        """Real-utility chain should normalise the first heading."""
        # Arrange
        from scitex_msword.utils import (
            create_post_import_hook,
            normalize_section_headings,
            validate_document,
        )
        hook = create_post_import_hook(normalize_section_headings, validate_document)
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "intro"},
                {"type": "heading", "level": 1, "text": "method"},
            ],
            "references": [],
            "warnings": [],
        }
        # Act
        result = hook(doc)
        # Assert
        assert result["blocks"][0]["text"] == "Introduction"

    def test_create_hook_with_real_utils_normalizes_second(self):
        """Real-utility chain should normalise the second heading."""
        # Arrange
        from scitex_msword.utils import (
            create_post_import_hook,
            normalize_section_headings,
            validate_document,
        )
        hook = create_post_import_hook(normalize_section_headings, validate_document)
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "intro"},
                {"type": "heading", "level": 1, "text": "method"},
            ],
            "references": [],
            "warnings": [],
        }
        # Act
        result = hook(doc)
        # Assert
        assert result["blocks"][1]["text"] == "Methods"

    def test_create_hook_with_real_utils_attaches_warnings(self):
        """Real-utility chain should leave a warnings list on the document."""
        # Arrange
        from scitex_msword.utils import (
            create_post_import_hook,
            normalize_section_headings,
            validate_document,
        )
        hook = create_post_import_hook(normalize_section_headings, validate_document)
        doc = {
            "blocks": [
                {"type": "heading", "level": 1, "text": "intro"},
                {"type": "heading", "level": 1, "text": "method"},
            ],
            "references": [],
            "warnings": [],
        }
        # Act
        result = hook(doc)
        # Assert
        assert "warnings" in result

    def test_create_hook_no_functions_passes_doc_through(self):
        """An empty-hook chain should pass the document through unchanged."""
        # Arrange
        from scitex_msword.utils import create_post_import_hook
        hook = create_post_import_hook()
        doc = {"blocks": [], "test": "value"}
        # Act
        result = hook(doc)
        # Assert
        assert result["test"] == "value"


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])
