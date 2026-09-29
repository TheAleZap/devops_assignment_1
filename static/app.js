fetch("/health")
  .then((response) => response.json())
  .then((data) => {
    document.getElementById("status").textContent = `API status: ${data.status}`;
  })
  .catch(() => {
    document.getElementById("status").textContent = "API unreachable";
  });