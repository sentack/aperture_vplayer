import QtQuick
import QtQuick.Controls.Basic as T

// Glass popover above the options chip: one pill per speed preset.
T.Popup {
    id: menu

    padding: 16

    background: Rectangle {
        radius: 18
        color: theme.popover_bg
        border.width: 1
        border.color: theme.bar_border
    }

    contentItem: Column {
        spacing: 12

        UiText {
            text: "PLAYBACK SPEED"
            font.pixelSize: 11
            font.weight: Font.DemiBold
            font.letterSpacing: 11 * 0.06
            color: theme.text_tertiary
        }

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
    }
}
