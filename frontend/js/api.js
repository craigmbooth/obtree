// API Client for RedBuds App backend
// Version: 2.0 - Using relative URLs
// Use relative URLs to automatically inherit the page's protocol (HTTP or HTTPS)
// This prevents mixed content errors and works in all environments
const API_BASE_URL = '';  // Empty string means relative to current origin

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE_URL;
        console.log('ApiClient initialized - Version 2.0 - Base URL:', this.baseUrl || '(relative)');
    }

    getAuthHeaders() {
        const token = localStorage.getItem('token');
        if (token) {
            return {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };
        }
        return {
            'Content-Type': 'application/json'
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getAuthHeaders(),
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);

            // Handle 204 No Content responses
            if (response.status === 204) {
                return null;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'An error occurred');
            }

            return data;
        } catch (error) {
            throw error;
        }
    }

    // Auth endpoints
    async login(email, password) {
        const formData = new URLSearchParams();
        formData.append('username', email);  // OAuth2 uses 'username' field
        formData.append('password', password);

        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        return data;
    }

    async signup(email, password, inviteCode = null) {
        return this.request('/api/auth/signup', {
            method: 'POST',
            body: JSON.stringify({
                email,
                password,
                invite_code: inviteCode
            })
        });
    }

    async getCurrentUser() {
        return this.request('/api/auth/me');
    }

    async getAllUsers() {
        return this.request('/api/auth/users');
    }

    // Organization endpoints
    async getOrganizations() {
        return this.request('/api/organizations/');
    }

    async getOrganization(id) {
        return this.request(`/api/organizations/${id}/`);
    }

    async createOrganization(name) {
        return this.request('/api/organizations/', {
            method: 'POST',
            body: JSON.stringify({ name })
        });
    }

    async removeMember(organizationId, userId) {
        return this.request(`/api/organizations/${organizationId}/members/${userId}`, {
            method: 'DELETE'
        });
    }

    async reactivateMember(organizationId, userId) {
        return this.request(`/api/organizations/${organizationId}/members/${userId}/reactivate`, {
            method: 'POST'
        });
    }

    async updateMemberRole(organizationId, userId, role) {
        return this.request(`/api/organizations/${organizationId}/members/${userId}/role`, {
            method: 'PATCH',
            body: JSON.stringify({ role })
        });
    }

    async updateOrganization(organizationId, data) {
        return this.request(`/api/organizations/${organizationId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    // Invite endpoints
    async createInvite(organizationId, role) {
        return this.request('/api/invites', {
            method: 'POST',
            body: JSON.stringify({
                organization_id: organizationId,
                role: role
            })
        });
    }

    async getOrganizationInvites(organizationId) {
        return this.request(`/api/invites/organization/${organizationId}`);
    }

    async validateInvite(uuid) {
        // This endpoint doesn't require auth
        const response = await fetch(`${this.baseUrl}/api/invites/validate/${uuid}`);
        return response.json();
    }

    async revokeInvite(uuid) {
        return this.request(`/api/invites/${uuid}`, {
            method: 'DELETE'
        });
    }

    // Project endpoints
    async getProjects(organizationId) {
        return this.request(`/api/organizations/${organizationId}/projects`);
    }

    async getProject(organizationId, projectId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}`);
    }

    async createProject(organizationId, title, description = null) {
        return this.request(`/api/organizations/${organizationId}/projects`, {
            method: 'POST',
            body: JSON.stringify({
                title,
                description
            })
        });
    }

    async updateProject(organizationId, projectId, data) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteProject(organizationId, projectId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}`, {
            method: 'DELETE'
        });
    }

    async archiveProject(organizationId, projectId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/archive`, {
            method: 'POST'
        });
    }

    async unarchiveProject(organizationId, projectId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/unarchive`, {
            method: 'POST'
        });
    }

    async undeleteProject(organizationId, projectId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/undelete`, {
            method: 'POST'
        });
    }

    async getProjectAccessions(organizationId, projectId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/accessions`);
    }

    // Project Field endpoints
    async getProjectFields(organizationId, projectId, includeDeleted = false) {
        const params = includeDeleted ? '?include_deleted=true' : '';
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/fields${params}`);
    }

    async createProjectField(organizationId, projectId, data) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/fields`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateProjectField(organizationId, projectId, fieldId, data) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/fields/${fieldId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteProjectField(organizationId, projectId, fieldId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/fields/${fieldId}`, {
            method: 'DELETE'
        });
    }

    // Project Plant Field endpoints
    async getProjectPlantFields(organizationId, projectId, includeDeleted = false) {
        const params = includeDeleted ? '?include_deleted=true' : '';
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/plant_fields${params}`);
    }

    async createProjectPlantField(organizationId, projectId, data) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/plant_fields`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateProjectPlantField(organizationId, projectId, fieldId, data) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/plant_fields/${fieldId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteProjectPlantField(organizationId, projectId, fieldId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/plant_fields/${fieldId}`, {
            method: 'DELETE'
        });
    }

    // Species endpoints
    async getSpecies(organizationId) {
        return this.request(`/api/organizations/${organizationId}/species`);
    }

    async getSpeciesById(organizationId, speciesId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}`);
    }

    async createSpecies(organizationId, data) {
        return this.request(`/api/organizations/${organizationId}/species`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateSpecies(organizationId, speciesId, data) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteSpecies(organizationId, speciesId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}`, {
            method: 'DELETE'
        });
    }

    // Accession endpoints (organization-level)
    async getAllAccessions(organizationId) {
        return this.request(`/api/organizations/${organizationId}/accessions`);
    }

    async getOrgAccession(organizationId, accessionId) {
        return this.request(`/api/organizations/${organizationId}/accessions/${accessionId}`);
    }

    async getOrgPlant(organizationId, plantId) {
        return this.request(`/api/organizations/${organizationId}/plants/${plantId}`);
    }

    async updateOrgPlant(organizationId, plantId, data) {
        return this.request(`/api/organizations/${organizationId}/plants/${plantId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async createOrgAccession(organizationId, data) {
        return this.request(`/api/organizations/${organizationId}/accessions`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateOrgAccession(organizationId, accessionId, data) {
        return this.request(`/api/organizations/${organizationId}/accessions/${accessionId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteOrgAccession(organizationId, accessionId) {
        return this.request(`/api/organizations/${organizationId}/accessions/${accessionId}`, {
            method: 'DELETE'
        });
    }

    // Accession endpoints (species-level - kept for backwards compatibility)
    async getAccessions(organizationId, speciesId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions`);
    }

    async getAccession(organizationId, speciesId, accessionId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}`);
    }

    async createAccession(organizationId, speciesId, data) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateAccession(organizationId, speciesId, accessionId, data) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteAccession(organizationId, speciesId, accessionId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}`, {
            method: 'DELETE'
        });
    }

    // Plant endpoints
    async getPlants(organizationId, speciesId, accessionId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants`);
    }

    async getPlant(organizationId, speciesId, accessionId, plantId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants/${plantId}`);
    }

    async createPlant(organizationId, speciesId, accessionId, data) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updatePlant(organizationId, speciesId, accessionId, plantId, data) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants/${plantId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deletePlant(organizationId, speciesId, accessionId, plantId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants/${plantId}`, {
            method: 'DELETE'
        });
    }

    // Organization Event Type endpoints
    async getOrganizationEventTypes(organizationId, includeDeleted = false) {
        const params = includeDeleted ? '?include_deleted=true' : '';
        return this.request(`/api/organizations/${organizationId}/event-types${params}`);
    }

    async getOrganizationEventType(organizationId, eventTypeId) {
        return this.request(`/api/organizations/${organizationId}/event-types/${eventTypeId}`);
    }

    async createOrganizationEventType(organizationId, data) {
        return this.request(`/api/organizations/${organizationId}/event-types`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateOrganizationEventType(organizationId, eventTypeId, data) {
        return this.request(`/api/organizations/${organizationId}/event-types/${eventTypeId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteOrganizationEventType(organizationId, eventTypeId) {
        return this.request(`/api/organizations/${organizationId}/event-types/${eventTypeId}`, {
            method: 'DELETE'
        });
    }

    async addOrganizationEventTypeField(organizationId, eventTypeId, data) {
        return this.request(`/api/organizations/${organizationId}/event-types/${eventTypeId}/fields`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateOrganizationEventTypeField(organizationId, eventTypeId, fieldId, data) {
        return this.request(`/api/organizations/${organizationId}/event-types/${eventTypeId}/fields/${fieldId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteOrganizationEventTypeField(organizationId, eventTypeId, fieldId) {
        return this.request(`/api/organizations/${organizationId}/event-types/${eventTypeId}/fields/${fieldId}`, {
            method: 'DELETE'
        });
    }

    // Organization Location Type endpoints
    async getOrganizationLocationTypes(organizationId, includeDeleted = false) {
        const params = includeDeleted ? '?include_deleted=true' : '';
        return this.request(`/api/organizations/${organizationId}/location-types${params}`);
    }

    async getOrganizationLocationType(organizationId, locationTypeId) {
        return this.request(`/api/organizations/${organizationId}/location-types/${locationTypeId}`);
    }

    async createOrganizationLocationType(organizationId, data) {
        return this.request(`/api/organizations/${organizationId}/location-types`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateOrganizationLocationType(organizationId, locationTypeId, data) {
        return this.request(`/api/organizations/${organizationId}/location-types/${locationTypeId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteOrganizationLocationType(organizationId, locationTypeId) {
        return this.request(`/api/organizations/${organizationId}/location-types/${locationTypeId}`, {
            method: 'DELETE'
        });
    }

    // Location endpoints
    async getLocations(organizationId) {
        return this.request(`/api/organizations/${organizationId}/locations`);
    }

    async getLocation(organizationId, locationId) {
        return this.request(`/api/organizations/${organizationId}/locations/${locationId}`);
    }

    async createLocation(organizationId, data) {
        return this.request(`/api/organizations/${organizationId}/locations`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateLocation(organizationId, locationId, data) {
        return this.request(`/api/organizations/${organizationId}/locations/${locationId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteLocation(organizationId, locationId) {
        return this.request(`/api/organizations/${organizationId}/locations/${locationId}`, {
            method: 'DELETE'
        });
    }

    // Project Event Type endpoints
    async getProjectEventTypes(organizationId, projectId, includeDeleted = false) {
        const params = includeDeleted ? '?include_deleted=true' : '';
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/event-types${params}`);
    }

    async getProjectEventType(organizationId, projectId, eventTypeId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/event-types/${eventTypeId}`);
    }

    async createProjectEventType(organizationId, projectId, data) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/event-types`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateProjectEventType(organizationId, projectId, eventTypeId, data) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/event-types/${eventTypeId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteProjectEventType(organizationId, projectId, eventTypeId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/event-types/${eventTypeId}`, {
            method: 'DELETE'
        });
    }

    async addProjectEventTypeField(organizationId, projectId, eventTypeId, data) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/event-types/${eventTypeId}/fields`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateProjectEventTypeField(organizationId, projectId, eventTypeId, fieldId, data) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/event-types/${eventTypeId}/fields/${fieldId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deleteProjectEventTypeField(organizationId, projectId, eventTypeId, fieldId) {
        return this.request(`/api/organizations/${organizationId}/projects/${projectId}/event-types/${eventTypeId}/fields/${fieldId}`, {
            method: 'DELETE'
        });
    }

    // Plant Event endpoints
    async getPlantEvents(organizationId, speciesId, accessionId, plantId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants/${plantId}/events`);
    }

    async getPlantEvent(organizationId, speciesId, accessionId, plantId, eventId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants/${plantId}/events/${eventId}`);
    }

    async createPlantEvent(organizationId, speciesId, accessionId, plantId, data) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants/${plantId}/events`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updatePlantEvent(organizationId, speciesId, accessionId, plantId, eventId, data) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants/${plantId}/events/${eventId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async deletePlantEvent(organizationId, speciesId, accessionId, plantId, eventId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants/${plantId}/events/${eventId}`, {
            method: 'DELETE'
        });
    }

    async getAccessibleEventTypes(organizationId, speciesId, accessionId, plantId) {
        return this.request(`/api/organizations/${organizationId}/species/${speciesId}/accessions/${accessionId}/plants/${plantId}/events/accessible-types`);
    }
}

const api = new ApiClient();
