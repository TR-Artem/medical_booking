document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.alert').forEach(function (alert) {
    setTimeout(function () {
      alert.classList.remove('show');
    }, 5000);
  });
});
