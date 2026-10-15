import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import "Icons.js" as Icons

// Floating glass bar: transport, seek, volume, view toggles.
Rectangle {
    id: bar

    property bool fullscreen: false

    signal fullscreenToggled()

    readonly property bool hovered: hover.hovered
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
            Layout.fillWidth: true
            label: "Seek"
            knobSize: 14
            enabled: player.seekable
            value: player.duration > 0 ? player.position / player.duration : 0
            onMoved: value => player.seek(Math.round(value * player.duration))
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
            glyph: bar.fullscreen ? Icons.exitFullscreen : Icons.fullscreen
            label: bar.fullscreen ? "Exit fullscreen" : "Enter fullscreen"
            onClicked: bar.fullscreenToggled()
        }
    }
}
