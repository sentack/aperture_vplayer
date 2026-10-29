import QtQuick

// Spotify-style lyrics for audio files: big bold lines on an accent wash, the sung line
// bright, the rest dimmed, scrolling to keep the sung line in the upper third.
Item {
    id: view

    signal loadRequested()
    signal editRequested()

    readonly property color accent: theme.accent

    Rectangle {
        anchors.fill: parent
        radius: 26
        gradient: Gradient {
            GradientStop { position: 0; color: Qt.darker(view.accent, 1.4) }
            GradientStop { position: 1; color: Qt.darker(view.accent, 3.2) }
        }
    }

    Row {
        anchors { top: parent.top; right: parent.right; margins: 16 }
        spacing: 6
        visible: lyrics.available

        UiText {
            anchors.verticalCenter: parent.verticalCenter
            text: lyrics.synced ? lyrics.source : `${lyrics.source} · not synced`
            font.pixelSize: 12
            color: Qt.rgba(1, 1, 1, 0.6)
        }

        PillButton {
            text: "Edit lyrics"
            onClicked: view.editRequested()
        }
    }

    ListView {
        id: list
        anchors { fill: parent; topMargin: 56; bottomMargin: 24; leftMargin: 48; rightMargin: 48 }
        visible: lyrics.available
        clip: true
        spacing: 14
        model: lyrics.lines
        boundsBehavior: Flickable.StopAtBounds
        currentIndex: lyrics.currentIndex
        highlightRangeMode: lyrics.synced ? ListView.ApplyRange : ListView.NoHighlightRange
        preferredHighlightBegin: height * 0.3
        preferredHighlightEnd: height * 0.3 + 60
        highlightMoveDuration: 450
        header: Item { height: lyrics.synced ? list.height * 0.3 : 0 }
        footer: Item { height: lyrics.synced ? list.height * 0.6 : 24 }

        delegate: UiText {
            id: line

            required property int index
            required property var modelData
            readonly property bool sung: lyrics.synced && index === lyrics.currentIndex
            readonly property bool past: lyrics.synced && index < lyrics.currentIndex

            width: ListView.view.width
            text: modelData.text || "♪"
            wrapMode: Text.WordWrap
            elide: Text.ElideNone
            font.pixelSize: 30
            font.weight: Font.Bold
            color: "white"
            opacity: !lyrics.synced || sung ? 1 : past ? 0.55 : 0.35

            Behavior on opacity { NumberAnimation { duration: 250 } }

            MouseArea {
                anchors.fill: parent
                enabled: lyrics.synced
                cursorShape: Qt.PointingHandCursor
                onClicked: lyrics.seekToLine(line.index)
            }
        }
    }

    Column {
        anchors.centerIn: parent
        spacing: 12
        visible: !lyrics.available

        UiText {
            anchors.horizontalCenter: parent.horizontalCenter
            text: player.title
            font.pixelSize: 28
            font.weight: Font.Bold
            color: "white"
        }

        UiText {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "No lyrics for this track"
            color: Qt.rgba(1, 1, 1, 0.7)
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            topPadding: 8
            spacing: 8

            PillButton {
                text: "Load lyrics file"
                onClicked: view.loadRequested()
            }

            PillButton {
                text: "Write lyrics"
                onClicked: view.editRequested()
            }
        }
    }
}
