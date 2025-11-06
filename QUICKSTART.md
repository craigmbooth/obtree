# Quick Start Guide

Get up and running with OBTree in 5 minutes!

## Setup

```bash
# 1. Install dependencies
make install

# 2. Create database
make db-create

# 3. Create a site admin user
make seed-admin
# Enter email and password when prompted

# 4. Start the server
make run
```

## Access the Application

Open your browser and visit: **http://localhost:8000**

You'll be automatically redirected to the login page.

## Your First Login

1. **Login** with the email and password you just created
2. You'll see the Dashboard (currently empty since you have no organizations)
3. Click **Admin** in the top navigation (only visible to site admins)

## Create Your First Organization

1. On the Admin page, enter an organization name (e.g., "My Company")
2. Click **Create Organization**
3. You'll be redirected to the organization detail page

## Invite Users

1. On the organization page, scroll to **Admin Controls**
2. Select a role (User or Admin)
3. Click **Generate Invite**
4. Click **Copy Link** next to the generated invite
5. Share this link with users you want to invite

## Test the Invite System

1. **Open an incognito/private browser window**
2. **Paste the invite link** you just copied
3. The signup form will show which organization you're joining
4. **Fill out the signup form** with a new email/password
5. **Login** with the new account
6. You'll see the organization in your dashboard!

## Features to Explore

### As Site Admin
- ✅ Create multiple organizations
- ✅ Manage all organizations you created
- ✅ Generate invite codes with different roles
- ✅ View all organization members

### As Organization Admin
- ✅ View organization details
- ✅ See all members
- ✅ Generate invite codes
- ✅ Copy invite links to share

### As Organization User
- ✅ View organization details
- ✅ See all members
- ✅ Access organization resources

## API Access

The REST API is also available:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Base URL**: http://localhost:8000/api/

## Common Commands

```bash
make run          # Start the server
make seed-admin   # Create another site admin
make upgrade      # Apply database migrations
make help         # See all available commands
```

## Troubleshooting

**Problem**: Can't access the frontend
- **Solution**: Make sure you're using `http://localhost:8000` not `http://127.0.0.1:8000`

**Problem**: Login fails
- **Solution**: Double-check the email/password you entered during `make seed-admin`

**Problem**: Invite code doesn't work
- **Solution**: Check if the invite has expired (default: 7 days) or was already used

**Problem**: Port 8000 is already in use
- **Solution**: Stop the other process or change the port in the Makefile

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:8000/docs
- Check out the code in `app/` and `frontend/` directories
- Deploy to production (see README.md for production tips)

Enjoy using OBTree! 🌳
