import QtQuick

// Window-wide key bindings. Keys come from `keymap.keys`, so a rebind in Settings applies at
// once; while Settings is listening for a new key, every shortcut stands down.
Item {
    id: keys

    property bool fullscreen: false
    // Settings or another modal is up: Esc closes it before it leaves fullscreen.
    property bool modalOpen: false

    signal fullscreenToggled()
    signal openRequested()
    signal openUrlRequested()
    signal miniToggled()
    signal settingsToggled()
    signal modalClosed()
    signal contextMenuRequested()

    readonly property bool live: !keymap.capturing

    component Bound: Shortcut {
        required property string action
        sequence: keymap.keys[action] || ""
        enabled: keys.live && sequence !== ""
    }

    Bound { action: "play_pause"; onActivated: player.togglePlay() }
    Bound { action: "seek_back_5"; onActivated: player.seekBy(-5000) }
    Bound { action: "seek_forward_5"; onActivated: player.seekBy(5000) }
    Bound { action: "seek_back_10"; onActivated: player.seekBy(-10000) }
    Bound { action: "seek_forward_10"; onActivated: player.seekBy(10000) }
    Bound { action: "seek_back_30"; onActivated: player.seekBy(-30000) }
    Bound { action: "seek_forward_30"; onActivated: player.seekBy(30000) }
    Bound { action: "seek_start"; onActivated: player.seek(0) }
    Bound { action: "frame_previous"; onActivated: player.stepFrame(-1) }
    Bound { action: "frame_next"; onActivated: player.stepFrame(1) }
    Bound { action: "ab_loop"; onActivated: player.cycleLoop() }
    Bound { action: "slower"; onActivated: player.stepRate(-1) }
    Bound { action: "faster"; onActivated: player.stepRate(1) }
    Bound { action: "normal_speed"; onActivated: player.resetRate() }
    Bound { action: "volume_up"; onActivated: player.adjustVolume(0.05) }
    Bound { action: "volume_down"; onActivated: player.adjustVolume(-0.05) }
    Bound { action: "mute"; onActivated: player.toggleMute() }
    Bound { action: "subtitles"; onActivated: tracks.toggleSubtitles() }
    Bound { action: "audio_track"; onActivated: tracks.cycleAudio() }
    Bound { action: "next"; onActivated: player.playNext() }
    Bound { action: "previous"; onActivated: player.playPrevious() }
    Bound { action: "fullscreen"; onActivated: keys.fullscreenToggled() }
    Bound { action: "mini_player"; onActivated: keys.miniToggled() }
    Bound { action: "screenshot"; onActivated: player.screenshot() }
    Bound { action: "open_files"; onActivated: keys.openRequested() }
    Bound { action: "open_url"; onActivated: keys.openUrlRequested() }
    Bound { action: "settings"; onActivated: keys.settingsToggled() }
    Bound { action: "context_menu"; onActivated: keys.contextMenuRequested() }

    // Fixed keys, not rebindable (the keymap reserves them).
    Shortcut {
        sequence: "Escape"
        enabled: keys.live && (keys.modalOpen || keys.fullscreen)
        onActivated: keys.modalOpen ? keys.modalClosed() : keys.fullscreenToggled()
    }
    Shortcut {
        sequence: "Menu"
        enabled: keys.live
        onActivated: keys.contextMenuRequested()
    }
}
