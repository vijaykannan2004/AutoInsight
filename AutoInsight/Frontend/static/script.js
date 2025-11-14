// ===== AutoInsight Dashboard - Enhanced Script =====

class AutoInsightApp {
    constructor() {
        this.currentDataId = null;
        this.analysisData = null;
        this.queryHistory = [];
        this.charts = [];
        this.uploadedFile = null;
        this.init();
    }

    async init() {
        console.log('🚗 AutoInsight App Initializing...');

        // Initialize theme
        AutoInsightUtils.initTheme();

        // Check service health
        await this.checkHealthStatus();

        // Set up event listeners
        this.setupEventListeners();

        // Load saved active tab
        this.loadActiveTab();

        console.log('✅ AutoInsight App Ready');
    }

    async checkHealthStatus() {
        try {
            const health = await AutoInsightUtils.checkServiceHealth();
            const statusBtn = document.getElementById('healthStatus');
            if (statusBtn) {
                if (health.healthy) {
                    statusBtn.innerHTML = '🟢 Connected';
                    statusBtn.className = 'btn btn-ghost';
                } else {
                    statusBtn.innerHTML = '🔴 Disconnected';
                    statusBtn.className = 'btn btn-danger';
                }
            }
        } catch (error) {
            console.log('Health check failed:', error);
        }
    }

    setupEventListeners() {
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => AutoInsightUtils.toggleTheme());
        }

        // Upload functionality
        this.setupUploadHandlers();

        // Analysis functionality
        this.setupAnalysisHandlers();

        // Visualization functionality
        this.setupVisualizationHandlers();

        // Query functionality
        this.setupQueryHandlers();

        // Export functionality
        this.setupExportHandlers();

        // Tab switching
        this.setupTabHandlers();

        // Help functions
        window.showHelp = () => this.showHelpModal();
        window.showAbout = () => this.showAboutModal();
        window.showPrivacy = () => this.showPrivacyModal();
    }

    setupUploadHandlers() {
        const uploadBox = document.getElementById('uploadBox');
        const fileInput = document.getElementById('csvFile');
        const browseBtn = document.getElementById('browseBtn');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const clearBtn = document.getElementById('clearBtn');

        if (uploadBox && fileInput) {
            // Drag and drop
            uploadBox.addEventListener('click', () => fileInput.click());

            uploadBox.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadBox.classList.add('drag-over');
            });

            uploadBox.addEventListener('dragleave', () => {
                uploadBox.classList.remove('drag-over');
            });

            uploadBox.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadBox.classList.remove('drag-over');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });

            // File input change
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelect(e.target.files[0]);
                }
            });
        }

        if (browseBtn) {
            browseBtn.addEventListener('click', () => fileInput.click());
        }

        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzeDataset());
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearUpload());
        }
    }

    handleFileSelect(file) {
        const validation = AutoInsightUtils.validateCSVFile(file);

        if (!validation.isValid) {
            AutoInsightUtils.showNotification(validation.errors.join(', '), 'error');
            return;
        }

        this.uploadedFile = file;
        const uploadOptions = document.getElementById('uploadOptions');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');

        if (uploadOptions && fileName && fileSize) {
            uploadOptions.style.display = 'block';
            fileName.textContent = file.name;
            fileSize.textContent = AutoInsightUtils.formatFileSize(file.size);
        }
    }

    async analyzeDataset() {
        if (!this.uploadedFile) {
            AutoInsightUtils.showNotification('Please select a file first', 'warning');
            return;
        }

        const enhancedAnalysis = document.getElementById('enhancedAnalysis').checked;
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        // Show progress
        if (progressContainer && progressBar && progressText) {
            progressContainer.style.display = 'block';
            progressBar.style.width = '0%';
            progressText.textContent = 'Uploading file...';
        }

        try {
            // Simulate progress
            const progressInterval = setInterval(() => {
                const currentWidth = parseFloat(progressBar.style.width) || 0;
                if (currentWidth < 90) {
                    progressBar.style.width = (currentWidth + 10) + '%';
                    progressText.textContent = 'Processing your data...';
                }
            }, 200);

            const result = await AutoInsightUtils.uploadFile(this.uploadedFile, enhancedAnalysis);

            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            progressText.textContent = 'Analysis complete!';

            setTimeout(() => {
                progressContainer.style.display = 'none';

                if (result.status === 'success') {
                    this.currentDataId = result.data_id;
                    this.analysisData = result;
                    AutoInsightUtils.showNotification('Dataset analyzed successfully!', 'success');

                    // Auto-switch to analysis tab
                    if (enhancedAnalysis) {
                        AutoInsightUtils.switchTab('analysis');
                        this.displayAnalysisResults(result);
                    } else {
                        this.displayBasicResults(result);
                    }
                } else {
                    AutoInsightUtils.showNotification(`Analysis failed: ${result.detail}`, 'error');
                }
            }, 1000);
        } catch (error) {
            clearInterval(progressInterval);
            progressContainer.style.display = 'none';
            AutoInsightUtils.handleError(error, 'file analysis');
        }
    }

    clearUpload() {
        this.uploadedFile = null;
        const fileInput = document.getElementById('csvFile');
        const uploadOptions = document.getElementById('uploadOptions');

        if (fileInput) fileInput.value = '';
        if (uploadOptions) uploadOptions.style.display = 'none';

        AutoInsightUtils.showNotification('Upload cleared', 'info');
    }

    displayBasicResults(result) {
        const resultDiv = document.getElementById('result');
        if (!resultDiv) return;

        let aiInsightText = '';
        if (typeof result.ai_insights === 'string') {
            if (result.ai_insights.includes('API key expired')) {
                aiInsightText = '❌ AI key was expired — Please try again';
            } else {
                aiInsightText = result.ai_insights;
            }
        } else {
            aiInsightText = '⚠️ AI insights not available';
        }

        resultDiv.innerHTML = `
            <div class="analysis-card">
                <h3>📊 Dataset Summary</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <label>Rows</label>
                        <value>${result.cleaning_report.rows.toLocaleString()}</value>
                    </div>
                    <div class="stat-item">
                        <label>Columns</label>
                        <value>${result.cleaning_report.cols}</value>
                    </div>
                </div>

                <h3>🧠 AI Insights</h3>
                <div class="insights-content">
                    <p>${aiInsightText}</p>
                </div>

                <h3>📈 Correlations</h3>
                <div class="correlations-content">
                    ${this.formatCorrelations(result.cleaning_report.highly_correlated_pairs)}
                </div>
            </div>
        `;
    }

    formatCorrelations(correlations) {
        if (!correlations || correlations.length === 0) {
            return '<p>No strong correlations found</p>';
        }

        return correlations.slice(0, 5).map(corr => `
            <div class="correlation-item">
                <strong>${corr[0]}</strong> ↔ <strong>${corr[1]}</strong>
                <span class="corr-value">${corr[2].toFixed(3)}</span>
            </div>
        `).join('');
    }

    displayAnalysisResults(result) {
        const analysisContent = document.getElementById('analysisContent');
        if (!analysisContent) return;

        analysisContent.innerHTML = `
            <div class="analysis-grid">
                ${this.createDataOverviewCard(result)}
                ${this.createCleaningReportCard(result.cleaning_report)}
                ${this.createInsightsCard(result.insights)}
                ${this.createRecommendationsCard(result.insights)}
            </div>
        `;
    }

    createDataOverviewCard(result) {
        const { original_shape, cleaned_shape, data_preview } = result;

        return `
            <div class="analysis-card">
                <h3>📊 Data Overview</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <label>Original Rows</label>
                        <value>${original_shape[0].toLocaleString()}</value>
                    </div>
                    <div class="stat-item">
                        <label>Cleaned Rows</label>
                        <value>${cleaned_shape[0].toLocaleString()}</value>
                    </div>
                    <div class="stat-item">
                        <label>Columns</label>
                        <value>${data_preview.columns.length}</value>
                    </div>
                    <div class="stat-item">
                        <label>Reduction</label>
                        <value>${((original_shape[0] - cleaned_shape[0]) / original_shape[0] * 100).toFixed(1)}%</value>
                    </div>
                </div>

                <div class="data-types">
                    <h4>Column Types</h4>
                    <div class="type-distribution">
                        ${Object.entries(
                            data_preview.dtypes.reduce((acc, dtype) => {
                                acc[dtype] = (acc[dtype] || 0) + 1;
                                return acc;
                            }, {})
                        ).map(([type, count]) => `
                            <div class="type-item">
                                <span class="type-icon">${AutoInsightUtils.formatDataType(type)}</span>
                                <span class="type-count">${count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    createCleaningReportCard(cleaningReport) {
        const { cleaning_applied, cleaning_log } = cleaningReport;

        return `
            <div class="analysis-card">
                <h3>🧹 Cleaning Applied</h3>
                <div class="cleaning-stats">
                    ${Object.entries(cleaning_applied).map(([action, count]) => `
                        <div class="cleaning-item">
                            <label>${this.formatActionName(action)}</label>
                            <value>${count.toLocaleString()}</value>
                        </div>
                    `).join('')}
                </div>

                ${cleaning_log.length > 0 ? `
                    <h4>Actions Taken</h4>
                    <ul class="cleaning-log">
                        ${cleaning_log.slice(0, 5).map(log => `<li>${log}</li>`).join('')}
                        ${cleaning_log.length > 5 ? `<li>... and ${cleaning_log.length - 5} more</li>` : ''}
                    </ul>
                ` : ''}
            </div>
        `;
    }

    createInsightsCard(insights) {
        const { ai_generated_insights, business_insights } = insights;

        return `
            <div class="analysis-card">
                <h3>🧠 AI Insights</h3>

                ${ai_generated_insights.key_findings ? `
                    <div class="insight-section">
                        <h4>Key Findings</h4>
                        <ul class="insights-list">
                            ${ai_generated_insights.key_findings.map(finding => `<li>${finding}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${business_insights.insights ? `
                    <div class="insight-section">
                        <h4>Business Insights</h4>
                        <div class="business-insights">
                            ${business_insights.insights.map(insight => `
                                <div class="business-insight">
                                    <strong>${insight.category}</strong>
                                    <p>${insight.insight}</p>
                                    <span class="impact-badge badge-${insight.impact.toLowerCase()}">${insight.impact} Impact</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    createRecommendationsCard(insights) {
        const recommendations = insights.recommendations || [];

        return `
            <div class="analysis-card">
                <h3>💡 Recommendations</h3>
                <ul class="insights-list">
                    ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    formatActionName(action) {
        const actionNames = {
            'missing_values_handled': 'Missing Values',
            'duplicates_removed': 'Duplicates Removed',
            'outliers_removed': 'Outliers Removed',
            'data_types_converted': 'Type Conversions'
        };
        return actionNames[action] || action;
    }

    setupAnalysisHandlers() {
        // Additional analysis-specific handlers can be added here
    }

    setupVisualizationHandlers() {
        const chartTypeSelect = document.getElementById('chartTypeSelect');
        const xAxisSelect = document.getElementById('xAxisSelect');
        const yAxisSelect = document.getElementById('yAxisSelect');
        const colorSelect = document.getElementById('colorSelect');
        const createChartBtn = document.getElementById('createChartBtn');
        const autoChartsBtn = document.getElementById('autoChartsBtn');

        if (createChartBtn) {
            createChartBtn.addEventListener('click', () => this.createCustomChart());
        }

        if (autoChartsBtn) {
            autoChartsBtn.addEventListener('click', () => this.generateAutoCharts());
        }
    }

    async createCustomChart() {
        if (!this.currentDataId) {
            AutoInsightUtils.showNotification('No dataset loaded', 'warning');
            return;
        }

        const chartType = document.getElementById('chartTypeSelect').value;
        const xAxis = document.getElementById('xAxisSelect').value;
        const yAxis = document.getElementById('yAxisSelect').value;
        const colorBy = document.getElementById('colorSelect').value;

        if (!chartType) {
            AutoInsightUtils.showNotification('Please select a chart type', 'warning');
            return;
        }

        try {
            const chartConfig = {
                chart_type: chartType,
                x_column: xAxis,
                y_column: yAxis,
                color_column: colorBy || null
            };

            const result = await AutoInsightUtils.createChart(chartConfig, this.currentDataId);

            if (result.status === 'success') {
                this.addChartToContainer(result.chart);
                AutoInsightUtils.showNotification('Chart created successfully', 'success');
            } else {
                AutoInsightUtils.showNotification('Failed to create chart', 'error');
            }
        } catch (error) {
            AutoInsightUtils.handleError(error, 'chart creation');
        }
    }

    async generateAutoCharts() {
        if (!this.currentDataId) {
            AutoInsightUtils.showNotification('No dataset loaded', 'warning');
            return;
        }

        try {
            const result = await AutoInsightUtils.getChartRecommendations(this.currentDataId);

            if (result.status === 'success') {
                this.displayRecommendedCharts(result.recommendations);
                AutoInsightUtils.showNotification('Auto-charts generated', 'success');
            }
        } catch (error) {
            AutoInsightUtils.handleError(error, 'auto charts generation');
        }
    }

    displayRecommendedCharts(recommendations) {
        const chartsContainer = document.getElementById('chartsContainer');
        if (!chartsContainer) return;

        // Clear empty state
        chartsContainer.innerHTML = '';

        recommendations.forEach((rec, index) => {
            const chartId = `auto_chart_${index}`;
            const chartContainer = chartManager.createChartContainer({
                id: chartId,
                type: rec.type,
                title: rec.title,
                config: {} // Will be populated by backend
            }, chartsContainer);

            // Create chart with delay for smooth rendering
            setTimeout(async () => {
                try {
                    const result = await AutoInsightUtils.createChart({
                        chart_type: rec.type,
                        ...rec
                    }, this.currentDataId);

                    if (result.status === 'success') {
                        await chartManager.renderChart(`${chartId}-chart-content`, result.chart);
                        chartManager.hideLoading(`${chartId}-chart-content`);
                    }
                } catch (error) {
                    console.error('Failed to render chart:', error);
                    chartManager.hideLoading(`${chartId}-chart-content`);
                }
            }, index * 100);
        });
    }

    addChartToContainer(chart) {
        const chartsContainer = document.getElementById('chartsContainer');
        if (!chartsContainer) return;

        // Clear empty state
        const emptyState = chartsContainer.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }

        const chartContainer = chartManager.createChartContainer(chart, chartsContainer);

        // Render chart
        setTimeout(async () => {
            await chartManager.renderChart(`${chartContainer.id}-chart-content`, chart);
            chartManager.hideLoading(`${chartContainer.id}-chart-content`);
        }, 100);
    }

    setupQueryHandlers() {
        const queryInput = document.getElementById('queryInput');
        const submitQueryBtn = document.getElementById('submitQueryBtn');

        if (submitQueryBtn) {
            submitQueryBtn.addEventListener('click', () => this.submitQuery());
        }

        if (queryInput) {
            queryInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    e.preventDefault();
                    this.submitQuery();
                }
            });
        }
    }

    async submitQuery() {
        if (!this.currentDataId) {
            AutoInsightUtils.showNotification('No dataset loaded', 'warning');
            return;
        }

        const queryInput = document.getElementById('queryInput');
        const query = queryInput.value.trim();

        if (!query) {
            AutoInsightUtils.showNotification('Please enter a question', 'warning');
            return;
        }

        try {
            this.addToQueryHistory(query);

            const result = await AutoInsightUtils.queryData(query, this.currentDataId);

            if (result.status === 'success') {
                this.displayQueryResult(result.result);
                AutoInsightUtils.showNotification('Query processed successfully', 'success');
            } else {
                AutoInsightUtils.showNotification('Query failed', 'error');
            }
        } catch (error) {
            AutoInsightUtils.handleError(error, 'query processing');
        }
    }

    addToQueryHistory(query) {
        this.queryHistory.unshift(query);
        if (this.queryHistory.length > 10) {
            this.queryHistory = this.queryHistory.slice(0, 10);
        }

        this.updateQueryHistoryDisplay();
    }

    updateQueryHistoryDisplay() {
        const queryHistoryList = document.getElementById('queryHistoryList');
        if (!queryHistoryList) return;

        queryHistoryList.innerHTML = this.queryHistory.map((query, index) => `
            <div class="query-history-item" onclick="autoInsightApp.useHistoryQuery('${encodeURIComponent(query)}')">
                ${AutoInsightUtils.truncateText(query, 60)}
            </div>
        `).join('');
    }

    useHistoryQuery(encodedQuery) {
        const queryInput = document.getElementById('queryInput');
        if (queryInput) {
            queryInput.value = decodeURIComponent(encodedQuery);
        }
    }

    displayQueryResult(result) {
        const queryResults = document.getElementById('queryResults');
        if (!queryResults) return;

        const { answer, evidence, visualization_suggestion, confidence } = result.response || {};

        queryResults.innerHTML = `
            <div class="query-result-card">
                <div class="query-answer">
                    <h4>Answer</h4>
                    <p>${answer || 'No answer available'}</p>
                    <div class="confidence-indicator">
                        <span class="confidence-badge badge-${confidence?.toLowerCase() || 'medium'}">
                            ${confidence || 'Unknown'} Confidence
                        </span>
                    </div>
                </div>

                ${evidence && Object.keys(evidence).length > 0 ? `
                    <div class="query-evidence">
                        <h4>Evidence</h4>
                        <div class="evidence-content">
                            ${typeof evidence === 'string' ? evidence : JSON.stringify(evidence, null, 2)}
                        </div>
                    </div>
                ` : ''}

                ${visualization_suggestion ? `
                    <div class="viz-suggestion">
                        <h4>Visualization Suggestion</h4>
                        <button class="btn btn-primary btn-sm" onclick="autoInsightApp.createSuggestedChart(${JSON.stringify(visualization_suggestion).replace(/"/g, '&quot;')})">
                            📊 Create ${visualization_suggestion.type} Chart
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }

    async createSuggestedChart(suggestion) {
        try {
            const result = await AutoInsightUtils.createChart(suggestion, this.currentDataId);

            if (result.status === 'success') {
                AutoInsightUtils.switchTab('visualization');
                this.addChartToContainer(result.chart);
            }
        } catch (error) {
            AutoInsightUtils.handleError(error, 'suggested chart creation');
        }
    }

    setupExportHandlers() {
        const exportDataBtn = document.getElementById('exportDataBtn');
        const exportChartsBtn = document.getElementById('exportChartsBtn');
        const exportReportBtn = document.getElementById('exportReportBtn');

        if (exportDataBtn) {
            exportDataBtn.addEventListener('click', () => this.exportData());
        }

        if (exportChartsBtn) {
            exportChartsBtn.addEventListener('click', () => this.exportCharts());
        }

        if (exportReportBtn) {
            exportReportBtn.addEventListener('click', () => this.exportReport());
        }
    }

    async exportData() {
        if (!this.currentDataId) {
            AutoInsightUtils.showNotification('No dataset loaded', 'warning');
            return;
        }

        const format = document.getElementById('dataExportFormat').value;

        try {
            await AutoInsightUtils.exportData(format, this.currentDataId);
        } catch (error) {
            AutoInsightUtils.handleError(error, 'data export');
        }
    }

    async exportCharts() {
        if (!this.currentDataId || !chartManager.getChartList().length) {
            AutoInsightUtils.showNotification('No charts to export', 'warning');
            return;
        }

        const format = document.getElementById('chartExportFormat').value;
        const chartConfigs = chartManager.getChartList();

        try {
            await AutoInsightUtils.exportChart(chartConfigs, format, this.currentDataId);
        } catch (error) {
            AutoInsightUtils.handleError(error, 'chart export');
        }
    }

    async exportReport() {
        if (!this.currentDataId) {
            AutoInsightUtils.showNotification('No dataset loaded', 'warning');
            return;
        }

        const format = document.getElementById('reportExportFormat').value;

        try {
            await AutoInsightUtils.generateReport(format, this.currentDataId);
        } catch (error) {
            AutoInsightUtils.handleError(error, 'report generation');
        }
    }

    setupTabHandlers() {
        // Tab switching is handled by AutoInsightUtils.switchTab()
    }

    loadActiveTab() {
        const activeTab = AutoInsightUtils.getActiveTab();
        if (activeTab) {
            AutoInsightUtils.switchTab(activeTab);
        }
    }

    showHelpModal() {
        this.showModal('Help', `
            <h3>📚 How to Use AutoInsight</h3>
            <div class="help-content">
                <h4>Getting Started</h4>
                <ol>
                    <li>Upload a CSV file using the upload interface</li>
                    <li>Choose between basic or enhanced analysis</li>
                    <li>Explore insights and visualizations</li>
                    <li>Ask questions about your data</li>
                    <li>Export your results</li>
                </ol>

                <h4>Tips</h4>
                <ul>
                    <li>Use enhanced analysis for comprehensive insights</li>
                    <li>Try natural language queries for specific questions</li>
                    <li>Export charts in multiple formats for presentations</li>
                </ul>
            </div>
        `);
    }

    showAboutModal() {
        this.showModal('About AutoInsight', `
            <h3>🚗 About AutoInsight</h3>
            <p><strong>Version:</strong> 2.0.0</p>
            <p><strong>Description:</strong> AI-Powered Data Analytics Platform</p>
            <p>AutoInsight makes data analysis simple, fast, and accessible without coding. Upload any CSV file and get instant insights with Google Gemini AI.</p>
            <p><strong>Features:</strong></p>
            <ul>
                <li>Advanced data cleaning and preprocessing</li>
                <li>AI-powered insights generation</li>
                <li>Interactive visualizations with Plotly.js</li>
                <li>Natural language querying</li>
                <li>Multiple export formats</li>
            </ul>
        `);
    }

    showPrivacyModal() {
        this.showModal('Privacy Policy', `
            <h3>🔒 Privacy Policy</h3>
            <p><strong>Data Privacy:</strong></p>
            <ul>
                <li>Your data is processed locally and not stored permanently</li>
                <li>CSV files are temporarily stored in memory during analysis</li>
                <li>No data is shared with third parties without consent</li>
                <li>All temporary data is cleared when you close the browser</li>
            </ul>

            <p><strong>AI Processing:</strong></p>
            <p>Queries and insights are processed using Google Gemini API. Your data is sent to Google's servers only when you use AI features.</p>

            <p><strong>Your Rights:</strong></p>
            <ul>
                <li>Right to access your data</li>
                <li>Right to delete your data</li>
                <li>Right to export your data at any time</li>
                <li>Right to opt-out of AI features</li>
            </ul>
        `);
    }

    showModal(title, content) {
        // Simple modal implementation
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${title}</h2>
                    <button class="modal-close" onclick="this.parentElement.parentElement.parentElement.remove()">✕</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="this.parentElement.parentElement.parentElement.remove()">Close</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Add show class for animation
        setTimeout(() => modal.classList.add('active'), 10);

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.autoInsightApp = new AutoInsightApp();
    window.autoInsight = window.autoInsightApp; // Backward compatibility
});
