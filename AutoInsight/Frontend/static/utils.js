// ===== AutoInsight Utility Functions =====

class AutoInsightUtils {
    // API Configuration
    static API_BASE = 'http://127.0.0.1:8000';
    static DATA_ID_KEY = 'autoinsight_data_id';
    static ANALYSIS_CACHE_KEY = 'autoinsight_analysis_cache';

    // Theme Management
    static initTheme() {
        const savedTheme = localStorage.getItem('autoinsight_theme') || 'light';
        this.setTheme(savedTheme);
    }

    static setTheme(theme) {
        const body = document.body;
        const themeToggle = document.getElementById('themeToggle');

        if (theme === 'dark') {
            body.classList.add('dark-mode');
            if (themeToggle) {
                themeToggle.textContent = '☀️ Light Mode';
                themeToggle.title = 'Switch to light mode';
            }
        } else {
            body.classList.remove('dark-mode');
            if (themeToggle) {
                themeToggle.textContent = '🌙 Dark Mode';
                themeToggle.title = 'Switch to dark mode';
            }
        }

        localStorage.setItem('autoinsight_theme', theme);
    }

    static toggleTheme() {
        const currentTheme = localStorage.getItem('autoinsight_theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    // API Communication
    static async makeRequest(endpoint, options = {}) {
        const url = `${this.API_BASE}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    static async uploadFile(file, enhanced = false) {
        const formData = new FormData();
        formData.append('file', file);

        const endpoint = enhanced ? '/upload/enhanced' : '/upload';

        try {
            const response = await fetch(`${this.API_BASE}${endpoint}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.status === 'success') {
                this.setDataId(result.data_id);
                this.cacheAnalysis(result.data_id, result);
            }

            return result;
        } catch (error) {
            console.error('File upload failed:', error);
            throw error;
        }
    }

    static async queryData(query, dataId, context = {}) {
        try {
            return await this.makeRequest(`/query?data_id=${dataId}`, {
                method: 'POST',
                body: JSON.stringify({ query, context })
            });
        } catch (error) {
            console.error('Query failed:', error);
            throw error;
        }
    }

    static async createChart(chartConfig, dataId) {
        try {
            return await this.makeRequest(`/visualize?data_id=${dataId}`, {
                method: 'POST',
                body: JSON.stringify(chartConfig)
            });
        } catch (error) {
            console.error('Chart creation failed:', error);
            throw error;
        }
    }

    static async getChartRecommendations(dataId) {
        try {
            return await this.makeRequest(`/charts/recommendations/${dataId}`);
        } catch (error) {
            console.error('Failed to get chart recommendations:', error);
            throw error;
        }
    }

    static async exportData(format, dataId) {
        try {
            const result = await this.makeRequest(`/export/data?data_id=${dataId}`, {
                method: 'POST',
                body: JSON.stringify({ format })
            });

            if (result.status === 'success' && result.export) {
                this.downloadFile(
                    result.export.content,
                    result.export.filename,
                    result.export.content_type
                );
            }

            return result;
        } catch (error) {
            console.error('Data export failed:', error);
            throw error;
        }
    }

    static async exportChart(chartConfigs, format, dataId) {
        try {
            const result = await this.makeRequest(`/export/chart?data_id=${dataId}`, {
                method: 'POST',
                body: JSON.stringify({
                    format,
                    chart_configs: chartConfigs
                })
            });

            if (result.status === 'success') {
                result.exports.forEach((export, index) => {
                    if (!export.error) {
                        this.downloadFile(
                            export.content,
                            export.filename,
                            export.content_type
                        );
                    }
                });
            }

            return result;
        } catch (error) {
            console.error('Chart export failed:', error);
            throw error;
        }
    }

    static async generateReport(format, dataId) {
        try {
            const result = await this.makeRequest(`/export/report?data_id=${dataId}`, {
                method: 'POST',
                body: JSON.stringify({ format })
            });

            if (result.status === 'success' && result.export) {
                this.downloadFile(
                    result.export.content,
                    result.export.filename,
                    result.export.content_type
                );
            }

            return result;
        } catch (error) {
            console.error('Report generation failed:', error);
            throw error;
        }
    }

    // Data Management
    static setDataId(dataId) {
        localStorage.setItem(this.DATA_ID_KEY, dataId);
    }

    static getDataId() {
        return localStorage.getItem(this.DATA_ID_KEY);
    }

    static clearDataId() {
        localStorage.removeItem(this.DATA_ID_KEY);
        this.clearAnalysisCache();
    }

    static cacheAnalysis(dataId, analysisData) {
        const cache = this.getAnalysisCache();
        cache[dataId] = {
            ...analysisData,
            timestamp: Date.now()
        };
        localStorage.setItem(this.ANALYSIS_CACHE_KEY, JSON.stringify(cache));
    }

    static getAnalysisCache(dataId = null) {
        const cache = localStorage.getItem(this.ANALYSIS_CACHE_KEY);
        const parsedCache = cache ? JSON.parse(cache) : {};

        if (dataId) {
            return parsedCache[dataId];
        }

        return parsedCache;
    }

    static clearAnalysisCache() {
        localStorage.removeItem(this.ANALYSIS_CACHE_KEY);
    }

    // File Operations
    static downloadFile(content, filename, contentType) {
        try {
            const blob = this.base64ToBlob(content, contentType);
            const url = window.URL.createObjectURL(blob);

            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.style.display = 'none';

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Clean up
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('File download failed:', error);
        }
    }

    static base64ToBlob(base64, mimeType) {
        try {
            const byteCharacters = atob(base64);
            const byteNumbers = new Array(byteCharacters.length);

            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }

            const byteArray = new Uint8Array(byteNumbers);
            return new Blob([byteArray], { type: mimeType });
        } catch (error) {
            console.error('Base64 conversion failed:', error);
            throw error;
        }
    }

    // File Validation
    static validateCSVFile(file) {
        const validation = {
            isValid: true,
            errors: []
        };

        if (!file) {
            validation.isValid = false;
            validation.errors.push('No file selected');
            return validation;
        }

        // Check file type
        if (!file.name.toLowerCase().endsWith('.csv')) {
            validation.isValid = false;
            validation.errors.push('File must be a CSV file');
        }

        // Check file size (100MB limit)
        const maxSize = 100 * 1024 * 1024; // 100MB in bytes
        if (file.size > maxSize) {
            validation.isValid = false;
            validation.errors.push('File size exceeds 100MB limit');
        }

        return validation;
    }

    // UI Utilities
    static showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} notification`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
        `;

        notification.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                <span style="font-size: 1.2rem;">
                    ${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}
                </span>
                <div>
                    <strong>${this.capitalizeFirst(type)}:</strong>
                    <div>${message}</div>
                </div>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after duration
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    static showLoading(elementId, message = 'Loading...') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="loading-container" style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 2rem;
                ">
                    <div class="loading-spinner lg"></div>
                    <p style="margin-top: 1rem; color: #64748b;">${message}</p>
                </div>
            `;
        }
    }

    static hideLoading(elementId, content = '') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = content;
        }
    }

    // Data Formatting
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    static formatNumber(num) {
        if (num === null || num === undefined) return 'N/A';
        return num.toLocaleString();
    }

    static formatPercentage(num) {
        if (num === null || num === undefined) return 'N/A';
        return (num * 100).toFixed(1) + '%';
    }

    static formatDataType(dtype) {
        const typeMap = {
            'int64': 'Integer',
            'float64': 'Decimal',
            'object': 'Text',
            'bool': 'Boolean',
            'datetime64': 'Date/Time',
            'category': 'Category'
        };
        return typeMap[str(dtype)] || str(dtype);
    }

    static capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    static truncateText(text, maxLength = 50) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    // Tab Management
    static switchTab(tabId) {
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Remove active class from all tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });

        // Show selected tab content
        const selectedContent = document.getElementById(`${tabId}-content`);
        if (selectedContent) {
            selectedContent.classList.add('active');
        }

        // Add active class to selected tab
        const selectedTab = document.querySelector(`[data-tab="${tabId}"]`);
        if (selectedTab) {
            selectedTab.classList.add('active');
        }

        // Save active tab
        localStorage.setItem('autoinsight_active_tab', tabId);

        // Trigger chart resize if on visualization tab
        if (tabId === 'visualization') {
            setTimeout(() => {
                if (window.chartManager) {
                    window.chartManager.resizeAllCharts();
                }
            }, 100);
        }
    }

    static getActiveTab() {
        return localStorage.getItem('autoinsight_active_tab') || 'upload';
    }

    // Error Handling
    static handleError(error, context = '') {
        console.error(`Error in ${context}:`, error);

        let userMessage = 'An unexpected error occurred';

        if (error.message) {
            if (error.message.includes('Failed to fetch')) {
                userMessage = 'Cannot connect to the server. Please check your connection.';
            } else if (error.message.includes('404')) {
                userMessage = 'Requested resource not found.';
            } else if (error.message.includes('500')) {
                userMessage = 'Server error occurred. Please try again later.';
            } else {
                userMessage = error.message;
            }
        }

        this.showNotification(userMessage, 'error', 8000);
    }

    // Debounce utility
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

    // Check service health
    static async checkServiceHealth() {
        try {
            const response = await this.makeRequest('/health');
            return {
                healthy: response.status === 'healthy',
                services: response.services,
                apiKeyConfigured: response.api_key_configured
            };
        } catch (error) {
            return {
                healthy: false,
                error: error.message
            };
        }
    }

    // Get current dataset info
    static async getCurrentDatasetInfo() {
        const dataId = this.getDataId();
        if (!dataId) return null;

        try {
            const cache = this.getAnalysisCache(dataId);
            if (cache && cache.data) {
                return {
                    dataId,
                    ...cache.data,
                    fromCache: true
                };
            }

            const response = await this.makeRequest(`/data/${dataId}/preview`);
            if (response.status === 'success') {
                return {
                    dataId,
                    totalRows: response.total_rows,
                    columns: response.columns,
                    preview: response.data,
                    fromCache: false
                };
            }

            return null;
        } catch (error) {
            console.error('Failed to get dataset info:', error);
            return null;
        }
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .notification {
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        border-radius: 0.5rem;
        backdrop-filter: blur(8px);
    }
`;
document.head.appendChild(style);

// Export for global access
window.AutoInsightUtils = AutoInsightUtils;

// Initialize theme on load
document.addEventListener('DOMContentLoaded', () => {
    AutoInsightUtils.initTheme();
    console.log('🛠️ Utility module initialized');
});