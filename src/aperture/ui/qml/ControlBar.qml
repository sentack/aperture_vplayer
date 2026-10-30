import QtQuick
import QtQuick.Controls.Basic as T
import QtQuick.Effects
import QtQuick.Layouts
import "Icons.js" as Icons

// Floating glass bar: transport, seek, volume, view toggles.
Rectangle {
    id: bar

    property bool fullscreen: false
    property bool playlistOpen: false
    property bool settingsOpen: false

    signal fullscreenToggled()
    signal playlistToggled()
    signal subtitleFileRequested()
    signal miniToggled()
    signal settingsToggled()

    readonly property bool hovered: hover.hovered
    readonly property bool menuOpen: optionsMenu.visible
    readonly property color accent: theme.accent

    implicitHeight: 88
    radius: 26
    color: theme.bar_bg
    border.width: 1
    border.color: theme.bar_border

    component Divider: Rectangle {
        Layout.preferredWidth: 1
        Layout.preferredHeight: 26
        color: theme.divider
    }

    component ToggleButton: IconButton {
        Layout.preferredWidth: 40
        Layout.preferredHeight: 40
        radius: 12
    }

    component Clock: UiText {
        font.features: ({ "tnum": 1 })
        elide: Text.ElideNone
    }

    HoverHandler { id: hover }

    // Swallow presses on the glass so they never reach the video's tap handler.
    MouseArea { anchors.fill: parent }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 26
        anchors.rightMargin: 26
        spacing: 20

        RowLayout {
            spacing: 8

            IconButton {
                glyph: Icons.previous
                label: "Previous"
                enabled: player.hasMedia
                onClicked: player.playPrevious()
            }

            Rectangle {
                id: playButton
                Layout.preferredWidth: 52
                Layout.preferredHeight: 52
                radius: 26
                color: bar.accent
                opacity: player.hasMedia ? 1 : 0.5
                layer.enabled: true
                layer.effect: MultiEffect {
                    shadowEnabled: true
                    shadowColor: Qt.rgba(bar.accent.r, bar.accent.g, bar.accent.b, 0.4)
                    shadowBlur: 0.8
                    shadowVerticalOffset: 6
                }

                Accessible.role: Accessible.Button
                Accessible.name: player.playing ? "Pause" : "Play"
                Accessible.onPressAction: player.togglePlay()

                Icon {
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: player.playing ? 0 : 1
                    size: 18
                    glyph: player.playing ? Icons.pause : Icons.play
                    color: "white"
                }

                MouseArea {
                    anchors.fill: parent
                    enabled: player.hasMedia
                    cursorShape: Qt.PointingHandCursor
                    onClicked: player.togglePlay()
                }
            }

            IconButton {
                glyph: Icons.next
                label: "Next"
                enabled: player.hasNext
                onClicked: player.playNext()
            }

            IconButton {
                glyph: Icons.stop
                label: "Stop"
                enabled: player.hasMedia
                onClicked: player.stop()
            }
        }

        Clock {
            Layout.minimumWidth: 40
            text: player.formatTime(player.position)
        }

        TrackSlider {
            id: seekSlider
            Layout.fillWidth: true
            label: "Seek"
            knobSize: 14
            enabled: player.seekable
            value: player.duration > 0 ? player.position / player.duration : 0
            onMoved: value => player.seek(Math.round(value * player.duration))

            // A–B loop: a tinted span between the two points, or a tick while only A is set.
            Rectangle {
                readonly property real scale_: player.duration > 0 ? seekSlider.width / player.duration : 0
                visible: player.loopA >= 0 && scale_ > 0
                x: player.loopA * scale_
                width: player.loopB >= 0 ? Math.max(2, (player.loopB - player.loopA) * scale_) : 2
                height: 14
                anchors.verticalCenter: parent.verticalCenter
                radius: 3
                color: Qt.rgba(bar.accent.r, bar.accent.g, bar.accent.b, player.loopB >= 0 ? 0.28 : 1)
                border.width: player.loopB >= 0 ? 1 : 0
                border.color: bar.accent
            }

            SeekPreview {
                readonly property real pointerX: seekSlider.hoverValue * seekSlider.width
                x: Math.max(-40, Math.min(seekSlider.width - width + 40, pointerX - width / 2))
                y: -height - 26
                visible: seekSlider.hovering || seekSlider.pressed
                position: Math.round(seekSlider.hoverValue * player.duration)
            }
        }

        Clock {
            Layout.minimumWidth: 48
            horizontalAlignment: Text.AlignRight
            text: "-" + player.formatTime(player.duration - player.position)
        }

        Divider {}

        RowLayout {
            spacing: 10

            IconButton {
                glyph: player.muted || player.volume === 0 ? Icons.muted : Icons.volume
                label: player.muted ? "Unmute" : "Mute"
                onClicked: player.toggleMute()
            }

            TrackSlider {
                Layout.preferredWidth: 76
                label: "Volume"
                trackHeight: 4
                value: player.muted ? 0 : player.volume
                onMoved: value => player.volume = value
            }
        }

        Divider {}

        ToggleButton {
            glyph: Icons.playlist
            label: bar.playlistOpen ? "Hide playlist" : "Show playlist"
            color: bar.playlistOpen || hovered ? theme.chip_bg : "transparent"
            onClicked: bar.playlistToggled()
        }

        ToggleButton {
            glyph: Icons.mini
            label: "Picture-in-picture"
            enabled: player.hasMedia
            onClicked: bar.miniToggled()
        }

        ToggleButton {
            glyph: bar.fullscreen ? Icons.exitFullscreen : Icons.fullscreen
            label: bar.fullscreen ? "Exit fullscreen" : "Enter fullscreen"
            onClicked: bar.fullscreenToggled()
        }

        // Options chip: playback options (speed, subtitles, audio).
        Rectangle {
            id: optionsChip
            Layout.preferredWidth: chipContent.implicitWidth + 8
            Layout.preferredHeight: 40
            radius: 16
            color: theme.chip_bg

            function toggle() {
                if (optionsMenu.visible)
                    optionsMenu.close()
                else
                    optionsMenu.open()
            }

            Row {
                id: chipContent
                anchors.centerIn: parent
                spacing: 4

                Rectangle {
                    width: optionsContent.implicitWidth + 12
                    height: 30
                    radius: 15
                    color: optionsArea.containsMouse || optionsMenu.visible ? theme.chip_bg : "transparent"

                    Accessible.role: Accessible.ButtonMenu
                    Accessible.name: `Playback options, speed ${player.rateLabel}`
                    Accessible.onPressAction: optionsChip.toggle()

                    Row {
                        id: optionsContent
                        anchors.centerIn: parent
                        spacing: 4

                        Icon {
                            anchors.verticalCenter: parent.verticalCenter
                            size: 18
                            glyph: Icons.settings
                            color: optionsArea.containsMouse ? theme.text_primary : theme.text_secondary
                        }

                        Clock {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: player.rate !== 1
                            text: player.rateLabel
                            font.weight: Font.DemiBold
                            color: theme.text_primary
                        }
                    }

                    MouseArea {
                        id: optionsArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: optionsChip.toggle()
                    }
                }
            }

            OptionsMenu {
                id: optionsMenu
                onSubtitleFileRequested: bar.subtitleFileRequested()
            }
        }

        // Settings sheet toggle: always the rightmost control.
        ToggleButton {
            glyph: Icons.gear
            label: bar.settingsOpen ? "Close settings" : "Settings"
            color: bar.settingsOpen || hovered ? theme.chip_bg : "transparent"
            onClicked: bar.settingsToggled()
        }
    }
}
