function toggleDarkMode() {
  //Check if there is a value in Session Storage or Not!
  if (sessionStorage.getItem("theme") != "") {
    $("body").attr("data-theme", "light");
  } else {
    theme = sessionStorage.getItem("theme"); //Get Value of theme from session
    $("body").attr("data-theme", theme);
  }
  var dataTheme = $("body").attr("data-theme");

  if (dataTheme === "dark") {
    $("body").attr("data-theme", "light");
    sessionStorage.setItem("theme", "light"); // Store the value in Session Storage
  } else {
    sessionStorage.setItem("theme", "dark"); // Store the value in Session Storage
    $("body").attr("data-theme", "dark");
  }
}
