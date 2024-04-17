// Wait for the DOM to be fully loaded before executing any JavaScript
document.addEventListener("DOMContentLoaded", function () {
    // Get the modal and the button that opens it
    var modal = document.getElementById("cancelOrderModal");
    var btnOpenModal = document.getElementById("cancelOrderBtn");

    // Get the <span> element that closes the modal
    var spanClose = document.getElementsByClassName("close")[0];

    // When the user clicks the Cancel Order button, open the modal
    btnOpenModal.onclick = function () {
        modal.style.display = "block";
    }

    // When the user clicks on <span> (x) or the Close button, close the modal
    spanClose.onclick = function () {
        modal.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
});
