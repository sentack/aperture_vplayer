import QtQuick
import QtQuick.Window

// Edge and corner handles for the frameless window. Inert unless windowed.
Item {
    id: grips

    property int size: 6

    anchors.fill: parent
    visible: Window.window !== null && Window.window.visibility === Window.Windowed

    component Grip: MouseArea {
        property int edges
        onPressed: grips.Window.window.startSystemResize(edges)
    }

    Grip { edges: Qt.LeftEdge; cursorShape: Qt.SizeHorCursor; y: grips.size; width: grips.size; height: grips.height - 2 * grips.size }
    Grip { edges: Qt.RightEdge; cursorShape: Qt.SizeHorCursor; x: grips.width - grips.size; y: grips.size; width: grips.size; height: grips.height - 2 * grips.size }
    Grip { edges: Qt.TopEdge; cursorShape: Qt.SizeVerCursor; x: grips.size; width: grips.width - 2 * grips.size; height: grips.size }
    Grip { edges: Qt.BottomEdge; cursorShape: Qt.SizeVerCursor; x: grips.size; y: grips.height - grips.size; width: grips.width - 2 * grips.size; height: grips.size }
    Grip { edges: Qt.TopEdge | Qt.LeftEdge; cursorShape: Qt.SizeFDiagCursor; width: grips.size; height: grips.size }
    Grip { edges: Qt.TopEdge | Qt.RightEdge; cursorShape: Qt.SizeBDiagCursor; x: grips.width - grips.size; width: grips.size; height: grips.size }
    Grip { edges: Qt.BottomEdge | Qt.LeftEdge; cursorShape: Qt.SizeBDiagCursor; y: grips.height - grips.size; width: grips.size; height: grips.size }
    Grip { edges: Qt.BottomEdge | Qt.RightEdge; cursorShape: Qt.SizeFDiagCursor; x: grips.width - grips.size; y: grips.height - grips.size; width: grips.size; height: grips.size }
}
