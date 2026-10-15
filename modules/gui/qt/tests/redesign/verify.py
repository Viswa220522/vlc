#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise production QML in real Qt with isolated VLC service adapters.

This is not a VLC engine integration test. It checks QML parsing and the
layout/input behavior of the actual components, without decoding media.
Run with the Python environment from requirements.txt. Generated files and
reports go into --output (outside the source tree by default).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"))

import PySide6
from PySide6.QtCore import QObject, Property, Signal, Slot, QPointF, QSize, Qt, QUrl, QUrlQuery, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QColor, QImage, QImageReader, QPainter
from PySide6.QtQml import QQmlEngine, QQmlComponent, QJSValue, QmlAttached, QmlNamedElement
from PySide6.QtQuick import QQuickItem, QQuickImageProvider
from PySide6.QtTest import QTest

REPO = Path(__file__).resolve().parents[5]
QT = REPO / "modules/gui/qt"
QML_IMPORT_NAME = "VLC.MainInterface"
QML_IMPORT_MAJOR_VERSION = 1

CHECKED_QML = [
    "maininterface/qml/MainDisplay.qml", "maininterface/qml/SideNavigationDelegate.qml",
    "maininterface/qml/SideNavigationPane.qml", "player/qml/ControlBar.qml",
    "player/qml/Player.qml", "player/qml/PlayerControlLayout.qml", "player/qml/SliderBar.qml",
    "player/qml/TracksMenu.qml",
    "player/qml/TopBar.qml", "player/qml/controlbarcontrols/PlayButton.qml", "style/VLCStyle.qml",
    "widgets/qml/ButtonExt.qml", "widgets/qml/IconToolButton.qml", "widgets/qml/LabelExt.qml",
    "widgets/qml/TextFieldExt.qml", "widgets/qml/DesignIcon.qml",
    "widgets/qml/DesignIconButton.qml", "widgets/qml/DesignTitleBar.qml",
    "maininterface/qml/DesignNavigationPane.qml", "player/qml/MiniPlayer.qml",
    "player/qml/DesignPlayerControls.qml", "player/qml/controlbarcontrols/VolumeWidget.qml",
    "maininterface/qml/DesignBrowser.qml", "player/qml/PlayerBrowser.qml",
    "dialogs/dialogs/qml/DesignNewPlaylist.qml", "maininterface/qml/MainInterface.qml",
    "medialibrary/qml/PlaylistMediaList.qml",
]


def attached_property(kind, name, default, notify):
    def get(self):
        return self.values.get(name, default)
    def set_value(self, value):
        if self.values.get(name, default) != value:
            self.values[name] = value
            self.changed.emit()
    return Property(kind, get, set_value, notify=notify)


class Attached(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = {}


class NavAttached(Attached):
    changed = Signal(name="changed")
    navigable = attached_property(bool, "navigable", True, changed)
    parentItem = attached_property(QObject, "parentItem", None, changed)
    upItem = attached_property(QObject, "upItem", None, changed)
    downItem = attached_property(QObject, "downItem", None, changed)
    leftItem = attached_property(QObject, "leftItem", None, changed)
    rightItem = attached_property(QObject, "rightItem", None, changed)
    cancelItem = attached_property(QObject, "cancelItem", None, changed)
    upAction = attached_property(QJSValue, "upAction", QJSValue(), changed)
    downAction = attached_property(QJSValue, "downAction", QJSValue(), changed)
    leftAction = attached_property(QJSValue, "leftAction", QJSValue(), changed)
    rightAction = attached_property(QJSValue, "rightAction", QJSValue(), changed)
    cancelAction = attached_property(QJSValue, "cancelAction", QJSValue(), changed)

    @Slot(QObject)
    def defaultKeyAction(self, event):
        if event.property("accepted"):
            return
        methods = {Qt.Key_Right: self.defaultNavigationRight, Qt.Key_Left: self.defaultNavigationLeft,
                   Qt.Key_Up: self.defaultNavigationUp, Qt.Key_Down: self.defaultNavigationDown}
        fn = methods.get(event.property("key"))
        if fn:
            event.setProperty("accepted", True)
            fn()

    @Slot(QObject)
    def defaultKeyReleaseAction(self, event):
        pass

    def move(self, direction):
        action = self.values.get(direction + "Action")
        if action and action.isCallable():
            result = action.call()
            if not result.isBool() or result.toBool():
                return
        target = self.values.get(direction + "Item")
        if isinstance(target, QQuickItem) and target.isEnabled() and target.isVisible():
            target.forceActiveFocus(Qt.TabFocusReason)

    @Slot()
    def defaultNavigationRight(self): self.move("right")
    @Slot()
    def defaultNavigationLeft(self): self.move("left")
    @Slot()
    def defaultNavigationUp(self): self.move("up")
    @Slot()
    def defaultNavigationDown(self): self.move("down")


@QmlNamedElement("Navigation")
@QmlAttached(NavAttached)
class Navigation(QObject):
    @staticmethod
    def qmlAttachedProperties(_type, parent): return NavAttached(parent)


QML_IMPORT_NAME = "VLC.Util"


class IdAttached(Attached):
    changed = Signal(name="changed")
    id = attached_property(str, "id", "", changed)


@QmlNamedElement("AccessibleCompat")
@QmlAttached(IdAttached)
class AccessibleCompat(QObject):
    @staticmethod
    def qmlAttachedProperties(_type, parent): return IdAttached(parent)


QML_IMPORT_NAME = "VLC.Widgets"


class TooltipAttached(Attached):
    changed = Signal(name="changed")
    instance = attached_property(QObject, "instance", None, changed)
    visible = attached_property(bool, "visible", False, changed)
    text = attached_property(str, "text", "", changed)
    pos = attached_property(QPointF, "pos", QPointF(), changed)


@QmlNamedElement("PointingToolTipAttached")
@QmlAttached(TooltipAttached)
class PointingToolTipAttached(QObject):
    @staticmethod
    def qmlAttachedProperties(_type, parent): return TooltipAttached(parent)


def write_module(base, module, sources):
    directory = base / "VLC" / module
    directory.mkdir(parents=True, exist_ok=True)
    entries = [f"module VLC.{module}"]
    manifest = {}
    for name, content in sources.items():
        if isinstance(content, Path):
            manifest[str(content.relative_to(REPO))] = hashlib.sha256(content.read_bytes()).hexdigest()
            content = content.read_text(encoding="utf-8-sig")
        (directory / f"{name}.qml").write_text(content, encoding="utf-8")
        prefix = "singleton " if "pragma Singleton" in content else ""
        entries.append(f"{prefix}{name} 1.0 {name}.qml")
    (directory / "qmldir").write_text("\n".join(entries) + "\n", encoding="utf-8")
    return manifest


def fixture_modules(base):
    manifest = {}
    main = {
        "MainCtx": '''pragma Singleton
import QtQuick
import VLC.PlayerControls
QtObject {
    property real intfScaleFactor: 1
    property bool pinVideoControls: true
    property bool mediaLibraryAvailable: false
    property bool showRemainingTime: false
    property bool usingTouch: false
    property color testAccent: "#D37918"
    property real safeArea: 0
    property QtObject colorScheme: QtObject { property int scheme: 2 }
    property QtObject controlbarProfileModel: QtObject {
        property QtObject currentModel: QtObject {
            property PlayerControlbarModel fixture: PlayerControlbarModel {}
            function getModel(identifier) { return fixture }
        }
    }
    function dp(value, scale) { return Math.round(value * (scale || intfScaleFactor)) }
}''',
        "History": '''pragma Singleton
import QtQuick
QtObject { function previous(reason) {} }''',
    }
    style = {
        "VLCStyle": QT / "style/VLCStyle.qml",
        "ColorSchemeModel": '''pragma Singleton
import QtQuick
QtObject { enum Scheme { System, Day, Night } }''',
        "SystemPalette": '''import QtQuick
QtObject { property int source: 2; property var ctx; property bool isDark: source === 2 }''',
        "ColorContext": '''import QtQuick
import VLC.MainInterface
QtObject {
    id: root
    enum Sets { View, Window, Item, Badge, ButtonStandard, ButtonAccent, ToolButton, TabButton, MenuBar, Tooltip, Slider, ComboBox, SpinBox, TextField, Switch }
    property int colorSet: ColorContext.View
    property var palette: VLCStyle.palette
    property bool enabled: true
    property bool focused: false
    property bool hovered: false
    property bool pressed: false
    property bool initialized: true
    readonly property bool dark: palette?.isDark ?? true
    readonly property color accent: MainCtx.testAccent
    readonly property color visualFocus: dark ? "#E7E7E7" : "#2E2E2E"
    readonly property color separator: dark ? "#373737" : "#ACACAC"
    readonly property color border: "transparent"
    readonly property QtObject bg: QtObject {
        readonly property color highlight: "#D37918"
        readonly property color primary: root.colorSet === ColorContext.ButtonAccent ? root.accent
            : root.colorSet === ColorContext.Slider || root.colorSet === ColorContext.TextField ? (root.dark ? "#090909" : "#DEDEDE")
            : root.colorSet === ColorContext.Window ? (root.dark ? "#1B1B1B" : "#D5D5D5")
            : root.colorSet === ColorContext.ToolButton ? "transparent" : (root.dark ? "#0E0E0E" : "#E7E7E7")
    }
    readonly property QtObject fg: QtObject {
        readonly property color highlight: "#161616"
        readonly property color primary: root.colorSet === ColorContext.ButtonAccent ? (Qt.colorEqual(root.accent, "#D37918") ? "#161616" : "#FFFFFF")
            : root.colorSet === ColorContext.Slider ? root.accent : (root.dark ? "#E7E7E7" : "#2E2E2E")
        readonly property color secondary: root.dark ? "#8F8F8F" : "#4A4A4A"
        readonly property color neutral: root.accent
    }
}''',
        "VLCIcons": '',  # Generated from the native icon header below.
    }
    controls = {
        "PlayButton": QT / "player/qml/controlbarcontrols/PlayButton.qml",
        "FixtureControl": '''import QtQuick
import VLC.Style
import VLC.Widgets as Widgets
Widgets.IconToolButton {
    text: VLCIcons.ellipsis
    description: "Fixture option (test backend)"
    activeFocusOnTab: true
}''',
        "PlayerControlbarModel": '''import QtQuick
import QtQml.Models
QtObject {
    property ListModel left: ListModel { ListElement { controlId: "PlayButton" } }
    property ListModel center: ListModel {}
    property ListModel right: ListModel { ListElement { controlId: "FixtureControl" } }
    readonly property bool empty: left.count + center.count + right.count === 0
}''',
        "ControlListFilter": '''import QtQuick
import QtQml.Models
ListModel {
    id: root
    property var sourceModel: null
    property var player
    property var ctx
    function reload() {
        clear()
        if (sourceModel) for (let i = 0; i < sourceModel.count; ++i) append({ id: sourceModel.get(i).controlId })
    }
    onSourceModelChanged: reload()
    property Connections listener: Connections { target: root.sourceModel; function onCountChanged() { root.reload() } }
}''',
    }
    player = {name: QT / f"player/qml/{name}.qml" for name in
              ["ControlBar", "PlayerControlLayout", "ControlRepeater", "ControlLayout", "SliderBar"]}
    player["PlayerControlbarControls"] = '''pragma Singleton
import QtQuick
QtObject { function control(id) { return { source: Qt.resolvedUrl("../PlayerControls/" + id + ".qml") } } }'''
    player["Player"] = '''pragma Singleton
import QtQuick
import QtQml.Models
QtObject {
    enum States { PLAYING_STATE_STOPPED, PLAYING_STATE_PAUSED, PLAYING_STATE_PLAYING }
    property int playingState: Player.PLAYING_STATE_PLAYING
    property real position: 0.25
    property real buffering: 1
    property real rate: 1
    property bool hasChapters: false
    signal inputChanged()
    property QtObject time: QtObject {
        function formatHMS(flags) { return "02:10" }
        function isSubHour() { return true }
    }
    property QtObject length: QtObject {
        function formatHMS(flags) { return "25:40" }
        function isSubHour() { return true }
        function isSubSecond() { return false }
        function scale(value) { return this }
    }
    property QtObject remainingTime: QtObject { function valid() { return true } function formatHMS() { return "23:30" } }
    property ListModel chapters: ListModel {
        function getClosestChapterFromPos(position, threshold) {
            for (let i = 0; i < count; ++i) if (Math.abs(get(i).startPosition - position) <= threshold) return i
            return -1
        }
        function selectChapter(index) { Player.position = get(index).startPosition }
        function getNameAtPosition(position) { return "Chapter" }
    }
    function jumpFwd() { position = Math.min(1, position + 0.02) }
    function jumpBwd() { position = Math.max(0, position - 0.02) }
}'''
    player["VLCTick"] = '''pragma Singleton
import QtQuick
QtObject { enum Format { SubSecondFormattedAsMS } }'''
    util = {name: QT / f"util/qml/{name}.qml" for name in ["FSM", "FSMState", "Helpers", "DelayedBehavior"]}
    util["Effects"] = """pragma Singleton
import QtQuick
QtObject {
    enum Effect { TintedImage }
    function url(effect, properties) {
        return "image://effects/TintedImage?path=" + encodeURIComponent(properties.path)
            + "&color=" + encodeURIComponent(properties.color)
    }
}"""
    util["KeyHelper"] = '''pragma Singleton
import QtQuick
QtObject { function matchOk(event) { return event.key === Qt.Key_Space || event.key === Qt.Key_Return } }'''
    util["WheelToVLCConverter"] = '''import QtQuick
QtObject {
    signal wheelUpDown(int steps)
    signal wheelLeftRight(int steps)
    function qmlWheelEvent(event) { wheelUpDown(event.angleDelta.y / 120) }
}'''
    widgets = {name: QT / f"widgets/qml/{name}.qml" for name in
               ["AnimatedBackground", "LabelExt", "IconLabel", "IconToolButton", "ButtonExt", "TextFieldExt", "DesignIcon", "DesignIconButton"]}
    widgets["ToolTipExt"] = '''import QtQuick
import QtQuick.Controls.Basic
import VLC.Style
ToolTip { property ColorContext colorContext: ColorContext {} }'''
    playlist = {"MainPlaylistController": '''pragma Singleton
import QtQuick
import VLC.Player
QtObject {
    property int toggles: 0
    property int stops: 0
    function togglePlayPause() {
        toggles++
        Player.playingState = Player.playingState === Player.PLAYING_STATE_PLAYING ? Player.PLAYING_STATE_PAUSED : Player.PLAYING_STATE_PLAYING
    }
    function stop() { stops++; Player.playingState = Player.PLAYING_STATE_STOPPED }
}'''}
    icon_header = QT / "style/vlcicons.hpp"
    icon_glyphs = re.findall(r"QChar (\w+)\{ u'\\u([0-9a-f]{4})'", icon_header.read_text(encoding="utf-8"))
    if not icon_glyphs:
        raise AssertionError("No native icon glyphs found in vlcicons.hpp")
    style["VLCIcons"] = '''pragma Singleton
import QtQuick
QtObject {
    property FontLoader loader: FontLoader { source: "VLCIcons.ttf" }
    readonly property string fontFamily: loader.name
''' + "\n".join(f'    readonly property string {name}: "\\u{code}"' for name, code in icon_glyphs) + "\n}"
    for module, sources in [("MainInterface", main), ("Style", style), ("PlayerControls", controls),
                            ("Player", player), ("Util", util), ("Widgets", widgets), ("Playlist", playlist)]:
        manifest.update(write_module(base, module, sources))
    icon_font = QT / "pixmaps/VLCIcons.ttf"
    (base / "VLC/Style/VLCIcons.ttf").write_bytes(icon_font.read_bytes())
    for source in (icon_font, icon_header):
        manifest[str(source.relative_to(REPO))] = hashlib.sha256(source.read_bytes()).hexdigest()
    return manifest


SCENE = '''import QtQuick
import QtQuick.Window
import VLC.MainInterface
import VLC.Player
import VLC.PlayerControls
import VLC.Playlist
import VLC.Style
import VLC.Widgets as Widgets
Window {
    id: root
    width: 1600; height: 240; visible: true
    color: VLCStyle.palette.isDark ? "#0E0E0E" : "#E7E7E7"
    readonly property var testBar: bar
    readonly property var testSlider: bar.contentItem.trackPositionSlider
    readonly property var testPlay: play
    readonly property var testLayout: bar.contentItem.playerControlLayout
    readonly property var testStandaloneSlider: standaloneSlider
    property bool standaloneCompact: true
    readonly property int toggles: MainPlaylistController.toggles
    readonly property int stops: MainPlaylistController.stops
    readonly property real position: Player.position
    readonly property color playColor: play.contentItem.color
    readonly property color playBackground: play.background.children[1].color
    ControlBar {
        id: bar
        anchors.bottom: parent.bottom; width: parent.width
        textPosition: ControlBar.TimeTextPosition.LeftRightSlider
        identifier: 0
    }
    PlayButton { id: play; x: 24; y: 24; activeFocusOnTab: true }
    Widgets.IconToolButton { x: 100; y: 24; text: VLCIcons.settings; description: "Options" }
    Widgets.ButtonExt { x: 160; y: 24; text: "Open" }
    Widgets.TextFieldExt { x: 280; y: 24; width: 240; placeholderText: "Search" }
    SliderBar { id: standaloneSlider; x: 600; y: 24; width: 300; compact: root.standaloneCompact; barHeight: compact ? 28 : 4 }
    function configure(mode: string, newWidth: int) {
        root.width = newWidth
        MainCtx.pinVideoControls = mode !== "floating"
        const model = MainCtx.controlbarProfileModel.currentModel.fixture
        model.left.clear(); model.center.clear(); model.right.clear()
        if (mode === "empty") return
        model.left.append({controlId: "PlayButton"})
        if (mode === "center") model.center.append({controlId: "FixtureControl"})
        const count = mode === "crowded" ? 45 : 4
        for (let i = 0; i < count; ++i) model.right.append({controlId: "FixtureControl"})
    }
    function setCompact(value: bool) { testSlider.compact = value; testSlider.barHeight = value ? 28 : 4 }
    function setScale(value: real) { MainCtx.intfScaleFactor = value }
    function setScheme(value: int) { MainCtx.colorScheme.scheme = value }
    function setAccent(value: string) { MainCtx.testAccent = value }
    function resumePlayback() { Player.playingState = Player.PLAYING_STATE_PLAYING }
    function setChapters(enabled: bool) {
        Player.chapters.clear()
        if (enabled) for (let i = 0; i < 3; ++i) Player.chapters.append({ startPosition: i / 3, endPosition: (i + 1) / 3 })
        Player.hasChapters = enabled
    }
}
'''


def call(engine, obj, name, *args):
    result = engine.newQObject(obj).property(name).call([QJSValue(value) for value in args])
    if result.isError():
        raise AssertionError(result.toString())


class DesignImageProvider(QQuickImageProvider):
    """Adapter for the production provider's CPU tint; does not test its C++ implementation."""
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)

    def requestImage(self, identifier, _size, requested):
        query = QUrlQuery(QUrl(identifier))
        name = Path(query.queryItemValue("path", QUrl.FullyDecoded)).name
        reader = QImageReader(str(QT / "pixmaps/juxtopposed" / name), b"SVG")
        reader.setScaledSize(requested)
        image = reader.read().convertToFormat(QImage.Format_ARGB32_Premultiplied)
        if image.isNull():
            return image
        painter = QPainter(image)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(image.rect(), QColor(query.queryItemValue("color", QUrl.FullyDecoded)))
        painter.end()
        return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO.parent / ".validation/redesign")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if os.name != "nt" and not os.environ.get("XDG_RUNTIME_DIR"):
        runtime_directory = args.output / "xdg-runtime"
        runtime_directory.mkdir(mode=0o700, exist_ok=True)
        runtime_directory.chmod(0o700)
        os.environ["XDG_RUNTIME_DIR"] = str(runtime_directory.resolve())
    # Keep coverage after the source changes are committed (git diff is then empty).
    qml_files = [str(QT / p) for p in CHECKED_QML]
    tool = Path(PySide6.__file__).parent / ("qmllint.exe" if os.name == "nt" else "qmllint")
    lint = subprocess.run([str(tool), "--ignore-settings", "--max-warnings", "-1",
                           "--duplicate-property-binding", "warning", "--duplicated-name", "warning",
                           "--json", str(args.output / "syntax-lint.json"), *qml_files], capture_output=True, text=True)
    (args.output / "syntax-lint.log").write_text(lint.stdout + lint.stderr, encoding="utf-8")
    if lint.returncode:
        print(lint.stdout + lint.stderr)
        return lint.returncode
    invalid = args.output / "invalid-parser-fixture.qml"
    invalid.write_text("import QtQuick\nItem { width: }\n", encoding="utf-8")
    rejected = subprocess.run([str(tool), str(invalid)], capture_output=True, text=True)
    if not rejected.returncode:
        raise AssertionError("qmllint accepted deliberately invalid QML")
    lint_report = json.loads((args.output / "syntax-lint.json").read_text(encoding="utf-8"))
    lint_diagnostics = [w for f in lint_report["files"] for w in f.get("warnings", [])]
    # Qt 6.8 permits only disable/info/warning for diagnostic categories. Enforce
    # duplicates here so older Qt versions retain the same failure policy.
    lint_errors = [w for w in lint_diagnostics if w["type"] == "error"
                   or w.get("id") in ("duplicate-property-binding", "duplicated-name")]
    if lint_errors:
        raise AssertionError(lint_errors)
    print(f"PASS: Qt QML syntax/duplicate-binding checks ({len(qml_files)} source files); full diagnostics retained in syntax-lint.json", flush=True)
    manifest = fixture_modules(args.output / "imports")
    (args.output / "source-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (args.output / "Scene.qml").write_text(SCENE, encoding="utf-8")
    messages = []
    def handle_message(kind, context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            messages.append(message)
            print("QT:", message, flush=True)
    qInstallMessageHandler(handle_message)
    app = QGuiApplication(sys.argv[:1])
    from PySide6.QtGui import QFontDatabase
    for font in (QT / "pixmaps/fonts").rglob("*.ttf"):
        if QFontDatabase.addApplicationFont(str(font)) < 0:
            raise AssertionError(f"Cannot load reference font: {font}")
    if not {"Inter", "DM Mono"}.issubset(set(QFontDatabase.families())):
        raise AssertionError("The bundled reference typefaces did not register")
    engine = QQmlEngine()
    engine.addImageProvider("effects", DesignImageProvider())
    engine.addImportPath(str(args.output / "imports"))
    component = QQmlComponent(engine, QUrl.fromLocalFile(str((args.output / "Scene.qml").resolve())))
    root = component.create()
    if root is None:
        for error in component.errors(): print(error.toString())
        return 1
    QTest.qWait(250)
    print("Component created:", root.property("testBar"), flush=True)
    if args.probe:
        return 1 if messages else 0
    failures = []
    cases = []
    def check(name, action):
        try:
            action()
            cases.append({"name": name, "passed": True})
            print("PASS:", name, flush=True)
        except Exception as error:
            failures.append(f"{name}: {error}")
            cases.append({"name": name, "passed": False, "error": str(error)})
            print("FAIL:", failures[-1], flush=True)
    def assert_true(condition, message):
        if not condition: raise AssertionError(message)
    def palette_literals():
        for name in ["systempalette.cpp", "systempalette.hpp"]:
            text = (QT / "style" / name).read_text(encoding="utf-8-sig")
            invalid = [value for value in re.findall(r'"(#[^"\n]+)"', text) if not QColor(value).isValid()]
            assert_true(not invalid, f"invalid QColor literals in {name}: {invalid}")
    check("native palette QColor literals", palette_literals)
    def profile_inventory():
        text = (QT / "dialogs/toolbar/controlbar_profile_model.cpp").read_text(encoding="utf-8-sig")
        block = text.split("Style::DEFAULT_STYLE", 1)[1].split("Style::MINIMALIST_STYLE", 1)[0]
        expected = {
            "Videoplayer": "LANG_BUTTON BOOKMARK_BUTTON EXTENDED_BUTTON NAVIGATION_BUTTONS SKIP_BACK_BUTTON PREVIOUS_BUTTON PLAY_BUTTON NEXT_BUTTON SKIP_FW_BUTTON VOLUME RENDERER_BUTTON FULLSCREEN_BUTTON".split(),
            "Audioplayer": "LANG_BUTTON BOOKMARK_BUTTON EXTENDED_BUTTON RANDOM_BUTTON PREVIOUS_BUTTON PLAY_BUTTON NEXT_BUTTON LOOP_BUTTON VOLUME RENDERER_BUTTON FULLSCREEN_BUTTON".split(),
            "Miniplayer": "ARTWORK_INFO RANDOM_BUTTON PREVIOUS_BUTTON PLAY_BUTTON NEXT_BUTTON LOOP_BUTTON VOLUME PLAYER_SWITCH_BUTTON".split(),
        }
        for model, controls in expected.items():
            section = block.split("PlayerControlbarModel::" + model, 1)[1].split("PlayerControlbarModel::", 1)[0]
            actual = re.findall(r"ControlListModel::(\w+)", section)
            assert_true(sorted(actual) == sorted(controls), f"{model} lost or duplicated controls: {actual}")
    check("default toolbar control inventory", profile_inventory)
    bar = root.property("testBar")
    slider = root.property("testSlider")
    play = root.property("testPlay")
    for mode, width, expect_inline in [("default", 1600, True), ("default", 800, False),
                                      ("default", 1199, False), ("default", 1200, True),
                                      ("center", 1600, False), ("empty", 1600, False),
                                      ("crowded", 1600, False), ("default", 1600, True),
                                      ("floating", 1600, False), ("default", 1600, True)]:
        def test_layout(mode=mode, width=width, expected=expect_inline):
            call(engine, root, "configure", mode, width)
            QTest.qWait(150)
            assert_true(bar.property("inlineSeek") == expected, f"inlineSeek={bar.property('inlineSeek')}, expected {expected}")
            assert_true(slider.width() > 0 and slider.height() > 0, "seek bar lost its geometry")
            point = slider.mapToItem(bar, QPointF(0, 0))
            assert_true(point.x() >= -0.5 and point.y() >= -0.5, f"seek origin outside bar: {point}")
            assert_true(point.x() + slider.width() <= bar.width() + 0.5, "seek bar extends beyond controls")
        check(f"layout {mode} at {width}px", test_layout)
    for scale in [1, 1.5, 2, 1]:
        def test_scale(scale=scale):
            call(engine, root, "setScale", scale)
            call(engine, root, "configure", "default", round(1600 * scale))
            QTest.qWait(150)
            assert_true(bar.property("inlineSeek"), "compact layout failed at scaled width")
            assert_true(abs(play.width() - 54 * scale) <= 1, "play width does not scale")
            assert_true(abs(play.height() - 28 * scale) <= 1, "play height does not scale")
        check(f"interface scale {scale}", test_scale)
    for scheme in [1, 2]:
        def test_scheme(scheme=scheme):
            call(engine, root, "setScheme", scheme)
            QTest.qWait(100)
            assert_true(root.property("playColor").isValid(), "invalid play foreground color")
        check(f"scheme {scheme}", test_scheme)
    def click_play():
        before = root.property("toggles")
        point = play.mapToScene(QPointF(play.width()/2, play.height()/2)).toPoint()
        QTest.mouseClick(root, Qt.LeftButton, Qt.NoModifier, point)
        QTest.qWait(50)
        assert_true(root.property("toggles") == before + 1, "pointer click did not toggle playback")
    check("pointer Play/Pause", click_play)
    def keyboard_play():
        before = root.property("toggles")
        play.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(root, Qt.Key_Space)
        QTest.qWait(50)
        assert_true(root.property("toggles") == before + 1, "Space did not toggle playback")
    check("keyboard Play/Pause", keyboard_play)
    def hold_stop():
        before = root.property("stops")
        play.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyPress(root, Qt.Key_Space)
        QTest.qWait(1200)
        QTest.keyRelease(root, Qt.Key_Space)
        assert_true(root.property("stops") == before + 1, "hold did not stop playback")
    check("keyboard press-and-hold Stop", hold_stop)
    def pointer_seek():
        call(engine, root, "resumePlayback")
        QTest.qWait(50)
        point = slider.mapToScene(QPointF(slider.width()*0.7, slider.height()/2)).toPoint()
        QTest.mouseClick(root, Qt.LeftButton, Qt.NoModifier, point)
        QTest.qWait(50)
        assert_true(abs(root.property("position") - 0.7) < 0.025, "pointer seek position incorrect")
    check("pointer seek", pointer_seek)
    def seek_arrow():
        before = root.property("position")
        slider.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(root, Qt.Key_Right)
        QTest.qWait(50)
        assert_true(root.property("position") > before, "arrow key did not advance playback")
    check("keyboard seek", seek_arrow)
    def compact_handle_restore():
        standalone = root.property("testStandaloneSlider")
        root.setProperty("standaloneCompact", False)
        QTest.qWait(300)
        root.setProperty("standaloneCompact", True)
        QTest.qWait(300)
        handle = next(item for item in standalone.childItems() if item.metaObject().indexOfProperty("_size") >= 0)
        assert_true(handle.width() > 0 and handle.height() > 0, "compact thumb disappeared after mode switch")
        assert_true(handle.isVisible(), "compact thumb remains hidden after mode switch")
        assert_true(abs(handle.width() - 8) < 0.5 and abs(handle.height() - 24) < 0.5, "compact thumb size is stale")
    check("compact thumb restores after stacked mode", compact_handle_restore)
    def tab_chain():
        layout = root.property("testLayout")
        left = layout.property("seekBarLeftItem")
        right = layout.property("seekBarRightItem")
        left.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(root, Qt.Key_Tab)
        QTest.qWait(50)
        assert_true(root.activeFocusItem() == slider, "Tab from transport skipped the seek bar")
        QTest.keyClick(root, Qt.Key_Tab)
        QTest.qWait(50)
        assert_true(root.activeFocusItem() == right, "Tab from seek did not reach options")
    check("Tab through transport, seek, options", tab_chain)
    def chapter_seek():
        call(engine, root, "setChapters", True)
        QTest.qWait(150)
        pointer_seek()
        call(engine, root, "setChapters", False)
        QTest.qWait(150)
    check("chaptered seek and return to plain timeline", chapter_seek)
    def pointer_hold():
        before = root.property("stops")
        point = play.mapToScene(QPointF(play.width()/2, play.height()/2)).toPoint()
        QTest.mousePress(root, Qt.LeftButton, Qt.NoModifier, point)
        QTest.qWait(1200)
        QTest.mouseRelease(root, Qt.LeftButton, Qt.NoModifier, point)
        assert_true(root.property("stops") == before + 1, "pointer hold did not stop playback")
    check("pointer press-and-hold Stop", pointer_hold)
    def luminance(color):
        return sum(weight * (channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
                   for weight, channel in zip((0.2126, 0.7152, 0.0722), (color.redF(), color.greenF(), color.blueF())))
    for accent in ["#D37918", "#FFFFFF", "#FFFF00", "#0088FF", "#101010"]:
        def accent_contrast(accent=accent):
            call(engine, root, "setAccent", accent)
            QTest.qWait(150)
            foreground, background = root.property("playColor"), root.property("playBackground")
            a, b = sorted((luminance(foreground), luminance(background)))
            ratio = (b + 0.05) / (a + 0.05)
            assert_true(ratio >= 4.5, f"custom accent contrast is only {ratio:.2f}:1")
        check(f"play contrast for accent {accent}", accent_contrast)
    for name, mode, width, scheme in [("wide-controls", "default", 1600, 2),
                                      ("narrow-controls", "default", 800, 2),
                                      ("day-controls", "default", 1600, 1)]:
        def capture(name=name, mode=mode, width=width, scheme=scheme):
            call(engine, root, "setAccent", "#D37918")
            call(engine, root, "setScheme", scheme)
            call(engine, root, "configure", mode, width)
            QTest.qWait(200)
            image = root.grabWindow()
            assert_true(not image.isNull(), "Qt renderer returned an empty image")
            assert_true(image.save(str(args.output / f"{name}.png")), "could not save Qt capture")
        check(f"Qt rendering capture {name}", capture)
    if messages:
        failures.append(f"{len(messages)} Qt runtime warning/error messages")
    (args.output / "runtime-report.json").write_text(json.dumps({"qt": PySide6.__version__, "cases": cases,
        "messages": messages, "failures": failures, "qmlSyntaxErrors": len(lint_errors),
        "fullLintWarnings": sum(w["type"] == "warning" for w in lint_diagnostics),
        "nativeVlcBuildVerified": False,
        "scope": "Production QML in Qt, with isolated VLC backend/type adapters. Full lint retains diagnostics from unavailable native VLC modules."}, indent=2), encoding="utf-8")
    root.close()
    root.deleteLater()
    QTest.qWait(50)
    print(f"Result: {len(cases)} cases, {len(failures)} failures, {len(messages)} Qt warnings/errors", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
