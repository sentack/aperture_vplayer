import QtQuick

// Bottom-right question card: a title, one line of context, and up to two answers.
// Fades in and out; hidden cards take no clicks.
Rectangle {
    id: card

    property alias title: heading.text
    property alias message: body.text
    property string acceptText
    property string rejectText
    property string laterText  // optional third, quieter answer
    property bool shown: false

    signal accepted()
    signal rejected()
    signal deferred()

    implicitWidth: 320
    implicitHeight: content.implicitHeight + 36
    radius: 18
    color: theme.popover_bg
    border.width: 1
    border.color: theme.bar_border
    opacity: shown ? 1 : 0
    visible: opacity > 0
    enabled: shown

    Behavior on opacity { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }

    Accessible.role: Accessible.AlertMessage
    Accessible.name: `${title}. ${message}`

    // Keep clicks on the card from toggling playback underneath.
    MouseArea { anchors.fill: parent }

    Column {
        id: content
        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 18 }
        spacing: 6

        UiText {
            id: heading
            width: parent.width
            font.pixelSize: 15
            font.weight: Font.Bold
            color: theme.text_primary
        }

        UiText {
            id: body
            width: parent.width
            visible: text !== ""
            wrapMode: Text.WordWrap
            elide: Text.ElideNone
        }

        Item {
            width: 1
            height: 6
        }

        Row {
            spacing: 8

            PillButton {
                text: card.acceptText
                primary: true
                onClicked: card.accepted()
            }

            PillButton {
                text: card.rejectText
                visible: text !== ""
                onClicked: card.rejected()
            }
        }

        UiText {
            visible: card.laterText !== ""
            topPadding: 4
            text: card.laterText
            font.pixelSize: 12
            font.underline: laterArea.containsMouse
            color: theme.text_tertiary

            MouseArea {
                id: laterArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: card.deferred()
            }
        }
    }
}
