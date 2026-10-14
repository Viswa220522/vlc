# Desktop redesign checks

Create a Python environment and install `requirements.txt`, then run:

```sh
python modules/gui/qt/tests/redesign/verify.py --output /path/to/test-artifacts
```

The runner checks all 14 QML files changed by the redesign even after committing
them. Qt's `qmllint` parses the files and treats duplicate bindings/names as
errors. A deliberately invalid fixture verifies that the parser rejects errors.
The full lint JSON is retained, including warnings about unavailable native VLC
modules; this is not a clean, fully typed VLC lint run.

Production control bar, control layout, repeaters, timeline, Play/Pause, shared
widgets, and style files are loaded without rewriting them. A hash manifest
records the source files used. The tests use real Qt Quick layout, rendering,
pointer, and keyboard events. VLC backend services and native attached types
are isolated test adapters. Option buttons stand in for backend-dependent
menus, so these tests do not validate media decoding, popup menus, or the
complete VLC application.

The checks cover resizing, profile replacement, empty/crowded profiles,
100%/150%/200% scaling, Day/Night selection, Tab order, pointer/keyboard seeking,
chaptered timelines, Play/Pause and Stop holds, custom accent contrast, palette
color literals, and retention of the default toolbar controls. All Qt runtime
warnings and errors fail the run. Component screenshots and JSON reports are
written to the output directory. A full native VLC build remains required for
C++ compilation and application integration checks.
