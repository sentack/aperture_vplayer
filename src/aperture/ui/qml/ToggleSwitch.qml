import QtQuick

// Pill switch: accent track with a white knob when on.
Rectangle {
    id: toggle

    property bool checked: false
    property string label

    signal toggled(bool checked)

    implicitWidth: 40
    implicitHeight: 24
    radius: height / 2
    color: checked ? theme.accent : theme.track_bg

    Accessible.role: Accessible.CheckBox
    Accessible.name: label
    Accessible.checked: checked
    Accessible.onPressAction: toggle.toggled(!toggle.checked)

    Behavior on color { ColorAnimation { duration: 150 } }

    Rectangle {
        x: toggle.checked ? toggle.width - width - 3 : 3
        anchors.verticalCenter: parent.verticalCenter
        width: toggle.height - 6
        height: width
        radius: width / 2
        color: "white"

        Behavior on x { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: toggle.toggled(!toggle.checked)
    }
}
