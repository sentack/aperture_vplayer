import QtQuick
import "Icons.js" as Icons

// Playback speed presets, subtitle choice and audio track choice.
GlassPopup {
    id: menu

    signal subtitleFileRequested()

    component OptionRow: Rectangle {
        id: row

        property string text
        property bool active: false

        signal picked()

        width: parent ? parent.width : 0
        height: 32
        radius: 10
        color: rowArea.containsMouse ? theme.chip_bg : "transparent"

        Accessible.role: Accessible.RadioButton
        Accessible.name: text
        Accessible.checked: active
        Accessible.onPressAction: picked()

        Icon {
            anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
            size: 16
            strokeWidth: 2
            glyph: Icons.check
            color: theme.text_primary
            visible: row.active
        }

        UiText {
            anchors { left: parent.left; leftMargin: 30; right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
            text: row.text
            font.weight: row.active ? Font.DemiBold : Font.Medium
            color: row.active ? theme.text_primary : theme.text_secondary
        }

        MouseArea {
            id: rowArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: row.picked()
        }
    }

    contentItem: Column {
        width: 206
        spacing: 12

        SectionLabel { text: "Playback speed" }

        Grid {
            columns: 4
            spacing: 8

            Repeater {
                model: player.rates

                Rectangle {
                    id: pill

                    required property real modelData
                    readonly property bool active: Math.abs(player.rate - modelData) < 0.001

                    width: 44
                    height: 30
                    radius: 15
                    color: active ? theme.accent : pillArea.containsMouse ? theme.track_bg : theme.chip_bg

                    Accessible.role: Accessible.RadioButton
                    Accessible.name: `${pill.modelData}×`
                    Accessible.checked: pill.active
                    Accessible.onPressAction: player.rate = pill.modelData

                    UiText {
                        anchors.centerIn: parent
                        text: `${pill.modelData}×`
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        color: pill.active ? "white" : theme.text_secondary
                        elide: Text.ElideNone
                    }

                    MouseArea {
                        id: pillArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: player.rate = pill.modelData
                    }
                }
            }
        }

        SectionLabel { text: "Subtitles" }

        Column {
            width: parent.width
            spacing: 2

            OptionRow {
                text: "Off"
                active: tracks.subtitleIndex === -1
                onPicked: tracks.selectSubtitle(-1)
            }

            Repeater {
                model: tracks.subtitleOptions

                OptionRow {
                    required property int index
                    required property string modelData
                    text: modelData
                    active: tracks.subtitleIndex === index
                    onPicked: tracks.selectSubtitle(index)
                }
            }

            OptionRow {
                text: "Load file…"
                enabled: player.hasMedia
                opacity: enabled ? 1 : 0.4
                onPicked: {
                    menu.close()
                    menu.subtitleFileRequested()
                }
            }
        }

        SectionLabel {
            text: "Audio"
            visible: audioList.visible
        }

        Column {
            id: audioList
            width: parent.width
            spacing: 2
            visible: tracks.audioOptions.length > 1

            Repeater {
                model: tracks.audioOptions

                OptionRow {
                    required property int index
                    required property string modelData
                    text: modelData
                    active: tracks.audioIndex === index
                    onPicked: tracks.selectAudio(index)
                }
            }
        }

        SectionLabel { text: "Subtitle timing" }

        // Fine-tune .srt/.vtt timing (also G / H).
        Item {
            width: parent.width
            height: 30

            UiText {
                anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                text: `Delay ${(tracks.subtitleDelay / 1000).toFixed(1)} s`
                font.features: ({ "tnum": 1 })
                color: theme.text_secondary
            }

            Row {
                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                spacing: 4

                PillButton {
                    implicitHeight: 28
                    text: "−"
                    onClicked: tracks.nudgeSubtitles(-100)
                }

                PillButton {
                    implicitHeight: 28
                    text: "+"
                    onClicked: tracks.nudgeSubtitles(100)
                }

                PillButton {
                    implicitHeight: 28
                    text: "0"
                    visible: tracks.subtitleDelay !== 0
                    onClicked: tracks.resetSubtitleDelay()
                }
            }
        }

        SectionLabel { text: "Audio boost" }

        Row {
            spacing: 6

            Repeater {
                model: player.boostLevels

                Rectangle {
                    id: boostPill

                    required property real modelData
                    readonly property bool active: Math.abs(player.audioBoost - modelData) < 0.001

                    width: 44
                    height: 30
                    radius: 15
                    color: active ? theme.accent : boostArea.containsMouse ? theme.track_bg : theme.chip_bg

                    Accessible.role: Accessible.RadioButton
                    Accessible.name: `Audio boost ${Math.round(modelData * 100)} percent`
                    Accessible.checked: active
                    Accessible.onPressAction: player.audioBoost = modelData

                    UiText {
                        anchors.centerIn: parent
                        text: `${Math.round(boostPill.modelData * 100)}%`
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        color: boostPill.active ? "white" : theme.text_secondary
                        elide: Text.ElideNone
                    }

                    MouseArea {
                        id: boostArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: player.audioBoost = boostPill.modelData
                    }
                }
            }
        }
    }
}
