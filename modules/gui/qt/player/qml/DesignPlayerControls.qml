// SPDX-License-Identifier: GPL-2.0-or-later
// Juxtopposed reference: 54px strip, 130px transport, 120px volume,
// 114px options, 30px queue; 20px group gaps and horizontal padding.
import QtQuick
import QtQuick.Layouts
import QtQuick.Templates as T
import VLC.MainInterface
import VLC.Player
import VLC.PlayerControls
import VLC.Style
import VLC.Widgets as Widgets

T.Pane {
    id: root
    readonly property bool inlineSeek: true
    readonly property real sliderY: timeline.mapToItem(root, 0, 0).y
    property int textPosition: 0
    property bool showRemainingTime: true
    property int identifier: 0
    signal requestLockUnlockAutoHide(bool lock)
    signal forceUnlock()
    signal audioRequested()
    signal subtitlesRequested()
    signal settingsRequested()
    signal queueRequested()
    readonly property ColorContext colorContext: ColorContext {
        id: theme
        colorSet: ColorContext.Window
    }
    padding: 0
    leftPadding: VLCStyle.dp(20, VLCStyle.scale)
    rightPadding: VLCStyle.dp(20, VLCStyle.scale)
    topPadding: VLCStyle.dp(11, VLCStyle.scale)
    bottomPadding: VLCStyle.dp(11, VLCStyle.scale)
    implicitHeight: VLCStyle.dp(54, VLCStyle.scale)
    hoverEnabled: true
    Accessible.name: qsTr("Playback controls")
    Accessible.role: Accessible.ToolBar
    background: Rectangle { color: theme.bg.primary }
    function showChapterMarks() { timeline.showChapterMarks() }
    function formatTime(tick) {
        const value = tick.formatHMS()
        return value === "--:--" ? "--:--:--" : value.length === 5 ? "00:" + value : value
    }
    contentItem: RowLayout {
        spacing: VLCStyle.dp(20, VLCStyle.scale)
        Row {
            objectName: "referenceTransport"
            Layout.alignment: Qt.AlignVCenter
            spacing: VLCStyle.dp(8, VLCStyle.scale)
            PreviousButton {
                objectName: "referencePrevious"
                width: VLCStyle.dp(30, VLCStyle.scale)
                height: VLCStyle.dp(28, VLCStyle.scale)
                activeFocusOnTab: true
            }
            PlayButton { objectName: "referencePlay"; activeFocusOnTab: true }
            NextButton {
                objectName: "referenceNext"
                width: VLCStyle.dp(30, VLCStyle.scale)
                height: VLCStyle.dp(28, VLCStyle.scale)
                activeFocusOnTab: true
            }
        }
        RowLayout {
            objectName: "referenceTimelineGroup"
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: VLCStyle.dp(8, VLCStyle.scale)
            Widgets.LabelExt {
                Layout.preferredWidth: VLCStyle.dp(76, VLCStyle.scale)
                visible: root.width >= VLCStyle.dp(800, VLCStyle.scale)
                text: root.formatTime(Player.time)
                font.pixelSize: VLCStyle.dp(15, VLCStyle.scale)
                color: theme.fg.secondary
                horizontalAlignment: Text.AlignHCenter
            }
            SliderBar {
                id: timeline
                objectName: "referenceTimeline"
                Layout.fillWidth: true
                Layout.minimumWidth: VLCStyle.dp(80, VLCStyle.scale)
                Layout.preferredHeight: VLCStyle.dp(28, VLCStyle.scale)
                compact: true
                barHeight: VLCStyle.dp(28, VLCStyle.scale)
                activeFocusOnTab: true
                focus: true
            }
            Widgets.LabelExt {
                Layout.preferredWidth: VLCStyle.dp(76, VLCStyle.scale)
                visible: root.width >= VLCStyle.dp(800, VLCStyle.scale)
                text: MainCtx.showRemainingTime ? "-" + root.formatTime(Player.remainingTime) : root.formatTime(Player.length)
                font.pixelSize: VLCStyle.dp(15, VLCStyle.scale)
                color: theme.fg.secondary
                horizontalAlignment: Text.AlignHCenter
            }
        }
        VolumeWidget { objectName: "referenceVolume"; Layout.alignment: Qt.AlignVCenter }
        Row {
            objectName: "referenceOptions"
            Layout.alignment: Qt.AlignVCenter
            spacing: VLCStyle.dp(12, VLCStyle.scale)
            Widgets.DesignIconButton {
                iconName: "audio"
                description: qsTr("Audio")
                onClicked: root.audioRequested()
            }
            Widgets.DesignIconButton {
                iconName: "subtitles"
                description: qsTr("Subtitles")
                onClicked: root.subtitlesRequested()
            }
            Widgets.DesignIconButton {
                iconName: "settings"
                description: qsTr("Settings")
                onClicked: root.settingsRequested()
            }
        }
        Widgets.DesignIconButton {
            Layout.alignment: Qt.AlignVCenter
            iconName: "queue"
            description: qsTr("Play queue")
            checked: MainCtx.playqueuePanel.visible
            onClicked: root.queueRequested()
        }
    }
}
