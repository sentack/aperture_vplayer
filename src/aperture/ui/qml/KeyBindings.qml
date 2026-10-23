import QtQuick

// Window-wide key bindings. Shortcut context is the window, so placement does not matter.
Item {
    id: keys

    property bool fullscreen: false

    signal fullscreenToggled()
    signal openRequested()
    signal miniToggled()

    Shortcut { sequences: ["Space", "K"]; onActivated: player.togglePlay() }
    Shortcut { sequence: "Left"; onActivated: player.seekBy(-5000) }
    Shortcut { sequence: "Right"; onActivated: player.seekBy(5000) }
    Shortcut { sequence: "J"; onActivated: player.seekBy(-10000) }
    Shortcut { sequence: "L"; onActivated: player.seekBy(10000) }
    Shortcut { sequence: "Shift+Left"; onActivated: player.seekBy(-30000) }
    Shortcut { sequence: "Shift+Right"; onActivated: player.seekBy(30000) }
    Shortcut { sequence: "Home"; onActivated: player.seek(0) }
    Shortcut { sequence: "Up"; onActivated: player.adjustVolume(0.05) }
    Shortcut { sequence: "Down"; onActivated: player.adjustVolume(-0.05) }
    Shortcut { sequence: "M"; onActivated: player.toggleMute() }
    Shortcut { sequence: "N"; onActivated: player.playNext() }
    Shortcut { sequence: "P"; onActivated: player.playPrevious() }
    Shortcut { sequence: "]"; onActivated: player.stepRate(1) }
    Shortcut { sequence: "["; onActivated: player.stepRate(-1) }
    Shortcut { sequence: "="; onActivated: player.resetRate() }
    Shortcut { sequence: "C"; onActivated: tracks.toggleSubtitles() }
    Shortcut { sequence: "A"; onActivated: tracks.cycleAudio() }
    Shortcut { sequences: ["F", "F11"]; onActivated: keys.fullscreenToggled() }
    Shortcut { sequence: "I"; onActivated: keys.miniToggled() }
    Shortcut { sequence: "Escape"; enabled: keys.fullscreen; onActivated: keys.fullscreenToggled() }
    Shortcut { sequences: [StandardKey.Open]; onActivated: keys.openRequested() }
}
