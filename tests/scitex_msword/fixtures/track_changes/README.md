# Track Changes — vendored Word ground-truth fixtures

This directory holds files that desktop Word itself wrote, captured as
the canonical reference for what `scitex_msword.track_changes` should
emit. The vendored copy exists so the conformance tests pin against
**Word's actual output**, not against our own helper's output — which
is what let the trackChanges/trackRevisions name bug silently ship from
v0.2.0 through v0.3.0 (the self-consistent wrong-name state matched
itself in CI and looked fine until proj-grant's BOOST v40 dogfood
crashed it on the operator's desktop Word).

## word_groundtruth_settings.xml

The `word/settings.xml` member of:

```
draft_v39_ywata-turned-on-edit-history.docx
```

The source `.docx` is the **operator's manual Track Changes ON save**
during the BOOST v40 dogfood: open `draft_v39`, click the Track
Changes button to ON, type nothing, save. That makes the resulting
settings.xml the cleanest possible "what does desktop Word actually
emit when Track Changes is on" reference we have.

| Field           | Value                                                                            |
|-----------------|----------------------------------------------------------------------------------|
| Date captured   | 2026-06-04                                                                       |
| Environment     | Word 365 on Win10/11 (operator's enterprise build per the v40 thread)            |
| Provenance      | `proj-grant` a2a `46f07cc4c43546daa3b866d4680421e9` + `bc312cccebaf40bf97c85fea750f2f4d` |
| Source `.docx`  | `/home/ywatanabe/proj/grant/2026-06-11---2027-04-2032-03---20-PERC---1000---BOOST/draft_v39_ywata-turned-on-edit-history.docx` |
| Parent docx sha256 | `af2845ddb6f1ec3b02b288f48627d0b6c57f5e93f7eccda10821de6c00e4bdae`             |
| settings.xml sha256 | `1099e0a53236908a9869225d312627d5e5ec0b5845c4663813ec77bd8da29088`             |
| Size            | 47604 bytes                                                                      |
| Personal data   | None (verified — only XML namespace declarations contain colons)                 |

### What it pins

The relevant Track Changes slice of this file is, in order:

```xml
<w:stylePaneSortMethod w:val="0003"/>
<w:trackRevisions/>
<w:doNotTrackFormatting/>
<w:documentProtection w:edit="trackedChanges" w:enforcement="0"/>
```

— i.e. the actual ECMA-376 §17.15.1.92 toggle (`<w:trackRevisions/>`),
followed by the matching `<w:documentProtection>` echo with
`enforcement="0"` (state-only, not enforced). The
`TestTrackRevisionsAgainstVendoredWordGroundTruth` test class in
`tests/scitex_msword/test__settings_order.py` pins against this
exact slice — both the presence of the elements **and** that
`scitex_msword.track_changes.save_with_track_changes_on` emits the
same slice.

### When to update

Don't update unless desktop Word genuinely changes its emission
recipe across a major Word version bump — and only after
re-verifying against the operator's environment. If you re-capture,
update the date, environment, parent-docx sha256, and
settings.xml sha256 in this README alongside the new bytes.
