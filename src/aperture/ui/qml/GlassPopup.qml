import QtQuick
import QtQuick.Controls.Basic as T

// Popover shell matching the control bar glass. Opens above its parent, right-aligned.
T.Popup {
    x: parent ? parent.width - width : 0
    y: -height - 14
    padding: 16
    closePolicy: T.Popup.CloseOnEscape | T.Popup.CloseOnPressOutsideParent

    background: Rectangle {
        radius: 18
        color: theme.popover_bg
        border.width: 1
        border.color: theme.bar_border
    }
}
