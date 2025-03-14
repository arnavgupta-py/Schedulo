/**
 * Schedulo - Timetable Optimizer JavaScript
 * Handles UI interactions and job status polling
 */

document.addEventListener("DOMContentLoaded", function() {
    // Close alert buttons
    setupAlertCloseButtons();
});

/**
 * Sets up event listeners for alert close buttons
 */
function setupAlertCloseButtons() {
    document.querySelectorAll('.alert-close').forEach(function(button) {
        button.addEventListener('click', function() {
            const alert = this.parentElement;
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.style.display = 'none';
            }, 300);
        });
    });
}

/**
 * Initialize job polling with the specified interval
 * @param {number} pollingInterval - Interval in milliseconds
 */
function initJobPolling(pollingInterval) {
    // Set up polling for job status updates
    const jobItems = document.querySelectorAll('.job-item');
    
    if (jobItems.length > 0) {
        // Poll for updates every pollingInterval milliseconds
        setInterval(function() {
            updateJobStatus(jobItems);
        }, pollingInterval);
        
        // Initial update
        updateJobStatus(jobItems);
    }
}

/**
 * Updates the status of all jobs
 * @param {NodeList} jobItems - Collection of job elements to update
 */
function updateJobStatus(jobItems) {
    jobItems.forEach(function(jobItem) {
        const jobId = jobItem.dataset.jobId;
        const statusSpan = jobItem.querySelector('.job-status');
        const timeSpan = jobItem.querySelector('.job-time');
        
        fetch(`/scheduler/api/job/${jobId}`)
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                // Update status
                let statusText = data.status;
                let statusClass = '';
                
                switch (data.status) {
                    case 'SOLVING':
                        statusText = 'Running';
                        statusClass = 'status-running';
                        break;
                    case 'COMPLETED':
                        statusText = 'Completed';
                        statusClass = 'status-completed';
                        break;
                    case 'ERROR':
                        statusText = 'Error';
                        statusClass = 'status-error';
                        break;
                    default:
                        statusText = data.status;
                        statusClass = 'status-unknown';
                }
                
                statusSpan.textContent = statusText;
                statusSpan.className = 'job-status ' + statusClass;
                
                // Update elapsed time
                if (data.elapsed_seconds) {
                    const minutes = Math.floor(data.elapsed_seconds / 60);
                    const seconds = Math.floor(data.elapsed_seconds % 60);
                    timeSpan.textContent = `${minutes}m ${seconds}s`;
                }
            })
            .catch(function(error) {
                console.error(`Error fetching status for job ${jobId}:`, error);
                statusSpan.textContent = 'Error';
                statusSpan.className = 'job-status status-error';
            });
    });
}