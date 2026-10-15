#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Render and exercise the production reference chrome with isolated services.

This validates QML layout and signal wiring. The C++ media engine, native window
buttons, native menus, and C++ image provider require the separate portable test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

import verify as v
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QResource, QSize, QUrlQuery
from PySide6.QtGui import QFontDatabase, QImageReader


class ReferenceImageProvider(v.DesignImageProvider):
    def requestImage(self, identifier, size, requested):
        if not identifier.startswith("DesignVolume"):
            return super().requestImage(identifier, size, requested)
        query = QUrlQuery(v.QUrl(identifier))
        volume = max(0, min(2, float(query.queryItemValue("volume"))))
        svg = (v.QT / "pixmaps/juxtopposed/volume.svg").read_bytes()
        svg = svg.replace(b'layer-name="Rectangle 7"',
                          f'transform="scale({volume * 88 / 66},1)" layer-name="Rectangle 7"'.encode())
        svg = svg.replace(b'fill="#262626"', b'fill="#ffffff"')
        svg = svg.replace(b'fill="rgb(0 0 0 / 20%)"', b'fill="#000000" fill-opacity="0.2"')
        buffer = QBuffer()
        buffer.setData(QByteArray(svg))
        buffer.open(QIODevice.ReadOnly)
        reader = QImageReader(buffer, QByteArray(b"SVG"))
        reader.setScaledSize(requested)
        return reader.read()


def fixtures(output):
    imports = output / "imports"
    manifest = v.fixture_modules(imports)
    extra = {
        "Widgets": {name: v.QT / f"widgets/qml/{name}.qml" for name in
                    ("DesignTitleBar", "SliderExt")},
        "MainInterface": {"DesignNavigationPane": v.QT / "maininterface/qml/DesignNavigationPane.qml",
            "DesignBrowser": v.QT / "maininterface/qml/DesignBrowser.qml",
            "NavigationModel": "import QtQuick\nQtObject { property bool hasMedialib: true }",
            "CSDButton": "pragma Singleton\nimport QtQuick\nQtObject { enum Types { Minimize, MaximizeRestore, Close } }"},
        "Player": {"DesignPlayerControls": v.QT / "player/qml/DesignPlayerControls.qml",
                   "PlayerBrowser": v.QT / "player/qml/PlayerBrowser.qml"},
        "PlayerControls": {name: v.QT / f"player/qml/controlbarcontrols/{name}.qml" for name in
                           ("PreviousButton", "NextButton", "VolumeWidget")},
        "Menus": {"QmlGlobalMenu": """import QtQuick
QtObject {
    property var ctx
    signal aboutToShow()
    signal aboutToHide()
    function popup(position) { aboutToShow() }
    function close() { aboutToHide() }
}"""},
        "Dialogs": {"DesignNewPlaylist": v.QT / "dialogs/dialogs/qml/DesignNewPlaylist.qml",
            "DialogsProvider": """pragma Singleton
import QtQuick
QtObject {
    property int opens: 0
    function simpleOpenDialog() { opens++ }
    function showSimpleOpen(title) { return ["file:///test-track.wav"] }
    function selectPlaylistThumbnail() { return "" }
    function selectMediaFolder() { return "" }
}"""},
        "MediaLibrary": {
            "MediaLib": "pragma Singleton\nimport QtQuick\nQtObject { property var lastPlayed; function addAndPlay(id) { lastPlayed = id } }",
            "MLPlaylistListModel": """import QtQuick
import QtQml.Models
ListModel {
    enum Types { PLAYLIST_TYPE_ALL, PLAYLIST_TYPE_AUDIO, PLAYLIST_TYPE_VIDEO }
    property var ml
    property int playlistType: 0
    property int sortOrder: 0
    property bool transactionPending: false
    signal playlistCreated(string id)
    function create(name, files) {
        append({name: name, id: "playlist-3"})
        playlistCreated("VLC_ML_PARENT_PLAYLIST - 3")
    }
    Component.onCompleted: {
        append({ name: "Cool Songs", id: "playlist-1" })
        append({ name: "Anime to Watch", id: "playlist-2" })
    }
}""",
            "MLPlaylistModel": """import QtQuick
import QtQml.Models
ListModel { property var ml; property var parentId; property int sortOrder: 0
    Component.onCompleted: append({ title: "Track", id: "track-1" })
}""",
            "MLVideoFoldersModel": """import QtQuick
import QtQml.Models
ListModel { property var ml; property int sortOrder: 0
    Component.onCompleted: append({ title: "Shows", id: "folder-1" })
}""",
            "MLVideoModel": "import QtQuick\nimport QtQml.Models\nListModel { property var ml; property var parentId; property int sortOrder: 0 }",
            "MLRecentMediaModel": "import QtQuick\nimport QtQml.Models\nListModel { property var ml; property int sortOrder: 0 }",
        },
        "Network": {"MLFolderModel": "import QtQuick\nQtObject { property var ctx; function add(url) {} }"},
    }
    for module, sources in extra.items():
        directory = imports / "VLC" / module
        existing = (directory / "qmldir").read_text() if (directory / "qmldir").exists() else f"module VLC.{module}\n"
        generated = v.write_module(imports, module, sources)
        entries = (directory / "qmldir").read_text().splitlines()[1:]
        (directory / "qmldir").write_text(existing.rstrip() + "\n" + "\n".join(entries) + "\n")
        manifest.update(generated)
    main_file = imports / "VLC/MainInterface/MainCtx.qml"
    main = main_file.read_text().replace("    function dp", """    property int maxVolume: 200
    property bool clientSideDecoration: true
    property int fullScreens: 0
    property bool playerView: true
    property bool gridView: true
    property var fixtureSettings: ({})
    function settingValue(key, fallback) { return fixtureSettings[key] ?? fallback }
    function setSettingValue(key, value) { fixtureSettings[key] = value }
    property QtObject search: QtObject { function askShow() {} }
    property QtObject intfMainWindow: QtObject { property int visibility: 2 }
    property QtObject playqueuePanel: QtObject { property bool visible: false }
    property QtObject csdButtonModel: QtObject {
        property list<QtObject> windowCSDButtons: [
            QtObject { property int type: 0; property rect rect; property int clicks: 0; function click() { clicks++ } },
            QtObject { property int type: 1; property rect rect; property int clicks: 0; function click() { clicks++ } },
            QtObject { property int type: 2; property rect rect; property int clicks: 0; function click() { clicks++ } }
        ]
    }
    function toggleInterfaceFullScreen() { fullScreens++ }
    function dp""")
    main_file.write_text(main)
    history = imports / "VLC/MainInterface/History.qml"
    history.write_text("""pragma Singleton
import QtQuick
QtObject {
    property var viewPath: ["video", "playlists"]
    function previous(reason) {}
    function push(path, properties) { viewPath = path }
}""")
    player = imports / "VLC/Player/Player.qml"
    player.write_text(player.read_text().replace("    property real rate: 1", """    property real rate: 1
    property real volume: 0.75
    property bool muted: false
    function setVolumeUp(steps) { volume = Math.min(2, volume + (steps || 1) * 0.05) }
    function setVolumeDown(steps) { volume = Math.max(0, volume - (steps || 1) * 0.05) }"""))
    playlist = imports / "VLC/Playlist/MainPlaylistController.qml"
    playlist.write_text(playlist.read_text().replace("    property int stops: 0", """    property int stops: 0
    property bool hasPrev: true
    property bool hasNext: true
    property int previousCalls: 0
    property int nextCalls: 0
    function prev() { previousCalls++ }
    function next() { nextCalls++ }"""))
    palette = imports / "VLC/Style/ColorContext.qml"
    palette.write_text(palette.read_text().replace("readonly property color highlight: \"#D37918\"",
        'readonly property color secondary: root.dark ? "#262626" : "#bdbdbd"\n        readonly property color highlight: "#D37918"')
        .replace('readonly property color highlight: "#161616"',
                 'readonly property color negative: "#ff3737"\n        readonly property color highlight: "#161616"'))
    effects = imports / "VLC/Util/Effects.qml"
    effects.write_text(effects.read_text().replace("enum Effect { TintedImage }", "enum Effect { TintedImage, DesignVolume }")
        .replace('"image://effects/TintedImage?path="', '(effect === Effects.DesignVolume ? "image://effects/DesignVolume?path=" : "image://effects/TintedImage?path=")')
        .replace('+ "&color=" + encodeURIComponent(properties.color)', '+ "&color=" + encodeURIComponent(properties.color) + "&volume=" + (properties.volume || 0)'))
    assets = list((v.QT / "pixmaps/juxtopposed").glob("*.svg"))
    qrc = output / "reference-assets.qrc"
    drag_adapter = output / "csd-drag-adapter.qml"
    drag_adapter.write_text("import QtQuick\nItem { property bool csdMenuVisible: false }")
    qrc.write_text('<RCC><qresource prefix="/juxtopposed">' + ''.join(
        f'<file alias="{escape(p.name)}">{escape(p.as_posix())}</file>' for p in assets)
        + '</qresource><qresource prefix="/qt/qml/VLC/Widgets">'
        + f'<file alias="CSDTitlebarTapNDrapHandler.qml">{escape(drag_adapter.as_posix())}</file>'
        + '</qresource></RCC>')
    rcc = Path(v.PySide6.__file__).parent / ("rcc.exe" if sys.platform == "win32" else "Qt/libexec/rcc")
    subprocess.run([str(rcc), "--binary", str(qrc), "-o", str(output / "reference-assets.rcc")], check=True)
    if not QResource.registerResource(str(output / "reference-assets.rcc")):
        raise AssertionError("Could not register the reference asset bundle")
    for path in assets:
        manifest[str(path.relative_to(v.REPO))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output / "source-manifest.json").write_text(json.dumps(manifest, indent=2))
    return imports


SCENE = """import QtQuick
import QtQuick.Window
import VLC.MainInterface
import VLC.Player
import VLC.Style
import VLC.Widgets as Widgets
Window {
    id: root
    width: 1920; height: 1080; visible: true
    color: "#000000"
    property var controlStrip: strip
    property var titleBar: titleBar
    property var browser: browser
    property int audioRequests: 0
    property int subtitleRequests: 0
    property int settingsRequests: 0
    property int queueRequests: 0
    readonly property real volume: Player.volume
    readonly property bool muted: Player.muted
    readonly property int previousCalls: MainPlaylistController.previousCalls
    readonly property int nextCalls: MainPlaylistController.nextCalls
    readonly property int fullScreens: MainCtx.fullScreens
    readonly property int opens: DialogsProvider.opens
    function enableLibrary() { MainCtx.mediaLibraryAvailable = true }
    function setVolume(value) { Player.volume = value }
    PlayerBrowser { id: browser; width: 427; y: 40; height: 986 }
    Widgets.DesignTitleBar { id: titleBar; width: parent.width; libraryControls: true }
    DesignPlayerControls {
        id: strip
        anchors.bottom: parent.bottom
        width: parent.width
        onAudioRequested: root.audioRequests++
        onSubtitlesRequested: root.subtitleRequests++
        onSettingsRequested: root.settingsRequests++
        onQueueRequested: root.queueRequests++
    }
}
""".replace("import VLC.Style", "import VLC.Style\nimport VLC.Playlist\nimport VLC.Dialogs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if sys.platform != "win32" and not v.os.environ.get("XDG_RUNTIME_DIR"):
        runtime = output / "xdg-runtime"
        runtime.mkdir(mode=0o700, exist_ok=True)
        runtime.chmod(0o700)
        v.os.environ["XDG_RUNTIME_DIR"] = str(runtime)
    imports = fixtures(output)
    messages = []
    def diagnostic(kind, context, message):
        if kind in (v.QtMsgType.QtWarningMsg, v.QtMsgType.QtCriticalMsg, v.QtMsgType.QtFatalMsg):
            messages.append(message)
            print("QT:", message, flush=True)
    v.qInstallMessageHandler(diagnostic)
    app = v.QGuiApplication(sys.argv[:1])
    for font in (v.QT / "pixmaps/fonts").rglob("*.ttf"):
        if QFontDatabase.addApplicationFont(str(font)) < 0:
            raise AssertionError(f"Font registration failed: {font}")
    engine = v.QQmlEngine()
    engine.addImageProvider("effects", ReferenceImageProvider())
    engine.addImportPath(str(imports))
    scene = output / "ReferenceScene.qml"
    scene.write_text(SCENE)
    component = v.QQmlComponent(engine, v.QUrl.fromLocalFile(str(scene)))
    root = component.create()
    if not root:
        raise AssertionError([error.toString() for error in component.errors()])
    v.call(engine, root, "enableLibrary")
    v.QTest.qWait(300)
    tests = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        tests.append(name)
        print("PASS:", name, flush=True)
    for vector in sorted((v.QT / "pixmaps/juxtopposed").glob("*.svg")):
        if vector.name == "volume.svg":
            continue  # The dynamic gauge needs the normalization tested below.
        document = ET.parse(vector).getroot()
        check(f"{vector.name} contains vector artwork", all(
            element.tag.rsplit('}', 1)[-1] != 'image' for element in document.iter()))
        width, height = float(document.get("width")), float(document.get("height"))
        for density in (1, 1.5, 2, 3):
            requested = QSize(round(width * density), round(height * density))
            reader = QImageReader(str(vector), b"SVG")
            reader.setScaledSize(requested)
            rendered = reader.read()
            if rendered.size() != requested or not any(
                rendered.pixelColor(x, y).alpha() for x in range(rendered.width()) for y in range(rendered.height())):
                raise AssertionError(f"{vector.name} failed at pixel density {density}: {reader.errorString()}")
        check(f"{vector.name} renders at 1x/1.5x/2x/3x without diagnostics", not messages)
    def item(name):
        result = root.findChild(v.QQuickItem, name)
        if result is None:
            raise AssertionError(f"Missing production item: {name}")
        return result
    def visual_items():
        pending = [root.contentItem()]
        while pending:
            current = pending.pop()
            yield current
            pending.extend(current.childItems())
    def button(description):
        for current in visual_items():
            if current.property("description") == description:
                return current
        raise AssertionError(f"Missing button: {description}")
    def text_button(text):
        return next(o for o in visual_items() if o.property("text") == text and o.property("down") is not None)
    def click(target):
        pos = target.mapToScene(v.QPointF(target.width()/2, target.height()/2))
        v.QTest.mouseClick(root, v.Qt.LeftButton, v.Qt.NoModifier, pos.toPoint())
        v.QTest.qWait(80)
    strip = root.property("controlStrip")
    check("reference strip height 54", strip.height() == 54)
    for name, x, width in (("referenceTransport", 20, 130), ("referenceTimelineGroup", 170, 1406),
                           ("referenceVolume", 1596, 120), ("referenceOptions", 1736, 114)):
        target = item(name)
        pos = target.mapToItem(strip, v.QPointF())
        check(f"reference geometry {name}", abs(pos.x()-x) < 1 and abs(target.width()-width) < 1)
    check("reference title bar height 40", root.property("titleBar").height() == 40)
    check("reference rail width 50", item("referenceNavigationRail").width() == 50)
    check("reference browser width 427", root.property("browser").width() == 427)
    # Native video auto-resize previously shrank the window below the strip's
    # usable width. Exercise the new minimum as well as the timestamp boundary.
    for width in (614, 800):
        root.setWidth(width)
        v.QTest.qWait(100)
        groups = [item(name) for name in ("referenceTransport", "referenceTimelineGroup",
                  "referenceVolume", "referenceOptions")] + [button("Play queue")]
        bounds = [(group.mapToItem(strip, v.QPointF()).x(), group.width()) for group in groups]
        check(f"all playback groups fit at {width}px", all(x >= 19 and x + w <= width - 19
              for x, w in bounds) and all(x + w <= nx for (x, w), (nx, _) in zip(bounds, bounds[1:])))
    root.setWidth(1920)
    v.QTest.qWait(100)
    click(item("referencePrevious"))
    check("previous command", root.property("previousCalls") == 1)
    click(item("referenceNext"))
    check("next command", root.property("nextCalls") == 1)
    for desc, prop in (("Audio", "audioRequests"), ("Subtitles", "subtitleRequests"),
                       ("Settings", "settingsRequests"), ("Play queue", "queueRequests")):
        click(button(desc))
        check(f"{desc} action", root.property(prop) == 1)
    click(button("Mute"))
    check("mute command", root.property("muted"))
    click(button("Full screen"))
    check("full screen command", root.property("fullScreens") == 1)
    slider = item("referenceTimeline")
    click(slider)
    v.QTest.keyClick(root, v.Qt.Key_Right)
    check("timeline receives keyboard focus", slider.hasActiveFocus())
    # Crop this render only for component QA. It is never used as an application asset.
    image = root.grabWindow()
    image.copy(0, 0, 1920, 40).save(str(output / "titlebar.png"))
    image.copy(0, 1026, 1920, 54).save(str(output / "controls.png"))
    image.copy(0, 40, 50, 986).save(str(output / "navigation-rail.png"))
    image.copy(0, 40, 427, 986).save(str(output / "browser.png"))
    browser = root.property("browser")
    click(text_button("Cool Songs"))
    check("playlist opens its native model", browser.property("locationKind") == "playlist" and browser.property("itemCount") == 1)
    click(button("Back"))
    check("browser back restores playlist list", browser.property("locationKind") == "playlists" and browser.property("itemCount") == 2)
    click(button("Forward"))
    check("browser forward restores playlist contents", browser.property("locationKind") == "playlist")
    click(button("Back"))
    click(text_button("Create playlist"))
    save = item("newPlaylistSave")
    check("unnamed playlist cannot be saved", not save.isEnabled())
    popup_image = root.grabWindow()
    popup_image.copy((1920-713)//2, (1080-590)//2, 713, 590).save(str(output / "new-playlist.png"))
    field = item("newPlaylistTitle")
    click(field)
    for character in "Test playlist":
        modifiers = v.Qt.ShiftModifier if character.isupper() else v.Qt.NoModifier
        v.QTest.keyClick(root, ord(character.upper()), modifiers)
    check("named playlist can be saved", save.isEnabled())
    click(button("Select files"))
    click(save)
    check("playlist creation reaches model", browser.property("itemCount") == 3)
    provider = ReferenceImageProvider()
    pixels = []
    for volume in (0, 0.5, 0.75, 1, 1.5, 2):
        v.call(engine, root, "setVolume", volume)
        v.QTest.qWait(100)
        gauge = provider.requestImage(f"DesignVolume?volume={volume}", QSize(), QSize(264, 84))
        count = 0
        for x in range(gauge.width()):
            for y in range(gauge.height()):
                color = gauge.pixelColor(x, y)
                if color.alpha() > 100 and max(color.red(), color.green(), color.blue()) - min(color.red(), color.green(), color.blue()) > 10:
                    count += 1
        pixels.append(count)
        check(f"volume {volume} renders without diagnostics", not messages)
    check("volume indicator is empty at zero and grows with level", pixels[0] == 0 and all(a < b for a, b in zip(pixels, pixels[1:])))
    check("no Qt warnings/errors", not messages)
    (output / "report.json").write_text(json.dumps({"checks": tests, "runtimeMessages": messages,
        "scope": __doc__}, indent=2))
    root.close()
    root.deleteLater()
    app.processEvents()
    print(f"Result: {len(tests)} reference checks passed", flush=True)


if __name__ == "__main__":
    main()
