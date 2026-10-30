import QtQuick
import "Icons.js" as Icons

// One rebindable action: label, its key as a chip (click, then press the new keys), and an
// unbind button. A refused key shows why underneath; nothing changes until a key is accepted.
Column {
    id: row

    required property var modelData
    property bool listening: false
    property string error: ""

    width: parent ? parent.width : 0
    spacing: 4

    function startListening() {
        error = ""
        listening = true
        keymap.capturing = true
        chip.forceActiveFocus()
    }

    function stopListening() {
        listening = false
        keymap.capturing = false
    }

    Item {
        width: parent.width
        height: 30

        UiText {
            anchors { left: parent.left; right: controls.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
            text: row.modelData.label
            color: theme.text_primary
        }

        Row {
            id: controls
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            spacing: 4

            Rectangle {
                id: chip

                width: Math.max(72, chipText.implicitWidth + 20)
                height: 26
                radius: 7
                color: row.listening ? theme.track_bg : chipArea.containsMouse ? theme.chip_bg : "transparent"
                border.width: row.listening ? 2 : 1
                border.color: row.listening ? theme.accent : theme.divider
                focus: row.listening

                Accessible.role: Accessible.Button
                Accessible.name: `${row.modelData.label}: ${keymap.display(row.modelData.key)}. Press to change.`
                Accessible.onPressAction: row.startListening()

                UiText {
                    id: chipText
                    anchors.centerIn: parent
                    text: row.listening ? "Press keys…" : keymap.display(row.modelData.key)
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    font.italic: !row.listening && row.modelData.key === ""
                    color: row.modelData.key === "" && !row.listening ? theme.text_tertiary : theme.text_secondary
                    elide: Text.ElideNone
                }

                MouseArea {
                    id: chipArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: row.startListening()
                }

                // Claim every key while listening, so no shortcut fires instead.
                Keys.onShortcutOverride: event => event.accepted = row.listening
                Keys.onPressed: event => {
                    if (!row.listening)
                        return
                    event.accepted = true
                    if (event.key === Qt.Key_Escape) {
                        row.stopListening()
                        return
                    }
                    const sequence = keymap.sequenceFor(event.key, event.modifiers)
                    if (sequence === "")
                        return  // a lone modifier: keep listening for the rest of the combo
                    row.error = keymap.bind(row.modelData.id, sequence)
                    row.stopListening()
                }
                onActiveFocusChanged: if (!activeFocus && row.listening) row.stopListening()
            }

            IconButton {
                width: 26
                height: 26
                iconSize: 14
                glyph: Icons.close
                label: `Unbind ${row.modelData.label}`
                enabled: row.modelData.key !== ""
                onClicked: {
                    row.error = ""
                    keymap.unbind(row.modelData.id)
                }
            }
        }
    }

    UiText {
        width: parent.width
        visible: row.error !== ""
        text: row.error
        wrapMode: Text.WordWrap
        elide: Text.ElideNone
        font.pixelSize: 12
        color: "#E5484D"
    }
}
