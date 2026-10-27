import QtQuick
import QtQuick.Window
import "Icons.js" as Icons

// Overlay for the mini window: transport in the middle, restore and close in the corner.
// Sits on video in either theme, so glyphs are always light.
Item {
    id: controls

    signal restoreRequested()

    readonly property bool hovered: hover.hovered

    component MiniButton: IconButton {
        iconColor: Qt.rgba(1, 1, 1, 0.8)
        iconHoverColor: "white"
        color: hovered ? Qt.rgba(1, 1, 1, 0.14) : "transparent"
    }

    HoverHandler { id: hover }

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.35)
    }

    Row {
        anchors.centerIn: parent
        spacing: 14

        MiniButton {
            anchors.verticalCenter: parent.verticalCenter
            glyph: Icons.previous
            label: "Previous"
            onClicked: player.playPrevious()
        }

        Rectangle {
            width: 44
            height: 44
            radius: 22
            color: theme.accent

            Accessible.role: Accessible.Button
            Accessible.name: player.playing ? "Pause" : "Play"
            Accessible.onPressAction: player.togglePlay()

            Icon {
                anchors.centerIn: parent
                anchors.horizontalCenterOffset: player.playing ? 0 : 1
                size: 16
                glyph: player.playing ? Icons.pause : Icons.play
                color: "white"
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: player.togglePlay()
            }
        }

        MiniButton {
            anchors.verticalCenter: parent.verticalCenter
            glyph: Icons.next
            label: "Next"
            enabled: player.hasNext
            onClicked: player.playNext()
        }
    }

    Row {
        anchors { top: parent.top; right: parent.right; margins: 8 }
        spacing: 2

        MiniButton {
            glyph: Icons.expand
            iconSize: 16
            label: "Restore full player"
            onClicked: controls.restoreRequested()
        }

        MiniButton {
            glyph: Icons.close
            iconSize: 16
            label: "Close"
            onClicked: controls.Window.window.close()
        }
    }
}
