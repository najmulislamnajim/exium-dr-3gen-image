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

// Rows Per Page Functionality
        const rowsPerPageInput = document.getElementById('rowsPerPage');
        const rowsDisplayedSpan = document.getElementById('rowsDisplayed');
        const tableBody = document.querySelector('#doctorTable tbody');
        const allRows = Array.from(tableBody.querySelectorAll('tr'));

        function updateRowsDisplayed() {
            const rowsToShow = parseInt(rowsPerPageInput.value) || 14;
            allRows.forEach((row, index) => {
                row.style.display = index < rowsToShow ? '' : 'none';
            });
            rowsDisplayedSpan.textContent = Math.min(rowsToShow, allRows.length);
        }

        rowsPerPageInput.addEventListener('input', updateRowsDisplayed);
        updateRowsDisplayed();

        // Switching Forms for Doctor 1 and Doctor 2
        const doctor1Btn = document.getElementById('doctor1Btn');
        const doctor2Btn = document.getElementById('doctor2Btn');

        function switchForm(doctorId) {
            document.getElementById('doctorId').value = doctorId;
            document.getElementById('formHeader').textContent = `Upload Doctor ${doctorId}`;
            document.getElementById('doctorForm').reset();

            // Toggle button colors
            if (doctorId === 1) {
                doctor1Btn.classList.remove('btn-secondary');
                doctor1Btn.classList.add('btn-primary');
                doctor2Btn.classList.remove('btn-primary');
                doctor2Btn.classList.add('btn-secondary');
            } else {
                doctor1Btn.classList.remove('btn-primary');
                doctor1Btn.classList.add('btn-secondary');
                doctor2Btn.classList.remove('btn-secondary');
                doctor2Btn.classList.add('btn-primary');
            }
        }

        // Form Submission Handler
        document.getElementById('doctorForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const doctorId = document.getElementById('doctorId').value;
            const territoryId = document.getElementById('territoryId').value;
            const drRplId = document.getElementById('drRplId').value;
            const drName = document.getElementById('drName').value;
            const drImage = document.getElementById('drImage').files[0];
            const drParentImage = document.getElementById('drParentImage').files[0];
            const drChildImage = document.getElementById('drChildImage').files[0];

            // For demonstration, log the form data
            console.log({
                doctorId,
                territoryId,
                drRplId,
                drName,
                drImage: drImage ? drImage.name : null,
                drParentImage: drParentImage ? drParentImage.name : null,
                drChildImage: drChildImage ? drChildImage.name : null
            });

            alert(`Doctor ${doctorId} data submitted successfully!`);
            this.reset();
        });