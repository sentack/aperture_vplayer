import QtQuick

// Files opened from the file manager while a playlist plays: add them to it, or give them
// a window of their own. Closing the dialog opens nothing.
Modal {
    id: dialog

    readonly property var names: opening.names
    readonly property int shown: Math.min(names.length, 4)

    open: opening.pending
    cardWidth: 460
    cardHeight: 190 + shown * 22 + (names.length > shown ? 22 : 0)

    onCloseRequested: opening.dismiss()

    UiText {
        id: heading
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
        text: dialog.names.length === 1 ? "Open this file?" : `Open these ${dialog.names.length} files?`
        font.pixelSize: 18
        font.weight: Font.Bold
        color: theme.text_primary
    }

    UiText {
        id: hint
        anchors { left: parent.left; right: parent.right; top: heading.bottom; leftMargin: 24; rightMargin: 24; topMargin: 6 }
        text: "A playlist is already playing."
        font.pixelSize: 12
        color: theme.text_tertiary
    }

    Column {
        id: fileList
        anchors { left: parent.left; right: parent.right; top: hint.bottom; leftMargin: 24; rightMargin: 24; topMargin: 12 }
        spacing: 4

        Repeater {
            model: dialog.names.slice(0, dialog.shown)

            UiText {
                required property string modelData
                width: fileList.width
                text: modelData
                color: theme.text_secondary
            }
        }

        UiText {
            visible: dialog.names.length > dialog.shown
            text: `and ${dialog.names.length - dialog.shown} more`
            font.pixelSize: 12
            color: theme.text_tertiary
        }
    }

    Row {
        anchors { right: parent.right; bottom: parent.bottom; margins: 24 }
        spacing: 8

        PillButton {
            text: "Cancel"
            onClicked: opening.dismiss()
        }

        PillButton {
            text: "Open in new window"
            onClicked: opening.openInNewWindow()
        }

        PillButton {
            text: "Add to current playlist"
            primary: true
            onClicked: opening.addToPlaylist()
        }
    }
}
