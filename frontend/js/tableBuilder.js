/**
 * TableBuilder - Helper utilities for building tables from backend configurations
 */

/**
 * Build a table from a model configuration
 * @param {string|HTMLElement} container - Container element or selector for the table
 * @param {string} dataEndpoint - API endpoint to fetch table data from
 * @param {string} modelName - Name of the model (User, Organization, etc.)
 * @param {Object} options - Additional options for the DataTable
 * @returns {Promise<DataTable>} Promise that resolves to the initialized DataTable
 */
async function buildTableFromConfig(container, dataEndpoint, modelName, options = {}) {
    try {
        // Show loading state
        const containerEl = typeof container === 'string' ? document.querySelector(container) : container;
        if (containerEl) {
            containerEl.innerHTML = '<div class="text-center py-8 text-gray-500">Loading table...</div>';
        }

        // Fetch table configuration from backend
        const configResponse = await fetch(`/api/table-config/${modelName}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!configResponse.ok) {
            throw new Error(`Failed to fetch table configuration: ${configResponse.statusText}`);
        }

        const tableConfig = await configResponse.json();

        // Fetch table data
        const dataResponse = await fetch(dataEndpoint, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!dataResponse.ok) {
            throw new Error(`Failed to fetch table data: ${dataResponse.statusText}`);
        }

        const tableData = await dataResponse.json();

        // Clear loading state
        if (containerEl) {
            containerEl.innerHTML = '';
        }

        // Initialize DataTable
        const dataTable = new DataTable(container, options);
        dataTable.init(tableData, tableConfig);

        return dataTable;

    } catch (error) {
        console.error('Error building table:', error);

        // Show error state
        const containerEl = typeof container === 'string' ? document.querySelector(container) : container;
        if (containerEl) {
            containerEl.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    <p class="font-medium">Failed to load table</p>
                    <p class="text-sm mt-2">${error.message}</p>
                </div>
            `;
        }

        throw error;
    }
}

/**
 * Build a table with manual configuration (not from backend)
 * @param {string|HTMLElement} container - Container element or selector for the table
 * @param {Array} data - Array of data objects
 * @param {Array} columns - Array of column definitions
 * @param {Object} options - Additional options for the DataTable
 * @returns {DataTable} The initialized DataTable
 */
function buildTableManual(container, data, columns, options = {}) {
    const config = {
        visible_columns: columns,
        default_sort: options.defaultSort || null
    };

    const dataTable = new DataTable(container, options);
    dataTable.init(data, config);

    return dataTable;
}

/**
 * Refresh a table by fetching new data from an endpoint
 * @param {DataTable} dataTable - The DataTable instance to refresh
 * @param {string} dataEndpoint - API endpoint to fetch fresh data from
 * @returns {Promise<void>}
 */
async function refreshTable(dataTable, dataEndpoint) {
    try {
        const response = await fetch(dataEndpoint, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to refresh table data: ${response.statusText}`);
        }

        const data = await response.json();
        dataTable.setData(data);

    } catch (error) {
        console.error('Error refreshing table:', error);
        throw error;
    }
}

/**
 * Add action buttons to a Tabulator table column
 * @param {string} label - Column label
 * @param {Function} formatter - Custom formatter function that returns button HTML
 * @returns {Object} Column definition with action buttons
 */
function createActionColumn(label = 'Actions', formatter) {
    return {
        field: 'actions',
        label: label,
        visible: true,
        sortable: false,
        width: 150,
        formatter: formatter || function(cell) {
            return `
                <div class="flex gap-2">
                    <button class="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                    <button class="text-red-600 hover:text-red-800 text-sm">Delete</button>
                </div>
            `;
        }
    };
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        buildTableFromConfig,
        buildTableManual,
        refreshTable,
        createActionColumn
    };
}
