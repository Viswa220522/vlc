// SPDX-License-Identifier: GPL-2.0-or-later
// Juxtopposed's 713 x 590 New Playlist dialog.
import QtQuick
import QtQuick.Window
import QtQuick.Templates as T
import VLC.Style
import VLC.Widgets as Widgets
import VLC.Dialogs

T.Popup {
    id: root
    function dp(value) { return VLCStyle.dp(value, VLCStyle.scale) }
    width: dp(713); height: dp(590); padding: 0
    modal: true; focus: true
    closePolicy: T.Popup.CloseOnEscape
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    property var selectedUrls: []
    property url selectedThumbnail: ""
    property bool busy: false
    signal saveRequested(string name, var files, url thumbnail)
    function chooseFiles() {
        selectedUrls = [...selectedUrls, ...DialogsProvider.showSimpleOpen(qsTr("Select files"))]
    }
    readonly property ColorContext colorContext: ColorContext { id: theme; colorSet: ColorContext.Window }
    readonly property bool dark: theme.palette?.isDark ?? true
    readonly property color canvas: dark ? "#191919" : theme.bg.primary
    readonly property color recessed: dark ? "#090909" : theme.bg.secondary
    readonly property color bodyText: dark ? "#c6c6c6" : theme.fg.primary
    readonly property color mutedText: dark ? "#6b6b6b" : theme.fg.secondary
    background: Rectangle { radius: root.dp(14); color: root.canvas }
    onOpened: nameField.forceActiveFocus()
    onClosed: { selectedUrls = []; selectedThumbnail = ""; nameField.clear() }
    contentItem: Item {
        component Copy: Widgets.LabelExt {
            x: root.dp(20)
            height: root.dp(25)
            font.pixelSize: root.dp(14)
            color: root.mutedText
            verticalAlignment: Text.AlignVCenter
        }
        Rectangle {
            width: parent.width; height: root.dp(50)
            color: root.recessed; radius: root.dp(14)
            Rectangle { width: parent.width; y: root.dp(14); height: root.dp(36); color: parent.color }
            Copy { x: root.dp(19); anchors.verticalCenter: parent.verticalCenter; text: qsTr("New Playlist"); color: theme.fg.secondary }
            Widgets.DesignIconButton {
                x: parent.width - width - root.dp(9); y: root.dp(9)
                width: root.dp(32); height: width
                iconName: "close"; description: qsTr("Close")
                onClicked: root.close()
            }
        }
        Copy {
            y: root.dp(72); height: root.dp(28)
            text: qsTr("Playlist Details"); font.pixelSize: root.dp(16); color: root.bodyText
        }
        Copy { y: root.dp(105); text: qsTr("The playlist will be saved and displayed with this title and thumbnail.") }
        Widgets.TextFieldExt {
            id: nameField
            objectName: "newPlaylistTitle"
            x: root.dp(22); y: root.dp(154); width: root.dp(537); height: root.dp(34)
            placeholderText: qsTr("e.g., Favorite Videos")
            font.pixelSize: root.dp(14); color: root.bodyText; placeholderTextColor: root.mutedText
            Accessible.name: qsTr("Playlist title")
            onAccepted: if (saveButton.enabled) saveButton.clicked()
            background: Rectangle { color: root.recessed; radius: root.dp(4) }
        }
        Rectangle {
            x: root.dp(583); y: root.dp(79); width: root.dp(112); height: width
            radius: root.dp(6); color: root.recessed
            border.width: root.dp(2); border.color: root.canvas
            Image { anchors.fill: parent; source: root.selectedThumbnail; fillMode: Image.PreserveAspectFit }
            Widgets.DesignIconButton {
                anchors.centerIn: parent
                iconName: "add"; description: qsTr("Choose playlist thumbnail")
                background: Rectangle { radius: root.dp(5); color: root.dark ? "#161616" : theme.bg.primary }
                onClicked: {
                    const selected = DialogsProvider.selectPlaylistThumbnail()
                    if (selected.toString().length) root.selectedThumbnail = selected
                }
            }
        }
        Rectangle { x: root.dp(20); y: root.dp(211); width: root.dp(673); height: root.dp(1); color: theme.separator; opacity: 0.3 }
        Copy { y: root.dp(232); height: root.dp(28); text: qsTr("Select Files"); font.pixelSize: root.dp(16); color: root.bodyText }
        Copy { y: root.dp(265); text: qsTr("These files will be added to the playlist.") }
        Rectangle {
            x: root.dp(20); y: root.dp(310); width: root.dp(673); height: root.dp(186)
            color: root.recessed; radius: root.dp(6)
            MouseArea { anchors.fill: parent; onClicked: root.chooseFiles() }
            Image {
                anchors.fill: parent
                source: "qrc:/juxtopposed/playlist-drop-border.svg"
                sourceSize: Qt.size(Math.ceil(width * Screen.devicePixelRatio),
                                    Math.ceil(height * Screen.devicePixelRatio))
            }
            DropArea {
                anchors.fill: parent
                onDropped: drop => {
                    if (drop.hasUrls) { root.selectedUrls = [...root.selectedUrls, ...drop.urls]; drop.acceptProposedAction() }
                }
            }
            Copy {
                x: 0; y: root.dp(56); width: parent.width; horizontalAlignment: Text.AlignHCenter
                text: root.selectedUrls.length ? qsTr("%1 files selected").arg(root.selectedUrls.length)
                                              : qsTr("Drag files into the box or click here to select files.")
            }
            Widgets.DesignIconButton {
                anchors.horizontalCenter: parent.horizontalCenter
                y: root.dp(97); width: root.dp(84); height: root.dp(30)
                iconName: "add"; description: qsTr("Select files")
                background: Rectangle { radius: root.dp(5); color: root.dark ? "#161616" : theme.bg.primary }
                onClicked: root.chooseFiles()
            }
        }
        component DialogButton: T.Button {
            property bool primary: false
            width: root.dp(100); height: root.dp(32); y: root.dp(538)
            opacity: enabled ? 1 : 0.5
            activeFocusOnTab: true
            background: Rectangle {
                radius: root.dp(6)
                color: parent.primary ? "#371f06" : theme.bg.primary
                border.color: parent.visualFocus ? theme.visualFocus : "transparent"
            }
            contentItem: Widgets.LabelExt {
                text: parent.text
                color: parent.primary ? theme.accent : theme.fg.secondary
                font.pixelSize: root.dp(14)
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }
        }
        DialogButton { x: root.dp(20); text: qsTr("Cancel"); onClicked: root.close() }
        DialogButton {
            id: saveButton
            objectName: "newPlaylistSave"
            x: root.dp(593); text: qsTr("Save"); primary: true
            enabled: nameField.text.trim().length > 0 && !root.busy
            onClicked: { root.saveRequested(nameField.text.trim(), root.selectedUrls, root.selectedThumbnail); root.close() }
        }
    }
}
