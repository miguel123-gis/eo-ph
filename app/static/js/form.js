// Listen to mode buttons
const modeButtonA = document.getElementById("modeButtonA")
const modeButtonE = document.getElementById("modeButtonE")
const modeButtonR = document.getElementById("modeButtonR")
const allButtons = [modeButtonA, modeButtonE, modeButtonR]

function listenToButton(buttonId) {
    buttonId.addEventListener("click", function(event) {
        console.log('Clicked', event);
        console.log('Clicked', event.target);
    })
}

allButtons.forEach(listenToButton)