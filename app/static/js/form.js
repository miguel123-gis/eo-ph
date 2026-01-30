// Listen to mode buttons
const allButtons = [
    document.getElementById("btnRegMd"),
    document.getElementById("btnAnntMd"),
    document.getElementById("btnExpAllMd"),
    document.getElementById("btnCloudlessMd")
]

function listenToButton(buttonId) {
    buttonId.addEventListener("click", function(event) {
        console.log('Clicked', event);
        console.log('Clicked', event.target);
    })
}

allButtons.forEach(listenToButton)