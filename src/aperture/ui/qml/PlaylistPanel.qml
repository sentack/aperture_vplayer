import QtQuick
import "Icons.js" as Icons

// Glass side sheet listing the queue. Click a row to play it, hover to remove it.
Rectangle {
    id: panel

    signal addRequested()

    implicitWidth: 340
    radius: 22
    color: theme.bar_bg
    border.width: 1
    border.color: theme.bar_border

    // Swallow presses on the glass so they never reach the video's tap handler.
    MouseArea { anchors.fill: parent }

    Item {
        id: header
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 56

        Row {
            anchors { left: parent.left; leftMargin: 20; verticalCenter: parent.verticalCenter }
            spacing: 8

            UiText {
                text: "PLAYLIST"
                font.pixelSize: 11
                font.weight: Font.DemiBold
                font.letterSpacing: 11 * 0.08
                color: theme.text_tertiary
            }

            UiText {
                text: player.playlist.length
                font.pixelSize: 11
                font.weight: Font.DemiBold
                color: theme.text_tertiary
                visible: player.playlist.length > 0
            }
        }

        Row {
            anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
            spacing: 4

            IconButton {
                glyph: Icons.add
                label: "Add files"
                onClicked: panel.addRequested()
            }

            IconButton {
                glyph: Icons.trash
                label: "Clear playlist"
                enabled: player.playlist.length > 0
                onClicked: player.clearPlaylist()
            }
        }
    }

    Rectangle {
        anchors { left: parent.left; right: parent.right; top: header.bottom; leftMargin: 16; rightMargin: 16 }
        height: 1
        color: theme.divider
    }

    ListView {
        id: list
        anchors { left: parent.left; right: parent.right; top: header.bottom; bottom: parent.bottom; margins: 8 }
        clip: true
        spacing: 2
        boundsBehavior: Flickable.StopAtBounds
        model: player.playlist
        currentIndex: player.currentIndex

        delegate: Rectangle {
            id: row

            required property int index
            required property string modelData
            readonly property bool current: index === player.currentIndex
            readonly property bool hovered: rowHover.hovered || removeButton.hovered

            width: ListView.view.width
            height: 44
            radius: 12
            color: current || hovered ? theme.chip_bg : "transparent"

            HoverHandler { id: rowHover }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: player.playIndex(row.index)
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
                    right: removeButton.left; rightMargin: 8
                    verticalCenter: parent.verticalCenter
                }
                text: row.modelData
                color: row.current ? theme.text_primary : theme.text_secondary
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

    UiText {
        anchors.centerIn: list
        visible: list.count === 0
        text: "Queue is empty — add videos with +"
        color: theme.text_tertiary
    }
}
