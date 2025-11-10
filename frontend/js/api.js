// API Client for RedBuds App backend
const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE_URL;
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
        return this.request('/api/organizations');
    }

    async getOrganization(id) {
        return this.request(`/api/organizations/${id}`);
    }

    async createOrganization(name) {
        return this.request('/api/organizations', {
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
}

const api = new ApiClient();
