/*****************************************************************************
 * Copyright (C) 2019 VLC authors and VideoLAN
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * ( at your option ) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/

import QtQuick
import QtQuick.Templates as T


import VLC.MainInterface
import VLC.Widgets as Widgets
import VLC.Style
import VLC.Util

T.ToolButton {
    id: control

    // Properties

    property bool paintOnly: false

    // Use the original reference artwork wherever a matching design icon exists.
    readonly property string designIcon: {
        if (text === VLCIcons.previous) return "previous"
        if (text === VLCIcons.next) return "next"
        if (text === VLCIcons.playlist) return "queue"
        if (text === VLCIcons.ellipsis) return "more"
        if (text === VLCIcons.fullscreen || text === VLCIcons.defullscreen) return "fullscreen"
        if (text === VLCIcons.back) return "back"
        if (text === VLCIcons.settings) return "settings"
        if (text === VLCIcons.effect_filter) return "audio"
        if ([VLCIcons.volume_muted, VLCIcons.volume_zero, VLCIcons.volume_low,
             VLCIcons.volume_medium, VLCIcons.volume_high].includes(text)) return "volume"
        return ""
    }

    required property string description

    property color color: control.checked ? theme.accent : designIcon.length ? theme.fg.secondary : theme.fg.primary

    property color backgroundColor: theme.bg.primary

    property real radius: VLCStyle.button_radius

    // Settings

    padding: VLCStyle.margin_xxsmall

    enabled: !paintOnly

    implicitWidth: designIcon.length ? VLCStyle.dp(30, VLCStyle.scale) : Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: designIcon.length ? VLCStyle.dp(32, VLCStyle.scale) : Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding)

    baselineOffset: contentItem.y + contentItem.baselineOffset

    font.pixelSize: VLCStyle.icon_toolbar
    font.family: VLCIcons.fontFamily

    // Keys

    Keys.priority: Keys.AfterItem

    Keys.onPressed: (event) => Navigation.defaultKeyAction(event)

    // Accessible

    Accessible.onPressAction: control.clicked()

    Accessible.name: description

    // Tooltip

    T.ToolTip.visible: (hovered || visualFocus)

    T.ToolTip.delay: VLCStyle.delayToolTipAppear

    T.ToolTip.text: description

    // Events

    Component.onCompleted: console.assert(text !== "", "text is empty")

    // Children

    readonly property ColorContext colorContext : ColorContext {
        id: theme
        colorSet: ColorContext.ToolButton

        enabled: control.paintOnly || control.enabled
        focused: control.visualFocus
        hovered: control.hovered
        pressed: control.down
    }

    background: Widgets.AnimatedBackground {
        implicitWidth: control.font.pixelSize
        implicitHeight: control.font.pixelSize

        enabled: theme.initialized

        color: control.backgroundColor

        border.color: visualFocus ? theme.visualFocus : theme.border

        radius: control.radius
    }

    contentItem: Widgets.IconLabel {
        text: control.designIcon.length ? "" : control.text

        color: control.color

        DelayedBehavior on color {
            delayedEnabled: theme.initialized

            ColorAnimation {
                duration: VLCStyle.duration_long
            }
        }

        font: control.font

        Widgets.DesignIcon {
            visible: control.designIcon.length > 0
            anchors.centerIn: parent
            width: implicitWidth
            height: implicitHeight
            name: control.designIcon
            color: control.color
        }
    }
}
