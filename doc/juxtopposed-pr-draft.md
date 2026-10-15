# Draft: Port VLC player chrome and browser from Juxtopposed's design

Replace the earlier style adaptation with the supplied native player layout:
a 40 px title bar, 50 px rail and 377 px browser, and a 54 px playback strip.
Bundle the original icons and reference typefaces, connect playlist/folder
models, and implement the supplied New Playlist dialog.

Credit and thanks to [Juxtopposed (@juxtopposed)](https://www.youtube.com/@juxtopposed)
for [I Redesigned VLC After 25 Years](https://www.youtube.com/watch?v=ERFeOgqk324)
and [the original community design](https://www.figma.com/community/file/1691465999134370980).

Validation: 35 existing component checks and 31 reference checks pass locally,
with zero runtime Qt diagnostics. Native backend services are adapters in these
runners. The baseline native build succeeded; the new source needs compilation,
portable smoke tests, and native scene review. Packaging includes the matching
compiler runtime after baseline smoke tests found missing plug-in dependencies.

This is unfinished. Full settings, library content, music playback, onboarding,
subtitle timelines, menus, and toolbar customization remain to be ported. See
[the current scope and validation notes](juxtopposed-redesign.md).

Do not open this draft until the requested implementation and validation are
complete and the user approves PR creation.
