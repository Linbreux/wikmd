const notyf = new Notyf({duration: 2000, ripple: false, position: { x: 'center', y: 'top' }});
var codeblocks = document.getElementsByTagName("PRE");
var block;

for (block = 0; block < codeblocks.length; block++) {
    codeblocks[block].innerHTML += "<button id= \"copybutton" + block + "\" onclick=\"copyCodeBlock(" + block + ")\">📋</button>"
}

function copyCodeBlock() {
    var codeBlock = document.getElementById("copybutton" + arguments[0]).parentNode.children[0].textContent;
    var dummy = document.createElement("textarea");
    document.body.appendChild(dummy);
    dummy.value = codeBlock;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);
    notyf.success('Copied');
}
