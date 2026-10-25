import QtQuick

// Shown instead of a frozen frame when a file cannot be played.
Rectangle {
    id: card

    signal openRequested()

    implicitHeight: content.implicitHeight + 48
    radius: 22
    color: theme.popover_bg
    border.width: 1
    border.color: theme.bar_border

    Accessible.role: Accessible.AlertMessage
    Accessible.name: `${player.errorTitle}. ${player.error}`

    // Keep clicks on the card from toggling playback underneath.
    MouseArea { anchors.fill: parent }

    Column {
        id: content
        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 24 }
        spacing: 8

        UiText {
            width: parent.width
            text: player.errorTitle
            font.pixelSize: 18
            font.weight: Font.Bold
            color: theme.text_primary
        }

        UiText {
            width: parent.width
            text: player.error
            wrapMode: Text.WordWrap
            elide: Text.ElideNone
        }

        Item {
            width: 1
            height: 8
        }

        Row {
            spacing: 8

            PillButton {
                text: "Play next"
                primary: true
                visible: player.hasNext
                onClicked: player.playNext()
            }

            PillButton {
                text: "Open another file"
                primary: !player.hasNext
                onClicked: card.openRequested()
            }
        }
    }
}
