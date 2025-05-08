document.querySelectorAll('.dropdown-item input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', function(e) {
        const columnIndex = this.getAttribute('data-column');
        const isChecked = this.checked;

        // Toggle column visibility
        document.querySelectorAll(`#doctorTable th:nth-child(${parseInt(columnIndex) + 1}), #doctorTable td:nth-child(${parseInt(columnIndex) + 1})`).forEach(cell => {
            cell.style.display = isChecked ? '' : 'none';
        });
    });
});

// Prevent dropdown from closing when clicking inside
document.querySelector('.dropdown-menu').addEventListener('click', function(e) {
    e.stopPropagation();
});