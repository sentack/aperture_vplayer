import QtQuick

// Frame and timestamp above the seek bar for the hovered position.
// The time shows at once; the frame appears when the thumbnail decoder catches up.
Rectangle {
    id: preview

    property int position: 0
    readonly property bool hasFrame: thumbs.source !== "" && frame.status === Image.Ready
    // Title of the chapter under the pointer, "" for files without chapters.
    readonly property string chapter: {
        let title = ""
        for (const c of player.chapters) {
            if (c.time > position)
                break
            title = c.title
        }
        return title
    }

    width: hasFrame ? frame.width + 8 : Math.min(260, time.implicitWidth + 24)
    height: (hasFrame ? frame.height + 4 : 0) + 30
    radius: 12
    color: theme.popover_bg
    border.width: 1
    border.color: theme.bar_border

    onPositionChanged: if (visible) thumbs.request(position, player.duration)
    onVisibleChanged: if (visible) thumbs.request(position, player.duration)

    Image {
        id: frame
        x: 4
        y: 4
        width: 192
        height: sourceSize.width > 0 ? Math.round(width * sourceSize.height / sourceSize.width) : 108
        visible: preview.hasFrame
        source: thumbs.source
        cache: false
        fillMode: Image.PreserveAspectFit
    }

    UiText {
        id: time
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 7 }
        width: Math.min(implicitWidth, preview.width - 16)
        text: preview.chapter ? `${preview.chapter} · ${player.formatTime(preview.position)}`
                              : player.formatTime(preview.position)
        font.weight: Font.DemiBold
        font.features: ({ "tnum": 1 })
        color: theme.text_primary
        elide: Text.ElideMiddle
    }
}
