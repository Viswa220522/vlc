// SPDX-License-Identifier: GPL-2.0-or-later
// Layout and original icon artwork by Juxtopposed.
import QtQuick
import QtQuick.Window
import VLC.Style
import VLC.MainInterface
import VLC.Menus as Menus
import VLC.Widgets as Widgets

FocusScope {
    id: root
    implicitHeight: VLCStyle.dp(40, VLCStyle.scale)
    height: implicitHeight
    property bool libraryControls: false
    property bool navigationVisible: false
    property bool playqueueVisible: false
    property Item plListView: null
    property bool showCSD: MainCtx.clientSideDecoration && MainCtx.intfMainWindow.visibility !== Window.FullScreen
    property string sectionTitle: qsTr("Videos")
    signal toggleNavigationVisibility()
    signal togglePlayqueueVisibility()
    signal libraryRequested()
    signal requestLockUnlockAutoHide(bool lock)
    signal forceUnlock()
    Accessible.role: Accessible.ToolBar
    Accessible.name: qsTr("Title bar")

    readonly property ColorContext colorContext: ColorContext {
        id: theme
        colorSet: ColorContext.Window
    }
    Rectangle {
        anchors.fill: parent
        color: !root.libraryControls && (theme.palette?.isDark ?? true) ? "#f2191919" : theme.bg.primary
    }
    Loader {
        anchors.fill: parent
        active: root.showCSD
        source: "qrc:///qt/qml/VLC/Widgets/CSDTitlebarTapNDrapHandler.qml"
    }
    Row {
        id: leftGroup
        anchors.left: parent.left
        anchors.leftMargin: VLCStyle.dp(6, VLCStyle.scale)
        anchors.verticalCenter: parent.verticalCenter
        spacing: VLCStyle.dp(7, VLCStyle.scale)
        Item {
            width: VLCStyle.dp(38, VLCStyle.scale)
            height: VLCStyle.dp(28, VLCStyle.scale)
            Image {
                anchors.centerIn: parent
                width: VLCStyle.dp(24, VLCStyle.scale)
                height: width
                source: "qrc:/juxtopposed/cone.png"
                fillMode: Image.PreserveAspectFit
                Accessible.ignored: true
            }
        }
        Row {
            Widgets.DesignIconButton {
                id: menuButton
                width: VLCStyle.dp(28, VLCStyle.scale)
                height: VLCStyle.dp(28, VLCStyle.scale)
                iconName: "more"
                description: qsTr("Menu")
                onClicked: globalMenu.popup(mapToGlobal(0, height))
            }
            Item {
                visible: root.libraryControls
                width: VLCStyle.dp(10, VLCStyle.scale)
                height: VLCStyle.dp(28, VLCStyle.scale)
            }
            Row {
                visible: root.libraryControls
                spacing: 0
                Widgets.DesignIconButton {
                    width: VLCStyle.dp(28, VLCStyle.scale)
                    height: VLCStyle.dp(28, VLCStyle.scale)
                    iconName: "sidebar"
                    description: qsTr("Show navigation")
                    onClicked: root.toggleNavigationVisibility()
                }
                Widgets.DesignIcon {
                    anchors.verticalCenter: parent.verticalCenter
                    name: "divider"
                    width: VLCStyle.dp(24, VLCStyle.scale)
                    height: width
                    color: theme.fg.secondary
                }
                Widgets.DesignIconButton {
                    width: VLCStyle.dp(28, VLCStyle.scale)
                    height: VLCStyle.dp(28, VLCStyle.scale)
                    iconName: "folder"
                    description: qsTr("Media library")
                    onClicked: root.libraryRequested()
                }
                Widgets.LabelExt {
                    leftPadding: VLCStyle.dp(4, VLCStyle.scale)
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.sectionTitle
                    font.pixelSize: VLCStyle.dp(14, VLCStyle.scale)
                    color: theme.fg.secondary
                }
            }
        }
    }
    Widgets.LabelExt {
        anchors.centerIn: parent
        visible: root.width > VLCStyle.dp(650, VLCStyle.scale)
        text: qsTr("VLC Media Player")
        color: theme.fg.secondary
        font.pixelSize: VLCStyle.dp(14, VLCStyle.scale)
    }
    Row {
        id: windowButtons
        anchors.right: parent.right
        anchors.rightMargin: VLCStyle.dp(6, VLCStyle.scale)
        anchors.verticalCenter: parent.verticalCenter
        spacing: 0
        function buttonFor(type) {
            const buttons = MainCtx.csdButtonModel.windowCSDButtons
            for (let i = 0; i < buttons.length; ++i) {
                if (buttons[i].type === type)
                    return buttons[i]
            }
            return null
        }
        Repeater {
            model: [
                { icon: "minimize", title: qsTr("Minimize"), type: CSDButton.Minimize },
                { icon: "maximize", title: qsTr("Maximize or restore"), type: CSDButton.MaximizeRestore },
                { icon: "fullscreen", title: qsTr("Full screen"), type: -1 },
                { icon: "close", title: qsTr("Close"), type: CSDButton.Close }
            ]
            Widgets.DesignIconButton {
                id: windowButton
                required property var modelData
                readonly property var nativeButton: windowButtons.buttonFor(modelData.type)
                visible: modelData.type === -1 || root.showCSD
                width: VLCStyle.dp(36, VLCStyle.scale)
                height: VLCStyle.dp(24, VLCStyle.scale)
                iconName: modelData.icon
                description: modelData.title
                externalHovered: nativeButton?.showHovered ?? false
                externalPressed: nativeButton?.externalPressed ?? false
                onClicked: {
                    if (modelData.type === -1)
                        MainCtx.toggleInterfaceFullScreen()
                    else if (nativeButton)
                        nativeButton.click()
                }
                function updateRect() {
                    if (nativeButton) {
                        const position = mapToItem(null, 0, 0)
                        nativeButton.rect = Qt.rect(position.x, position.y, width, height)
                    }
                }
                Component.onCompleted: updateRect()
                onXChanged: updateRect()
                onYChanged: updateRect()
                onWidthChanged: updateRect()
                onHeightChanged: updateRect()
                Connections {
                    target: root
                    function onWidthChanged() { windowButton.updateRect() }
                }
            }
        }
    }
    Menus.QmlGlobalMenu {
        id: globalMenu
        ctx: MainCtx
        onAboutToShow: root.requestLockUnlockAutoHide(true)
        onAboutToHide: root.requestLockUnlockAutoHide(false)
    }
    Connections {
        target: root
        function onForceUnlock() { globalMenu.close() }
    }
}
