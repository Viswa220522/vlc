// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Templates as T
import VLC.Style
import VLC.Widgets as Widgets
import VLC.MainInterface

T.ToolButton {
    id: root
    required property string iconName
    required property string description
    property bool externalHovered: false
    property bool externalPressed: false
    property color color: checked ? theme.accent : theme.fg.secondary
    implicitWidth: VLCStyle.dp(30, VLCStyle.scale)
    implicitHeight: VLCStyle.dp(32, VLCStyle.scale)
    padding: 0
    hoverEnabled: true
    activeFocusOnTab: true
    down: pressed || externalPressed
    Accessible.name: description
    Accessible.onPressAction: root.clicked()
    T.ToolTip.text: description
    T.ToolTip.visible: hovered || visualFocus
    T.ToolTip.delay: VLCStyle.delayToolTipAppear
    Keys.onPressed: event => Navigation.defaultKeyAction(event)
    readonly property ColorContext colorContext: ColorContext {
        id: theme
        colorSet: ColorContext.ToolButton
        enabled: root.enabled
        focused: root.visualFocus
        hovered: root.hovered || root.externalHovered
        pressed: root.down
    }
    background: Rectangle {
        radius: VLCStyle.dp(4, VLCStyle.scale)
        color: root.down || root.hovered || root.externalHovered ? theme.bg.secondary : "transparent"
        border.color: root.visualFocus ? theme.visualFocus : "transparent"
    }
    contentItem: Item {
        Widgets.DesignIcon {
            anchors.centerIn: parent
            width: implicitWidth
            height: implicitHeight
            name: root.iconName
            color: root.color
            opacity: root.enabled ? 1 : 0.3
        }
    }
}
