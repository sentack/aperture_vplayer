import QtQuick
import QtQuick.Window
import "Icons.js" as Icons

// Title bar for the frameless window: drag to move, double-click to maximize.
Item {
    id: bar

    property bool fullscreen: false

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
        anchors.left: parent.left
        anchors.leftMargin: 36
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
        anchors.right: parent.right
        anchors.rightMargin: 30
        anchors.verticalCenter: parent.verticalCenter
        spacing: 6
        visible: !bar.fullscreen

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
            glyph: Icons.close
            label: "Close window"
            onClicked: bar.Window.window.close()
        }
    }
}
