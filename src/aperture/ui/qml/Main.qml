import QtQuick
import QtQuick.Window
import QtMultimedia

Window {
    id: root

    readonly property bool fullscreen: visibility === Window.FullScreen
    readonly property color scrimTop: theme.scrim_top
    readonly property color scrimBottom: theme.scrim_bottom

    // Chrome fades out after a still pointer during playback; any movement brings it back.
    property bool idle: false
    readonly property bool chromeVisible: !idle || !player.playing || controlBar.hovered
    property real chromeOpacity: chromeVisible ? 1 : 0
    Behavior on chromeOpacity { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }

    property int restoreVisibility: Window.Windowed

    function wake() {
        idle = false
        if (player.playing)
            idleTimer.restart()
        else
            idleTimer.stop()
    }

    function toggleFullscreen() {
        if (fullscreen) {
            visibility = restoreVisibility
        } else {
            restoreVisibility = visibility
            showFullScreen()
        }
    }

    width: 1440
    height: 900
    minimumWidth: 720
    minimumHeight: 450
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    title: player.title ? `${player.title} — Aperture` : "Aperture"
    color: theme.bg_0

    Timer {
        id: idleTimer
        interval: 2500
        onTriggered: root.idle = true
    }

    Connections {
        target: player
        function onPlayingChanged() { root.wake() }
    }

    Shortcut {
        sequence: "Escape"
        enabled: root.fullscreen
        onActivated: root.toggleFullscreen()
    }

    Item {
        id: stage
        anchors.fill: parent

        HoverHandler {
            cursorShape: root.chromeVisible ? Qt.ArrowCursor : Qt.BlankCursor
            onPointChanged: root.wake()
        }

        BackgroundArt {
            anchors.fill: parent
            visible: !player.hasMedia
        }

        VideoOutput {
            id: video
            anchors.fill: parent
            fillMode: VideoOutput.PreserveAspectFit
            Component.onCompleted: player.attachVideoOutput(video)

            TapHandler {
                onTapped: root.wake()
                onSingleTapped: player.togglePlay()
                onDoubleTapped: root.toggleFullscreen()
            }
        }

        IdleProgress {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 32; rightMargin: 32; bottomMargin: 52 }
            value: player.duration > 0 ? player.position / player.duration : 0
            opacity: player.hasMedia ? 1 - root.chromeOpacity : 0
        }

        Rectangle {
            id: chromeScrimTop
            opacity: root.chromeOpacity
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: parent.height * 0.19
            gradient: Gradient {
                GradientStop { position: 0; color: root.scrimTop }
                GradientStop { position: 1; color: Qt.rgba(root.scrimTop.r, root.scrimTop.g, root.scrimTop.b, 0) }
            }
        }

        Rectangle {
            id: chromeScrimBottom
            opacity: root.chromeOpacity
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: parent.height * 0.33
            gradient: Gradient {
                GradientStop { position: 0; color: Qt.rgba(root.scrimBottom.r, root.scrimBottom.g, root.scrimBottom.b, 0) }
                GradientStop { position: 1; color: root.scrimBottom }
            }
        }

        TopBar {
            id: topBar
            anchors { left: parent.left; right: parent.right; top: parent.top }
            fullscreen: root.fullscreen
            opacity: root.chromeOpacity
            enabled: root.chromeVisible
        }

        Column {
            id: nowPlaying
            anchors { left: parent.left; leftMargin: 48; bottom: parent.bottom; bottomMargin: 150 }
            width: parent.width * 0.44
            spacing: 8
            visible: player.hasMedia
            opacity: root.chromeOpacity

            UiText {
                width: parent.width
                text: player.title
                font.pixelSize: 34
                font.weight: Font.Bold
                font.letterSpacing: -34 * 0.02
                color: theme.text_primary
            }

            UiText {
                width: parent.width
                text: player.error || player.subtitle
                font.pixelSize: 14
            }
        }

        ControlBar {
            id: controlBar
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 32 }
            fullscreen: root.fullscreen
            opacity: root.chromeOpacity
            enabled: root.chromeVisible
            onFullscreenToggled: root.toggleFullscreen()
        }
    }

    ResizeGrips {}
}
