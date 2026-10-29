.pragma library

// Read-only reference shown in Settings. Mirrors KeyBindings.qml; tests keep the two in sync.
// "Ctrl" is shown as ⌘ on macOS, where Qt maps it to the Command key.

var groups = [
    { title: "Playback", items: [
        { keys: ["Space", "K"], action: "Play / pause" },
        { keys: ["←", "→"], action: "Seek 5 s" },
        { keys: ["J", "L"], action: "Seek 10 s" },
        { keys: ["Shift+←", "Shift+→"], action: "Seek 30 s" },
        { keys: ["Home"], action: "Back to start" },
        { keys: ["[", "]"], action: "Slower / faster" },
        { keys: ["="], action: "Normal speed" },
    ] },
    { title: "Sound and tracks", items: [
        { keys: ["↑", "↓"], action: "Volume ±5%" },
        { keys: ["M"], action: "Mute" },
        { keys: ["C"], action: "Subtitles on / off" },
        { keys: ["A"], action: "Next audio track" },
    ] },
    { title: "Playlist and window", items: [
        { keys: ["N", "P"], action: "Next / previous" },
        { keys: ["F", "F11"], action: "Fullscreen" },
        { keys: ["Esc"], action: "Close settings or dialog / leave fullscreen" },
        { keys: ["I"], action: "Mini player" },
        { keys: ["Ctrl+O"], action: "Open files" },
        { keys: ["Ctrl+,"], action: "Settings" },
    ] },
]

function label(key, mac) {
    return mac ? key.replace("Ctrl+", "⌘") : key
}
