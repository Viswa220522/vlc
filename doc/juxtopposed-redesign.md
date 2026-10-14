# Juxtopposed-inspired VLC interface

This personal fork adapts the desktop Qt/QML interface to the community concept
by [Juxtopposed (@juxtopposed)](https://www.youtube.com/@juxtopposed). Thank you
for [I Redesigned VLC After 25 Years](https://www.youtube.com/watch?v=ERFeOgqk324)
and [the original design file](https://www.figma.com/community/file/1691465999134370980).
The design concept is credited to Juxtopposed; the implementation is an independent
community adaptation and is not an endorsed VideoLAN release.

## Source implementation

- Native Day and Night palettes use the reference orange (#D37918), graphite
  window chrome (#1B1B1B), near-black canvas (#0E0E0E), recessed seek surface
  (#090909), and muted labels (#8F8F8F). System theme providers still control the
  System scheme.
- Inter is used when installed, with Segoe UI on Windows or the application's
  font as fallback. DM Mono is used for time if installed, with Consolas/monospace
  fallback. No font binaries are bundled.
- Shared labels, buttons, text fields, navigation, and player titles use the
  reference typography and rounded controls. The collapsed navigation rail is
  50 logical pixels; expanded navigation retains VLC's existing tree model.
- Play/Pause uses a 54 by 32 logical-pixel accent button, including keyboard focus
  and the existing press-and-hold Stop action.
- Pinned video/audio controls embed the seek row between transport and options
  when the window is at least 1200 logical pixels wide and all controls plus
  the seek row fit. Smaller windows and profiles with a center group use the
  stacked layout. Chapter seeking, bookmarks, time toggling, and playback menus
  continue using VLC's existing components and handlers.
- The built-in Default Style moves video/audio transport controls to the left
  and playback options to the right. Its control IDs are retained. Saved toolbar
  profiles are not migrated or overwritten; the miniplayer profile is unchanged.

## Trying it after building

Use VLC's **Night** scheme for the dark reference, or **Day** for the light
variant. System mode follows the operating system palette rather than these
reference colors. Enable pinned video controls and use a wide window to see
the inline seek row. If an existing Default Style was saved before this fork,
create/select a fresh Default Style in the toolbar editor to use the new groups.
Do not reset all VLC preferences just to preview the redesign.

Build prerequisites and procedures are maintained in [INSTALL](../INSTALL) and
VLC's platform-specific build documentation. This branch changes native source;
opening a QML file alone does not provide VLC's registered C++ types and services.

### Portable Windows build on the personal fork

The [Windows build workflow](../.github/workflows/vlc-win64-build.yml) uses
VideoLAN's win64 CI image pinned by digest and the matching upstream prebuilt
contribs. Its [build script](../.github/scripts/build-win64.sh) compiles the full
Qt interface and packages a portable Windows ZIP. The workflow uploads build
logs, a source/dependency receipt, and ZIP checksums. It does not install tools
or VLC on the user's PC. Run the extracted `vlc.exe` after a successful build.

The workflow runs when its files are pushed on `redesign/juxtopposed-ui`, or by
manual dispatch. It is restricted to the `Viswa220522/vlc` fork. If the matching
upstream dependency bundle is unavailable, it stops with the dependency URL
rather than attempting to compile the entire dependency stack. A successful
package still needs application runtime and visual checks.

## Reference gaps and adaptations

The Brix import was inspected directly through JSX and computed styles. It has
no design tokens. The imported player image is broken, so no replacement video
artwork was inferred or added. The 50-pixel rail and 377-pixel browser in the
concept are adapted to VLC's existing resizable navigation pane; this change
does not implement a second library browser beside the rail.

The concept's onboarding, waveform timeline, subtitle timeline, and redesigned
settings panels are not implemented here. VLC's QWidget preferences and dialogs
remain existing native dialogs. Imported screenshots, font files, and media
artwork are not copied into the application. These gaps require further design
mapping and native implementation before claiming a complete concept port.

## Validation status

Source files were reviewed, delimiters checked, QML IDs checked for duplicates,
and the default profile's control IDs compared with the original. Measured
contrast ratios are 15.61:1 for primary dark text, 5.33:1 for secondary dark text
on window chrome, 5.62:1 for the play icon, and 10.98:1 for primary light text.

Verification on Windows with Qt 6.11.2 now passes **35 checks with zero failures
and zero Qt runtime warnings/errors**. The real production QML components were
loaded in Qt with isolated VLC service/type adapters. Resize/profile changes,
empty/crowded profiles, 100%/150%/200% scaling, Day/Night selection, Tab order,
pointer/keyboard seeking, chaptered timelines, Play/Pause, both Stop hold actions,
custom accent contrast, and component rendering were exercised. Qt-rendered
wide, narrow, and light component captures were visually reviewed.

`qmllint` reports zero syntax/duplicate-binding errors for all 14 changed QML
files. Its full diagnostics are retained: native VLC module/type information is
not built, so the full semantic lint still contains unresolved-type/import and
related warnings. These results do not constitute a clean fully typed lint run.
Git whitespace checks, Python compilation, palette color literal validation,
default toolbar control inventory checks, and workflow `actionlint` pass.

The runtime checks reproduced and fixed the disappearing compact seek thumb,
unreadable custom accent foregrounds, and seek-host null accesses. A malformed
native palette color literal was corrected, and font fallback was made explicit.
See [the repeatable test runner](../modules/gui/qt/tests/redesign/README.md).
The GitHub workflow is prepared for Windows and Linux; it has not been run on
GitHub yet. Local reports and component captures are in the workspace's
`.validation/redesign` directory.

**Pending:** a full C++ VLC build, fully typed lint against the generated VLC
modules, and application integration testing with real media/backend services.
This machine has no C++ build toolchain or VLC native dependencies installed.
The test adapters do not validate decoding, preferences dialogs, or live menus.

Application integration checks to complete before treating this branch as ready:

- Load Day, Night, and System themes; verify custom accents and 100%/150% scaling.
- Play video and audio; compare pinned wide, pinned narrow, and floating controls.
- Resize across the compact threshold and change toolbar profiles while playing.
- Use Tab, arrows, and accessibility actions across transport, seek, and options.
- Seek chaptered and unchaptered media, resume playback, display bookmarks,
  toggle remaining time, and open playback menus.
- Use pointer and keyboard press-and-hold Stop and verify toolbar editor previews.
- Inspect long titles, expanded/collapsed navigation, and the miniplayer.

## Submission

Changes are intended for the Viswa220522 personal fork. No PR has been opened.
PR creation requires the user's approval after validation. VLC upstream directs
contributions through [VideoLAN GitLab](https://code.videolan.org/videolan/vlc).
