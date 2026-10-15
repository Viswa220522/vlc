# VLC reference redesign ? work in progress

Design credit and thanks to [Juxtopposed (@juxtopposed)](https://www.youtube.com/@juxtopposed)
for [I Redesigned VLC After 25 Years](https://www.youtube.com/watch?v=ERFeOgqk324)
and [the community design](https://www.figma.com/community/file/1691465999134370980).
This is an independent implementation in the Viswa220522 personal fork.

Figma's [Community licensing policy](https://help.figma.com/hc/en-us/articles/360042296374-Figma-Community-copyright-and-licensing)
states that free design files use [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The specific resource's license panel and any separate third-party asset notices
have not yet been verified. This note records that outstanding check; it does
not assert a verified license for every imported icon or imply endorsement.
The implementation changes the source layout into native QML, flattens icon
wrapper transforms into SVG, and adds live playback and library bindings.

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

Native compilation and component tests are separate from application validation.
The portable smoke test must verify audio/image decoding, Qt startup with and
without the media library, plugin loading, scene capture, and normal shutdown.
Its logs and report are uploaded even when the runtime job fails.

The [native build and Windows runtime job passed](https://github.com/Viswa220522/vlc/actions/runs/38776677021)
at `01a86aa`. The identical ZIP also passes all four native cases on the local
Windows machine: both decoding cases and both Qt cases exit normally, with no
forbidden QML/plugin diagnostics. Its SHA-256 is
`0d2a237b8726b17fcbdc27367d6427f1ceaced08f19a3230d8811a2f4a4efef5`.
The native captures were visually inspected at 1x and 2x device pixel ratios.
The Qt scene capture contains the actual interface; the video region is
transparent because VLC renders video in a separate native layer.

The current local checks pass 35 existing component cases and 100 reference cases,
with zero runtime Qt warnings/errors. The reference cases exercise the actual
production title bar, navigation, browser, playback strip, volume widget, and
New Playlist dialog with isolated VLC service adapters. They check reference
geometry, button commands, seeking focus, playlist navigation/creation, input
validation, volume rendering, and captures. Every icon is checked for vector
content and rendered at 1x, 1.5x, 2x, and 3x pixel densities. These adapters do not validate the
C++ backend or native system menus/window actions.

`qmllint` parses 27 affected QML files with no syntax or duplicate-binding/name
errors. Full typed diagnostics retain warnings about unavailable generated VLC
modules. Python compilation, shell syntax, workflow actionlint, and Git
whitespace checks are also required before pushing.

The [component workflow](../.github/workflows/qt-redesign-checks.yml) runs both
runners on Windows/Linux and Qt 6.8.3/6.11.2. The 135-check matrix passed
[on all four combinations](https://github.com/Viswa220522/vlc/actions/runs/38776676734)
at commit `01a86aa`. These isolated adapters previously missed native integration
errors: an incorrectly named singleton, eager loading of optional library types,
and Canvas being absent from the contrib build. They do not establish that the
complete native app is error-free.

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

The pinned MinGW runtime also needs a portable-build workaround: its static
libstdc++ cleanup can call `pthread_key_delete` after Windows has terminated
other threads, leaving that call waiting for an abandoned reader lock.
The wrapper in `.github/scripts/qt-runtime-shutdown.c` bypasses key deletion only
while the process is terminating. Normal deletion and explicit DLL unload retain
their runtime behavior. Ordinary source builds do not enable this wrapper.

No upstream `make check` or `make distcheck` result exists for this branch.
These targeted checks do not replace upstream contribution requirements.

No PR has been opened. Ask the user before creating one. VLC upstream uses
[VideoLAN GitLab](https://code.videolan.org/videolan/vlc); personal use or a PR
within the fork remains the intended path.
