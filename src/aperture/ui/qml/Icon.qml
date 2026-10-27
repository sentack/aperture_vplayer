import QtQuick
import QtQuick.Shapes

// One glyph from Icons.js: `stroke` path outlined, `fill` path solid, both on a 24×24 grid.
Shape {
    id: icon

    property var glyph: ({})
    property color color: theme.text_secondary
    property real size: 20
    property real strokeWidth: 1.75

    implicitWidth: size
    implicitHeight: size
    preferredRendererType: Shape.CurveRenderer

    ShapePath {
        // From `size`, not width/height: Shape adjusts its own geometry, which would loop.
        scale: Qt.size(icon.size / 24, icon.size / 24)
        strokeColor: icon.color
        strokeWidth: icon.glyph.stroke ? icon.strokeWidth : -1
        fillColor: "transparent"
        capStyle: ShapePath.RoundCap
        joinStyle: ShapePath.RoundJoin
        PathSvg { path: icon.glyph.stroke || "" }
    }

    ShapePath {
        // From `size`, not width/height: Shape adjusts its own geometry, which would loop.
        scale: Qt.size(icon.size / 24, icon.size / 24)
        strokeWidth: -1
        fillColor: icon.glyph.fill ? icon.color : "transparent"
        PathSvg { path: icon.glyph.fill || "" }
    }
}
