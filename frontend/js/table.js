/**
 * DataTable - A wrapper class for Tabulator table library
 * Provides a simplified interface for creating tables with built-in formatters
 */

class DataTable {
    /**
     * Create a new DataTable instance
     * @param {string|HTMLElement} container - The container element or selector for the table
     * @param {Object} options - Configuration options
     */
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = options;
        this.table = null;
        this.formatters = this.createFormatters();
    }

    /**
     * Create custom formatters for different data types
     * @returns {Object} Object containing formatter functions
     */
    createFormatters() {
        return {
            plaintext: (cell) => {
                const value = cell.getValue();
                return value !== null && value !== undefined ? String(value) : '';
            },

            datetime: (cell) => {
                const value = cell.getValue();
                if (!value) return '';
                try {
                    // Ensure the datetime string is treated as UTC
                    let utcString = value;
                    if (!value.endsWith('Z') && !value.match(/[+-]\d{2}:\d{2}$/)) {
                        utcString = value + 'Z';
                    }
                    // Parse as UTC and convert to local timezone
                    const date = new Date(utcString);
                    return date.toLocaleString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: true
                    });
                } catch (e) {
                    return String(value);
                }
            },

            date: (cell) => {
                const value = cell.getValue();
                if (!value) return '';
                try {
                    // Ensure the datetime string is treated as UTC
                    let utcString = value;
                    if (!value.endsWith('Z') && !value.match(/[+-]\d{2}:\d{2}$/)) {
                        utcString = value + 'Z';
                    }
                    // Parse as UTC and convert to local timezone
                    const date = new Date(utcString);
                    return date.toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                    });
                } catch (e) {
                    return String(value);
                }
            },

            boolean: (cell) => {
                const value = cell.getValue();
                const span = document.createElement('span');
                if (value === true || value === 'true') {
                    span.className = 'text-green-600 font-medium';
                    span.textContent = 'Yes';
                } else if (value === false || value === 'false') {
                    span.className = 'text-gray-400';
                    span.textContent = 'No';
                } else {
                    return '';
                }
                return span;
            },

            badge: (cell) => {
                const value = cell.getValue();
                if (!value) return '';

                // Color mapping for common values
                const colorMap = {
                    'admin': 'bg-purple-100 text-purple-800',
                    'user': 'bg-blue-100 text-blue-800',
                    'active': 'bg-green-100 text-green-800',
                    'inactive': 'bg-gray-100 text-gray-800',
                    'pending': 'bg-yellow-100 text-yellow-800',
                };

                const colorClass = colorMap[String(value).toLowerCase()] || 'bg-gray-100 text-gray-800';
                const span = document.createElement('span');
                span.className = `px-2 py-1 rounded text-xs font-medium ${colorClass}`;
                span.textContent = value;
                return span;
            },

            email: (cell) => {
                const value = cell.getValue();
                if (!value) return '';
                const link = document.createElement('a');
                link.href = `mailto:${value}`;
                link.className = 'text-blue-600 hover:underline';
                link.textContent = value;
                return link;
            },

            link: (cell) => {
                const value = cell.getValue();
                if (!value) return '';
                const link = document.createElement('a');
                link.href = value;
                link.target = '_blank';
                link.className = 'text-blue-600 hover:underline';
                link.textContent = 'Link →';
                return link;
            },

            money: (cell) => {
                const value = cell.getValue();
                if (value === null || value === undefined) return '';
                try {
                    const num = parseFloat(value);
                    return '$' + num.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
                } catch (e) {
                    return String(value);
                }
            }
        };
    }

    /**
     * Convert backend column config to Tabulator column format
     * @param {Object} columnConfig - Column configuration from backend
     * @returns {Object} Tabulator column definition
     */
    convertColumnConfig(columnConfig) {
        const column = {
            field: columnConfig.field,
            title: columnConfig.label,
            sorter: columnConfig.sortable ? 'string' : undefined,
            headerSort: columnConfig.sortable || false,
        };

        // Add width if specified
        if (columnConfig.width) {
            column.width = columnConfig.width;
        }

        // Add formatter
        if (columnConfig.formatter) {
            // Check if formatter is a function (custom formatter)
            if (typeof columnConfig.formatter === 'function') {
                column.formatter = columnConfig.formatter;
            }
            // Otherwise, look it up in the predefined formatters
            else if (this.formatters[columnConfig.formatter]) {
                column.formatter = columnConfig.formatter === 'plaintext' ? 'plaintext' : this.formatters[columnConfig.formatter];
            }
        }

        // Add header filter if enabled
        if (this.options.headerFilter && columnConfig.filterable !== false) {
            // Only add header filter if formatter is a string (not a custom function)
            const formatterType = typeof columnConfig.formatter === 'string' ? columnConfig.formatter : 'input';
            column.headerFilter = this.getHeaderFilterType(formatterType);
            column.headerFilterPlaceholder = `Filter ${columnConfig.label}...`;
        }

        return column;
    }

    /**
     * Get appropriate header filter type based on formatter
     * @param {string} formatter - The formatter type
     * @returns {string} Header filter type
     */
    getHeaderFilterType(formatter) {
        const filterMap = {
            'boolean': 'tickCross',
            'date': 'input',
            'datetime': 'input',
            'badge': 'input',
            'email': 'input',
            'money': 'number',
        };
        return filterMap[formatter] || 'input';
    }

    /**
     * Initialize the table with data and configuration
     * @param {Array} data - Array of data objects
     * @param {Object} config - Table configuration from backend
     */
    init(data, config) {
        if (!this.container) {
            console.error('DataTable: Container element not found');
            return;
        }

        // Convert backend column configs to Tabulator format
        const columns = config.visible_columns.map(col => this.convertColumnConfig(col));

        // Build Tabulator options with modern styling
        const tabulatorOptions = {
            data: data,
            columns: columns,
            layout: 'fitDataFill',
            pagination: true,
            paginationSize: this.options.pageSize || 20,
            paginationSizeSelector: [10, 20, 50, 100],
            paginationCounter: 'rows',
            responsiveLayout: 'collapse',
            movableColumns: true,
            resizableColumnFit: true,
            height: '100%',
            placeholder: 'No data available',
            tooltips: true,
            headerSortTristate: true,
            ...this.options.tabulatorOptions
        };

        // Add initial sort if specified in config
        if (config.default_sort) {
            tabulatorOptions.initialSort = [{
                column: config.default_sort.field,
                dir: config.default_sort.dir
            }];
        }

        // Initialize Tabulator
        this.table = new Tabulator(this.container, tabulatorOptions);

        return this.table;
    }

    /**
     * Load data into the table
     * @param {Array} data - Array of data objects
     */
    setData(data) {
        if (this.table) {
            this.table.setData(data);
        }
    }

    /**
     * Refresh table data
     */
    refresh() {
        if (this.table) {
            this.table.redraw(true);
        }
    }

    /**
     * Get selected rows
     * @returns {Array} Array of selected row data
     */
    getSelectedData() {
        if (this.table) {
            return this.table.getSelectedData();
        }
        return [];
    }

    /**
     * Clear the table
     */
    clear() {
        if (this.table) {
            this.table.clearData();
        }
    }

    /**
     * Set a filter on the table
     * @param {string} field - Field name to filter
     * @param {string} type - Filter type (like, =, >, <, etc.)
     * @param {*} value - Value to filter by
     */
    setFilter(field, type, value) {
        if (this.table) {
            this.table.setFilter(field, type, value);
        }
    }

    /**
     * Add a filter to existing filters
     * @param {string} field - Field name to filter
     * @param {string} type - Filter type (like, =, >, <, etc.)
     * @param {*} value - Value to filter by
     */
    addFilter(field, type, value) {
        if (this.table) {
            this.table.addFilter(field, type, value);
        }
    }

    /**
     * Clear all filters
     */
    clearFilter() {
        if (this.table) {
            this.table.clearFilter();
        }
    }

    /**
     * Search across all columns
     * @param {string} searchTerm - Term to search for
     */
    search(searchTerm) {
        if (this.table) {
            if (!searchTerm || searchTerm.trim() === '') {
                this.table.clearFilter();
                return;
            }

            // Get all columns
            const columns = this.table.getColumns();
            const filters = [];

            // Create OR filter across all searchable columns
            columns.forEach(column => {
                const field = column.getField();
                if (field && field !== 'actions') { // Skip action columns
                    filters.push({
                        field: field,
                        type: 'like',
                        value: searchTerm
                    });
                }
            });

            // Apply filters with OR logic
            this.table.setFilter([filters]);
        }
    }

    /**
     * Get current filters
     * @returns {Array} Current filters
     */
    getFilters() {
        if (this.table) {
            return this.table.getFilters();
        }
        return [];
    }

    /**
     * Destroy the table instance
     */
    destroy() {
        if (this.table) {
            this.table.destroy();
            this.table = null;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataTable;
}
