function toggleEdit1() {
    // Selecting all elements with class "edit-input"
    var editInputs = document.querySelectorAll('.edit-input');
    var saveButton = document.querySelector('.save-button');
    var cancelButton = document.querySelector('.cancel-button');
    var spanValues = document.querySelectorAll('.profile-info-item > span');
    var genderInput = document.getElementById('gender-input');

    // Loop through each input element
    editInputs.forEach(function(input) {
        // Toggle the display style between "block" and "none"
        input.style.display = input.style.display === 'none' ? 'block' : 'none';
    });

    // Loop through each span element
    spanValues.forEach(function(span) {
        // Toggle the display style between "block" and "none"
        span.style.display = span.style.display === 'none' ? 'inline' : 'none';
    });

    // Toggle the display style of the gender input
    genderInput.style.display = genderInput.style.display === 'none' ? 'block' : 'none';

    // Toggle the display style of the save button
    saveButton.style.display = saveButton.style.display === 'none' ? 'block' : 'none';
    // Display the cancel button
    cancelButton.style.display = cancelButton.style.display === 'none' ? 'block' : 'none';
}

function cancelEdit() {
    // Selecting all elements with class "edit-input"
    var editInputs = document.querySelectorAll('.edit-input');
    var saveButton = document.querySelector('.save-button');
    var cancelButton = document.querySelector('.cancel-button');
    var spanValues = document.querySelectorAll('.profile-info-item > span');
    var genderInput = document.getElementById('gender-input');

    // Loop through each input element
    editInputs.forEach(function(input) {
        // Hide the input fields
        input.style.display = 'none';
    });

    // Loop through each span element
    spanValues.forEach(function(span) {
        // Show the span elements
        span.style.display = 'inline';
    });

    // Hide the gender input
    genderInput.style.display = 'none';

    // Hide the save button
    saveButton.style.display = 'none';
    // Hide the cancel button
    cancelButton.style.display = 'none';
}




function toggleEdit2(section, editLinkId) {
    var editLink = document.getElementById(editLinkId);
    var form = document.getElementById(section + '-address-form');

    // Toggle the display style of the edit link
    editLink.style.display = editLink.style.display === 'none' ? 'block' : 'none';
    // Toggle the display style of the form
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

function editAddress(addressId) {
    var infoDiv = document.getElementById('address-info-' + addressId);
    var editForm = document.getElementById('address-edit-form-' + addressId);

    // Toggle the display style of the address info
    infoDiv.style.display = infoDiv.style.display === 'none' ? 'block' : 'none';
    // Toggle the display style of the edit form
    editForm.style.display = editForm.style.display === 'none' ? 'block' : 'none';
}

function cancelEdit(addressId) {
    var infoDiv = document.getElementById('address-info-' + addressId);
    var editForm = document.getElementById('address-edit-form-' + addressId);

    // Toggle the display style of the address info
    infoDiv.style.display = infoDiv.style.display === 'none' ? 'block' : 'none';
    // Toggle the display style of the edit form
    editForm.style.display = editForm.style.display === 'none' ? 'block' : 'none';
}
