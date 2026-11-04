import QtQuick
import QtQuick.Controls.Basic as T
import "Icons.js" as Icons

// Glass side sheet listing the queue, or the recently used playlists. Click a row to select
// it, double-click to play; hover a row to remove it.
Rectangle {
    id: panel

    signal addRequested()
    signal openRequested()
    signal saveRequested()

    // The recent-playlists view: chosen with the clock button, and shown by itself while
    // the queue is empty and there is something to bring back.
    property bool historyChosen: false
    readonly property bool showHistory: historyChosen || (list.count === 0 && playlists.hasRecent)

    implicitWidth: 340
    radius: 22
    color: theme.bar_bg
    border.width: 1
    border.color: theme.bar_border

    // Presses and wheel turns on the glass stay here (not the video, not the lyrics below).
    InputShield {}

    Item {
        id: header
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 56

        Row {
            anchors { left: parent.left; leftMargin: 20; right: tools.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
            spacing: 8

            SectionLabel { text: panel.showHistory ? "Recent playlists" : "Playlist" }

            UiText {
                anchors.verticalCenter: parent.verticalCenter
                text: player.playlistLength ? `${player.playlist.length} · ${player.playlistLength}` : player.playlist.length
                font.pixelSize: 11
                font.weight: Font.DemiBold
                font.features: ({ "tnum": 1 })
                color: theme.text_tertiary
                visible: !panel.showHistory && player.playlist.length > 0
                elide: Text.ElideNone
            }
        }

        Row {
            id: tools
            anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
            spacing: 2

            IconButton {
                glyph: Icons.add
                label: "Add files"
                onClicked: panel.addRequested()
            }

            IconButton {
                glyph: Icons.folderOpen
                label: "Open playlist"
                onClicked: panel.openRequested()
            }

            IconButton {
                glyph: Icons.save
                label: playlists.fileName ? "Save playlist as" : "Save playlist"
                enabled: player.playlist.length > 0
                onClicked: panel.saveRequested()
            }

            IconButton {
                glyph: Icons.history
                label: panel.historyChosen ? "Back to the playlist" : "Recent playlists"
                iconColor: panel.historyChosen ? theme.accent : theme.text_secondary
                onClicked: panel.historyChosen = !panel.historyChosen
            }

            IconButton {
                glyph: Icons.trash
                label: panel.showHistory ? "Clear recent playlists" : "Clear playlist"
                enabled: panel.showHistory ? playlists.hasRecent : player.playlist.length > 0
                onClicked: panel.showHistory ? playlists.clear() : player.clearPlaylist()
            }
        }
    }

    Rectangle {
        anchors { left: parent.left; right: parent.right; top: header.bottom; leftMargin: 16; rightMargin: 16 }
        height: 1
        color: theme.divider
    }

    // The playlist file this queue came from: its name, and Save once files were added or
    // removed (or a note that autosave takes care of it).
    Item {
        id: fileBar
        anchors { left: parent.left; right: parent.right; top: header.bottom; topMargin: 1 }
        height: visible ? 44 : 0
        visible: !panel.showHistory && playlists.fileName !== ""

        UiText {
            anchors { left: parent.left; leftMargin: 20; right: fileStatus.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
            text: playlists.fileName
            font.pixelSize: 12
            font.weight: Font.DemiBold
            color: theme.text_secondary
        }

        Item {
            id: fileStatus
            anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
            width: saveChanges.visible ? saveChanges.width : savedNote.implicitWidth
            height: 28

            UiText {
                id: savedNote
                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                visible: !saveChanges.visible
                text: playlists.unsaved ? "Saving…" : prefs.autosavePlaylist ? "Saves automatically" : "Saved"
                font.pixelSize: 11
                color: theme.text_tertiary
                elide: Text.ElideNone
            }

            PillButton {
                id: saveChanges
                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                visible: playlists.unsaved && !prefs.autosavePlaylist
                implicitHeight: 28
                text: "Save"
                primary: true
                Accessible.name: `Save changes to ${playlists.fileName}`
                onClicked: playlists.saveChanges()
            }
        }
    }

    ListView {
        id: list
        anchors { left: parent.left; right: parent.right; top: fileBar.visible ? fileBar.bottom : header.bottom; bottom: parent.bottom; margins: 8 }
        visible: !panel.showHistory
        clip: true
        spacing: 2
        boundsBehavior: Flickable.StopAtBounds
        model: player.playlist
        currentIndex: player.currentIndex
        T.ScrollBar.vertical: GlassScrollBar {}

        // Single click selects a row; only a double click plays it.
        property int selectedIndex: -1

        onCountChanged: if (selectedIndex >= count) selectedIndex = -1

        delegate: Rectangle {
            id: row

            required property int index
            required property string modelData
            readonly property bool current: index === player.currentIndex
            readonly property bool selected: index === list.selectedIndex
            readonly property bool hovered: rowHover.hovered || removeButton.hovered
            readonly property string length: player.playlistDurations[index] || ""

            width: ListView.view.width
            height: 44
            radius: 12
            color: selected ? theme.track_bg : current || hovered ? theme.chip_bg : "transparent"

            Accessible.role: Accessible.ListItem
            Accessible.name: length ? `${modelData}, ${length}` : modelData
            Accessible.selected: selected
            Accessible.onPressAction: player.playIndex(row.index)

            HoverHandler { id: rowHover }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: list.selectedIndex = row.index
                onDoubleClicked: player.playIndex(row.index)
            }

            Rectangle {
                id: marker
                anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                width: 6
                height: 6
                radius: 3
                color: row.current ? theme.accent : theme.track_bg
            }

            UiText {
                anchors {
                    left: marker.right; leftMargin: 12
                    right: lengthLabel.left; rightMargin: 8
                    verticalCenter: parent.verticalCenter
                }
                text: row.modelData
                color: row.current ? theme.text_primary : theme.text_secondary
            }

            // The length, where the remove button appears on hover.
            UiText {
                id: lengthLabel
                anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                width: Math.max(28, implicitWidth)
                horizontalAlignment: Text.AlignRight
                text: row.length
                font.pixelSize: 12
                font.features: ({ "tnum": 1 })
                color: theme.text_tertiary
                elide: Text.ElideNone
                opacity: row.hovered ? 0 : 1
            }

            IconButton {
                id: removeButton
                anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                width: 28
                height: 28
                iconSize: 14
                glyph: Icons.close
                label: "Remove from playlist"
                opacity: row.hovered ? 1 : 0
                onClicked: player.removeIndex(row.index)
            }
        }
    }

    ListView {
        id: history
        anchors { left: parent.left; right: parent.right; top: header.bottom; bottom: parent.bottom; margins: 8 }
        visible: panel.showHistory
        clip: true
        spacing: 2
        boundsBehavior: Flickable.StopAtBounds
        model: playlists.recent
        T.ScrollBar.vertical: GlassScrollBar {}

        delegate: Rectangle {
            id: entry

            required property int index
            required property var modelData
            readonly property bool hovered: entryHover.hovered || forget.hovered

            width: ListView.view.width
            height: 54
            radius: 12
            color: hovered ? theme.chip_bg : "transparent"

            Accessible.role: Accessible.Button
            Accessible.name: `Open playlist ${modelData.name}, ${modelData.detail}`
            Accessible.onPressAction: entry.reopen()

            function reopen() {
                playlists.open(entry.index)
                panel.historyChosen = false
            }

            HoverHandler { id: entryHover }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: entry.reopen()
            }

            Column {
                anchors { left: parent.left; right: forget.left; leftMargin: 14; rightMargin: 8; verticalCenter: parent.verticalCenter }
                spacing: 3

                UiText {
                    width: parent.width
                    text: entry.modelData.name
                    color: theme.text_primary
                }

                UiText {
                    width: parent.width
                    text: entry.modelData.saved ? `${entry.modelData.detail} · saved` : entry.modelData.detail
                    font.pixelSize: 12
                    color: theme.text_tertiary
                }
            }

            IconButton {
                id: forget
                anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                width: 28
                height: 28
                iconSize: 14
                glyph: Icons.close
                label: "Remove from recent playlists"
                opacity: entry.hovered ? 1 : 0
                onClicked: playlists.remove(entry.index)
            }
        }
    }

    UiText {
        anchors.centerIn: list
        width: parent.width - 48
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        elide: Text.ElideNone
        visible: panel.showHistory ? history.count === 0 : list.count === 0
        text: panel.showHistory ? "Playlists you save, open or play through show up here"
                                : "Queue is empty — add or drop videos"
        color: theme.text_tertiary
    }

    DropZone {
        anchors.fill: parent
        inset: 6
        radius: 18
        hint: "Add to playlist"
        onUrlsDropped: urls => player.addUrls(urls)
    }
}
