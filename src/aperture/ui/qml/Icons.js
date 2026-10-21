.pragma library

// SVG path data on a 24×24 grid, traced from docs/reference.html.
// `stroke` paths render at 1.75px with round caps, `fill` paths solid.

var play = { fill: "M7 5.3c0-1 1.1-1.6 1.95-1.05l9.5 6.2c.8.5.8 1.7 0 2.2l-9.5 6.2C8.1 19.3 7 18.7 7 17.7V5.3Z" }
var pause = { fill: "M7.5 5h1a1.5 1.5 0 0 1 1.5 1.5v11a1.5 1.5 0 0 1-1.5 1.5h-1A1.5 1.5 0 0 1 6 17.5v-11A1.5 1.5 0 0 1 7.5 5ZM15.5 5h1a1.5 1.5 0 0 1 1.5 1.5v11a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5v-11A1.5 1.5 0 0 1 15.5 5Z" }

var previous = { stroke: "M6 5.5v13", fill: "M19 6.4v11.2c0 .8-.9 1.3-1.55.85l-8.1-5.6a1 1 0 0 1 0-1.7l8.1-5.6c.65-.45 1.55 0 1.55.85Z" }
var next = { stroke: "M18 5.5v13", fill: "M5 6.4v11.2c0 .8.9 1.3 1.55.85l8.1-5.6a1 1 0 0 0 0-1.7l-8.1-5.6C5.9 5.1 5 5.55 5 6.4Z" }
var stop = { stroke: "M8 6.5h8a1.5 1.5 0 0 1 1.5 1.5v8a1.5 1.5 0 0 1-1.5 1.5H8A1.5 1.5 0 0 1 6.5 16V8A1.5 1.5 0 0 1 8 6.5Z" }
var volume = { stroke: "M16.5 8.5a5 5 0 0 1 0 7M19 6a9 9 0 0 1 0 12", fill: "M4 9v6h4l5 4V5L8 9H4Z" }
var muted = { stroke: "M16.5 9.5l5 5M21.5 9.5l-5 5", fill: "M4 9v6h4l5 4V5L8 9H4Z" }

var fullscreen = { stroke: "M9 4H5a1 1 0 0 0-1 1v4M15 4h4a1 1 0 0 1 1 1v4M9 20H5a1 1 0 0 1-1-1v-4M15 20h4a1 1 0 0 0 1-1v-4" }
var exitFullscreen = { stroke: "M4 9h4a1 1 0 0 0 1-1V4M20 9h-4a1 1 0 0 1-1-1V4M4 15h4a1 1 0 0 1 1 1v4M20 15h-4a1 1 0 0 0-1 1v4" }

var playlist = { stroke: "M9.5 7H20M9.5 12H20M9.5 17H20", fill: "M3.6 7a1.4 1.4 0 1 0 2.8 0a1.4 1.4 0 1 0-2.8 0ZM3.6 12a1.4 1.4 0 1 0 2.8 0a1.4 1.4 0 1 0-2.8 0ZM3.6 17a1.4 1.4 0 1 0 2.8 0a1.4 1.4 0 1 0-2.8 0Z" }
var add = { stroke: "M12 5v14M5 12h14" }
var trash = { stroke: "M5 7h14M10 7V5h4v2M7 7l.8 11.2a1.5 1.5 0 0 0 1.5 1.3h5.4a1.5 1.5 0 0 0 1.5-1.3L17 7" }

var settings = { stroke: "M4 7h7.7M16.3 7H20M4 17h1.7M10.3 17H20M11.7 7a2.3 2.3 0 1 0 4.6 0a2.3 2.3 0 1 0-4.6 0ZM5.7 17a2.3 2.3 0 1 0 4.6 0a2.3 2.3 0 1 0-4.6 0Z" }

var check = { stroke: "M6 12.5l4 4 8-9" }

var minimize = { stroke: "M5.25 12h13.5" }
var maximize = { stroke: "M7.5 5.25h9a2.25 2.25 0 0 1 2.25 2.25v9a2.25 2.25 0 0 1-2.25 2.25h-9a2.25 2.25 0 0 1-2.25-2.25v-9A2.25 2.25 0 0 1 7.5 5.25Z" }
var close = { stroke: "M5.25 5.25l13.5 13.5M18.75 5.25l-13.5 13.5" }
