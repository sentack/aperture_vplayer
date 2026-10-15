import QtQuick
import QtQuick.Window
import QtMultimedia

Window {
    id: root

    readonly property bool fullscreen: visibility === Window.FullScreen
    readonly property color scrimTop: theme.scrim_top
    readonly property color scrimBottom: theme.scrim_bottom

    width: 1440
    height: 900
    minimumWidth: 720
    minimumHeight: 450
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    title: player.title ? `${player.title} — Aperture` : "Aperture"
    color: theme.bg_0

    Item {
        id: stage
        anchors.fill: parent

        BackgroundArt {
            anchors.fill: parent
            visible: !player.hasMedia
        }

        VideoOutput {
            id: video
            anchors.fill: parent
            fillMode: VideoOutput.PreserveAspectFit
            Component.onCompleted: player.attachVideoOutput(video)
        }

        Rectangle {
            id: chromeScrimTop
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: parent.height * 0.19
            gradient: Gradient {
                GradientStop { position: 0; color: root.scrimTop }
                GradientStop { position: 1; color: Qt.rgba(root.scrimTop.r, root.scrimTop.g, root.scrimTop.b, 0) }
            }
        }

        Rectangle {
            id: chromeScrimBottom
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
        }

        Column {
            id: nowPlaying
            anchors { left: parent.left; leftMargin: 48; bottom: parent.bottom; bottomMargin: 150 }
            width: parent.width * 0.44
            spacing: 8
            visible: player.hasMedia

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
    }

    ResizeGrips {}
}
