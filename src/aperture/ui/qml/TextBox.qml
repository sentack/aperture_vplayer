import QtQuick
import QtQuick.Controls.Basic as T

// Single-line text input in the app's style, with an optional label above it.
Column {
    id: box

    property alias text: field.text
    property alias placeholder: field.placeholderText
    property alias echoMode: field.echoMode
    property string label

    signal accepted()

    function focusField() {
        field.forceActiveFocus()
        field.selectAll()
    }

    spacing: 6

    UiText {
        visible: box.label !== ""
        text: box.label
        font.pixelSize: 12
        color: theme.text_secondary
    }

    T.TextField {
        id: field
        width: box.width
        font.family: "Inter"
        font.pixelSize: 14
        color: theme.text_primary
        placeholderTextColor: theme.text_tertiary
        selectionColor: theme.accent
        leftPadding: 12
        rightPadding: 12
        Accessible.name: box.label || box.placeholder
        background: Rectangle {
            implicitHeight: 38
            radius: 11
            color: theme.chip_bg
            border.width: field.activeFocus ? 2 : 1
            border.color: field.activeFocus ? theme.accent : theme.divider
        }
        onAccepted: box.accepted()
    }
}
