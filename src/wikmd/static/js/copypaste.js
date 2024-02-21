const notyf = new Notyf({duration: 2000, ripple: false, position: { x: 'center', y: 'top' }});
var codeblocks = document.getElementsByTagName("PRE");
var block;

const pathToCopyIcon = darktheme == "False" ? "file-copy.svg" : "file-copy-white.svg"
console.log(darktheme)

for (block = 0; block < codeblocks.length; block++) {
    codeblocks[block].innerHTML += 
        "<img id=\"copybutton" 
        + block 
        + "\" onclick=\"copyCodeBlock(" 
        + block 
        + ")\" title=\"Copy to clipboard\" src=\"/static/images/" + pathToCopyIcon + "\""
        + "></img>"
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
