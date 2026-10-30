import QtQuick
import "Icons.js" as Icons

// Settings, as a modal opened from the gear at the right edge of the control bar.
// Categories on the left, one page on the right. Every control changes something you can
// see or hear; nothing else belongs here.
Modal {
    id: dialog

    readonly property bool mac: Qt.platform.os === "osx"
    readonly property var categories: ["General", "Playback", "Appearance", "Subtitles", "Keyboard shortcuts"]
    property int page: 0

    cardWidth: 760
    cardHeight: 560

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

    // A titled group of controls on a page.
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

    // Label on the left, control on the right.
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

    component Note: UiText {
        width: parent ? parent.width : 0
        wrapMode: Text.WordWrap
        elide: Text.ElideNone
        font.pixelSize: 12
        color: theme.text_tertiary
    }

    component Page: Column {
        required property int index

        width: parent ? parent.width : 0
        spacing: 28
        visible: dialog.page === index
    }

    // --- navigation ----------------------------------------------------------------------

    Rectangle {
        id: nav
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
        width: 200
        radius: 22
        color: theme.chip_bg

        UiText {
            id: navTitle
            anchors { left: parent.left; top: parent.top; leftMargin: 22; topMargin: 22 }
            text: "Settings"
            font.pixelSize: 18
            font.weight: Font.Bold
            color: theme.text_primary
        }

        Column {
            anchors { left: parent.left; right: parent.right; top: navTitle.bottom; margins: 10; topMargin: 18 }
            spacing: 2

            Repeater {
                model: dialog.categories

                Rectangle {
                    id: navItem

                    required property int index
                    required property string modelData
                    readonly property bool active: dialog.page === index

                    width: parent.width
                    height: 36
                    radius: 10
                    color: active ? theme.track_bg : navArea.containsMouse ? theme.chip_bg : "transparent"

                    Accessible.role: Accessible.PageTab
                    Accessible.name: modelData
                    Accessible.selected: active
                    Accessible.onPressAction: dialog.page = index

                    UiText {
                        anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                        text: navItem.modelData
                        font.weight: navItem.active ? Font.DemiBold : Font.Medium
                        color: navItem.active ? theme.text_primary : theme.text_secondary
                    }

                    MouseArea {
                        id: navArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: dialog.page = navItem.index
                    }
                }
            }
        }
    }

    IconButton {
        anchors { right: parent.right; top: parent.top; margins: 14 }
        glyph: Icons.close
        iconSize: 16
        label: "Close settings"
        onClicked: dialog.closeRequested()
    }

    // --- pages ---------------------------------------------------------------------------

    Flickable {
        id: scroller
        anchors { left: nav.right; right: parent.right; top: parent.top; bottom: parent.bottom; topMargin: 56 }
        clip: true
        contentHeight: pages.implicitHeight + 28
        boundsBehavior: Flickable.StopAtBounds

        Column {
            id: pages
            x: 28
            width: scroller.width - 56

            Page {
                index: 0

                Section {
                    title: "Default player"

                    UiText {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        elide: Text.ElideNone
                        color: theme.text_primary
                        text: defaults.status === "default" ? "Aperture is your default video player."
                            : defaults.status === "other" ? "Another app opens your videos."
                            : "This system doesn't report its default player."
                    }

                    PillButton {
                        text: "Make Aperture the default"
                        primary: true
                        visible: defaults.canClaim && defaults.status !== "default"
                        onClicked: defaults.claim()
                    }

                    Row2 {
                        text: "Ask from time to time"

                        ToggleSwitch {
                            label: "Ask to make Aperture the default player"
                            checked: defaults.askEnabled
                            onToggled: checked => defaults.askEnabled = checked
                        }
                    }

                    Note { text: "At most once every 6 hours, and only while another app is the default." }
                }

                Section {
                    title: "Reset"

                    Note { text: "Put every setting back the way Aperture shipped. Your history and playlist stay." }

                    PillButton {
                        text: "Reset to defaults"
                        onClicked: {
                            prefs.reset()
                            player.noticed("Settings reset to defaults")
                        }
                    }
                }
            }

            Page {
                index: 1

                Section {
                    title: "New sessions"

                    Row2 {
                        text: "Starting volume"

                        Row {
                            spacing: 10

                            TrackSlider {
                                anchors.verticalCenter: parent.verticalCenter
                                width: 140
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
                        text: "Playback speed"
                        color: theme.text_primary
                    }

                    Segmented {
                        options: prefs.rateOptions
                        current: prefs.defaultRate
                        labels: ({ last: "Last used" })
                        suffix: "×"
                        onPicked: key => prefs.defaultRate = key
                    }

                    Note { text: "Picking a speed also applies it to what's playing now." }
                }

                Section {
                    title: "Saved positions"

                    UiText {
                        text: "When a file was left partway through"
                        color: theme.text_primary
                    }

                    Segmented {
                        options: prefs.resumeModes
                        current: prefs.resumeMode
                        labels: ({ ask: "Ask", always: "Resume", never: "Start over" })
                        onPicked: mode => prefs.resumeMode = mode
                    }
                }
            }

            Page {
                index: 2

                Section {
                    title: "Theme"

                    Segmented {
                        options: appearance.modes
                        current: appearance.mode
                        labels: ({ system: "System", dark: "Dark", light: "Light" })
                        onPicked: mode => appearance.mode = mode
                    }
                }

                Section {
                    title: "Accent color"

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

                    Note { text: "Used by the seek bar, play button, switches and selected items." }
                }
            }

            Page {
                index: 3

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

                    Note { text: "Size applies to .srt and .vtt files. Embedded tracks use the video's own styling." }
                }
            }

            Page {
                index: 4

                Section {
                    title: "Keyboard shortcuts"

                    Note { text: "Click a key, then press the new combination. Each key can do one thing; free a key with × before reusing it." }

                    PillButton {
                        text: "Reset shortcuts"
                        onClicked: keymap.resetShortcuts()
                    }
                }

                Repeater {
                    model: keymap.groups

                    Section {
                        id: group

                        required property string modelData

                        title: modelData

                        Repeater {
                            model: keymap.actions.filter(action => action.group === group.modelData)

                            ShortcutRow {}
                        }
                    }
                }

                Section {
                    title: "Built in"

                    Repeater {
                        model: keymap.fixed

                        Item {
                            id: fixedRow

                            required property var modelData

                            width: parent.width
                            height: 26

                            UiText {
                                anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                                text: fixedRow.modelData.label
                                color: theme.text_secondary
                            }

                            UiText {
                                anchors { right: parent.right; rightMargin: 34; verticalCenter: parent.verticalCenter }
                                text: fixedRow.modelData.key
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                                color: theme.text_tertiary
                            }
                        }
                    }
                }
            }
        }
    }
}
