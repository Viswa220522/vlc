// SPDX-License-Identifier: GPL-2.0-or-later
// Native media-library binding for the reference browser; no sample media data.
import QtQuick
import VLC.MainInterface
import VLC.MediaLibrary
import VLC.Player
import VLC.Style
import VLC.Dialogs
import VLC.Menus as Menus
import VLC.Network

DesignBrowser {
    id: root
    property string locationKind: "playlists"
    property var locationId: null
    property string locationTitle: qsTr("Playlists")
    property var previousLocations: []
    property var nextLocations: []
    property url pendingThumbnail: ""
    entries: modelLoader.item
    itemCount: entries?.count ?? 0
    title: locationTitle
    section: locationKind === "playlists" || locationKind === "playlist" ? "playlists"
             : locationKind === "videos" || locationKind === "folder" ? "video" : "recent"
    titleRole: locationKind === "playlists" ? "name" : "title"
    entryIcon: locationKind === "playlists" ? "playlists" : locationKind === "videos" ? "folder" : "videos"
    actionText: locationKind === "playlists" ? qsTr("Create playlist") : locationKind === "videos" ? qsTr("Add") : ""
    actionEnabled: MainCtx.mediaLibraryAvailable && !(entries?.transactionPending ?? false)
    canBack: previousLocations.length > 0
    canForward: nextLocations.length > 0
    function location() { return { kind: locationKind, id: locationId, title: locationTitle } }
    function restore(target) {
        locationKind = target.kind
        locationId = target.id
        locationTitle = target.title
    }
    function navigate(kind, id, title) {
        previousLocations = [...previousLocations, location()]
        nextLocations = []
        restore({ kind: kind, id: id, title: title })
    }
    function openLibrary() {
        let path = ["video"]
        let properties = {}
        if (locationKind === "playlists") path = ["video", "playlists"]
        else if (locationKind === "playlist") {
            path = ["video", "playlists", "list"]
            properties = { parentId: locationId, title: locationTitle }
        } else if (locationKind === "folder") {
            path = ["video", "all", "group"]
            properties = { parentId: locationId, title: locationTitle }
        } else if (locationKind === "recent") path = ["home", "continueWatching"]
        History.push(path, properties)
        MainCtx.playerView = false
    }
    onCategoryRequested: uri => {
        if (uri[1] === "playlists") navigate("playlists", null, qsTr("Playlists"))
        else if (uri[0] === "video") navigate("videos", null, qsTr("Videos"))
        else if (uri[1] === "continueWatching") navigate("recent", null, qsTr("Recent"))
        else { History.push(uri); MainCtx.playerView = false }
    }
    onBackRequested: {
        if (!canBack) return
        nextLocations = [...nextLocations, location()]
        const next = previousLocations[previousLocations.length-1]
        previousLocations = previousLocations.slice(0, -1)
        restore(next)
    }
    onForwardRequested: {
        if (!canForward) return
        previousLocations = [...previousLocations, location()]
        const next = nextLocations[nextLocations.length-1]
        nextLocations = nextLocations.slice(0, -1)
        restore(next)
    }
    onExpandRequested: openLibrary()
    onSearchRequested: { openLibrary(); MainCtx.search.askShow() }
    onSortRequested: {
        if (entries) entries.sortOrder = entries.sortOrder === Qt.AscendingOrder ? Qt.DescendingOrder : Qt.AscendingOrder
    }
    onViewRequested: { openLibrary(); MainCtx.gridView = !MainCtx.gridView }
    onOptionsRequested: position => browserMenu.popup(position)
    onActionRequested: {
        if (locationKind === "playlists") newPlaylist.open()
        else {
            const folder = DialogsProvider.selectMediaFolder()
            if (folder.toString().length && folderEditor.item) folderEditor.item.add(folder)
        }
    }
    onEntryActivated: entry => {
        if (locationKind === "playlists") navigate("playlist", entry.id, entry.name)
        else if (locationKind === "videos") navigate("folder", entry.id, entry.title)
        else MediaLib.addAndPlay(entry.id)
    }
    onEntryPlayRequested: entry => MediaLib.addAndPlay(entry.id)
    Loader {
        id: folderEditor
        active: MainCtx.mediaLibraryAvailable
        sourceComponent: MLFolderModel { ctx: MainCtx }
    }
    Loader {
        id: modelLoader
        active: MainCtx.mediaLibraryAvailable
        sourceComponent: root.locationKind === "playlists" ? playlistLists
                         : root.locationKind === "playlist" ? playlistContents
                         : root.locationKind === "videos" ? videoFolders
                         : root.locationKind === "folder" ? folderContents : recentMedia
    }
    Component {
        id: playlistLists
        MLPlaylistListModel {
            ml: MediaLib
            playlistType: MLPlaylistListModel.PLAYLIST_TYPE_ALL
            onPlaylistCreated: id => {
                if (root.pendingThumbnail.toString().length)
                    MainCtx.setSettingValue("Juxtopposed/playlistCover/" + id, root.pendingThumbnail)
                root.pendingThumbnail = ""
            }
        }
    }
    Component {
        id: playlistContents
        MLPlaylistModel {
            id: playlistModel
            ml: MediaLib
            Binding on parentId { when: root.locationKind === "playlist" && root.locationId !== null; value: root.locationId }
        }
    }
    Component { id: videoFolders; MLVideoFoldersModel { ml: MediaLib } }
    Component {
        id: folderContents
        MLVideoModel {
            id: folderModel
            ml: MediaLib
            Binding on parentId { when: root.locationKind === "folder" && root.locationId !== null; value: root.locationId }
        }
    }
    Component { id: recentMedia; MLRecentMediaModel { ml: MediaLib } }
    DesignNewPlaylist {
        id: newPlaylist
        busy: root.entries?.transactionPending ?? false
        onSaveRequested: (name, files, thumbnail) => {
            root.pendingThumbnail = thumbnail
            root.entries.create(name, files)
        }
    }
    Menus.QmlGlobalMenu {
        id: browserMenu
        ctx: MainCtx
    }
}
