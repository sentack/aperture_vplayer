import QtQuick

// One pill per speed preset.
GlassPopup {
    id: menu

    contentItem: Column {
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
    }
}
