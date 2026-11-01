# Changelog

## 0.1.12 — 1 November 2026

### Added
- 96 decorative banners: lion, dragon, and stag motifs in all 16 dye colours, each with gold or brown detailing.
- Four Ivy paintings: original portrait, coarse crown headshot, detailed crown portrait, and coarse Tudor library portrait.
- Custom Realms Beyond pack icon.
- Pack description with dark-purple square bullets, an aqua version number, and a gold author credit with an italicised username.
- Python validation and packaging script, version file, SHA-256 checksums, and GitHub draft-release script.

### Changed
- Standardised banner item IDs as `realm:banner_SYMBOL_COLOUR_TRIM`, retaining existing compatibility aliases.
- Made the coarse crown portrait the default `realm:painting_ivy_crown`; the detailed portrait uses `realm:painting_ivy_crown_detailed`.
- Consolidated the library painting under `realm:painting_ivy_doublet`.
- Rebuilt painting frames with solid wooden edges and fitted canvases to show complete edge pixels.
- Synchronised the displayed pack version automatically during packaging.

### Fixed
- Missing painting textures by placing them in the item texture directory.
- Clipped canvas edge pixels and gaps between painting canvases and frames.

### Removed
- Chair portrait and unused painting variants from active pack assets; previous variants remain archived.

### Compatibility
- Targets Minecraft Java 26.3.
- Custom decorations use vanilla item models in invisible wall-mounted item frames; no CIT mod is required.
- Retired painting IDs ending in `_coarse` must be replaced with the current IDs above.
