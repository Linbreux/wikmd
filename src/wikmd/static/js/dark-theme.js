document.addEventListener('DOMContentLoaded', function () {
  const themeToggle = document.getElementById('theme-toggle');
  const currentTheme = localStorage.getItem('theme') || 'wikmd-light';
  document.documentElement.setAttribute('data-theme', currentTheme);

  if (currentTheme === 'wikmd-dark') {
    themeToggle.checked = true;
  }

  themeToggle.addEventListener('change', function () {
    if (themeToggle.checked) {
      document.documentElement.setAttribute('data-theme', 'wikmd-dark');
      localStorage.setItem('theme', 'wikmd-dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'wikmd-light');
      localStorage.setItem('theme', 'wikmd-light');
    }
  });
});
