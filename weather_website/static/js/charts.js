class WeatherCharts {
    constructor() {
        this.charts = {};
        this.currentData = null;
        this.isInitialized = false;
    }

    // Initialize all charts
    initCharts() {
        if (this.isInitialized) {
            this.destroyCharts();
        }

        // Wait a bit for DOM to be fully ready and containers to have dimensions
        setTimeout(() => {
            this.createTemperatureChart();
            this.createRainfallChart();
            this.createSeasonalChart();
            this.createExtremeChart();
            this.isInitialized = true;
            console.log("✅ All charts initialized");
        }, 100);
    }

    // Destroy existing charts to prevent memory leaks
    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    // Check if canvas element is ready and has dimensions
    isCanvasReady(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element not found: ${canvasId}`);
            return false;
        }
        
        const container = canvas.parentElement;
        if (container.offsetWidth === 0 || container.offsetHeight === 0) {
            console.warn(`Chart container for ${canvasId} has no dimensions`);
            return false;
        }
        
        return true;
    }

    // NEW: Remove duplicate data for charts
    removeDuplicateData(data) {
        const uniqueData = [];
        const seenDates = new Set();
        
        data.forEach(row => {
            const dateObj = new Date(row.date);
            const dateKey = dateObj.toISOString().split('T')[0]; // YYYY-MM-DD format
            
            if (!seenDates.has(dateKey)) {
                seenDates.add(dateKey);
                uniqueData.push(row);
            }
        });
        
        console.log(`Charts: Removed ${data.length - uniqueData.length} duplicate entries`);
        return uniqueData;
    }

    // Format date to "MMM YYYY" format (e.g., "Jan 2024")
    formatDateToMonthYear(dateString) {
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return dateString; // Return original if invalid date
            }
            return date.toLocaleDateString('en-US', { 
                month: 'short', 
                year: 'numeric' 
            });
        } catch (error) {
            console.warn('Error formatting date:', dateString, error);
            return dateString;
        }
    }

    // Group data by month and calculate averages
    groupDataByMonth(data, valueField) {
        // Remove duplicates before processing
        const uniqueData = this.removeDuplicateData(data);
        
        const monthlyData = {};
        
        uniqueData.forEach(row => {
            try {
                if (!row.date) return;
                
                const date = new Date(row.date);
                if (isNaN(date.getTime())) return;
                
                const monthKey = date.toLocaleDateString('en-US', { 
                    month: 'short', 
                    year: 'numeric' 
                });
                
                const value = parseFloat(row[valueField]);
                if (!isNaN(value)) {
                    if (!monthlyData[monthKey]) {
                        monthlyData[monthKey] = {
                            values: [],
                            count: 0
                        };
                    }
                    monthlyData[monthKey].values.push(value);
                    monthlyData[monthKey].count++;
                }
            } catch (error) {
                console.warn('Error processing row for monthly grouping:', error);
            }
        });

        // Calculate monthly averages and sort by date
        const result = Object.keys(monthlyData)
            .map(month => {
                const values = monthlyData[month].values;
                const avg = values.reduce((a, b) => a + b, 0) / values.length;
                return {
                    month: month,
                    average: parseFloat(avg.toFixed(1)),
                    count: monthlyData[month].count
                };
            })
            .sort((a, b) => {
                // Sort by date
                const dateA = new Date(a.month);
                const dateB = new Date(b.month);
                return dateA - dateB;
            });

        return result;
    }

    createTemperatureChart() {
        if (!this.isCanvasReady('temperatureChart')) return;
        
        const ctx = document.getElementById('temperatureChart').getContext('2d');
        this.charts.temperature = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Max Temperature (°C)',
                        data: [],
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.2,
                        fill: true,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#e74c3c',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2
                    },
                    {
                        label: 'Min Temperature (°C)',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.2,
                        fill: true,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#3498db',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 13,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 12
                        },
                        padding: 12,
                        cornerRadius: 6
                    },
                    title: {
                        display: true,
                        text: 'Monthly Temperature Trends',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: 20
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Month',
                            font: {
                                size: 13,
                                weight: 'bold'
                            },
                            padding: { top: 10, bottom: 10 }
                        },
                        ticks: {
                            maxTicksLimit: 12,
                            font: {
                                size: 11
                            },
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Temperature (°C)',
                            font: {
                                size: 13,
                                weight: 'bold'
                            },
                            padding: { top: 10, bottom: 10 }
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'nearest'
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    createRainfallChart() {
        if (!this.isCanvasReady('rainfallChart')) return;
        
        const ctx = document.getElementById('rainfallChart').getContext('2d');
        this.charts.rainfall = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Monthly Rainfall (mm)',
                    data: [],
                    backgroundColor: 'rgba(52, 152, 219, 0.8)',
                    borderColor: '#2980b9',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 13,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 12
                        },
                        padding: 12,
                        cornerRadius: 6,
                        callbacks: {
                            label: function(context) {
                                return `Rainfall: ${context.parsed.y} mm`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Monthly Rainfall Analysis',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: 20
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Month',
                            font: {
                                size: 13,
                                weight: 'bold'
                            },
                            padding: { top: 10, bottom: 10 }
                        },
                        ticks: {
                            maxTicksLimit: 12,
                            font: {
                                size: 11
                            },
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Rainfall (mm)',
                            font: {
                                size: 13,
                                weight: 'bold'
                            },
                            padding: { top: 10, bottom: 10 }
                        },
                        ticks: {
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return value + ' mm';
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    createSeasonalChart() {
        if (!this.isCanvasReady('seasonalChart')) return;
        
        const ctx = document.getElementById('seasonalChart').getContext('2d');
        this.charts.seasonal = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [
                    {
                        label: 'Avg Max Temp (°C)',
                        data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        backgroundColor: '#e74c3c',
                        borderColor: '#c0392b',
                        borderWidth: 1
                    },
                    {
                        label: 'Avg Min Temp (°C)',
                        data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        backgroundColor: '#3498db',
                        borderColor: '#2980b9',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    createExtremeChart() {
        if (!this.isCanvasReady('extremeChart')) return;
        
        const ctx = document.getElementById('extremeChart').getContext('2d');
        this.charts.extreme = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Hot Days (>30°C)', 'Cold Days (<10°C)', 'Rainy Days (>1mm)', 'Heavy Rain (>10mm)'],
                datasets: [{
                    label: 'Number of Days',
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#e74c3c',
                        '#3498db',
                        '#27ae60',
                        '#8e44ad'
                    ],
                    borderColor: [
                        '#c0392b',
                        '#2980b9',
                        '#229954',
                        '#7d3c98'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Days'
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    // Update charts with new data
    updateCharts(apiData) {
        this.currentData = apiData;
        const data = apiData.data;
        
        if (!data || data.length === 0) {
            console.warn('No data available for charts');
            return;
        }
        
        console.log('📊 Updating charts with', data.length, 'records');
        
        // Make sure charts are initialized
        if (!this.isInitialized) {
            this.initCharts();
        }
        
        // Wait a bit for charts to be ready before updating
        setTimeout(() => {
            this.updateTemperatureChart(data);
            this.updateRainfallChart(data);
            this.updateSeasonalChart(data);
            this.updateExtremeChart(data);
            console.log("✅ All charts updated");
        }, 200);
    }

    updateTemperatureChart(data) {
        if (!this.charts.temperature) return;
        
        try {
            // Group data by month for better readability
            const monthlyMaxTemps = this.groupDataByMonth(data, 'temperature_max');
            const monthlyMinTemps = this.groupDataByMonth(data, 'temperature_min');

            const labels = monthlyMaxTemps.map(item => item.month);
            const maxTemps = monthlyMaxTemps.map(item => item.average);
            const minTemps = monthlyMinTemps.map(item => item.average);

            console.log('📈 Temperature chart data:', {
                labels: labels,
                maxTemps: maxTemps,
                minTemps: minTemps
            });

            this.charts.temperature.data.labels = labels;
            this.charts.temperature.data.datasets[0].data = maxTemps;
            this.charts.temperature.data.datasets[1].data = minTemps;
            this.charts.temperature.update();
            
            console.log('✅ Temperature chart updated with monthly data');
            
        } catch (error) {
            console.error('Error updating temperature chart:', error);
        }
    }

    updateRainfallChart(data) {
        if (!this.charts.rainfall) return;
        
        try {
            // Group data by month for better readability
            const monthlyRainfall = this.groupDataByMonth(data, 'rain_sum');

            const labels = monthlyRainfall.map(item => item.month);
            const rainfall = monthlyRainfall.map(item => item.average);

            console.log('🌧️ Rainfall chart data:', {
                labels: labels,
                rainfall: rainfall
            });

            this.charts.rainfall.data.labels = labels;
            this.charts.rainfall.data.datasets[0].data = rainfall;
            this.charts.rainfall.update();
            
            console.log('✅ Rainfall chart updated with monthly data');
            
        } catch (error) {
            console.error('Error updating rainfall chart:', error);
        }
    }

    updateSeasonalChart(data) {
        if (!this.charts.seasonal) return;
        
        try {
            // Remove duplicates before processing
            const uniqueData = this.removeDuplicateData(data);
            
            // Group by month and calculate averages
            const monthlyData = {};
            
            uniqueData.forEach(row => {
                try {
                    if (!row.date) return;
                    
                    const date = new Date(row.date);
                    if (isNaN(date.getTime())) return;
                    
                    const month = date.getMonth(); // 0-11
                    
                    if (!monthlyData[month]) {
                        monthlyData[month] = { maxTemps: [], minTemps: [] };
                    }
                    
                    if (row.temperature_max !== null && !isNaN(row.temperature_max)) {
                        monthlyData[month].maxTemps.push(row.temperature_max);
                    }
                    if (row.temperature_min !== null && !isNaN(row.temperature_min)) {
                        monthlyData[month].minTemps.push(row.temperature_min);
                    }
                } catch (error) {
                    console.log('Error processing row for seasonal chart:', error);
                }
            });

            const avgMaxTemps = [];
            const avgMinTemps = [];
            
            for (let month = 0; month < 12; month++) {
                if (monthlyData[month] && monthlyData[month].maxTemps.length > 0) {
                    const avgMax = monthlyData[month].maxTemps.reduce((a, b) => a + b, 0) / monthlyData[month].maxTemps.length;
                    const avgMin = monthlyData[month].minTemps.reduce((a, b) => a + b, 0) / monthlyData[month].minTemps.length;
                    avgMaxTemps.push(parseFloat(avgMax.toFixed(1)));
                    avgMinTemps.push(parseFloat(avgMin.toFixed(1)));
                } else {
                    avgMaxTemps.push(0);
                    avgMinTemps.push(0);
                }
            }

            this.charts.seasonal.data.datasets[0].data = avgMaxTemps;
            this.charts.seasonal.data.datasets[1].data = avgMinTemps;
            this.charts.seasonal.update();
            
        } catch (error) {
            console.error('Error updating seasonal chart:', error);
        }
    }

    updateExtremeChart(data) {
        if (!this.charts.extreme) return;
        
        try {
            // Remove duplicates before processing
            const uniqueData = this.removeDuplicateData(data);
            
            const hotDays = uniqueData.filter(row => row.temperature_max > 30).length;
            const coldDays = uniqueData.filter(row => row.temperature_min < 10).length;
            const rainyDays = uniqueData.filter(row => row.rain_sum > 1).length;
            const heavyRainDays = uniqueData.filter(row => row.rain_sum > 10).length;

            this.charts.extreme.data.datasets[0].data = [hotDays, coldDays, rainyDays, heavyRainDays];
            this.charts.extreme.update();
            
        } catch (error) {
            console.error('Error updating extreme chart:', error);
        }
    }

    // Force resize of all charts (useful when making containers visible)
    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.resize();
            }
        });
    }
    
    getChartCanvas(chartName) {
        const chartId = chartName + 'Chart';
        return document.getElementById(chartId);
    }
}

// Initialize charts when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.weatherCharts = new WeatherCharts();
    console.log("✅ WeatherCharts instance created");
});