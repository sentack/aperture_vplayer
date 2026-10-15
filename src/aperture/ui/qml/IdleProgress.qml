import QtQuick
import QtQuick.Effects

// The one thing left on screen while idle: a 3px progress line with a soft accent glow.
Rectangle {
    id: line

    property real value: 0
    readonly property color accent: theme.accent

    implicitHeight: 3
    radius: 2
    color: theme.idle_track

    Rectangle {
        width: parent.width * Math.max(0, Math.min(1, line.value))
        height: parent.height
        radius: parent.radius
        color: line.accent
        layer.enabled: true
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: Qt.rgba(line.accent.r, line.accent.g, line.accent.b, 0.6)
            shadowBlur: 0.6
            shadowVerticalOffset: 0
        }
    }
}
