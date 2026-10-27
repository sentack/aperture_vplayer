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
    }
}
