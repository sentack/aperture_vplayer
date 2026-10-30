import QtQuick
import QtQuick.Controls.Basic as T

// Play a network stream or a direct video link.
Modal {
    id: dialog

    cardWidth: 520
    cardHeight: 210

    function begin() {
        field.text = ""
        open = true
        field.forceActiveFocus()
    }

    function submit() {
        if (player.openUrl(field.text))
            open = false
    }

    onCloseRequested: open = false

    UiText {
        id: heading
        anchors { left: parent.left; top: parent.top; margins: 24 }
        text: "Open URL"
        font.pixelSize: 18
        font.weight: Font.Bold
        color: theme.text_primary
    }

    T.TextField {
        id: field
        anchors { left: parent.left; right: parent.right; top: heading.bottom; leftMargin: 24; rightMargin: 24; topMargin: 14 }
        placeholderText: "https://example.com/video.mp4, an .m3u8 stream, rtsp://…"
        font.family: "Inter"
        font.pixelSize: 14
        color: theme.text_primary
        placeholderTextColor: theme.text_tertiary
        selectionColor: theme.accent
        leftPadding: 12
        rightPadding: 12
        background: Rectangle {
            implicitHeight: 40
            radius: 12
            color: theme.chip_bg
            border.width: field.activeFocus ? 2 : 1
            border.color: field.activeFocus ? theme.accent : theme.divider
        }
        onAccepted: dialog.submit()
    }

    Row {
        anchors { right: parent.right; bottom: parent.bottom; margins: 24 }
        spacing: 8

        PillButton {
            text: "Cancel"
            onClicked: dialog.open = false
        }

        PillButton {
            text: "Play"
            primary: true
            onClicked: dialog.submit()
        }
    }
}
