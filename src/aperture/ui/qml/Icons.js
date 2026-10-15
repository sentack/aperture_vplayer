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

var minimize = { stroke: "M5.25 12h13.5" }
var maximize = { stroke: "M7.5 5.25h9a2.25 2.25 0 0 1 2.25 2.25v9a2.25 2.25 0 0 1-2.25 2.25h-9a2.25 2.25 0 0 1-2.25-2.25v-9A2.25 2.25 0 0 1 7.5 5.25Z" }
var close = { stroke: "M5.25 5.25l13.5 13.5M18.75 5.25l-13.5 13.5" }
