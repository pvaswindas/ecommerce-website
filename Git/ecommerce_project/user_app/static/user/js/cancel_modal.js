var modal = document.getElementById("cancelOrderModal");

var btn = document.getElementById("cancelOrderBtn");

var span = document.getElementsByClassName("close")[0];

btn.onclick = function() {
  modal.style.display = "block";
}

span.onclick = function() {
  modal.style.display = "none";
}

window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}

document.getElementById("closeModalBtn").onclick = function() {
  modal.style.display = "none";
}


