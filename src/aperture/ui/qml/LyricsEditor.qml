import QtQuick
import QtQuick.Controls.Basic as T

// Create lyrics for the playing audio file.
// Write: type or paste one line per lyric. Sync: play the track and tap as each line starts.
// Save writes <name>.lrc next to the file and can also embed it in the file's tags.
Modal {
    id: editor

    property bool syncing: false
    property int nextLine: 0
    // One entry per non-empty line: { text, time } with time -1 until tapped.
    property var rows: []

    cardWidth: 560
    cardHeight: 600

    function begin() {
        input.text = lyrics.plainText
        syncing = false
        open = true
    }

    function startSync() {
        rows = input.text.split("\n").map(t => t.trim()).filter(t => t !== "").map(t => ({ text: t, time: -1 }))
        nextLine = 0
        syncing = rows.length > 0
        if (syncing)
            player.seek(0)
    }

    function tap() {
        if (nextLine >= rows.length)
            return
        const copy = rows.slice()
        copy[nextLine] = { text: copy[nextLine].text, time: player.position }
        rows = copy
        nextLine += 1
    }

    function undo() {
        if (nextLine === 0)
            return
        nextLine -= 1
        const copy = rows.slice()
        copy[nextLine] = { text: copy[nextLine].text, time: -1 }
        rows = copy
    }

    function save(embed) {
        const out = syncing ? rows : input.text.split("\n").map(t => ({ text: t.trim(), time: -1 }))
        lyrics.save(out, embed)
        open = false
    }

    onCloseRequested: open = false

    UiText {
        id: heading
        anchors { left: parent.left; top: parent.top; margins: 24 }
        text: editor.syncing ? "Sync lyrics" : "Write lyrics"
        font.pixelSize: 18
        font.weight: Font.Bold
        color: theme.text_primary
    }

    UiText {
        id: hint
        anchors { left: parent.left; right: parent.right; top: heading.bottom; leftMargin: 24; rightMargin: 24; topMargin: 6 }
        text: editor.syncing
              ? "Play the track and press Tap (or Enter) as each highlighted line starts."
              : "One line per lyric. Sync them to the music next, or save them as plain lyrics."
        wrapMode: Text.WordWrap
        elide: Text.ElideNone
        font.pixelSize: 12
        color: theme.text_tertiary
    }

    T.ScrollView {
        anchors { left: parent.left; right: parent.right; top: hint.bottom; bottom: actions.top; margins: 24 }
        visible: !editor.syncing

        T.TextArea {
            id: input
            wrapMode: TextEdit.Wrap
            placeholderText: "Paste or type the lyrics here"
            font.family: "Inter"
            font.pixelSize: 14
            color: theme.text_primary
            placeholderTextColor: theme.text_tertiary
            selectionColor: theme.accent
            background: Rectangle {
                radius: 12
                color: theme.chip_bg
                border.width: 1
                border.color: theme.divider
            }
        }
    }

    ListView {
        id: syncList
        anchors { left: parent.left; right: parent.right; top: hint.bottom; bottom: actions.top; margins: 24 }
        visible: editor.syncing
        clip: true
        spacing: 4
        model: editor.rows
        currentIndex: editor.nextLine
        highlightRangeMode: ListView.ApplyRange
        preferredHighlightBegin: height * 0.35
        preferredHighlightEnd: height * 0.35 + 36
        focus: editor.syncing && editor.open

        Keys.onReturnPressed: editor.tap()
        Keys.onEnterPressed: editor.tap()

        delegate: Rectangle {
            id: syncRow

            required property int index
            required property var modelData
            readonly property bool next: index === editor.nextLine

            width: ListView.view.width
            height: 36
            radius: 10
            color: next ? theme.track_bg : "transparent"

            UiText {
                id: stamp
                anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                width: 52
                text: syncRow.modelData.time >= 0 ? player.formatTime(syncRow.modelData.time) : "—"
                font.features: ({ "tnum": 1 })
                color: theme.text_tertiary
                elide: Text.ElideNone
            }

            UiText {
                anchors { left: stamp.right; right: parent.right; leftMargin: 8; rightMargin: 10; verticalCenter: parent.verticalCenter }
                text: syncRow.modelData.text
                font.weight: syncRow.next ? Font.DemiBold : Font.Medium
                color: syncRow.next ? theme.text_primary : theme.text_secondary
            }
        }
    }

    Row {
        id: actions
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 24 }
        spacing: 8
        layoutDirection: Qt.RightToLeft

        PillButton {
            text: lyrics.canEmbed ? "Save and embed" : "Save .lrc"
            primary: true
            onClicked: editor.save(lyrics.canEmbed)
        }

        PillButton {
            text: "Save .lrc only"
            visible: lyrics.canEmbed
            onClicked: editor.save(false)
        }

        PillButton {
            text: editor.syncing ? "Back to text" : "Sync to music"
            onClicked: editor.syncing ? editor.syncing = false : editor.startSync()
        }

        PillButton {
            text: "Tap"
            visible: editor.syncing
            onClicked: editor.tap()
        }

        PillButton {
            text: "Undo tap"
            visible: editor.syncing && editor.nextLine > 0
            onClicked: editor.undo()
        }
    }
}
