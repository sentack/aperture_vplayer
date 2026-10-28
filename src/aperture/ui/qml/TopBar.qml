import QtQuick
import QtQuick.Window
import "Icons.js" as Icons

// Title bar for the frameless window: drag to move, double-click to maximize.
// macOS keeps its convention: window controls on the left, close first.
Item {
    id: bar

    property bool fullscreen: false
    readonly property bool mac: Qt.platform.os === "osx"

    implicitHeight: 64

    component WindowButton: IconButton {
        width: 28
        height: 28
        iconSize: 16
        strokeWidth: 1.4
    }

    function toggleMaximized() {
        const w = Window.window
        if (w.visibility === Window.Maximized)
            w.showNormal()
        else
            w.showMaximized()
    }

    DragHandler {
        target: null
        enabled: !bar.fullscreen
        onActiveChanged: if (active) bar.Window.window.startSystemMove()
    }

    TapHandler {
        enabled: !bar.fullscreen
        onDoubleTapped: bar.toggleMaximized()
    }

    Row {
        anchors.left: bar.mac && windowControls.visible ? windowControls.right : parent.left
        anchors.leftMargin: bar.mac && windowControls.visible ? 20 : 36
        anchors.verticalCenter: parent.verticalCenter
        spacing: 12

        Rectangle {
            width: 28
            height: 28
            radius: 9
            color: theme.accent

            Icon {
                anchors.centerIn: parent
                anchors.horizontalCenterOffset: 1
                size: 14
                glyph: Icons.play
                color: "white"
            }
        }

        UiText {
            anchors.verticalCenter: parent.verticalCenter
            text: "APERTURE"
            font.pixelSize: 13
            font.weight: Font.Bold
            font.letterSpacing: 13 * 0.14
            color: theme.text_primary
            opacity: 0.92
        }
    }

    Row {
        id: windowControls
        anchors.left: bar.mac ? parent.left : undefined
        anchors.leftMargin: 20
        anchors.right: bar.mac ? undefined : parent.right
        anchors.rightMargin: 30
        anchors.verticalCenter: parent.verticalCenter
        spacing: 6
        visible: !bar.fullscreen

        WindowButton {
            visible: bar.mac
            glyph: Icons.close
            label: "Close window"
            onClicked: bar.Window.window.close()
        }

        WindowButton {
            glyph: Icons.minimize
            label: "Minimize window"
            onClicked: bar.Window.window.showMinimized()
        }

        WindowButton {
            glyph: Icons.maximize
            label: "Maximize window"
            onClicked: bar.toggleMaximized()
        }

        WindowButton {
            visible: !bar.mac
            glyph: Icons.close
            label: "Close window"
            onClicked: bar.Window.window.close()
        }
    }
}
