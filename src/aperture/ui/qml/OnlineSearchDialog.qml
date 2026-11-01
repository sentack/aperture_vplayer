import QtQuick
import QtQuick.Controls.Basic as T

// Search lyrics (audio) or subtitles (video) online. The fields start from the file's tags
// or name, which are often wrong, so they stay editable; nothing is searched until asked.
Modal {
    id: dialog

    readonly property bool forLyrics: online.kind === "lyrics"

    signal settingsRequested()

    cardWidth: 620
    cardHeight: 600

    function begin(kind) {
        online.begin(kind)
        const guess = online.fields
        first.text = guess.title || ""
        second.text = forLyrics ? guess.artist || "" : guess.year || ""
        third.text = forLyrics ? guess.album || "" : guess.language || ""
        open = true
        first.focusField()
    }

    function search() {
        if (forLyrics)
            online.searchLyrics(first.text, second.text, third.text)
        else
            online.searchSubtitles(first.text, second.text, third.text)
    }

    function close() {
        online.cancel()
        open = false
    }

    onCloseRequested: close()

    Connections {
        target: online
        function onChosen() { dialog.open = false }
    }

    UiText {
        id: heading
        anchors { left: parent.left; top: parent.top; margins: 24 }
        text: dialog.forLyrics ? "Search lyrics online" : "Search subtitles online"
        font.pixelSize: 18
        font.weight: Font.Bold
        color: theme.text_primary
    }

    UiText {
        id: hint
        anchors { left: parent.left; right: parent.right; top: heading.bottom; leftMargin: 24; rightMargin: 24; topMargin: 6 }
        text: dialog.forLyrics
              ? "Filled in from the file's tags. Correct anything that's wrong. Lyrics from LRCLIB are saved into the audio file."
              : "Guessed from the file name. Correct anything that's wrong. Subtitles from OpenSubtitles are saved next to the video."
        wrapMode: Text.WordWrap
        elide: Text.ElideNone
        font.pixelSize: 12
        color: theme.text_tertiary
    }

    Column {
        id: form
        anchors { left: parent.left; right: parent.right; top: hint.bottom; leftMargin: 24; rightMargin: 24; topMargin: 16 }
        spacing: 10

        TextBox {
            id: first
            width: parent.width
            label: "Title"
            onAccepted: dialog.search()
        }

        Row {
            width: parent.width
            spacing: 10

            TextBox {
                id: second
                width: dialog.forLyrics ? (parent.width - 10) / 2 : 110
                label: dialog.forLyrics ? "Artist" : "Year"
                placeholder: dialog.forLyrics ? "" : "Optional"
                onAccepted: dialog.search()
            }

            TextBox {
                id: third
                width: parent.width - second.width - 10
                label: dialog.forLyrics ? "Album" : "Language"
                placeholder: dialog.forLyrics ? "Optional" : "en, or several: en,fr"
                onAccepted: dialog.search()
            }
        }
    }

    Row {
        id: searchRow
        anchors { left: parent.left; right: parent.right; top: form.bottom; leftMargin: 24; rightMargin: 24; topMargin: 14 }
        spacing: 10

        PillButton {
            id: searchButton
            text: online.busy ? "Cancel" : "Search"
            primary: !online.busy
            onClicked: online.busy ? online.cancel() : dialog.search()
        }

        PillButton {
            text: "Open Settings"
            visible: online.needsKey
            onClicked: dialog.settingsRequested()
        }

        UiText {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - x
            text: online.status
            wrapMode: Text.WordWrap
            elide: Text.ElideNone
            maximumLineCount: 3
            font.pixelSize: 12
            color: theme.text_secondary
        }
    }

    ListView {
        id: list
        anchors { left: parent.left; right: parent.right; top: searchRow.bottom; bottom: parent.bottom; margins: 24; topMargin: 16 }
        clip: true
        spacing: 2
        boundsBehavior: Flickable.StopAtBounds
        model: online.results
        T.ScrollBar.vertical: GlassScrollBar {}

        delegate: Rectangle {
            id: row

            required property int index
            required property var modelData

            width: ListView.view.width
            height: 54
            radius: 12
            color: rowArea.containsMouse ? theme.chip_bg : "transparent"
            opacity: online.busy ? 0.5 : 1

            Accessible.role: Accessible.Button
            Accessible.name: `${modelData.title}, ${modelData.detail}`
            Accessible.onPressAction: online.choose(row.index)

            Column {
                anchors { left: parent.left; right: badge.left; leftMargin: 14; rightMargin: 10; verticalCenter: parent.verticalCenter }
                spacing: 3

                UiText {
                    width: parent.width
                    text: row.modelData.title
                    color: theme.text_primary
                }

                UiText {
                    width: parent.width
                    text: row.modelData.detail
                    font.pixelSize: 12
                    color: theme.text_tertiary
                }
            }

            Rectangle {
                id: badge
                anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                visible: row.modelData.badge !== ""
                width: visible ? badgeText.implicitWidth + 16 : 0
                height: 22
                radius: 11
                color: row.modelData.badge === "Synced" ? theme.accent : theme.chip_bg

                UiText {
                    id: badgeText
                    anchors.centerIn: parent
                    text: row.modelData.badge
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                    color: row.modelData.badge === "Synced" ? "white" : theme.text_secondary
                    elide: Text.ElideNone
                }
            }

            MouseArea {
                id: rowArea
                anchors.fill: parent
                hoverEnabled: true
                enabled: !online.busy
                cursorShape: Qt.PointingHandCursor
                onClicked: online.choose(row.index)
            }
        }
    }
}
