import QtQuick

// Fills a floating surface (glass panel, card, modal) so presses and wheel turns on it never
// reach what lies underneath: the video's tap handler, or the lyrics list scrolling along
// with the playlist. Siblings declared after it sit on top and still get every event first.
MouseArea {
    anchors.fill: parent
    onWheel: wheel => wheel.accepted = true
}
