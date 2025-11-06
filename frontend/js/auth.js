// Authentication utilities
class Auth {
    static setToken(token) {
        localStorage.setItem('token', token);
    }

    static getToken() {
        return localStorage.getItem('token');
    }

    static removeToken() {
        localStorage.removeItem('token');
    }

    static isAuthenticated() {
        return !!this.getToken();
    }

    static setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    }

    static getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    }

    static removeUser() {
        localStorage.removeItem('user');
    }

    static logout() {
        this.removeToken();
        this.removeUser();
        window.location.href = '/login.html';
    }

    static async checkAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/login.html';
            return null;
        }

        try {
            const user = await api.getCurrentUser();
            this.setUser(user);
            return user;
        } catch (error) {
            console.error('Auth check failed:', error);
            this.logout();
            return null;
        }
    }

    static requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/login.html';
        }
    }

    static requireSiteAdmin() {
        const user = this.getUser();
        if (!user || !user.is_site_admin) {
            alert('This page requires site admin access');
            window.location.href = this.getHomePage(user);
        }
    }

    static getHomePage(user) {
        // Site admins go to admin page
        if (user && user.is_site_admin) {
            return '/admin.html';
        }
        // Regular users go to index which will redirect to their organization
        return '/';
    }

    static async redirectToHome() {
        const user = this.getUser();
        window.location.href = this.getHomePage(user);
    }
}
