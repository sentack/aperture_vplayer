import QtCore
import QtQuick
import QtQuick.Dialogs
import QtQuick.Window
import QtMultimedia
import "Icons.js" as Icons

Window {
    id: root

    readonly property bool fullscreen: visibility === Window.FullScreen
    readonly property color scrimTop: theme.scrim_top
    readonly property color scrimBottom: theme.scrim_bottom

    // Chrome fades out after a still pointer during playback; any movement brings it back.
    property bool idle: false
    readonly property bool chromeVisible: !idle || !player.playing || controlBar.hovered || playlistOpen
    property real chromeOpacity: chromeVisible ? 1 : 0
    Behavior on chromeOpacity { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }

    property int restoreVisibility: Window.Windowed
    property bool playlistOpen: false

    // append=false replaces the queue and plays; append=true adds to the end.
    function chooseFiles(append) {
        fileDialog.append = append
        fileDialog.open()
    }

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

    FileDialog {
        id: fileDialog

        property bool append: false

        title: append ? "Add to playlist" : "Open video"
        fileMode: FileDialog.OpenFiles
        nameFilters: player.nameFilters
        currentFolder: StandardPaths.writableLocation(StandardPaths.MoviesLocation)
        onAccepted: append ? player.addUrls(selectedFiles) : player.openUrls(selectedFiles)
    }

    KeyBindings {
        fullscreen: root.fullscreen
        onFullscreenToggled: root.toggleFullscreen()
        onOpenRequested: root.chooseFiles(false)
    }

    Connections {
        target: player
        function onNoticed(text) { toast.show(text) }
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

        Column {
            id: emptyState
            anchors.centerIn: parent
            spacing: 14
            visible: !player.hasMedia

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: openContent.implicitWidth + 44
                height: 44
                radius: 22
                color: theme.accent

                Accessible.role: Accessible.Button
                Accessible.name: "Open video"
                Accessible.onPressAction: root.chooseFiles(false)

                Row {
                    id: openContent
                    anchors.centerIn: parent
                    spacing: 8

                    Icon {
                        anchors.verticalCenter: parent.verticalCenter
                        size: 16
                        glyph: Icons.add
                        color: "white"
                    }

                    UiText {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Open video"
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        color: "white"
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.chooseFiles(false)
                }
            }

            UiText {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "MP4, MKV, AVI, MOV, WebM and more · Ctrl+O"
                font.pixelSize: 12
                color: theme.text_tertiary
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
            playlistOpen: root.playlistOpen
            opacity: root.chromeOpacity
            enabled: root.chromeVisible
            onFullscreenToggled: root.toggleFullscreen()
            onPlaylistToggled: root.playlistOpen = !root.playlistOpen
        }

        PlaylistPanel {
            anchors { right: parent.right; top: topBar.bottom; bottom: controlBar.top; rightMargin: 32; topMargin: 8; bottomMargin: 16 }
            visible: root.playlistOpen
            onAddRequested: root.chooseFiles(true)
        }
    }

    Toast {
        id: toast
        anchors.horizontalCenter: parent.horizontalCenter
        y: 84
    }

    ResizeGrips {}
}
