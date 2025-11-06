// Navigation component
class Navigation {
    constructor() {
        this.currentUser = null;
    }

    /**
     * Render the navigation HTML
     * @param {Object} options - Navigation options
     * @param {boolean} options.showOrgDropdown - Whether to show organization dropdown
     * @param {string} options.orgDropdownId - Current organization ID for dropdown
     * @returns {string} Navigation HTML
     */
    render(options = {}) {
        const { showOrgDropdown = false, orgDropdownId = null } = options;

        return `
            <nav class="bg-blue-600 text-white shadow-lg">
                <div class="container mx-auto px-4 py-4">
                    <div class="flex justify-between items-center">
                        <div class="flex items-center space-x-6">
                            <a href="/" class="text-2xl font-bold hover:underline">OBTree</a>
                            <a href="/admin.html" id="site-admin-link" class="hover:underline hidden">Admin</a>
                            ${showOrgDropdown ? `
                            <!-- Organization dropdown for non-admins -->
                            <div id="org-dropdown" class="hidden relative">
                                <select id="org-selector" onchange="handleOrgChange()"
                                    class="bg-blue-700 text-white px-3 py-2 rounded hover:bg-blue-800 cursor-pointer focus:outline-none focus:ring-2 focus:ring-white">
                                    <option value="">Loading...</option>
                                </select>
                            </div>
                            ` : ''}
                        </div>
                        <div class="flex items-center space-x-4">
                            <!-- User dropdown -->
                            <div class="relative">
                                <button id="user-menu-button" class="flex items-center space-x-2 text-sm hover:text-gray-200 focus:outline-none">
                                    <span id="user-email"></span>
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                                    </svg>
                                </button>
                                <div id="user-menu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                                    <a href="/profile.html" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Profile</a>
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
        if (options.showOrgDropdown && !user.is_site_admin) {
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
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            if (!userMenu.classList.contains('hidden')) {
                userMenu.classList.add('hidden');
            }
        });
    }

    /**
     * Load organization dropdown for non-admin users
     * @param {string} currentOrgId - Current organization ID
     */
    async loadOrganizationDropdown(currentOrgId = null) {
        try {
            const organizations = await api.getOrganizations();
            const dropdown = document.getElementById('org-selector');
            const dropdownContainer = document.getElementById('org-dropdown');

            if (!dropdown || !dropdownContainer) return;

            if (organizations.length > 0) {
                dropdownContainer.classList.remove('hidden');

                // Clear existing options
                dropdown.innerHTML = '';

                // Add organization options
                organizations.forEach(org => {
                    const option = document.createElement('option');
                    option.value = org.id;
                    option.textContent = org.name;
                    dropdown.appendChild(option);
                });

                // Set current organization as selected
                if (currentOrgId) {
                    dropdown.value = currentOrgId;
                }
            }
        } catch (error) {
            console.error('Failed to load organizations for dropdown:', error);
        }
    }
}

// Create global navigation instance
const navigation = new Navigation();

// Global function for org dropdown change (referenced in HTML)
function handleOrgChange() {
    const dropdown = document.getElementById('org-selector');
    const selectedOrgId = dropdown.value;
    if (selectedOrgId) {
        window.location.href = `/organization.html?id=${selectedOrgId}`;
    }
}
