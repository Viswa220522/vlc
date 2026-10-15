// SPDX-License-Identifier: GPL-2.0-or-later
// The seven destinations and both rail layouts follow Juxtopposed's reference.
import QtQuick
import QtQuick.Templates as T
import VLC.Style
import VLC.Widgets as Widgets
import VLC.MainInterface
import VLC.Dialogs

T.Pane {
    id: root
    signal itemClicked(var uri, Item item)
    property bool delegateShowText: true
    property bool useAcrylic: false
    property int safeAreaLeftMargin: 0
    property int safeAreaRightMargin: 0
    property string selectedSection: {
        const path = History.viewPath
        if (path[1] === "playlists") return "playlists"
        if (path[1] === "continueWatching") return "recent"
        return path[0] ?? "home"
    }
    readonly property int minimumWidth: VLCStyle.dp(217, VLCStyle.scale)
    property alias model: navigationModel
    implicitWidth: delegateShowText ? minimumWidth : VLCStyle.dp(50, VLCStyle.scale)
    padding: 0
    Accessible.name: qsTr("Navigation")
    readonly property ColorContext colorContext: ColorContext {
        id: theme
        colorSet: ColorContext.Window
    }
    readonly property bool dark: theme.palette?.isDark ?? true
    NavigationModel {
        id: navigationModel
        hasMedialib: MainCtx.mediaLibraryAvailable
    }
    background: Rectangle {
        color: root.delegateShowText ? (root.dark ? "#0e0e0e" : "#e7e7e7")
                                    : (root.dark ? "#191919" : "#d5d5d5")
    }
    contentItem: Item {
        Rectangle {
            anchors.fill: parent
            anchors.margins: root.delegateShowText ? VLCStyle.dp(8, VLCStyle.scale) : 0
            radius: root.delegateShowText ? VLCStyle.dp(6, VLCStyle.scale) : 0
            color: root.dark ? "#191919" : "#d5d5d5"
        }
        Column {
            anchors.top: parent.top
            anchors.topMargin: VLCStyle.dp(root.delegateShowText ? 20 : 8, VLCStyle.scale)
            anchors.left: parent.left
            anchors.leftMargin: VLCStyle.dp(root.delegateShowText ? 24 : 10, VLCStyle.scale)
            width: parent.width - anchors.leftMargin * 2
            spacing: VLCStyle.dp(14, VLCStyle.scale)
            Repeater {
                model: [
                    { section: "home", title: qsTr("Home"), uri: ["home"], height: 32 },
                    { section: "video", title: qsTr("Videos"), uri: ["video"], height: 26 },
                    { section: "music", title: qsTr("Music"), uri: ["music"], height: 26 },
                    { section: "network", title: qsTr("Network"), uri: ["network"], height: 32 },
                    { section: "playlists", title: qsTr("Playlists"), uri: ["video", "playlists"], height: 32 },
                    { section: "recent", title: qsTr("Recent"), uri: ["home", "continueWatching"], height: 32 },
                    { section: "add", title: qsTr("Add item"), uri: [], height: 32 }
                ]
                T.Button {
                    id: destination
                    required property var modelData
                    readonly property bool expandable: false
                    readonly property bool selected: root.selectedSection === modelData.section
                    width: parent.width
                    height: VLCStyle.dp(root.delegateShowText ? 32 : modelData.height, VLCStyle.scale)
                    padding: 0
                    hoverEnabled: true
                    activeFocusOnTab: true
                    enabled: MainCtx.mediaLibraryAvailable || ["home", "network", "add"].includes(modelData.section)
                    Accessible.name: modelData.title
                    Accessible.role: Accessible.PageTab
                    Accessible.selected: selected
                    Accessible.onPressAction: clicked()
                    T.ToolTip.text: modelData.title
                    T.ToolTip.visible: !root.delegateShowText && (hovered || visualFocus)
                    T.ToolTip.delay: VLCStyle.delayToolTipAppear
                    onClicked: {
                        if (modelData.section === "add")
                            DialogsProvider.simpleOpenDialog()
                        else
                            root.itemClicked(modelData.uri, destination)
                    }
                    Keys.onPressed: event => Navigation.defaultKeyAction(event)
                    background: Rectangle {
                        radius: VLCStyle.dp(4, VLCStyle.scale)
                        color: destination.hovered || destination.down ? theme.bg.secondary : "transparent"
                        border.color: destination.visualFocus ? theme.visualFocus : "transparent"
                    }
                    contentItem: Item {
                        Widgets.DesignIcon {
                            anchors.left: parent.left
                            anchors.leftMargin: VLCStyle.dp(3, VLCStyle.scale)
                            anchors.verticalCenter: parent.verticalCenter
                            width: VLCStyle.dp(24, VLCStyle.scale)
                            height: width
                            name: modelData.section === "video" ? "videos" : modelData.section
                            color: destination.selected ? theme.accent : theme.fg.secondary
                        }
                        Widgets.LabelExt {
                            visible: root.delegateShowText
                            anchors.left: parent.left
                            anchors.leftMargin: VLCStyle.dp(38, VLCStyle.scale)
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.title
                            color: destination.selected ? theme.accent : theme.fg.secondary
                            font.pixelSize: VLCStyle.dp(14, VLCStyle.scale)
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }
    }
}
