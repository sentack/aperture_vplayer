import QtQuick
import "Icons.js" as Icons
import "Shortcuts.js" as Shortcuts

// Settings sheet, opened from the gear at the right edge of the control bar.
// Every row changes something you can see or hear; nothing else belongs here.
Rectangle {
    id: panel

    signal closeRequested()

    readonly property bool mac: Qt.platform.os === "osx"

    implicitWidth: 360
    radius: 22
    color: theme.popover_bg
    border.width: 1
    border.color: theme.bar_border

    // One choice out of a few, as pills. A value shows as `labels[value]`, else value + suffix.
    component Segmented: Flow {
        id: segmented

        property var options: []
        property var current
        property var labels: ({})
        property string suffix: ""

        signal picked(var value)

        width: parent ? parent.width : 0
        spacing: 6

        Repeater {
            model: segmented.options

            Rectangle {
                id: pill

                required property var modelData
                readonly property bool active: segmented.current === modelData

                width: Math.max(44, pillText.implicitWidth + 24)
                height: 30
                radius: 15
                color: active ? theme.accent : pillArea.containsMouse ? theme.track_bg : theme.chip_bg

                Accessible.role: Accessible.RadioButton
                Accessible.name: pillText.text
                Accessible.checked: active
                Accessible.onPressAction: segmented.picked(modelData)

                UiText {
                    id: pillText
                    anchors.centerIn: parent
                    text: segmented.labels[pill.modelData] ?? `${pill.modelData}${segmented.suffix}`
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
                    onClicked: segmented.picked(pill.modelData)
                }
            }
        }
    }

    component Section: Column {
        property alias title: heading.text
        default property alias content: body.data

        width: parent ? parent.width : 0
        spacing: 12

        SectionLabel { id: heading }

        Column {
            id: body
            width: parent.width
            spacing: 14
        }
    }

    component Row2: Item {
        property alias text: rowLabel.text
        default property alias control: slot.data

        width: parent ? parent.width : 0
        height: Math.max(rowLabel.implicitHeight, slot.childrenRect.height)

        UiText {
            id: rowLabel
            anchors { left: parent.left; right: slot.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
            color: theme.text_primary
        }

        Item {
            id: slot
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            width: childrenRect.width
            height: childrenRect.height
        }
    }

    // Keep clicks on the sheet from reaching the video underneath.
    MouseArea { anchors.fill: parent }

    Item {
        id: header
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 60

        UiText {
            anchors { left: parent.left; leftMargin: 24; verticalCenter: parent.verticalCenter }
            text: "Settings"
            font.pixelSize: 18
            font.weight: Font.Bold
            color: theme.text_primary
        }

        IconButton {
            anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
            glyph: Icons.close
            iconSize: 16
            label: "Close settings"
            onClicked: panel.closeRequested()
        }
    }

    Flickable {
        id: scroller
        anchors { left: parent.left; right: parent.right; top: header.bottom; bottom: parent.bottom }
        clip: true
        contentHeight: content.implicitHeight + 24
        boundsBehavior: Flickable.StopAtBounds

        Column {
            id: content
            x: 24
            width: scroller.width - 48
            spacing: 28

            Section {
                title: "Appearance"

                Segmented {
                    options: appearance.modes
                    current: appearance.mode
                    labels: ({ system: "System", dark: "Dark", light: "Light" })
                    onPicked: mode => appearance.mode = mode
                }

                // 30px swatches; the active one gets a 2px gap then a 2px ring in its own color.
                Flow {
                    width: parent.width
                    spacing: 4

                    Repeater {
                        model: appearance.accents

                        Item {
                            id: swatch

                            required property var modelData
                            readonly property bool active: appearance.accent === modelData.name

                            width: 38
                            height: 38

                            Accessible.role: Accessible.RadioButton
                            Accessible.name: `${modelData.name} accent`
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
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: appearance.accent = swatch.modelData.name
                            }
                        }
                    }
                }
            }

            Section {
                title: "Playback"

                Row2 {
                    text: "Starting volume"

                    Row {
                        spacing: 10

                        TrackSlider {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 120
                            label: "Starting volume"
                            trackHeight: 4
                            knobSize: 12
                            value: prefs.defaultVolume
                            onMoved: value => prefs.defaultVolume = value
                        }

                        UiText {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 36
                            horizontalAlignment: Text.AlignRight
                            text: `${Math.round(prefs.defaultVolume * 100)}%`
                            font.features: ({ "tnum": 1 })
                            elide: Text.ElideNone
                        }
                    }
                }

                UiText {
                    text: "Starting speed"
                    color: theme.text_primary
                }

                Segmented {
                    options: prefs.rateOptions
                    current: prefs.defaultRate
                    labels: ({ last: "Last used" })
                    suffix: "×"
                    onPicked: key => prefs.defaultRate = key
                }
            }

            Section {
                title: "Subtitles"

                Row2 {
                    text: "Show subtitles automatically"

                    ToggleSwitch {
                        label: "Show subtitles automatically"
                        checked: prefs.subtitlesAuto
                        onToggled: checked => prefs.subtitlesAuto = checked
                    }
                }

                UiText {
                    text: "Text size"
                    color: theme.text_primary
                }

                Segmented {
                    options: prefs.subtitleSizes
                    current: prefs.subtitleSize
                    labels: ({ small: "S", medium: "M", large: "L", xlarge: "XL" })
                    onPicked: size => prefs.subtitleSize = size
                }

                UiText {
                    width: parent.width
                    text: "Applies to .srt and .vtt files. Embedded tracks use the video's own styling."
                    wrapMode: Text.WordWrap
                    elide: Text.ElideNone
                    font.pixelSize: 12
                    color: theme.text_tertiary
                }
            }

            Section {
                title: "Keyboard shortcuts"

                Repeater {
                    model: Shortcuts.groups

                    Column {
                        id: group

                        required property var modelData

                        width: parent.width
                        spacing: 8

                        UiText {
                            text: group.modelData.title
                            font.weight: Font.DemiBold
                            color: theme.text_secondary
                        }

                        Repeater {
                            model: group.modelData.items

                            Item {
                                id: shortcut

                                required property var modelData

                                width: group.width
                                height: 26

                                UiText {
                                    anchors { left: parent.left; right: keyRow.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
                                    text: shortcut.modelData.action
                                    color: theme.text_primary
                                }

                                Row {
                                    id: keyRow
                                    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                                    spacing: 4

                                    Repeater {
                                        model: shortcut.modelData.keys

                                        Rectangle {
                                            required property string modelData

                                            width: keyText.implicitWidth + 14
                                            height: 22
                                            radius: 6
                                            color: theme.chip_bg
                                            border.width: 1
                                            border.color: theme.divider

                                            UiText {
                                                id: keyText
                                                anchors.centerIn: parent
                                                text: Shortcuts.label(parent.modelData, panel.mac)
                                                font.pixelSize: 11
                                                font.weight: Font.DemiBold
                                                color: theme.text_secondary
                                                elide: Text.ElideNone
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            PillButton {
                text: "Reset to defaults"
                onClicked: {
                    prefs.reset()
                    player.noticed("Settings reset to defaults")
                }
            }
        }
    }
}
