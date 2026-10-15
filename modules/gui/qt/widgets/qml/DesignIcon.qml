// SPDX-License-Identifier: GPL-2.0-or-later
// Original icon artwork: Juxtopposed's VLC Redesign (Community).
import QtQuick
import VLC.Style
import VLC.Util

Item {
    id: root
    required property string name
    property color color: "#8f8f8f"
    implicitWidth: VLCStyle.dp(["minimize", "maximize", "fullscreen", "close"].includes(name) ? 36
                              : ["more", "sidebar", "folder"].includes(name) ? 28 : 24, VLCStyle.scale)
    implicitHeight: VLCStyle.dp(["videos", "music"].includes(name) ? 18
                               : ["more", "sidebar", "folder"].includes(name) ? 28 : 24, VLCStyle.scale)
    Accessible.ignored: true
    Image {
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit
        sourceSize: Qt.size(Math.ceil(width * 3), Math.ceil(height * 3))
        source: root.name.length ? EffectsImageProvider.url(EffectsImageProvider.TintedImage, {
            path: ":/juxtopposed/" + root.name + ".png",
            color: root.color
        }) : ""
    }
}
