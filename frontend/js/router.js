/**
 * Router utilities for path-based navigation.
 *
 * Provides helpers for parsing URL paths and navigating between pages
 * using RESTful URL patterns.
 */

/**
 * Parse path parameters from the current URL.
 *
 * Extracts parameters based on known URL patterns:
 * - /organizations/:orgId
 * - /organizations/:orgId/admin
 * - /organizations/:orgId/projects/:projectId
 * - /organizations/:orgId/species/:speciesId
 * - /organizations/:orgId/accessions/:accessionId
 * - /organizations/:orgId/plants/:plantId
 * - /signup/:inviteCode
 *
 * @returns {Object} Object containing extracted parameters (orgId, projectId, etc.)
 *
 * @example
 * // URL: /organizations/123/projects/456
 * const params = getPathParams();
 * // Returns: { orgId: '123', projectId: '456' }
 */
function getPathParams() {
    const path = window.location.pathname;
    const segments = path.split('/').filter(s => s); // Remove empty strings

    const params = {};

    // Match URL patterns and extract IDs
    for (let i = 0; i < segments.length; i++) {
        const segment = segments[i];
        const nextSegment = segments[i + 1];

        switch (segment) {
            case 'organizations':
                if (nextSegment) {
                    params.orgId = nextSegment;
                    i++; // Skip the next segment since we consumed it
                }
                break;
            case 'projects':
                if (nextSegment) {
                    params.projectId = nextSegment;
                    i++;
                }
                break;
            case 'species':
                if (nextSegment) {
                    params.speciesId = nextSegment;
                    i++;
                }
                break;
            case 'accessions':
                if (nextSegment) {
                    params.accessionId = nextSegment;
                    i++;
                }
                break;
            case 'plants':
                if (nextSegment) {
                    params.plantId = nextSegment;
                    i++;
                }
                break;
            case 'signup':
                if (nextSegment) {
                    params.inviteCode = nextSegment;
                    i++;
                }
                break;
        }
    }

    return params;
}

/**
 * Build a URL from path segments.
 *
 * @param {...string} segments - Path segments to join
 * @returns {string} Complete URL path
 *
 * @example
 * buildUrl('organizations', '123', 'projects', '456')
 * // Returns: '/organizations/123/projects/456'
 */
function buildUrl(...segments) {
    return '/' + segments.filter(s => s).join('/');
}

/**
 * Navigate to a URL constructed from path segments.
 *
 * @param {...string} segments - Path segments to join
 *
 * @example
 * navigateTo('organizations', orgId, 'projects', projectId)
 * // Navigates to: /organizations/123/projects/456
 */
function navigateTo(...segments) {
    window.location.href = buildUrl(...segments);
}

/**
 * Get the current page context from the URL.
 *
 * Determines what type of page is currently being viewed based on
 * the URL path pattern.
 *
 * @returns {Object} Context object with page type and relevant IDs
 *
 * @example
 * // URL: /organizations/123/projects/456
 * const context = getCurrentContext();
 * // Returns: {
 * //   page: 'project',
 * //   orgId: '123',
 * //   projectId: '456'
 * // }
 */
function getCurrentContext() {
    const path = window.location.pathname;
    const params = getPathParams();

    let context = { ...params };

    // Determine page type
    if (path === '/') {
        context.page = 'home';
    } else if (path === '/login') {
        context.page = 'login';
    } else if (path.startsWith('/signup')) {
        context.page = 'signup';
    } else if (path === '/profile') {
        context.page = 'profile';
    } else if (path === '/admin') {
        context.page = 'admin';
    } else if (path.includes('/plants/')) {
        context.page = 'plant';
    } else if (path.includes('/accessions/')) {
        context.page = 'accession';
    } else if (path.includes('/species/')) {
        context.page = 'species';
    } else if (path.includes('/projects/')) {
        context.page = 'project';
    } else if (path.endsWith('/admin')) {
        context.page = 'org-admin';
    } else if (path.includes('/organizations/')) {
        context.page = 'organization';
    }

    return context;
}

/**
 * Navigate to the organization page for a given org ID.
 *
 * @param {string} orgId - Organization UUID
 */
function navigateToOrganization(orgId) {
    navigateTo('organizations', orgId);
}

/**
 * Navigate to the organization admin page for a given org ID.
 *
 * @param {string} orgId - Organization UUID
 */
function navigateToOrgAdmin(orgId) {
    navigateTo('organizations', orgId, 'admin');
}

/**
 * Navigate to a project page.
 *
 * @param {string} orgId - Organization UUID
 * @param {string} projectId - Project UUID
 */
function navigateToProject(orgId, projectId) {
    navigateTo('organizations', orgId, 'projects', projectId);
}

/**
 * Navigate to a species page.
 *
 * @param {string} orgId - Organization UUID
 * @param {string} speciesId - Species UUID
 */
function navigateToSpecies(orgId, speciesId) {
    navigateTo('organizations', orgId, 'species', speciesId);
}

/**
 * Navigate to an accession page.
 *
 * @param {string} orgId - Organization UUID
 * @param {string} accessionId - Accession UUID
 */
function navigateToAccession(orgId, accessionId) {
    navigateTo('organizations', orgId, 'accessions', accessionId);
}

/**
 * Navigate to a plant page.
 *
 * @param {string} orgId - Organization UUID
 * @param {string} plantId - Plant UUID
 */
function navigateToPlant(orgId, plantId) {
    navigateTo('organizations', orgId, 'plants', plantId);
}
