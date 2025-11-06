// API Client for OBTree backend
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
}

const api = new ApiClient();
