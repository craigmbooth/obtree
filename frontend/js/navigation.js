// Navigation component
class Navigation {
    constructor() {
        this.currentUser = null;
        this.searchDebounceTimer = null;
    }

    /**
     * Render the navigation HTML
     * @param {Object} options - Navigation options
     * @param {boolean} options.showOrgDropdown - Whether to show organization dropdown
     * @param {string} options.orgDropdownId - Current organization ID for dropdown
     * @param {string} options.organizationName - Organization name to display
     * @returns {string} Navigation HTML
     */
    render(options = {}) {
        const { showOrgDropdown = false, orgDropdownId = null, organizationName = null } = options;

        return `
            <nav class="bg-blue-600 text-white shadow-lg">
                <div class="container mx-auto px-4 py-4">
                    <div class="flex justify-between items-center">
                        <div class="flex items-center space-x-6">
                            <a href="/" class="flex items-center space-x-3 hover:opacity-90 transition-opacity">
                                <img src="/assets/images/redbud.png" alt="RedBuds App Logo" class="h-10 w-10">
                                <span class="text-2xl font-bold">RedBuds App</span>
                            </a>
                            ${showOrgDropdown ? `
                            <!-- Organization dropdown -->
                            <div id="org-dropdown" class="hidden relative">
                                <button id="org-menu-button" class="flex items-center space-x-2 bg-blue-700 text-white px-3 py-2 rounded hover:bg-blue-800 cursor-pointer focus:outline-none focus:ring-2 focus:ring-white">
                                    <span id="org-current-name">Loading...</span>
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                                    </svg>
                                </button>
                                <div id="org-menu" class="hidden absolute left-0 mt-2 w-80 bg-white rounded-md shadow-lg z-50">
                                    <div class="p-2 border-b border-gray-200">
                                        <input type="text" id="org-search" placeholder="Search organizations..."
                                            class="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500">
                                    </div>
                                    <div id="org-menu-list" class="py-1 max-h-80 overflow-y-auto">
                                        <!-- Organization options will be populated here -->
                                    </div>
                                </div>
                            </div>
                            ` : ''}
                            ${orgDropdownId ? `
                            <!-- Quick navigation links -->
                            <div class="flex items-center space-x-4">
                                <span class="text-sm opacity-75">|</span>
                                <a href="${buildUrl('organizations', orgDropdownId)}" class="text-sm hover:underline">Organization</a>
                                <a href="${buildUrl('organizations', orgDropdownId, 'projects')}" class="text-sm hover:underline">Projects</a>
                                <a href="${buildUrl('organizations', orgDropdownId, 'species')}" class="text-sm hover:underline">Species</a>
                                <a href="${buildUrl('organizations', orgDropdownId, 'accessions')}" class="text-sm hover:underline">Accessions</a>
                            </div>
                            ` : ''}
                        </div>
                        <div class="flex items-center space-x-4">
                            <!-- Site Admin link -->
                            <a href="/admin" id="site-admin-link" class="hidden text-sm hover:underline">Site Admin</a>
                            <!-- User dropdown -->
                            <div class="relative">
                                <button id="user-menu-button" class="flex items-center space-x-2 text-sm hover:text-gray-200 focus:outline-none">
                                    <span id="user-email"></span>
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                                    </svg>
                                </button>
                                <div id="user-menu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                                    <a href="/profile" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Profile</a>
                                    <a href="#" id="org-admin-menu-link" class="hidden block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Manage Organization</a>
                                    <a href="#" id="org-page-menu-link" class="hidden block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">View Organization</a>
                                    <button onclick="Auth.logout()" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Logout</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </nav>
        `;
    }

    /**
     * Initialize navigation after rendering
     * @param {Object} user - Current user object
     * @param {Object} options - Navigation options
     */
    init(user, options = {}) {
        this.currentUser = user;

        // Update user email
        const userEmailSpan = document.getElementById('user-email');
        if (userEmailSpan && user) {
            userEmailSpan.textContent = user.email;
        }

        // Show site admin link
        const siteAdminLink = document.getElementById('site-admin-link');
        if (siteAdminLink && user && user.is_site_admin) {
            siteAdminLink.classList.remove('hidden');
        }

        // Setup dropdown toggle
        this.setupUserDropdown();

        // Load organization dropdown if needed
        if (options.showOrgDropdown) {
            this.loadOrganizationDropdown(options.orgDropdownId);
        }

        // Setup context-specific links
        if (options.orgAdminLink) {
            const orgAdminMenuLink = document.getElementById('org-admin-menu-link');
            if (orgAdminMenuLink) {
                orgAdminMenuLink.href = options.orgAdminLink;
                orgAdminMenuLink.classList.remove('hidden');
            }
        }

        if (options.orgPageLink) {
            const orgPageMenuLink = document.getElementById('org-page-menu-link');
            if (orgPageMenuLink) {
                orgPageMenuLink.href = options.orgPageLink;
                orgPageMenuLink.classList.remove('hidden');
            }
        }
    }

    /**
     * Setup user dropdown menu toggle
     */
    setupUserDropdown() {
        const userMenuButton = document.getElementById('user-menu-button');
        const userMenu = document.getElementById('user-menu');

        if (!userMenuButton || !userMenu) return;

        // Toggle dropdown
        userMenuButton.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenu.classList.toggle('hidden');

            // Close org menu if open
            const orgMenu = document.getElementById('org-menu');
            if (orgMenu && !orgMenu.classList.contains('hidden')) {
                orgMenu.classList.add('hidden');
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            if (!userMenu.classList.contains('hidden')) {
                userMenu.classList.add('hidden');
            }
        });
    }

    /**
     * Setup organization dropdown menu toggle
     */
    setupOrgDropdown() {
        const orgMenuButton = document.getElementById('org-menu-button');
        const orgMenu = document.getElementById('org-menu');
        const orgSearch = document.getElementById('org-search');

        if (!orgMenuButton || !orgMenu) return;

        // Toggle dropdown
        orgMenuButton.addEventListener('click', (e) => {
            e.stopPropagation();
            const wasHidden = orgMenu.classList.contains('hidden');
            orgMenu.classList.toggle('hidden');

            // Close user menu if open
            const userMenu = document.getElementById('user-menu');
            if (userMenu && !userMenu.classList.contains('hidden')) {
                userMenu.classList.add('hidden');
            }

            // Focus search input when opening
            if (wasHidden && orgSearch) {
                setTimeout(() => orgSearch.focus(), 100);
            }
        });

        // Prevent dropdown from closing when clicking inside
        orgMenu.addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // Setup search functionality with debouncing
        if (orgSearch) {
            orgSearch.addEventListener('input', (e) => {
                // Clear existing timer
                if (this.searchDebounceTimer) {
                    clearTimeout(this.searchDebounceTimer);
                }

                // Set new timer to filter after 150ms
                const searchValue = e.target.value;
                this.searchDebounceTimer = setTimeout(() => {
                    this.filterOrganizations(searchValue);
                }, 150);
            });

            // Prevent search input from closing dropdown
            orgSearch.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            if (!orgMenu.classList.contains('hidden')) {
                orgMenu.classList.add('hidden');
                // Clear search when closing
                if (orgSearch) {
                    orgSearch.value = '';
                    this.filterOrganizations('');
                }
            }
        });
    }

    /**
     * Filter organizations in dropdown based on search term
     * @param {string} searchTerm - Search term to filter by
     */
    filterOrganizations(searchTerm) {
        const orgMenuList = document.getElementById('org-menu-list');
        if (!orgMenuList) return;

        const items = orgMenuList.querySelectorAll('a');
        const lowerSearch = searchTerm.toLowerCase();

        items.forEach(item => {
            const orgName = item.textContent.toLowerCase();
            if (orgName.includes(lowerSearch)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    /**
     * Load organization dropdown
     * @param {string} currentOrgId - Current organization ID
     */
    async loadOrganizationDropdown(currentOrgId = null) {
        try {
            const organizations = await api.getOrganizations();
            const orgMenuList = document.getElementById('org-menu-list');
            const orgCurrentName = document.getElementById('org-current-name');
            const dropdownContainer = document.getElementById('org-dropdown');

            if (!orgMenuList || !orgCurrentName || !dropdownContainer) return;

            if (organizations.length > 0) {
                dropdownContainer.classList.remove('hidden');

                // Sort organizations alphabetically
                organizations.sort((a, b) => a.name.localeCompare(b.name));

                // Find current organization name
                const currentOrg = organizations.find(org => org.id === currentOrgId);
                if (currentOrg) {
                    orgCurrentName.textContent = currentOrg.name;
                } else {
                    orgCurrentName.textContent = organizations[0].name;
                }

                // Clear existing options
                orgMenuList.innerHTML = '';

                // Add organization options
                organizations.forEach(org => {
                    const item = document.createElement('a');
                    item.href = buildUrl('organizations', org.id);
                    item.className = 'block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100';

                    // Highlight current organization
                    if (org.id === currentOrgId) {
                        item.className = 'block px-4 py-2 text-sm text-gray-700 bg-gray-100 font-semibold';
                    }

                    item.textContent = org.name;
                    orgMenuList.appendChild(item);
                });

                // Setup dropdown toggle
                this.setupOrgDropdown();
            }
        } catch (error) {
            console.error('Failed to load organizations for dropdown:', error);
        }
    }

    /**
     * Render footer HTML
     * @returns {string} Footer HTML
     */
    renderFooter() {
        return `
            <footer class="bg-gray-800 text-gray-300 py-6 mt-12">
                <div class="container mx-auto px-4 text-center">
                    <p class="text-sm">Built by Craig and Susie</p>
                </div>
            </footer>
        `;
    }
}

// Create global navigation instance
const navigation = new Navigation();
