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

/**
 * Create a search input element for a table
 * @param {DataTable} dataTable - The DataTable instance to attach search to
 * @param {Object} options - Configuration options
 * @returns {HTMLElement} Search input element
 */
function createSearchInput(dataTable, options = {}) {
    const container = document.createElement('div');
    container.className = options.containerClass || 'mb-4';

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = options.placeholder || 'Search...';
    input.className = options.inputClass || 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent';

    // Debounce search for better performance
    let debounceTimer;
    input.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            dataTable.search(e.target.value);
        }, options.debounce || 300);
    });

    container.appendChild(input);
    return container;
}

/**
 * Add a search input above a table
 * @param {string|HTMLElement} tableContainer - Table container element or selector
 * @param {DataTable} dataTable - The DataTable instance
 * @param {Object} options - Configuration options
 * @returns {HTMLElement} The search input element
 */
function addSearchToTable(tableContainer, dataTable, options = {}) {
    const container = typeof tableContainer === 'string'
        ? document.querySelector(tableContainer)
        : tableContainer;

    if (!container) {
        console.error('Table container not found');
        return null;
    }

    const searchInput = createSearchInput(dataTable, options);
    container.parentElement.insertBefore(searchInput, container);

    return searchInput;
}

/**
 * Create filter controls for specific columns
 * @param {DataTable} dataTable - The DataTable instance
 * @param {Array} filters - Array of filter definitions
 * @returns {HTMLElement} Container with filter controls
 */
function createFilterControls(dataTable, filters) {
    const container = document.createElement('div');
    container.className = 'flex gap-4 mb-4 flex-wrap';

    filters.forEach(filter => {
        const filterDiv = document.createElement('div');
        filterDiv.className = 'flex flex-col';

        const label = document.createElement('label');
        label.className = 'text-sm font-medium text-gray-700 mb-1';
        label.textContent = filter.label;

        let input;
        if (filter.type === 'select') {
            input = document.createElement('select');
            input.className = 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500';

            // Add default option
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'All';
            input.appendChild(defaultOption);

            // Add filter options
            filter.options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.label;
                input.appendChild(option);
            });

            input.addEventListener('change', (e) => {
                if (e.target.value === '') {
                    dataTable.clearFilter();
                } else {
                    dataTable.setFilter(filter.field, '=', e.target.value);
                }
            });
        } else {
            input = document.createElement('input');
            input.type = filter.type || 'text';
            input.placeholder = filter.placeholder || '';
            input.className = 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500';

            let debounceTimer;
            input.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    if (e.target.value === '') {
                        dataTable.clearFilter();
                    } else {
                        const filterType = filter.filterType || 'like';
                        dataTable.setFilter(filter.field, filterType, e.target.value);
                    }
                }, 300);
            });
        }

        filterDiv.appendChild(label);
        filterDiv.appendChild(input);
        container.appendChild(filterDiv);
    });

    // Add clear button
    const clearButton = document.createElement('button');
    clearButton.className = 'self-end px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md transition';
    clearButton.textContent = 'Clear Filters';
    clearButton.addEventListener('click', () => {
        dataTable.clearFilter();
        container.querySelectorAll('input, select').forEach(input => {
            input.value = '';
        });
    });
    container.appendChild(clearButton);

    return container;
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        buildTableFromConfig,
        buildTableManual,
        refreshTable,
        createActionColumn,
        createSearchInput,
        addSearchToTable,
        createFilterControls
    };
}
