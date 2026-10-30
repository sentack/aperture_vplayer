import QtQuick
import QtQml
import QtQuick.Controls.Basic as T

// Right-click / Shift+F10 / Menu-key quick options: what you are likely to want right now,
// not a full menu bar.
T.Menu {
    // Not `menu`: every MenuItem has a `menu` property that would shadow the id.
    id: options

    property bool fullscreen: false

    signal openFilesRequested()
    signal openUrlRequested()
    signal subtitleFileRequested()
    signal fullscreenRequested()
    signal settingsRequested()

    component Item_: T.MenuItem {
        id: item

        implicitWidth: 240
        implicitHeight: 32
        padding: 0
        leftPadding: 30
        rightPadding: 14

        contentItem: UiText {
            text: item.text
            verticalAlignment: Text.AlignVCenter
            color: item.enabled ? theme.text_primary : theme.text_tertiary
        }

        indicator: UiText {
            x: 10
            anchors.verticalCenter: parent.verticalCenter
            visible: item.checkable && item.checked
            text: "✓"
            font.weight: Font.Bold
            // theme, not `menu`: inside a MenuItem, `menu` is the item's own (sub)menu.
            color: theme.accent
        }

        arrow: UiText {
            x: item.width - width - 12
            anchors.verticalCenter: parent.verticalCenter
            visible: item.subMenu !== null
            text: "›"
            font.pixelSize: 16
            color: theme.text_secondary
        }

        background: Rectangle {
            radius: 8
            color: item.highlighted && item.enabled ? theme.chip_bg : "transparent"
        }
    }

    component Separator_: T.MenuSeparator {
        topPadding: 4
        bottomPadding: 4
        contentItem: Rectangle {
            implicitHeight: 1
            color: theme.divider
        }
    }

    component SubMenu_: T.Menu {
        padding: 6
        delegate: Item_ {}
        background: Rectangle {
            implicitWidth: 220
            radius: 14
            color: theme.popover_bg
            border.width: 1
            border.color: theme.bar_border
        }
    }

    padding: 6
    delegate: Item_ {}
    background: Rectangle {
        implicitWidth: 240
        radius: 14
        color: theme.popover_bg
        border.width: 1
        border.color: theme.bar_border
    }

    Item_ {
        text: player.playing ? "Pause" : "Play"
        enabled: player.hasMedia
        onTriggered: player.togglePlay()
    }

    Separator_ {}

    Item_ {
        text: "Open file…"
        onTriggered: options.openFilesRequested()
    }

    Item_ {
        text: "Open URL…"
        onTriggered: options.openUrlRequested()
    }

    Separator_ {}

    SubMenu_ {
        title: "A–B loop"

        Item_ {
            text: "Set start (A) here"
            enabled: player.hasMedia && player.seekable
            onTriggered: player.setLoopA()
        }

        Item_ {
            text: "Set end (B) here"
            enabled: player.loopA >= 0
            onTriggered: player.setLoopB()
        }

        Item_ {
            text: "Clear loop"
            enabled: player.loopA >= 0
            onTriggered: player.clearLoop()
        }
    }

    Item_ {
        text: "Screenshot"
        enabled: player.hasVideo
        onTriggered: player.screenshot()
    }

    SubMenu_ {
        id: speedMenu
        title: `Playback speed (${player.rateLabel})`

        Instantiator {
            model: player.rates
            delegate: Item_ {
                required property real modelData
                text: `${modelData}×`
                checkable: true
                checked: Math.abs(player.rate - modelData) < 0.001
                onTriggered: player.rate = modelData
            }
            onObjectAdded: (index, object) => speedMenu.insertItem(index, object)
            onObjectRemoved: (index, object) => speedMenu.removeItem(object)
        }
    }

    SubMenu_ {
        id: audioMenu
        title: "Audio track"

        Item_ {
            text: "Only one audio track"
            enabled: false
            visible: tracks.audioOptions.length < 2
            height: visible ? implicitHeight : 0
        }

        Instantiator {
            model: tracks.audioOptions.length > 1 ? tracks.audioOptions : []
            delegate: Item_ {
                required property int index
                required property string modelData
                text: modelData
                checkable: true
                checked: tracks.audioIndex === index
                onTriggered: tracks.selectAudio(index)
            }
            onObjectAdded: (index, object) => audioMenu.insertItem(index + 1, object)
            onObjectRemoved: (index, object) => audioMenu.removeItem(object)
        }
    }

    SubMenu_ {
        id: subtitleMenu
        title: "Subtitles"

        Item_ {
            text: "Off"
            checkable: true
            checked: tracks.subtitleIndex === -1
            onTriggered: tracks.selectSubtitle(-1)
        }

        Instantiator {
            model: tracks.subtitleOptions
            delegate: Item_ {
                required property int index
                required property string modelData
                text: modelData
                checkable: true
                checked: tracks.subtitleIndex === index
                onTriggered: tracks.selectSubtitle(index)
            }
            onObjectAdded: (index, object) => subtitleMenu.insertItem(index + 1, object)
            onObjectRemoved: (index, object) => subtitleMenu.removeItem(object)
        }

        Item_ {
            text: "Load file…"
            enabled: player.hasMedia
            onTriggered: options.subtitleFileRequested()
        }
    }

    Separator_ {}

    Item_ {
        text: options.fullscreen ? "Exit fullscreen" : "Fullscreen"
        onTriggered: options.fullscreenRequested()
    }

    Item_ {
        text: "Settings…"
        onTriggered: options.settingsRequested()
    }
}
