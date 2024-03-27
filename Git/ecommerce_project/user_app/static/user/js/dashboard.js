
function toggleEdit() {
    var editAction = document.querySelector('.edit-action')
    var saveButton = document.querySelector('.save-button')
    var inputElements = document.querySelectorAll('.edit-input')
    var valueElements = document.querySelectorAll('.profile-info-item span:not(.edit-action)')
    var genderInput = document.getElementById('gender-input')
    var dobInput = document.getElementById('dob-input')

    if (inputElements[0].style.display === 'none') {
        editAction.innerHTML = 'Cancel <i class="bi bi-x-lg"></i>'
        saveButton.style.display = 'inline-block'
        inputElements.forEach((input) => (input.style.display = 'inline-block'))
        valueElements.forEach((value) => (value.style.display = 'none'))
        genderInput.style.display = 'block'
        dobInput.style.display = 'block'
    } else {
        editAction.innerHTML = 'Edit <i class="icon-edit"></i>'
        saveButton.style.display = 'none'
        inputElements.forEach((input) => (input.style.display = 'none'))
        valueElements.forEach((value) => (value.style.display = 'inline-block'))
        genderInput.style.display = 'none'
        dobInput.style.display = 'none'
    }
}
function editAddress(addressId) {
    var addressInfo = document.getElementById('address-info-' + addressId)
    var addressEditForm = document.getElementById('address-edit-form-' + addressId)

    addressInfo.style.display = 'none'
    addressEditForm.style.display = 'block'
}

function cancelEdit(addressId) {
    var addressInfo = document.getElementById('address-info-' + addressId)
    var addressEditForm = document.getElementById('address-edit-form-' + addressId)

    addressInfo.style.display = 'block'
    addressEditForm.style.display = 'none'
}
function toggleEdit(type, linkId) {
    var form = document.getElementById(type + '-address-form')
    if (form.style.display === 'none') {
        form.style.display = 'block'
        document.getElementById(linkId).innerHTML = 'Cancel <i class="bi bi-x-lg"></i>'
    } else {
        form.style.display = 'none'
        document.getElementById(linkId).innerHTML = 'Add <i class="bi bi-plus-square-dotted"></i>'
    }
}