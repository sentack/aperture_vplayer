import QtQuick
import QtQuick.Shapes

// Monochrome idle backdrop: two tonal ridges and an orb. Never reads the accent.
Item {
    id: art

    // Polygon in a band covering the bottom `band` of the item; points are fractions of that band.
    function ridge(band, points) {
        const top = height * (1 - band)
        return points.map(p => Qt.point(width * p[0], top + height * band * p[1]))
    }

    Rectangle {
        anchors.fill: parent
        color: theme.bg_0
    }

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer

        ShapePath {
            strokeWidth: -1
            fillColor: theme.bg_1
            PathPolyline { path: art.ridge(0.62, [[0, .48], [.22, .28], [.48, .42], [.74, .18], [1, .36], [1, 1], [0, 1]]) }
        }

        ShapePath {
            strokeWidth: -1
            fillColor: theme.bg_2
            PathPolyline { path: art.ridge(0.46, [[0, .62], [.18, .36], [.44, .54], [.66, .22], [1, .48], [1, 1], [0, 1]]) }
        }
    }

    Rectangle {
        x: parent.width * 0.733
        y: parent.height * 0.142
        width: parent.width * 0.092
        height: width
        radius: width / 2
        color: theme.bg_3
    }
}
