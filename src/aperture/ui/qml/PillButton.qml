import QtQuick

// Text button, fully rounded. `primary` fills with the accent.
Rectangle {
    id: button

    property alias text: label.text
    property bool primary: false

    signal clicked()

    implicitWidth: label.implicitWidth + 36
    implicitHeight: 36
    radius: height / 2
    color: primary ? theme.accent : area.containsMouse ? theme.track_bg : theme.chip_bg
    opacity: primary && area.containsMouse ? 0.9 : 1

    Accessible.role: Accessible.Button
    Accessible.name: text
    Accessible.onPressAction: button.clicked()

    UiText {
        id: label
        anchors.centerIn: parent
        font.weight: Font.DemiBold
        color: button.primary ? "white" : theme.text_primary
        elide: Text.ElideNone
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: button.clicked()
    }
}
