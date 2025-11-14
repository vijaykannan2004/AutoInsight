// ===== AutoInsight Chart Rendering Module =====

class ChartManager {
    constructor() {
        this.charts = new Map();
        this.isPlotlyLoaded = false;
        this.loadPlotly();
    }

    async loadPlotly() {
        if (this.isPlotlyLoaded) return;

        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.plot.ly/plotly-2.27.0.min.js';
            script.onload = () => {
                this.isPlotlyLoaded = true;
                console.log('✅ Plotly.js loaded successfully');
                resolve();
            };
            script.onerror = () => {
                console.error('❌ Failed to load Plotly.js');
                reject(new Error('Failed to load Plotly.js'));
            };
            document.head.appendChild(script);
        });
    }

    async renderChart(containerId, chartConfig) {
        if (!this.isPlotlyLoaded) {
            await this.loadPlotly();
        }

        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container with id '${containerId}' not found`);
        }

        try {
            const plotData = JSON.parse(chartConfig.config);

            // Customize Plotly configuration
            const layout = {
                ...plotData.layout,
                autosize: true,
                margin: { l: 50, r: 50, t: 80, b: 50 },
                font: {
                    family: "'Inter', system-ui, -apple-system, sans-serif"
                },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                modebar: {
                    orientation: 'v',
                    bgcolor: 'rgba(255,255,255,0.7)',
                    color: '#333',
                    activecolor: '#1e40af'
                }
            };

            const config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
                toImageButtonOptions: {
                    format: 'png',
                    filename: `autoinsight_${chartConfig.title.replace(/\s+/g, '_').toLowerCase()}`,
                    height: 600,
                    width: 1000,
                    scale: 2
                }
            };

            await Plotly.newPlot(containerId, plotData.data, layout, config, {responsive: true});

            this.charts.set(containerId, {
                id: chartConfig.id,
                type: chartConfig.type,
                title: chartConfig.title,
                config: plotData
            });

            return { success: true, chartId: chartConfig.id };
        } catch (error) {
            console.error('Error rendering chart:', error);
            return { success: false, error: error.message };
        }
    }

    updateChart(containerId, newData, updateLayout = {}) {
        const chart = this.charts.get(containerId);
        if (!chart) {
            throw new Error(`Chart in container '${containerId}' not found`);
        }

        try {
            const newData = {
                ...chart.config.data[0],
                ...newData
            };

            const newLayout = {
                ...chart.config.layout,
                ...updateLayout
            };

            Plotly.react(containerId, [newData], newLayout);

            // Update stored config
            chart.config.data[0] = newData;
            chart.config.layout = newLayout;

            return { success: true };
        } catch (error) {
            console.error('Error updating chart:', error);
            return { success: false, error: error.message };
        }
    }

    resizeChart(containerId) {
        if (this.charts.has(containerId)) {
            Plotly.Plots.resize(containerId);
        }
    }

    exportChart(containerId, format = 'png') {
        return new Promise((resolve, reject) => {
            if (!this.charts.has(containerId)) {
                reject(new Error(`Chart in container '${containerId}' not found`));
                return;
            }

            const chart = this.charts.get(containerId);

            try {
                Plotly.toImage(containerId, {
                    format: format,
                    width: 1200,
                    height: 600,
                    scale: 2
                }).then(imageData => {
                    resolve({
                        success: true,
                        data: imageData,
                        filename: `${chart.title.replace(/\s+/g, '_').toLowerCase()}.${format}`,
                        mimeType: format === 'png' ? 'image/png' : 'image/svg+xml'
                    });
                }).catch(error => {
                    reject(new Error(`Failed to export chart: ${error.message}`));
                });
            } catch (error) {
                reject(error);
            }
        });
    }

    destroyChart(containerId) {
        if (this.charts.has(containerId)) {
            Plotly.purge(containerId);
            this.charts.delete(containerId);
            return { success: true };
        }
        return { success: false, message: 'Chart not found' };
    }

    resizeAllCharts() {
        this.charts.forEach((chart, containerId) => {
            this.resizeChart(containerId);
        });
    }

    getChartList() {
        return Array.from(this.charts.entries()).map(([containerId, chart]) => ({
            containerId,
            id: chart.id,
            type: chart.type,
            title: chart.title
        }));
    }

    createChartContainer(chartConfig, parentContainer) {
        const container = document.createElement('div');
        container.id = `chart_${chartConfig.id}`;
        container.className = 'chart-container';
        container.style.cssText = `
            width: 100%;
            height: 500px;
            border-radius: 8px;
            overflow: hidden;
            position: relative;
        `;

        // Add loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'chart-loading';
        loadingIndicator.innerHTML = `
            <div class="loading-spinner lg"></div>
            <p style="margin-top: 1rem; color: #64748b;">Loading ${chartConfig.title}...</p>
        `;
        loadingIndicator.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: #f8fafc;
            z-index: 10;
        `;

        container.appendChild(loadingIndicator);

        // Add chart header
        const header = document.createElement('div');
        header.className = 'chart-header';
        header.innerHTML = `
            <h3 style="margin: 0; font-size: 1.125rem; font-weight: 600; color: #1e293b;">
                ${chartConfig.title}
            </h3>
            <div class="chart-actions">
                <button class="btn btn-sm btn-ghost" onclick="chartManager.exportChart('${container.id}', 'png')">
                    📷 PNG
                </button>
                <button class="btn btn-sm btn-ghost" onclick="chartManager.exportChart('${container.id}', 'svg')">
                    📊 SVG
                </button>
                <button class="btn btn-sm btn-ghost" onclick="chartManager.toggleFullscreen('${container.id}')">
                    🔍 Fullscreen
                </button>
            </div>
        `;
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            border-bottom: 1px solid #e2e8f0;
            background-color: #f8fafc;
        `;

        const chartContent = document.createElement('div');
        chartContent.className = 'chart-content';
        chartContent.style.cssText = `
            height: calc(100% - 80px);
            position: relative;
        `;

        container.appendChild(header);
        container.appendChild(chartContent);

        if (parentContainer) {
            parentContainer.appendChild(container);
        }

        return container;
    }

    async toggleFullscreen(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!document.fullscreenElement) {
            await container.requestFullscreen();
            container.style.cssText += `
                width: 100vw !important;
                height: 100vh !important;
                background-color: white;
            `;
            // Trigger resize after entering fullscreen
            setTimeout(() => this.resizeChart(containerId), 100);
        } else {
            await document.exitFullscreen();
            container.style.cssText = container.style.cssText.replace(/width: 100vw !important; height: 100vh !important; background-color: white;/, '');
            // Trigger resize after exiting fullscreen
            setTimeout(() => this.resizeChart(containerId), 100);
        }
    }

    hideLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            const loadingIndicator = container.querySelector('.chart-loading');
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        }
    }

    addChartFilters(containerId, filters) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const filtersContainer = document.createElement('div');
        filtersContainer.className = 'chart-filters';
        filtersContainer.style.cssText = `
            padding: 1rem;
            background-color: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        `;

        filters.forEach(filter => {
            const filterElement = this.createFilterElement(filter, containerId);
            filtersContainer.appendChild(filterElement);
        });

        // Insert filters after header
        const header = container.querySelector('.chart-header');
        if (header) {
            header.insertAdjacentElement('afterend', filtersContainer);
        }

        // Adjust chart content height
        const chartContent = container.querySelector('.chart-content');
        if (chartContent) {
            chartContent.style.height = 'calc(100% - 140px)';
        }
    }

    createFilterElement(filter, containerId) {
        const filterDiv = document.createElement('div');
        filterDiv.className = 'filter-group';
        filterDiv.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        `;

        const label = document.createElement('label');
        label.textContent = filter.label;
        label.style.cssText = `
            font-size: 0.875rem;
            font-weight: 500;
            color: #374151;
        `;

        let input;
        switch (filter.type) {
            case 'select':
                input = document.createElement('select');
                input.className = 'form-select';
                filter.options.forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option.value;
                    optionElement.textContent = option.label;
                    input.appendChild(optionElement);
                });
                break;

            case 'range':
                input = document.createElement('input');
                input.type = 'range';
                input.className = 'form-range';
                input.min = filter.min;
                input.max = filter.max;
                input.step = filter.step || 1;
                input.value = filter.default;
                break;

            case 'text':
                input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-input';
                input.placeholder = filter.placeholder || 'Filter...';
                break;
        }

        if (input) {
            input.style.cssText = `
                padding: 0.5rem;
                border: 1px solid #d1d5db;
                border-radius: 0.375rem;
                font-size: 0.875rem;
            `;

            input.addEventListener('change', (e) => {
                if (filter.onChange) {
                    filter.onChange(e.target.value, containerId);
                }
            });
        }

        filterDiv.appendChild(label);
        if (input) filterDiv.appendChild(input);

        return filterDiv;
    }
}

// Utility functions for chart operations
class ChartUtils {
    static getChartTypeIcon(chartType) {
        const icons = {
            'scatter': '📊',
            'bar': '📊',
            'histogram': '📊',
            'line': '📈',
            'pie': '🥧',
            'heatmap': '🔥',
            'box': '📦',
            'violin': '🎻',
            'correlation': '🔗'
        };
        return icons[chartType] || '📊';
    }

    static formatChartTitle(title) {
        return title.replace(/([A-Z])/g, ' $1').trim();
    }

    static getColorPalette() {
        return [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
            '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1',
            '#14b8a6', '#22c55e', '#eab308', '#dc2626', '#a855f7'
        ];
    }

    static createResponsiveConfig(chartConfig) {
        return {
            ...chartConfig,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    cornerRadius: 6,
                    displayColors: true,
                    padding: 12
                }
            }
        };
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static formatNumber(num) {
        if (num === null || num === undefined) return 'N/A';
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toLocaleString();
    }

    static formatPercentage(num) {
        if (num === null || num === undefined) return 'N/A';
        return (num * 100).toFixed(1) + '%';
    }
}

// Initialize global chart manager
const chartManager = new ChartManager();

// Handle window resize events
const debouncedResize = ChartUtils.debounce(() => {
    chartManager.resizeAllCharts();
}, 250);

window.addEventListener('resize', debouncedResize);

// Export for global access
window.ChartManager = ChartManager;
window.ChartUtils = ChartUtils;
window.chartManager = chartManager;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Chart module initialized');
});