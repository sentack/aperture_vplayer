import QtQuick

// Transient pill for keyboard feedback. Stays visible while idle; never takes input.
Rectangle {
    id: toast

    function show(text) {
        label.text = text
        opacity = 1
        hideTimer.restart()
    }

    implicitWidth: label.implicitWidth + 32
    implicitHeight: 36
    radius: 18
    color: theme.popover_bg
    border.width: 1
    border.color: theme.bar_border
    opacity: 0
    visible: opacity > 0

    Behavior on opacity { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }

    Timer {
        id: hideTimer
        interval: 1400
        onTriggered: toast.opacity = 0
    }

    UiText {
        id: label
        anchors.centerIn: parent
        font.pixelSize: 13
        font.weight: Font.DemiBold
        font.features: ({ "tnum": 1 })
        color: theme.text_primary
        elide: Text.ElideNone
    }
}
