// SPDX-License-Identifier: GPL-2.0-or-later
// Original layout and icon artwork: Juxtopposed, VLC Redesign (Community).
import QtQuick
import QtQuick.Layouts
import QtQuick.Templates as T
import VLC.MainInterface
import VLC.Style
import VLC.Widgets as Widgets

T.Pane {
    id: root
    implicitWidth: VLCStyle.dp(427, VLCStyle.scale)
    padding: 0
    property string section: "playlists"
    property string title: qsTr("Playlists")
    property var entries: null
    property int itemCount: entries?.count ?? 0
    property string titleRole: "name"
    property string entryIcon: "playlists"
    property string actionText: qsTr("Create playlist")
    property bool actionEnabled: true
    property bool canBack: false
    property bool canForward: false
    signal categoryRequested(var uri)
    signal backRequested()
    signal forwardRequested()
    signal expandRequested()
    signal optionsRequested(point globalPosition)
    signal sortRequested(point globalPosition)
    signal viewRequested(point globalPosition)
    signal searchRequested()
    signal actionRequested()
    signal entryActivated(var entry)
    signal entryPlayRequested(var entry)
    signal entryContextRequested(var entry, point globalPosition)
    readonly property ColorContext colorContext: ColorContext {
        id: theme
        colorSet: ColorContext.View
    }
    readonly property color mutedColor: (theme.palette?.isDark ?? true) ? "#6b6b6b" : theme.fg.secondary
    readonly property color entryColor: (theme.palette?.isDark ?? true) ? "#969696" : theme.fg.secondary
    background: Item {}
    DesignNavigationPane {
        id: rail
        objectName: "referenceNavigationRail"
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: VLCStyle.dp(50, VLCStyle.scale)
        delegateShowText: false
        selectedSection: root.section
        onItemClicked: (uri, item) => root.categoryRequested(uri)
    }
    Rectangle {
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: rail.right
        anchors.right: parent.right
        color: (theme.palette?.isDark ?? true) ? "#f20e0e0e" : "#f2e7e7e7"
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: VLCStyle.dp(20, VLCStyle.scale)
            spacing: VLCStyle.dp(17, VLCStyle.scale)
            ColumnLayout {
                Layout.fillWidth: true
                spacing: VLCStyle.dp(20, VLCStyle.scale)
                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: VLCStyle.dp(24, VLCStyle.scale)
                    spacing: VLCStyle.dp(10, VLCStyle.scale)
                    Row {
                        spacing: VLCStyle.dp(12, VLCStyle.scale)
                        Widgets.DesignIconButton {
                            width: VLCStyle.dp(24, VLCStyle.scale)
                            height: width
                            iconName: "back"
                            description: qsTr("Back")
                            enabled: root.canBack
                            onClicked: root.backRequested()
                        }
                        Widgets.DesignIconButton {
                            width: VLCStyle.dp(24, VLCStyle.scale)
                            height: width
                            iconName: "back"
                            description: qsTr("Forward")
                            rotation: 180
                            enabled: root.canForward
                            onClicked: root.forwardRequested()
                        }
                    }
                    Widgets.LabelExt {
                        Layout.fillWidth: true
                        text: root.title
                        font.pixelSize: VLCStyle.dp(16, VLCStyle.scale)
                        color: theme.fg.secondary
                        elide: Text.ElideRight
                    }
                    Row {
                        spacing: VLCStyle.dp(12, VLCStyle.scale)
                        Widgets.DesignIconButton {
                            width: VLCStyle.dp(24, VLCStyle.scale)
                            height: width
                            iconName: "browser-more"
                            description: qsTr("More options")
                            onClicked: root.optionsRequested(mapToGlobal(0, height))
                        }
                        Widgets.DesignIconButton {
                            width: VLCStyle.dp(24, VLCStyle.scale)
                            height: width
                            iconName: "expand"
                            description: qsTr("Open in library")
                            onClicked: root.expandRequested()
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: VLCStyle.dp(24, VLCStyle.scale)
                    spacing: 0
                    Widgets.LabelExt {
                        Layout.fillWidth: true
                        text: (root.itemCount === 1 ? qsTr("%1 item") : qsTr("%1 items")).arg(root.itemCount)
                        font.pixelSize: VLCStyle.dp(14, VLCStyle.scale)
                        color: root.mutedColor
                    }
                    Row {
                        spacing: VLCStyle.dp(12, VLCStyle.scale)
                        Repeater {
                            model: [
                                { icon: "sort", title: qsTr("Sort") },
                                { icon: "list", title: qsTr("View options") },
                                { icon: "search", title: qsTr("Search") }
                            ]
                            Widgets.DesignIconButton {
                                required property var modelData
                                width: VLCStyle.dp(24, VLCStyle.scale)
                                height: width
                                iconName: modelData.icon
                                color: root.mutedColor
                                description: modelData.title
                                onClicked: {
                                    if (iconName === "sort") root.sortRequested(mapToGlobal(0, height))
                                    else if (iconName === "list") root.viewRequested(mapToGlobal(0, height))
                                    else root.searchRequested()
                                }
                            }
                        }
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: VLCStyle.dp(1, VLCStyle.scale)
                color: (theme.palette?.isDark ?? true) ? "#222222" : theme.separator
                opacity: 0.5
            }
            ListView {
                id: list
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.topMargin: VLCStyle.dp(3, VLCStyle.scale)
                spacing: VLCStyle.dp(10, VLCStyle.scale)
                clip: true
                model: root.entries
                header: Item {
                    width: list.width
                    height: root.actionText.length ? VLCStyle.dp(42, VLCStyle.scale) : 0
                    visible: height > 0
                    T.Button {
                        objectName: "browserPrimaryAction"
                        width: parent.width
                        height: VLCStyle.dp(32, VLCStyle.scale)
                        padding: 0
                        enabled: root.actionEnabled
                        hoverEnabled: true
                        activeFocusOnTab: true
                        text: root.actionText
                        Accessible.name: text
                        onClicked: root.actionRequested()
                        background: Rectangle {
                            radius: VLCStyle.dp(4, VLCStyle.scale)
                            color: parent.hovered ? theme.bg.secondary : "transparent"
                            border.color: parent.visualFocus ? theme.visualFocus : "transparent"
                        }
                        contentItem: RowLayout {
                            spacing: VLCStyle.dp(10, VLCStyle.scale)
                            Item {
                                Layout.preferredWidth: VLCStyle.dp(32, VLCStyle.scale)
                                Layout.fillHeight: true
                                Widgets.DesignIcon {
                                    anchors.centerIn: parent
                                    width: implicitWidth
                                    height: implicitHeight
                                    name: "add"
                                    color: root.mutedColor
                                }
                            }
                            Widgets.LabelExt {
                                Layout.fillWidth: true
                                text: root.actionText
                                color: root.mutedColor
                                font.pixelSize: VLCStyle.dp(14, VLCStyle.scale)
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
                delegate: T.Button {
                    id: row
                    objectName: "browserEntry"
                    required property var model
                    width: list.width
                    height: VLCStyle.dp(32, VLCStyle.scale)
                    padding: 0
                    hoverEnabled: true
                    activeFocusOnTab: true
                    text: model?.[root.titleRole] ?? ""
                    Accessible.name: text
                    Accessible.role: Accessible.ListItem
                    onClicked: root.entryActivated(model)
                    background: Rectangle {
                        radius: VLCStyle.dp(4, VLCStyle.scale)
                        color: row.hovered || row.down ? theme.bg.secondary : "transparent"
                        border.color: row.visualFocus ? theme.visualFocus : "transparent"
                    }
                    contentItem: RowLayout {
                        spacing: VLCStyle.dp(10, VLCStyle.scale)
                        Item {
                            Layout.preferredWidth: VLCStyle.dp(32, VLCStyle.scale)
                            Layout.fillHeight: true
                            Widgets.DesignIcon {
                                anchors.centerIn: parent
                                width: implicitWidth
                                height: implicitHeight
                                name: root.entryIcon
                                color: theme.fg.secondary
                            }
                        }
                        Widgets.LabelExt {
                            Layout.fillWidth: true
                            text: row.Accessible.name
                            color: root.entryColor
                            font.pixelSize: VLCStyle.dp(14, VLCStyle.scale)
                            elide: Text.ElideRight
                        }
                    }
                    TapHandler {
                        acceptedButtons: Qt.RightButton
                        onTapped: eventPoint => root.entryContextRequested(row.model, eventPoint.globalPosition)
                    }
                }
            }
        }
    }
}
