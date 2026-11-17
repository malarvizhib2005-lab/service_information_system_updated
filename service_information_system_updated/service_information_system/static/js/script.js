document.addEventListener("DOMContentLoaded", function () {
  const search = document.getElementById("tableSearch");
  const table = document.getElementById("serviceTable");

  // Client-side search across the records currently displayed by the server.
  if (search && table) {
    search.addEventListener("input", function () {
      const term = search.value.toLowerCase().trim();
      table.querySelectorAll("tbody tr").forEach(function (row) {
        row.style.display = row.innerText.toLowerCase().includes(term) ? "" : "none";
      });
    });
  }
});
