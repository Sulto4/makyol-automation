// Placeholder for report generation JavaScript
// This file will be implemented in subtask-5-2

// Show/hide days threshold field based on report type
document.addEventListener('DOMContentLoaded', function() {
    const reportTypeSelect = document.getElementById('reportType');
    const daysThresholdGroup = document.getElementById('daysThresholdGroup');

    if (reportTypeSelect && daysThresholdGroup) {
        reportTypeSelect.addEventListener('change', function() {
            if (this.value === 'expiring_certificates') {
                daysThresholdGroup.style.display = 'flex';
            } else {
                daysThresholdGroup.style.display = 'none';
            }
        });
    }
});
