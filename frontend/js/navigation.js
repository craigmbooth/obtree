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
     * @param {string} options.organizationName - Organization name to display
     * @returns {string} Navigation HTML
     */
    render(options = {}) {
        const { showOrgDropdown = false, orgDropdownId = null, organizationName = null } = options;

        return `
            <nav class="bg-blue-600 text-white shadow-lg">
                <div class="container mx-auto px-4 py-3">
                    <div class="flex justify-between items-center">
                        <!-- Logo and Mobile Menu Button -->
                        <div class="flex items-center space-x-3">
                            <a href="/" class="flex items-center space-x-2 hover:opacity-90 transition-opacity">
                                <img src="/assets/images/redbud.png" alt="RedBuds App Logo" class="h-8 w-8 sm:h-10 sm:w-10">
                                <span class="text-lg sm:text-2xl font-bold">RedBuds App</span>
                            </a>
                        </div>

                        <!-- Desktop Navigation -->
                        <div class="hidden lg:flex items-center space-x-6">
                            ${showOrgDropdown ? `
                            <!-- Organization dropdown -->
                            <div id="org-dropdown" class="hidden relative">
                                <select id="org-selector" onchange="handleOrgChange()"
                                    class="bg-blue-700 text-white px-3 py-2 rounded hover:bg-blue-800 cursor-pointer focus:outline-none focus:ring-2 focus:ring-white text-sm">
                                    <option value="">Loading...</option>
                                </select>
                            </div>
                            ` : ''}
                            ${orgDropdownId ? `
                            <!-- Quick navigation links -->
                            <div class="flex items-center space-x-4">
                                <span class="text-sm opacity-75">|</span>
                                <a href="${buildUrl('organizations', orgDropdownId)}" class="text-sm hover:underline whitespace-nowrap">Organization</a>
                                <a href="${buildUrl('organizations', orgDropdownId, 'projects')}" class="text-sm hover:underline whitespace-nowrap">Projects</a>
                                <a href="${buildUrl('organizations', orgDropdownId, 'species')}" class="text-sm hover:underline whitespace-nowrap">Species</a>
                                <a href="${buildUrl('organizations', orgDropdownId, 'accessions')}" class="text-sm hover:underline whitespace-nowrap">Accessions</a>
                            </div>
                            ` : ''}
                            <!-- Site Admin link -->
                            <a href="/admin" id="site-admin-link" class="hidden text-sm hover:underline whitespace-nowrap">Site Admin</a>
                            <!-- User dropdown -->
                            <div class="relative">
                                <button id="user-menu-button" class="flex items-center space-x-2 text-sm hover:text-gray-200 focus:outline-none">
                                    <span id="user-email" class="max-w-[200px] truncate"></span>
                                    <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

                        <!-- Mobile Menu Button -->
                        <button id="mobile-menu-button" class="lg:hidden p-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-white">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                            </svg>
                        </button>
                    </div>

                    <!-- Mobile Menu -->
                    <div id="mobile-menu" class="hidden lg:hidden mt-4 pb-3 space-y-2 border-t border-blue-500 pt-3">
                        ${showOrgDropdown ? `
                        <div id="org-dropdown-mobile" class="hidden">
                            <select id="org-selector-mobile" onchange="handleOrgChange()"
                                class="w-full bg-blue-700 text-white px-3 py-3 rounded hover:bg-blue-800 cursor-pointer focus:outline-none focus:ring-2 focus:ring-white text-base">
                                <option value="">Loading...</option>
                            </select>
                        </div>
                        ` : ''}
                        ${orgDropdownId ? `
                        <a href="${buildUrl('organizations', orgDropdownId)}" class="block px-3 py-3 text-base hover:bg-blue-700 rounded">Organization</a>
                        <a href="${buildUrl('organizations', orgDropdownId, 'projects')}" class="block px-3 py-3 text-base hover:bg-blue-700 rounded">Projects</a>
                        <a href="${buildUrl('organizations', orgDropdownId, 'species')}" class="block px-3 py-3 text-base hover:bg-blue-700 rounded">Species</a>
                        <a href="${buildUrl('organizations', orgDropdownId, 'accessions')}" class="block px-3 py-3 text-base hover:bg-blue-700 rounded">Accessions</a>
                        ` : ''}
                        <a href="#" id="site-admin-link-mobile" class="hidden block px-3 py-3 text-base hover:bg-blue-700 rounded">Site Admin</a>
                        <div class="border-t border-blue-500 pt-2 mt-2">
                            <div class="px-3 py-2 text-sm text-blue-200" id="user-email-mobile"></div>
                            <a href="/profile" class="block px-3 py-3 text-base hover:bg-blue-700 rounded">Profile</a>
                            <a href="#" id="org-admin-menu-link-mobile" class="hidden block px-3 py-3 text-base hover:bg-blue-700 rounded">Manage Organization</a>
                            <a href="#" id="org-page-menu-link-mobile" class="hidden block px-3 py-3 text-base hover:bg-blue-700 rounded">View Organization</a>
                            <button onclick="Auth.logout()" class="block w-full text-left px-3 py-3 text-base hover:bg-blue-700 rounded">Logout</button>
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

        // Update user email (desktop)
        const userEmailSpan = document.getElementById('user-email');
        if (userEmailSpan && user) {
            userEmailSpan.textContent = user.email;
        }

        // Update user email (mobile)
        const userEmailMobile = document.getElementById('user-email-mobile');
        if (userEmailMobile && user) {
            userEmailMobile.textContent = user.email;
        }

        // Show site admin link (desktop)
        const siteAdminLink = document.getElementById('site-admin-link');
        if (siteAdminLink && user && user.is_site_admin) {
            siteAdminLink.classList.remove('hidden');
        }

        // Show site admin link (mobile)
        const siteAdminLinkMobile = document.getElementById('site-admin-link-mobile');
        if (siteAdminLinkMobile && user && user.is_site_admin) {
            siteAdminLinkMobile.classList.remove('hidden');
            siteAdminLinkMobile.href = '/admin';
        }

        // Setup mobile menu toggle
        this.setupMobileMenu();

        // Setup dropdown toggle
        this.setupUserDropdown();

        // Load organization dropdown if needed
        if (options.showOrgDropdown) {
            this.loadOrganizationDropdown(options.orgDropdownId);
        }

        // Setup context-specific links (desktop)
        if (options.orgAdminLink) {
            const orgAdminMenuLink = document.getElementById('org-admin-menu-link');
            if (orgAdminMenuLink) {
                orgAdminMenuLink.href = options.orgAdminLink;
                orgAdminMenuLink.classList.remove('hidden');
            }
            // Mobile version
            const orgAdminMenuLinkMobile = document.getElementById('org-admin-menu-link-mobile');
            if (orgAdminMenuLinkMobile) {
                orgAdminMenuLinkMobile.href = options.orgAdminLink;
                orgAdminMenuLinkMobile.classList.remove('hidden');
            }
        }

        if (options.orgPageLink) {
            const orgPageMenuLink = document.getElementById('org-page-menu-link');
            if (orgPageMenuLink) {
                orgPageMenuLink.href = options.orgPageLink;
                orgPageMenuLink.classList.remove('hidden');
            }
            // Mobile version
            const orgPageMenuLinkMobile = document.getElementById('org-page-menu-link-mobile');
            if (orgPageMenuLinkMobile) {
                orgPageMenuLinkMobile.href = options.orgPageLink;
                orgPageMenuLinkMobile.classList.remove('hidden');
            }
        }
    }

    /**
     * Setup mobile menu toggle
     */
    setupMobileMenu() {
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');

        if (!mobileMenuButton || !mobileMenu) return;

        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenuButton.contains(e.target) && !mobileMenu.contains(e.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
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
            const dropdownMobile = document.getElementById('org-selector-mobile');
            const dropdownContainerMobile = document.getElementById('org-dropdown-mobile');

            if (organizations.length > 0) {
                // Desktop dropdown
                if (dropdown && dropdownContainer) {
                    dropdownContainer.classList.remove('hidden');
                    dropdown.innerHTML = '';
                    organizations.forEach(org => {
                        const option = document.createElement('option');
                        option.value = org.id;
                        option.textContent = org.name;
                        dropdown.appendChild(option);
                    });
                    if (currentOrgId) {
                        dropdown.value = currentOrgId;
                    }
                }

                // Mobile dropdown
                if (dropdownMobile && dropdownContainerMobile) {
                    dropdownContainerMobile.classList.remove('hidden');
                    dropdownMobile.innerHTML = '';
                    organizations.forEach(org => {
                        const option = document.createElement('option');
                        option.value = org.id;
                        option.textContent = org.name;
                        dropdownMobile.appendChild(option);
                    });
                    if (currentOrgId) {
                        dropdownMobile.value = currentOrgId;
                    }
                }
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

// Global function for org dropdown change (referenced in HTML)
function handleOrgChange() {
    const dropdown = document.getElementById('org-selector');
    const selectedOrgId = dropdown.value;
    if (selectedOrgId) {
        window.location.href = buildUrl('organizations', selectedOrgId);
    }
}
