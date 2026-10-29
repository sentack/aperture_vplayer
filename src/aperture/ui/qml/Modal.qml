import QtQuick

// Full-window modal: dimmed backdrop plus a centred glass card. Children go in the card.
// Clicking the backdrop or pressing Esc (handled by KeyBindings) closes it.
Item {
    id: modal

    property bool open: false
    property real cardWidth: 720
    property real cardHeight: 520
    default property alias content: card.data

    signal closeRequested()

    anchors.fill: parent
    visible: opacity > 0
    opacity: open ? 1 : 0
    enabled: open

    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.45)

        MouseArea {
            anchors.fill: parent
            onClicked: modal.closeRequested()
        }
    }

    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(modal.cardWidth, modal.width - 48)
        height: Math.min(modal.cardHeight, modal.height - 48)
        radius: 22
        color: theme.popover_bg
        border.width: 1
        border.color: theme.bar_border
        scale: modal.open ? 1 : 0.97

        Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

        // Keep clicks inside the card from closing the modal.
        MouseArea { anchors.fill: parent }
    }
}
