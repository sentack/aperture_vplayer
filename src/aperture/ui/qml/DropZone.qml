import QtQuick

// Accepts dropped files or folders and outlines itself while a drag hovers.
DropArea {
    id: zone

    property string hint
    property real radius: 26
    property real inset: 16
    readonly property color accent: theme.accent

    signal urlsDropped(var urls)

    keys: ["text/uri-list"]
    onEntered: drag => drag.accepted = drag.hasUrls
    onDropped: drop => {
        if (!drop.hasUrls)
            return
        drop.accept(Qt.CopyAction)
        zone.urlsDropped(drop.urls)
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: zone.inset
        visible: zone.containsDrag
        radius: zone.radius
        color: Qt.rgba(zone.accent.r, zone.accent.g, zone.accent.b, 0.10)
        border.width: 2
        border.color: zone.accent

        UiText {
            anchors.centerIn: parent
            text: zone.hint
            font.pixelSize: 16
            font.weight: Font.DemiBold
            color: theme.text_primary
        }
    }
}
