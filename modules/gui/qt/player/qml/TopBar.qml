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
import VLC.MainInterface
import VLC.Style
import VLC.Player
import VLC.Widgets as Widgets

Widgets.DesignTitleBar {
    id: root
    required property int textWidth
    property int reservedHeight: height
    property int topMargin: 0
    property int sideMargin: 0
    property string title
    property bool showToolbar: false
    property bool pinControls: false
    property bool playlistVisible: false
    property alias resumeVisible: resumeDialog.visible
    signal togglePlaylistVisibility()
    signal backRequested()
    signal toggleBrowserVisibility()
    libraryControls: true
    onLibraryRequested: backRequested()
    onToggleNavigationVisibility: toggleBrowserVisibility()
    ResumeDialog {
        id: resumeDialog
        anchors.top: parent.bottom
        anchors.left: parent.left
        anchors.leftMargin: VLCStyle.dp(20, VLCStyle.scale)
        maxWidth: root.width - VLCStyle.dp(40, VLCStyle.scale)
        Navigation.parentItem: root
        onVisibleChanged: root.requestLockUnlockAutoHide(visible)
    }
}
