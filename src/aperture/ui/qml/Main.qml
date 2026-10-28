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
    readonly property bool chromeVisible: !idle || !player.playing || controlBar.hovered || controlBar.menuOpen
                                          || playlistOpen || settingsOpen || miniControls.hovered
    property real chromeOpacity: chromeVisible ? 1 : 0
    Behavior on chromeOpacity { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }

    property int restoreVisibility: Window.Windowed
    property bool playlistOpen: false
    property bool settingsOpen: false

    // The playlist and settings share the right edge; opening one closes the other.
    function togglePlaylist() {
        settingsOpen = false
        playlistOpen = !playlistOpen
    }

    function toggleSettings() {
        playlistOpen = false
        settingsOpen = !settingsOpen
    }

    // Mini player: compact always-on-top window. The full window's geometry is kept to restore it.
    property bool mini: false
    property rect fullGeometry
    property bool fullWasMaximized: false

    function toggleMini() {
        if (mini) {
            mini = false
            if (fullWasMaximized) {
                showMaximized()
            } else {
                x = fullGeometry.x
                y = fullGeometry.y
                width = fullGeometry.width
                height = fullGeometry.height
            }
            return
        }
        if (!player.hasMedia)
            return
        if (fullscreen)
            visibility = restoreVisibility
        fullWasMaximized = visibility === Window.Maximized
        if (fullWasMaximized)
            showNormal()
        fullGeometry = Qt.rect(x, y, width, height)
        playlistOpen = false
        settingsOpen = false
        mini = true
        width = 400
        height = 225
        x = screen.virtualX + screen.width - width - 24
        y = screen.virtualY + screen.height - height - 64
    }

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
            if (mini)
                toggleMini()
            restoreVisibility = visibility
            showFullScreen()
        }
    }

    width: 1440
    height: 900
    minimumWidth: mini ? 320 : 720
    minimumHeight: mini ? 180 : 450
    visible: true
    flags: mini ? Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint : Qt.Window | Qt.FramelessWindowHint
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

    FileDialog {
        id: subtitleDialog
        title: "Load subtitles"
        fileMode: FileDialog.OpenFiles
        nameFilters: ["Subtitles (*.srt *.vtt)", "All files (*)"]
        currentFolder: player.mediaFolder
        onAccepted: tracks.addSubtitleUrls(selectedFiles)
    }

    KeyBindings {
        fullscreen: root.fullscreen
        settingsOpen: root.settingsOpen
        onSettingsToggled: root.toggleSettings()
        onFullscreenToggled: root.toggleFullscreen()
        onOpenRequested: root.chooseFiles(false)
        onMiniToggled: root.toggleMini()
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

        // The mini window has no title bar: drag anywhere to move it.
        DragHandler {
            target: null
            enabled: root.mini
            onActiveChanged: if (active) root.startSystemMove()
        }

        BackgroundArt {
            anchors.fill: parent
            visible: !player.hasMedia
        }

        // Letterbox bars stay black in either theme.
        Rectangle {
            anchors.fill: parent
            color: "black"
            visible: player.hasMedia
        }

        VideoOutput {
            id: video
            anchors.fill: parent
            fillMode: VideoOutput.PreserveAspectFit
            Component.onCompleted: player.attachVideoOutput(video)

            TapHandler {
                onTapped: root.wake()
                onSingleTapped: player.togglePlay()
                onDoubleTapped: root.mini ? root.toggleMini() : root.toggleFullscreen()
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
                text: "MP4, MKV, AVI, MOV, WebM and more · Ctrl+O or drop files"
                font.pixelSize: 12
                color: theme.text_tertiary
            }

            Column {
                id: recentList
                anchors.horizontalCenter: parent.horizontalCenter
                width: 420
                topPadding: 26
                spacing: 2
                visible: player.recentFiles.length > 0

                Item {
                    width: parent.width
                    height: 28

                    SectionLabel {
                        anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                        text: "Recent"
                    }

                    UiText {
                        anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                        text: "Clear"
                        font.pixelSize: 12
                        color: clearArea.containsMouse ? theme.text_secondary : theme.text_tertiary

                        Accessible.role: Accessible.Button
                        Accessible.name: "Clear recent files"
                        Accessible.onPressAction: player.clearRecent()

                        MouseArea {
                            id: clearArea
                            anchors.fill: parent
                            anchors.margins: -6
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: player.clearRecent()
                        }
                    }
                }

                Repeater {
                    model: player.recentFiles.slice(0, 5)

                    Rectangle {
                        id: recentRow

                        required property var modelData

                        width: recentList.width
                        height: 44
                        radius: 12
                        color: recentArea.containsMouse ? theme.chip_bg : "transparent"

                        Accessible.role: Accessible.Button
                        Accessible.name: `Open ${modelData.name}`
                        Accessible.onPressAction: player.openRecent(modelData.path)

                        UiText {
                            anchors {
                                left: parent.left; leftMargin: 14
                                right: resumeLabel.left; rightMargin: 12
                                verticalCenter: parent.verticalCenter
                            }
                            text: recentRow.modelData.name
                            color: recentArea.containsMouse ? theme.text_primary : theme.text_secondary
                        }

                        UiText {
                            id: resumeLabel
                            anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                            text: recentRow.modelData.resume ? `Resume ${recentRow.modelData.resume}` : recentRow.modelData.folder
                            font.pixelSize: 12
                            font.features: ({ "tnum": 1 })
                            color: theme.text_tertiary
                            elide: Text.ElideNone
                        }

                        MouseArea {
                            id: recentArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: player.openRecent(recentRow.modelData.path)
                        }
                    }
                }
            }
        }

        ErrorCard {
            anchors.centerIn: parent
            width: Math.min(420, parent.width - 48)
            visible: player.errorTitle !== "" && !root.mini
            onOpenRequested: root.chooseFiles(false)
        }

        IdleProgress {
            anchors {
                left: parent.left; leftMargin: root.mini ? 12 : 32
                right: parent.right; rightMargin: root.mini ? 12 : 32
                bottom: parent.bottom; bottomMargin: root.mini ? 10 : 52
            }
            value: player.duration > 0 ? player.position / player.duration : 0
            opacity: !player.hasMedia ? 0 : root.mini ? 1 : 1 - root.chromeOpacity
        }

        Rectangle {
            id: chromeScrimTop
            visible: !root.mini
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
            visible: !root.mini
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
            visible: !root.mini
            opacity: root.chromeOpacity
            enabled: root.chromeVisible
        }

        Column {
            id: nowPlaying
            anchors { left: parent.left; leftMargin: 48; bottom: parent.bottom; bottomMargin: 150 }
            width: parent.width * 0.44
            spacing: 8
            // Gives way to subtitles, which sit in the same band above the control bar.
            visible: player.hasMedia && !subtitleOverlay.visible && !root.mini
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
                text: player.subtitle
                font.pixelSize: 14
            }
        }

        // External SRT/VTT cues; embedded subtitle streams are drawn by VideoOutput itself.
        UiText {
            id: subtitleOverlay
            anchors {
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
                bottomMargin: root.mini ? 22 : root.chromeVisible ? 140 : 48
            }
            width: parent.width * 0.8
            visible: text !== ""
            text: tracks.subtitleText
            textFormat: Text.StyledText
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideNone
            font.pixelSize: Math.round(Math.max(root.mini ? 13 : 18, root.height * 0.036) * prefs.subtitleScale)
            font.weight: Font.DemiBold
            color: "white"
            style: Text.Outline
            styleColor: Qt.rgba(0, 0, 0, 0.85)

            Behavior on anchors.bottomMargin { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
        }

        ControlBar {
            id: controlBar
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 32 }
            fullscreen: root.fullscreen
            playlistOpen: root.playlistOpen
            settingsOpen: root.settingsOpen
            visible: !root.mini
            opacity: root.chromeOpacity
            enabled: root.chromeVisible
            onFullscreenToggled: root.toggleFullscreen()
            onMiniToggled: root.toggleMini()
            onPlaylistToggled: root.togglePlaylist()
            onSettingsToggled: root.toggleSettings()
            onSubtitleFileRequested: subtitleDialog.open()
        }

        MiniControls {
            id: miniControls
            anchors.fill: parent
            visible: root.mini
            opacity: root.chromeOpacity
            enabled: root.chromeVisible
            onRestoreRequested: root.toggleMini()
        }

        DropZone {
            anchors.fill: parent
            hint: "Drop to play"
            onUrlsDropped: urls => player.openUrls(urls)
        }

        PlaylistPanel {
            anchors { right: parent.right; top: topBar.bottom; bottom: controlBar.top; rightMargin: 32; topMargin: 8; bottomMargin: 16 }
            visible: root.playlistOpen && !root.mini
            onAddRequested: root.chooseFiles(true)
        }

        SettingsPanel {
            anchors { right: parent.right; top: topBar.bottom; bottom: controlBar.top; rightMargin: 32; topMargin: 8; bottomMargin: 16 }
            visible: root.settingsOpen && !root.mini
            onCloseRequested: root.settingsOpen = false
        }
    }

    Toast {
        id: toast
        anchors.horizontalCenter: parent.horizontalCenter
        y: root.mini ? 12 : 84
    }

    ResizeGrips {}
}
