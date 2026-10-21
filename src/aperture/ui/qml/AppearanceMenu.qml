import QtQuick
import "Icons.js" as Icons

// Theme mode pills and the five accent swatches.
GlassPopup {
    id: menu

    contentItem: Column {
        spacing: 12

        SectionLabel { text: "Theme" }

        Row {
            spacing: 6

            Repeater {
                model: appearance.modes

                Rectangle {
                    id: modePill

                    required property string modelData
                    readonly property bool active: appearance.mode === modelData
                    readonly property string title: modelData.charAt(0).toUpperCase() + modelData.slice(1)

                    width: 64
                    height: 30
                    radius: 15
                    color: active ? theme.accent : modeArea.containsMouse ? theme.track_bg : theme.chip_bg

                    Accessible.role: Accessible.RadioButton
                    Accessible.name: `${title} theme`
                    Accessible.checked: active
                    Accessible.onPressAction: appearance.mode = modelData

                    UiText {
                        anchors.centerIn: parent
                        text: modePill.title
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        color: modePill.active ? "white" : theme.text_secondary
                        elide: Text.ElideNone
                    }

                    MouseArea {
                        id: modeArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: appearance.mode = modePill.modelData
                    }
                }
            }
        }

        SectionLabel { text: "Accent color" }

        Row {
            spacing: 4

            Repeater {
                model: appearance.accents

                // 30px swatch; the active one gets a 2px gap then a 2px ring in its own color.
                Item {
                    id: swatch

                    required property var modelData
                    readonly property bool active: appearance.accent === modelData.name

                    width: 38
                    height: 38

                    Accessible.role: Accessible.RadioButton
                    Accessible.name: modelData.name
                    Accessible.checked: active
                    Accessible.onPressAction: appearance.accent = modelData.name

                    Rectangle {
                        anchors.fill: parent
                        radius: width / 2
                        color: "transparent"
                        border.width: 2
                        border.color: swatch.modelData.color
                        visible: swatch.active
                    }

                    Rectangle {
                        anchors.centerIn: parent
                        width: 30
                        height: 30
                        radius: 15
                        color: swatch.modelData.color
                        scale: swatchArea.containsMouse && !swatch.active ? 1.08 : 1

                        Behavior on scale { NumberAnimation { duration: 120 } }
                    }

                    Icon {
                        anchors.centerIn: parent
                        size: 16
                        strokeWidth: 2
                        glyph: Icons.check
                        color: "white"
                        visible: swatch.active
                    }

                    MouseArea {
                        id: swatchArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: appearance.accent = swatch.modelData.name
                    }
                }
            }
        }
    }
}
