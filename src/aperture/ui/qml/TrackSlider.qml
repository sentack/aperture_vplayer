import QtQuick

// Accent-filled track. Press or drag to scrub: `moved` fires live, `value` follows the model.
// `hoverValue` tracks the pointer even without a press, for previews.
Item {
    id: slider

    property real value: 0
    property real trackHeight: 6
    property real knobSize: 0
    property string label

    signal moved(real value)

    readonly property bool pressed: area.pressed
    readonly property bool hovering: area.containsMouse
    readonly property real hoverValue: area.hoverValue
    readonly property real shown: Math.max(0, Math.min(1, area.pressed ? area.dragValue : value))

    implicitHeight: Math.max(knobSize + 6, 14)

    Accessible.role: Accessible.Slider
    Accessible.name: label

    Rectangle {
        id: track
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width
        height: slider.trackHeight
        radius: height / 2
        color: theme.track_bg
    }

    Rectangle {
        anchors.verticalCenter: track.verticalCenter
        width: track.width * slider.shown
        height: track.height
        radius: track.radius
        color: theme.accent
        visible: slider.shown > 0
    }

    // Knob sits on the fill's end, ringed by a 3px halo of the bar glass.
    Rectangle {
        visible: slider.knobSize > 0 && slider.enabled
        x: track.width * slider.shown - width / 2
        anchors.verticalCenter: track.verticalCenter
        width: slider.knobSize + 6
        height: width
        radius: width / 2
        color: theme.bar_bg

        Rectangle {
            anchors.centerIn: parent
            width: slider.knobSize
            height: width
            radius: width / 2
            color: theme.accent
        }
    }

    MouseArea {
        id: area

        property real dragValue: 0
        property real hoverValue: 0

        function scrub(x) {
            dragValue = Math.max(0, Math.min(1, x / width))
            slider.moved(dragValue)
        }

        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        preventStealing: true
        onPressed: mouse => scrub(mouse.x)
        onPositionChanged: mouse => {
            hoverValue = Math.max(0, Math.min(1, mouse.x / width))
            if (pressed)
                scrub(mouse.x)
        }
    }
}
