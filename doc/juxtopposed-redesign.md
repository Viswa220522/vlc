# VLC reference redesign ? work in progress

Design credit and thanks to [Juxtopposed (@juxtopposed)](https://www.youtube.com/@juxtopposed)
for [I Redesigned VLC After 25 Years](https://www.youtube.com/watch?v=ERFeOgqk324)
and [the community design](https://www.figma.com/community/file/1691465999134370980).
This is an independent implementation in the Viswa220522 personal fork.

The current target is the supplied design, including its layout and original
assets. The earlier palette-only adaptation is not a complete implementation.

## Implemented reference surfaces

- Native 40 px title bar, original cone and window/menu icons.
- Native 50 px navigation rail and 377 px browser; the library uses the supplied
  217 px expanded navigation layout with seven destinations.
- Native 54 px playback strip: 130 px transport, flexible timeline with 76 px time
  fields, 120 px volume, 114 px options, and 30 px queue. Group gaps and outer
  horizontal padding are 20 px. Play/Pause is 54 ? 28 px.
- Original vector icons in SVG; Inter and DM Mono bundled privately with OFL notices.
  Playback timestamps use Inter, as specified by the supplied player layers.
  SVG paths retain the design's geometry. CSS wrapper positions and rotations
  are flattened to SVG transforms; strokes scale with the artwork. The renderer
  tints vectors after rendering them at the display's physical pixel density.
  The new interface has no PNG icon resources or whole-screen image substitutes.
- The original volume SVG drives a live level indicator. Runtime normalization
  handles Qt's luminance masks and legacy SVG color syntax without redrawing
  the artwork.
- The browser reads VLC's media-library playlist, folder, and recent-media models.
  Playlist contents and back/forward navigation use real model IDs. No sample
  playlists or media are included in the application.
- The supplied 713 ? 590 New Playlist dialog supports title entry, file selection,
  dropped URLs, thumbnail selection, and native playlist creation. Custom covers
  are stored with the portable preferences and used by the playlist grid.
- The player's video frame uses the reference inset and corner treatment.

Dimensions are logical pixels at 100% interface scale. Real media, library names,
item counts, durations, and playback state depend on the user's content.
Original asset nodes and hashes are recorded in `pixmaps/juxtopposed/sources.json`;
font sources, hashes, and licenses are under `pixmaps/fonts`.

## Still unfinished

The full library grids/headers, music playback content, settings and effects
panels, onboarding, subtitle/waveform timelines, context menus, and toolbar
customization screens still require implementation against their reference
states. Several actions currently open VLC's existing native dialogs. Home,
Music, and Network rail destinations currently open the main library instead
of their narrow browser variants. The new player strip currently uses its fixed
reference arrangement; applying saved toolbar arrangements to this strip is
also unfinished. The existing toolbar data and miniplayer remain available.

Do not describe this branch as an exact, complete concept port or an error-free
release until these surfaces and full application behavior have been checked.
The imported player media image is missing; no replacement illustration was
invented. Screenshots of complete design boards are never application assets.

## Validation

The baseline [native Windows build succeeded](https://github.com/Viswa220522/vlc/actions/runs/38617568908)
at commit `75c3dac`. Its portable ZIP checksum was verified. Local native smoke
tests decoded audio and an image, but found an omitted shared GCC runtime and
shutdown callbacks accessing deleted QML objects. Packaging and callback fixes
are in the current work and require another native run.

The latest local checks pass 35 existing component cases and 93 reference cases,
with zero runtime Qt warnings/errors. The reference cases exercise the actual
production title bar, navigation, browser, playback strip, volume widget, and
New Playlist dialog with isolated VLC service adapters. They check reference
geometry, button commands, seeking focus, playlist navigation/creation, input
validation, volume rendering, and captures. Every icon is checked for vector
content and rendered at 1x, 1.5x, 2x, and 3x pixel densities. These adapters do not validate the
C++ backend or native system menus/window actions.

`qmllint` parses 26 affected QML files with no syntax or duplicate-binding/name
errors. Full typed diagnostics retain warnings about unavailable generated VLC
modules. Python compilation, shell syntax, workflow actionlint, and Git
whitespace checks are also required before pushing.

The [component workflow](../.github/workflows/qt-redesign-checks.yml) runs both
runners on Windows/Linux and Qt 6.8.3/6.11.2. The earlier 35-case matrix passed
[on all four combinations](https://github.com/Viswa220522/vlc/actions/runs/38617568651).
The expanded reference suite must pass the same matrix for the new source.

## Portable Windows build

The [build workflow](../.github/workflows/vlc-win64-build.yml) uses VideoLAN's
pinned win64 CI image and matching prebuilt contribs. It compiles native VLC and
packages a portable ZIP, source/dependency receipt, and SHA-256 checksum.
Extraction and launching `vlc.exe` need no VLC installation. Its `portable`
directory isolates preferences; fresh previews start with Night colors and
pinned controls. The user's installed VLC is separate.

CI validation builds include an opt-in `VLC_QT_UI_TEST_OUTPUT` environment hook
that saves the application's own Qt scene. Ordinary builds exclude this hook.
The hook captures no desktop content and performs no external GUI automation.

No PR has been opened. Ask the user before creating one. VLC upstream uses
[VideoLAN GitLab](https://code.videolan.org/videolan/vlc); personal use or a PR
within the fork remains the intended path.
