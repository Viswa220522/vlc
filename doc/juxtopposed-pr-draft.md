# Draft PR: Adapt VLC desktop controls to Juxtopposed's redesign

VLC's desktop interface uses a large circular play button and a seek row above
its controls. This change introduces the concept's graphite surfaces, muted
labels, solid orange rectangular play control, and an adaptive inline seek row
for wide pinned players. Narrow windows and profiles with center controls use
the stacked layout.

The changes use VLC's native Qt/QML components and semantic palette. Day and
Night palettes, shared typography, navigation sizing, input radii, and toolbar
grouping are updated. Existing playback handlers and default control IDs are
retained. Saved toolbar profiles are not overwritten.

Design credit and thanks to [Juxtopposed (@juxtopposed)](https://www.youtube.com/@juxtopposed)
for [I Redesigned VLC After 25 Years](https://www.youtube.com/watch?v=ERFeOgqk324)
and [the community design](https://www.figma.com/community/file/1691465999134370980).

Validation: 35 Windows Qt 6.11.2 checks pass with zero failures and zero Qt runtime
warnings/errors. Production QML is exercised with isolated VLC service/type
adapters, including resizing, profile switching, scaling, keyboard/pointer
controls, chaptered seeking, Stop holds, custom accent contrast, and rendering.
Qt component captures were reviewed. QML syntax/duplicate-binding checks for all
14 modified QML files, Python compilation, palette color literal/control inventory
checks, Git whitespace checks, and workflow actionlint pass. A repeatable runner
and Windows/Linux workflow are included; hosted CI has not run yet.

Full typed lint retains warnings because the generated native VLC modules are
unavailable. C++ compilation and complete VLC integration remain pending. This
draft is not ready to open until those checks and user approval are obtained.

Scope and reference gaps are documented in [the redesign notes](juxtopposed-redesign.md).
This is a desktop appearance and playback-layout adaptation; onboarding, waveform/
subtitle timelines, a second library browser, and the concept's settings panels
are not part of this patch.
