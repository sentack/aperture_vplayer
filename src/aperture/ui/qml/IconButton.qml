import QtQuick

// Rounded-square hit target around one Icon. Hover lifts the glyph to text_primary.
Rectangle {
    id: button

    property alias glyph: icon.glyph
    property alias iconSize: icon.size
    property alias strokeWidth: icon.strokeWidth
    property string label

    signal clicked()

    readonly property bool hovered: area.containsMouse

    implicitWidth: 32
    implicitHeight: 32
    radius: 10
    color: hovered ? theme.chip_bg : "transparent"
    opacity: enabled ? 1 : 0.4

    Accessible.role: Accessible.Button
    Accessible.name: label
    Accessible.onPressAction: button.clicked()

    Icon {
        id: icon
        anchors.centerIn: parent
        color: button.hovered ? theme.text_primary : theme.text_secondary
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: button.clicked()
    }
}
