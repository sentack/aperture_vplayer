import QtQuick
import QtQuick.Controls.Basic as T

// Slim themed scrollbar for lists and pages that can outgrow their panel. Shown only when
// there is more to scroll to; widens under the pointer so it is easy to grab.
T.ScrollBar {
    id: bar

    policy: size < 1 ? T.ScrollBar.AlwaysOn : T.ScrollBar.AlwaysOff
    padding: 2
    minimumSize: 0.08

    contentItem: Rectangle {
        implicitWidth: bar.hovered || bar.pressed ? 8 : 5
        implicitHeight: implicitWidth
        radius: width / 2
        color: bar.pressed ? theme.text_secondary : theme.text_tertiary
        opacity: bar.hovered || bar.pressed ? 1 : 0.7

        Behavior on implicitWidth { NumberAnimation { duration: 120 } }
    }

    background: Item {}
}
