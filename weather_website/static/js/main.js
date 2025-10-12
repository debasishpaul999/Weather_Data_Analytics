class WeatherApp {
    constructor() {
        this.currentData = null;
        this.currentPage = 1;
        this.rowsPerPage = 50;
        this.init();
    }

    async init() {
        await this.loadCities();
        this.setupEventListeners();
        this.setDefaultDates();
        this.setupFormValidation();
        this.setupExportFunctionality();
    }

    async loadCities() {
        try {
            const response = await fetch('/api/cities');
            const data = await response.json();
            
            if (data.success) {
                this.populateCitySelect(data.cities);
            } else {
                this.showError('Failed to load cities: ' + data.error);
            }
        } catch (error) {
            this.showError('Network error loading cities: ' + error.message);
        }
    }

    populateCitySelect(cities) {
        const select = document.getElementById('citySelect');
        select.innerHTML = '<option value="">Choose a city...</option>';
        
        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city.city;
            option.textContent = `${city.city} (${city.country})`;
            select.appendChild(option);
        });
    }

    setupEventListeners() {
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.handleAnalysis();
        });

        // Custom city toggle
        document.getElementById('useCustomCity').addEventListener('change', (e) => {
            this.toggleCustomCityInput(e.target.checked);
        });

        // City select change
        document.getElementById('citySelect').addEventListener('change', (e) => {
            if (e.target.value) {
                document.getElementById('useCustomCity').checked = false;
                this.toggleCustomCityInput(false);
            }
        });

        // Form validation on input
        document.getElementById('customCity').addEventListener('input', this.validateForm.bind(this));
        document.getElementById('startDate').addEventListener('change', this.validateForm.bind(this));
        document.getElementById('endDate').addEventListener('change', this.validateForm.bind(this));

        // Export data button
        document.getElementById('exportData').addEventListener('click', () => {
            this.exportData();
        });

        // Download chart buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.download-chart')) {
                const button = e.target.closest('.download-chart');
                const chartId = button.getAttribute('data-chart');
                this.downloadChart(chartId);
            }
        });
    }

    setupExportFunctionality() {
        // This will be used by exportData method
    }

    toggleCustomCityInput(showCustom) {
        const customCitySection = document.getElementById('customCitySection');
        const citySelect = document.getElementById('citySelect');
        
        if (showCustom) {
            customCitySection.style.display = 'block';
            citySelect.value = '';
            citySelect.disabled = true;
        } else {
            customCitySection.style.display = 'none';
            document.getElementById('customCity').value = '';
            citySelect.disabled = false;
        }
        this.validateForm();
    }

    setupFormValidation() {
        this.validateForm();
    }

    validateForm() {
        const useCustomCity = document.getElementById('useCustomCity').checked;
        const customCity = document.getElementById('customCity').value.trim();
        const selectedCity = document.getElementById('citySelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const analyzeBtn = document.getElementById('analyzeBtn');

        let isValid = true;
        let errorMessage = '';

        // Validate city selection
        if (!useCustomCity && !selectedCity) {
            isValid = false;
            errorMessage = 'Please select a city or use custom city input';
        } else if (useCustomCity && !customCity) {
            isValid = false;
            errorMessage = 'Please enter a custom city name';
        }

        // Validate date range
        if (!startDate || !endDate) {
            isValid = false;
            errorMessage = 'Please select both start and end dates';
        } else if (new Date(startDate) > new Date(endDate)) {
            isValid = false;
            errorMessage = 'Start date cannot be after end date';
        }

        // Update button state
        analyzeBtn.disabled = !isValid;
        analyzeBtn.title = isValid ? 'Generate comprehensive weather analysis' : errorMessage;

        // Visual feedback
        if (isValid) {
            analyzeBtn.style.opacity = '1';
            analyzeBtn.style.cursor = 'pointer';
        } else {
            analyzeBtn.style.opacity = '0.6';
            analyzeBtn.style.cursor = 'not-allowed';
        }

        return isValid;
    }

    setDefaultDates() {
        const today = new Date();
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        document.getElementById('startDate').value = oneYearAgo.toISOString().split('T')[0];
        document.getElementById('endDate').value = today.toISOString().split('T')[0];
        this.validateForm();
    }

    async handleAnalysis() {
        if (!this.validateForm()) {
            return;
        }

        const useCustomCity = document.getElementById('useCustomCity').checked;
        const customCity = document.getElementById('customCity').value.trim();
        const selectedCity = document.getElementById('citySelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        const city = useCustomCity ? customCity : selectedCity;

        this.showLoading();
        
        try {
            const response = await fetch(`/api/weather-data?city=${encodeURIComponent(city)}&start_date=${startDate}&end_date=${endDate}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data);
            } else {
                this.showError('Failed to load weather data: ' + data.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayResults(data) {
        this.currentData = data;
        this.currentPage = 1;
        
        // Update UI
        document.getElementById('resultsTitle').textContent = `Weather Analysis: ${data.city}`;
        document.getElementById('resultsSection').style.display = 'block';
        
        // Show summary with source info
        this.displaySummary(data.summary, data.source);
        
        // Initialize and update charts
        if (window.weatherCharts) {
            setTimeout(() => {
                window.weatherCharts.updateCharts(data);
                setTimeout(() => {
                    if (window.weatherCharts.resizeCharts) {
                        window.weatherCharts.resizeCharts();
                    }
                }, 500);
            }, 100);
        }
        
        // Populate data table
        this.populateDataTable(data.data);
        
        // Scroll to results
        setTimeout(() => {
            document.getElementById('resultsSection').scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }, 300);
    }

    displaySummary(summary, source) {
        const summaryDiv = document.getElementById('dataSummary');
        summaryDiv.innerHTML = `
            <div class="data-source">
                <span class="source-badge">${source === 'database' ? '📁 Local Database' : '🌐 Open-Meteo API'}</span>
            </div>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="summary-value">${summary.total_days}</span>
                    <span class="summary-label">Total Days Analyzed</span>
                </div>
                <div class="summary-item">
                    <span class="summary-value">${summary.avg_max_temp}°C</span>
                    <span class="summary-label">Average Max Temp</span>
                </div>
                <div class="summary-item">
                    <span class="summary-value">${summary.avg_min_temp}°C</span>
                    <span class="summary-label">Average Min Temp</span>
                </div>
                <div class="summary-item">
                    <span class="summary-value">${summary.total_rainfall}mm</span>
                    <span class="summary-label">Total Rainfall</span>
                </div>
                <div class="summary-item">
                    <span class="summary-value">${summary.rainy_days}</span>
                    <span class="summary-label">Rainy Days</span>
                </div>
                <div class="summary-item">
                    <span class="summary-value">${summary.avg_sunshine}h</span>
                    <span class="summary-label">Avg Sunshine</span>
                </div>
            </div>
        `;
    }

    // NEW: Remove duplicate data entries
    removeDuplicateData(data) {
        const uniqueData = [];
        const seenDates = new Set();
        
        data.forEach(row => {
            // Create a normalized date key (remove time component for daily data)
            const dateObj = new Date(row.date);
            const dateKey = dateObj.toISOString().split('T')[0]; // YYYY-MM-DD format
            
            if (!seenDates.has(dateKey)) {
                seenDates.add(dateKey);
                uniqueData.push(row);
            } else {
                console.log('Removed duplicate entry for date:', dateKey);
            }
        });
        
        console.log(`Removed ${data.length - uniqueData.length} duplicate entries`);
        return uniqueData;
    }

    populateDataTable(data) {
        // Remove duplicates before displaying
        const uniqueData = this.removeDuplicateData(data);
        
        const tbody = document.getElementById('weatherTableBody');
        tbody.innerHTML = '';
        
        const totalPages = Math.ceil(uniqueData.length / this.rowsPerPage);
        const startIndex = (this.currentPage - 1) * this.rowsPerPage;
        const endIndex = Math.min(startIndex + this.rowsPerPage, uniqueData.length);
        
        const pageData = uniqueData.slice(startIndex, endIndex);
        
        pageData.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${this.formatDisplayDate(row.date)}</td>
                <td>${row.temperature_max !== null ? row.temperature_max.toFixed(1) : 'N/A'}</td>
                <td>${row.temperature_min !== null ? row.temperature_min.toFixed(1) : 'N/A'}</td>
                <td>${row.rain_sum !== null ? row.rain_sum.toFixed(1) : 'N/A'}</td>
                <td>${row.sunshine_duration !== null ? (row.sunshine_duration / 3600).toFixed(1) : 'N/A'}</td>
            `;
            tbody.appendChild(tr);
        });

        this.createPaginationControls(uniqueData.length, totalPages);
    }

    // NEW: Format date for better display
    formatDisplayDate(dateString) {
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return dateString;
            }
            return date.toLocaleDateString('en-US', {
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            console.warn('Error formatting display date:', dateString, error);
            return dateString;
        }
    }

    createPaginationControls(totalRecords, totalPages) {
        const existingPagination = document.getElementById('paginationControls');
        if (existingPagination) {
            existingPagination.remove();
        }

        const paginationDiv = document.createElement('div');
        paginationDiv.id = 'paginationControls';
        paginationDiv.className = 'pagination-controls';
        
        paginationDiv.innerHTML = `
            <div class="pagination-info">
                Showing ${((this.currentPage - 1) * this.rowsPerPage) + 1} to ${Math.min(this.currentPage * this.rowsPerPage, totalRecords)} of ${totalRecords} records
            </div>
            <div class="pagination-buttons">
                <button class="btn-pagination" id="firstPage" ${this.currentPage === 1 ? 'disabled' : ''}>
                    &laquo; First
                </button>
                <button class="btn-pagination" id="prevPage" ${this.currentPage === 1 ? 'disabled' : ''}>
                    &lsaquo; Previous
                </button>
                
                <span class="page-numbers">
                    Page ${this.currentPage} of ${totalPages}
                </span>
                
                <button class="btn-pagination" id="nextPage" ${this.currentPage === totalPages ? 'disabled' : ''}>
                    Next &rsaquo;
                </button>
                <button class="btn-pagination" id="lastPage" ${this.currentPage === totalPages ? 'disabled' : ''}>
                    Last &raquo;
                </button>
            </div>
        `;

        document.querySelector('.data-table').appendChild(paginationDiv);
        this.setupPaginationEventListeners();
    }

    setupPaginationEventListeners() {
        document.getElementById('firstPage').addEventListener('click', () => {
            this.goToPage(1);
        });

        document.getElementById('prevPage').addEventListener('click', () => {
            this.goToPage(this.currentPage - 1);
        });

        document.getElementById('nextPage').addEventListener('click', () => {
            this.goToPage(this.currentPage + 1);
        });

        document.getElementById('lastPage').addEventListener('click', () => {
            const totalPages = Math.ceil(this.currentData.data.length / this.rowsPerPage);
            this.goToPage(totalPages);
        });
    }

    goToPage(page) {
        if (page < 1 || page > Math.ceil(this.currentData.data.length / this.rowsPerPage)) {
            return;
        }
        
        this.currentPage = page;
        this.populateDataTable(this.currentData.data);
        
        document.querySelector('.data-table').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }

    exportData() {
        if (!this.currentData || !this.currentData.data) {
            this.showError('No data available to export');
            return;
        }

        try {
            // Remove duplicates before export
            const uniqueData = this.removeDuplicateData(this.currentData.data);
            
            // Convert data to CSV format
            const headers = ['Date', 'Max Temperature (°C)', 'Min Temperature (°C)', 'Rainfall (mm)', 'Sunshine (hours)'];
            const csvData = uniqueData.map(row => [
                row.date.split('T')[0], // Export only date part (YYYY-MM-DD)
                row.temperature_max !== null ? row.temperature_max.toFixed(1) : 'N/A',
                row.temperature_min !== null ? row.temperature_min.toFixed(1) : 'N/A',
                row.rain_sum !== null ? row.rain_sum.toFixed(1) : 'N/A',
                row.sunshine_duration !== null ? (row.sunshine_duration / 3600).toFixed(1) : 'N/A'
            ]);

            // Create CSV content
            let csvContent = headers.join(',') + '\n';
            csvContent += csvData.map(row => row.join(',')).join('\n');

            // Create and download file
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            const city = this.currentData.city.replace(/\s+/g, '_');
            const startDate = this.currentData.start_date;
            const endDate = this.currentData.end_date;
            
            link.setAttribute('href', url);
            link.setAttribute('download', `weather_data_${city}_${startDate}_to_${endDate}.csv`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showSuccess('Data exported successfully!');
            
        } catch (error) {
            this.showError('Failed to export data: ' + error.message);
        }
    }

    downloadChart(chartId) {
        if (!window.weatherCharts || !window.weatherCharts.charts[chartId.replace('Chart', '').toLowerCase()]) {
            this.showError('Chart not available for download');
            return;
        }

        try {
            const chart = window.weatherCharts.charts[chartId.replace('Chart', '').toLowerCase()];
            const canvas = document.getElementById(chartId);
            
            if (!canvas) {
                this.showError('Chart canvas not found');
                return;
            }

            // Create a temporary link for download
            const link = document.createElement('a');
            link.download = `${chartId}_${this.currentData.city}_${new Date().toISOString().split('T')[0]}.png`;
            link.href = canvas.toDataURL('image/png');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showSuccess('Chart downloaded successfully!');
            
        } catch (error) {
            this.showError('Failed to download chart: ' + error.message);
        }
    }

    showLoading() {
        document.getElementById('loadingSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = true;
        document.getElementById('analyzeBtn').innerHTML = '<span class="btn-icon">⏳</span>Processing Analysis...';
    }

    hideLoading() {
        document.getElementById('loadingSection').style.display = 'none';
        this.validateForm();
        document.getElementById('analyzeBtn').innerHTML = '<span class="btn-icon">📊</span>Generate Comprehensive Analysis';
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.innerHTML = `
            <div class="error-content">
                <span class="error-icon">⚠️</span>
                <span class="error-message">${message}</span>
                <button class="error-close">&times;</button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
        
        // Close button
        errorDiv.querySelector('.error-close').addEventListener('click', () => {
            errorDiv.parentNode.removeChild(errorDiv);
        });
        
        this.hideLoading();
    }

    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-notification';
        successDiv.innerHTML = `
            <div class="success-content">
                <span class="success-icon">✅</span>
                <span class="success-message">${message}</span>
                <button class="success-close">&times;</button>
            </div>
        `;
        
        document.body.appendChild(successDiv);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 3000);
        
        // Close button
        successDiv.querySelector('.success-close').addEventListener('click', () => {
            successDiv.parentNode.removeChild(successDiv);
        });
    }
}

// Initialize app when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.weatherApp = new WeatherApp();
});