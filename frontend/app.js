/**
 * Makyol Compliance Report Generator - Frontend JavaScript
 * Handles form submission, API communication, and file downloads
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/reports`;

// DOM Elements
let reportForm;
let reportTypeSelect;
let daysThresholdGroup;
let generateBtn;
let statusMessage;

/**
 * Initialize the application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM references
    reportForm = document.getElementById('reportForm');
    reportTypeSelect = document.getElementById('reportType');
    daysThresholdGroup = document.getElementById('daysThresholdGroup');
    generateBtn = document.getElementById('generateBtn');
    statusMessage = document.getElementById('statusMessage');

    // Set up event listeners
    if (reportTypeSelect && daysThresholdGroup) {
        reportTypeSelect.addEventListener('change', handleReportTypeChange);
    }

    if (reportForm) {
        reportForm.addEventListener('submit', handleFormSubmit);
    }
});

/**
 * Handle report type change to show/hide days threshold field
 */
function handleReportTypeChange() {
    if (reportTypeSelect.value === 'expiring_certificates') {
        daysThresholdGroup.style.display = 'flex';
    } else {
        daysThresholdGroup.style.display = 'none';
    }
}

/**
 * Handle form submission
 * @param {Event} event - Form submit event
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    // Validate form
    if (!reportForm.checkValidity()) {
        reportForm.reportValidity();
        return;
    }

    // Collect form data
    const formData = collectFormData();

    // Validate required fields
    if (!formData.report_type) {
        showMessage('Please select a report type', 'error');
        return;
    }

    if (!formData.preparer || formData.preparer.trim() === '') {
        showMessage('Please enter your name in the "Prepared By" field', 'error');
        return;
    }

    // Show loading state
    setLoadingState(true);
    hideMessage();

    try {
        // Generate report
        await generateReport(formData);
        showMessage('Report generated successfully!', 'success');
    } catch (error) {
        showMessage(error.message || 'Failed to generate report. Please try again.', 'error');
    } finally {
        setLoadingState(false);
    }
}

/**
 * Collect form data into request payload
 * @returns {Object} Request payload for the API
 */
function collectFormData() {
    const formData = new FormData(reportForm);

    // Build request payload
    const payload = {
        report_type: formData.get('reportType') || '',
        format: formData.get('format') || 'pdf',
        preparer: formData.get('preparer') || ''
    };

    // Add optional filters (only if they have values)
    const supplierId = formData.get('supplierId');
    if (supplierId && supplierId.trim() !== '') {
        payload.supplier_id = parseInt(supplierId, 10);
    }

    const dateFrom = formData.get('dateFrom');
    if (dateFrom && dateFrom.trim() !== '') {
        payload.date_from = dateFrom;
    }

    const dateTo = formData.get('dateTo');
    if (dateTo && dateTo.trim() !== '') {
        payload.date_to = dateTo;
    }

    const status = formData.get('status');
    if (status && status.trim() !== '') {
        payload.status = status;
    }

    const daysThreshold = formData.get('daysThreshold');
    if (daysThreshold && daysThreshold.trim() !== '') {
        payload.days_threshold = parseInt(daysThreshold, 10);
    }

    return payload;
}

/**
 * Generate report by calling the API and downloading the file
 * @param {Object} payload - Request payload
 * @throws {Error} If the API request fails
 */
async function generateReport(payload) {
    try {
        // Make API request
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        // Check if request was successful
        if (!response.ok) {
            let errorMessage = 'Failed to generate report';

            // Try to extract error details from response
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch (e) {
                // If response is not JSON, use status text
                errorMessage = `Server error: ${response.status} ${response.statusText}`;
            }

            throw new Error(errorMessage);
        }

        // Get the blob from response
        const blob = await response.blob();

        // Check if blob is valid
        if (blob.size === 0) {
            throw new Error('Generated report is empty');
        }

        // Extract filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'report';

        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename=(.+)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        } else {
            // Fallback: generate filename based on report type and format
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            const extension = payload.format === 'excel' ? 'xlsx' : 'pdf';
            filename = `${payload.report_type}_${timestamp}.${extension}`;
        }

        // Download the file
        downloadBlob(blob, filename);

    } catch (error) {
        // Re-throw with a more user-friendly message if it's a network error
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('Unable to connect to the server. Please ensure the backend is running.');
        }
        throw error;
    }
}

/**
 * Download a blob as a file
 * @param {Blob} blob - The blob to download
 * @param {string} filename - The filename for the download
 */
function downloadBlob(blob, filename) {
    // Create a temporary URL for the blob
    const url = window.URL.createObjectURL(blob);

    // Create a temporary anchor element
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';

    // Add to document, click, and remove
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up the URL
    setTimeout(() => {
        window.URL.revokeObjectURL(url);
    }, 100);
}

/**
 * Set loading state for the generate button
 * @param {boolean} isLoading - Whether the button should show loading state
 */
function setLoadingState(isLoading) {
    if (!generateBtn) return;

    if (isLoading) {
        generateBtn.disabled = true;
        generateBtn.classList.add('loading');
        const btnText = generateBtn.querySelector('.btn-text');
        if (btnText) {
            btnText.textContent = 'Generating...';
        }
    } else {
        generateBtn.disabled = false;
        generateBtn.classList.remove('loading');
        const btnText = generateBtn.querySelector('.btn-text');
        if (btnText) {
            btnText.textContent = 'Generate Report';
        }
    }
}

/**
 * Show a status message to the user
 * @param {string} message - The message to display
 * @param {string} type - The type of message (success, error, info, warning)
 */
function showMessage(message, type = 'info') {
    if (!statusMessage) return;

    // Remove existing type classes
    statusMessage.classList.remove('success', 'error', 'info', 'warning');

    // Add new type class
    statusMessage.classList.add(type);

    // Set message text
    statusMessage.textContent = message;

    // Show the message
    statusMessage.style.display = 'block';

    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            hideMessage();
        }, 5000);
    }
}

/**
 * Hide the status message
 */
function hideMessage() {
    if (!statusMessage) return;
    statusMessage.style.display = 'none';
}
