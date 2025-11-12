# Event System Implementation Guide

This guide provides templates for completing the event system implementation.

## What's Already Done ✓

1. **Models**: EventType, EventTypeField, PlantEvent, EventFieldValue
2. **Schemas**: All request/response schemas created
3. **Migration**: `b62580483499_add_event_system_tables.py`
4. **Model Relationships**: Organization, Project, Plant updated

## What You Need to Implement

### 1. Backend Routes (3 files)
### 2. Route Registration
### 3. Frontend API Methods
### 4. Frontend UI Components

---

## 1. Organization Event Types Routes

**File**: `app/api/routes/organization_event_types.py`

**Purpose**: Manage organization-level event types (project_id = NULL)

**Endpoints**:
- `GET /api/organizations/{org_id}/event-types/` - List org event types
- `POST /api/organizations/{org_id}/event-types/` - Create event type (admin only)
- `GET /api/organizations/{org_id}/event-types/{type_id}` - Get event type details
- `PATCH /api/organizations/{org_id}/event-types/{type_id}` - Update event type (admin only)
- `DELETE /api/organizations/{org_id}/event-types/{type_id}` - Soft delete event type (admin only)

**Key Implementation Details**:

```python
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import is_org_member, can_manage_organization
from app.logging_config import get_logger
from app.models import User, Organization, EventType, EventTypeField
from app.schemas import (
    EventTypeCreate,
    EventTypeUpdate,
    EventTypeResponse,
)

logger = get_logger(__name__)
router = APIRouter()

# LIST endpoint
@router.get("", response_model=List[EventTypeResponse])
def list_organization_event_types(
    organization_id: UUID,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all org-level event types (all members can view).

    Steps:
    1. Check is_org_member(db, current_user, organization_id)
    2. Query EventType where organization_id = org_id AND project_id IS NULL
    3. If not include_deleted: filter is_deleted = False
    4. Eager load .fields relationship
    5. Filter out deleted fields if not include_deleted
    6. Return list
    """
    pass

# CREATE endpoint
@router.post("", response_model=EventTypeResponse, status_code=status.HTTP_201_CREATED)
def create_organization_event_type(
    organization_id: UUID,
    event_type_data: EventTypeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new org-level event type (admin only).

    Steps:
    1. Check can_manage_organization(db, current_user, organization_id)
    2. Verify organization exists
    3. Create EventType with organization_id and project_id = None
    4. If event_type_data.fields provided:
       - Create EventTypeField records for each field
       - Link to event type
    5. db.commit() and db.refresh()
    6. Return EventTypeResponse
    """
    pass

# GET DETAIL endpoint
@router.get("/{event_type_id}", response_model=EventTypeResponse)
def get_organization_event_type(
    organization_id: UUID,
    event_type_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get event type details."""
    pass

# UPDATE endpoint
@router.patch("/{event_type_id}", response_model=EventTypeResponse)
def update_organization_event_type(
    organization_id: UUID,
    event_type_id: UUID,
    event_type_update: EventTypeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update event type (admin only).

    Steps:
    1. Check can_manage_organization
    2. Query event type, verify belongs to org and project_id IS NULL
    3. Update fields from event_type_update.model_dump(exclude_unset=True)
    4. Commit and return

    Note: Field updates handled by separate field endpoints
    """
    pass

# DELETE endpoint
@router.delete("/{event_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization_event_type(
    organization_id: UUID,
    event_type_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete event type (admin only).

    Steps:
    1. Check can_manage_organization
    2. Query event type
    3. Set is_deleted = True, deleted_at = datetime.utcnow()
    4. Also soft delete all associated fields
    5. Commit
    """
    pass
```

**Additional Endpoints for Fields**:

```python
# Add these to manage individual fields within an event type

@router.post("/{event_type_id}/fields", response_model=EventTypeFieldResponse)
def create_event_type_field(...):
    """Add a field to an event type (admin only)."""
    pass

@router.patch("/{event_type_id}/fields/{field_id}", response_model=EventTypeFieldResponse)
def update_event_type_field(...):
    """
    Update a field (admin only).
    Check field.is_locked before allowing field_type change.
    """
    pass

@router.delete("/{event_type_id}/fields/{field_id}")
def delete_event_type_field(...):
    """Soft delete a field (admin only)."""
    pass
```

---

## 2. Project Event Types Routes

**File**: `app/api/routes/project_event_types.py`

**Purpose**: Manage project-level event types (project_id is set)

**Endpoints**: Same structure as org event types, but:
- Base path: `/api/organizations/{org_id}/projects/{project_id}/event-types/`
- Query: `project_id = project_id` (not NULL)
- Permissions: Use `can_manage_organization` for create/update/delete

**Key Differences**:
```python
# In CREATE:
new_event_type = EventType(
    event_name=event_type_data.event_name,
    description=event_type_data.description,
    organization_id=organization_id,
    project_id=project_id,  # <-- Set this
    display_order=event_type_data.display_order,
    created_by=current_user.id
)

# In LIST:
query = db.query(EventType).filter(
    EventType.organization_id == organization_id,
    EventType.project_id == project_id  # <-- Filter by project
)
```

**Copy organization_event_types.py and modify these points.**

---

## 3. Plant Events Routes

**File**: `app/api/routes/plant_events.py`

**Purpose**: CRUD operations on plant events

**Endpoints**:
- `GET /api/organizations/{org_id}/species/{species_id}/accessions/{acc_id}/plants/{plant_id}/events/`
- `POST .../events/` - Create event
- `GET .../events/{event_id}` - Get event details
- `PATCH .../events/{event_id}` - Update event
- `DELETE .../events/{event_id}` - Delete event

**Key Implementation**:

```python
from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import is_org_member
from app.logging_config import get_logger
from app.models import User, Plant, EventType, PlantEvent, EventFieldValue, EventTypeField
from app.schemas import (
    PlantEventCreate,
    PlantEventUpdate,
    PlantEventResponse,
)

logger = get_logger(__name__)
router = APIRouter()

@router.get("", response_model=List[PlantEventResponse])
def list_plant_events(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all events for a plant.

    Steps:
    1. Verify plant exists and belongs to correct accession/species/org
    2. Check is_org_member
    3. Query PlantEvent.filter(plant_id=plant_id)
    4. Order by event_date DESC
    5. For each event:
       - Get event_type.event_name for denormalization
       - Eager load field_values with field details
    6. Return list
    """
    pass

@router.post("", response_model=PlantEventResponse, status_code=status.HTTP_201_CREATED)
def create_plant_event(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    event_data: PlantEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new plant event (all org members can create).

    Steps:
    1. Verify plant exists and belongs to org
    2. Check is_org_member
    3. Get event_type and verify it's accessible to this plant:
       - Either event_type.project_id IS NULL (org-level)
       - OR event_type.project_id IN plant's accession's projects
    4. Validate required fields from event_type.fields
    5. Create PlantEvent record
    6. For each field_value in event_data.field_values:
       a. Get EventTypeField
       b. Validate value against field rules (use field_validation.py)
       c. Create EventFieldValue with appropriate value_string or value_number
    7. Commit and return

    Important: If event_date not provided, default to datetime.utcnow()
    """
    pass

@router.get("/{event_id}", response_model=PlantEventResponse)
def get_plant_event(...):
    """Get event details with all field values."""
    pass

@router.patch("/{event_id}", response_model=PlantEventResponse)
def update_plant_event(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    event_id: UUID,
    event_update: PlantEventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a plant event.

    Steps:
    1. Verify plant and event exist
    2. Check is_org_member (or created_by if you want owner-only)
    3. Update event_date, notes, event_type_id if provided
    4. If field_values provided:
       - Delete existing EventFieldValue records for this event
       - Create new ones from event_update.field_values
       - Validate each value
    5. Commit and return
    """
    pass

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plant_event(...):
    """Delete event (CASCADE will delete field_values)."""
    pass
```

**Helper Function for Event Type Access**:

```python
def get_accessible_event_types(db: Session, plant_id: UUID, organization_id: UUID) -> List[EventType]:
    """
    Get all event types accessible to a plant.

    Returns:
    - All org-level event types (project_id IS NULL)
    - All project-level event types for projects the plant's accession belongs to
    """
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        return []

    # Get plant's accession's projects
    accession = plant.accession
    project_ids = [p.id for p in accession.projects]

    # Query event types
    query = db.query(EventType).filter(
        EventType.organization_id == organization_id,
        EventType.is_deleted == False
    )

    # Org-level OR in plant's projects
    from sqlalchemy import or_
    query = query.filter(
        or_(
            EventType.project_id.is_(None),  # Org-level
            EventType.project_id.in_(project_ids)  # Project-level
        )
    )

    return query.all()
```

---

## 4. Route Registration

**File**: `app/main.py`

Add to existing route imports and registration:

```python
# Add imports
from app.api.routes import (
    # ... existing imports ...
    organization_event_types,
    project_event_types,
    plant_events,
)

# Add route registration (around line 50-80 where other routes are)
app.include_router(
    organization_event_types.router,
    prefix="/api/organizations/{organization_id}/event-types",
    tags=["event-types"]
)

app.include_router(
    project_event_types.router,
    prefix="/api/organizations/{organization_id}/projects/{project_id}/event-types",
    tags=["event-types"]
)

app.include_router(
    plant_events.router,
    prefix="/api/organizations/{organization_id}/species/{species_id}/accessions/{accession_id}/plants/{plant_id}/events",
    tags=["events"]
)
```

---

## 5. Frontend API Methods

**File**: `frontend/js/api.js`

Add these methods to the `ApiClient` class:

```javascript
// ===== Organization Event Types =====

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

// ===== Project Event Types =====

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

// ===== Plant Events =====

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

// ===== Event Type Fields Management (optional - for fine-grained control) =====

async createEventTypeField(organizationId, eventTypeId, data, projectId = null) {
    const basePath = projectId
        ? `/api/organizations/${organizationId}/projects/${projectId}/event-types/${eventTypeId}/fields`
        : `/api/organizations/${organizationId}/event-types/${eventTypeId}/fields`;
    return this.request(basePath, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async updateEventTypeField(organizationId, eventTypeId, fieldId, data, projectId = null) {
    const basePath = projectId
        ? `/api/organizations/${organizationId}/projects/${projectId}/event-types/${eventTypeId}/fields/${fieldId}`
        : `/api/organizations/${organizationId}/event-types/${eventTypeId}/fields/${fieldId}`;
    return this.request(basePath, {
        method: 'PATCH',
        body: JSON.stringify(data)
    });
}

async deleteEventTypeField(organizationId, eventTypeId, fieldId, projectId = null) {
    const basePath = projectId
        ? `/api/organizations/${organizationId}/projects/${projectId}/event-types/${eventTypeId}/fields/${fieldId}`
        : `/api/organizations/${organizationId}/event-types/${eventTypeId}/fields/${fieldId}`;
    return this.request(basePath, {
        method: 'DELETE'
    });
}
```

---

## 6. Frontend UI - Organization Admin Page

**File**: `frontend/org-admin.html`

**Location**: Add after the "Members" section, before the "Invites" section

**HTML Structure**:

```html
<!-- Event Types Section -->
<div class="bg-white rounded-lg shadow-md p-6 mt-6">
    <div class="flex justify-between items-center mb-4">
        <div>
            <h3 class="text-xl font-semibold text-gray-800">Organization Event Types</h3>
            <p class="text-sm text-gray-600 mt-1">Event types available to all plants in this organization</p>
        </div>
        <button id="add-org-event-type-btn" class="hidden bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Add Event Type
        </button>
    </div>

    <div id="org-event-types-loading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-2 text-gray-600">Loading event types...</p>
    </div>

    <div id="org-event-types-content" class="hidden">
        <div id="org-event-types-empty" class="text-center py-8 text-gray-600 hidden">
            No organization event types defined yet.
        </div>

        <table id="org-event-types-table" class="min-w-full divide-y divide-gray-200 hidden">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event Type</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fields</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody id="org-event-types-tbody" class="bg-white divide-y divide-gray-200">
            </tbody>
        </table>
    </div>
</div>

<!-- Add/Edit Event Type Modal -->
<div id="event-type-modal" class="hidden fixed z-10 inset-0 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <h3 id="event-type-modal-title" class="text-lg font-medium text-gray-900 mb-4">Add Event Type</h3>

                <form id="event-type-form">
                    <!-- Event Type Name -->
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Event Type Name *</label>
                        <input type="text" id="event-type-name" required
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>

                    <!-- Description -->
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                        <textarea id="event-type-description" rows="2"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
                    </div>

                    <!-- Display Order -->
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Display Order</label>
                        <input type="number" id="event-type-order" value="0"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>

                    <!-- Fields Section -->
                    <div class="mb-4">
                        <div class="flex justify-between items-center mb-2">
                            <label class="block text-sm font-medium text-gray-700">Fields</label>
                            <button type="button" id="add-field-to-type-btn" class="text-sm text-blue-600 hover:underline">
                                + Add Field
                            </button>
                        </div>
                        <div id="event-type-fields-list" class="space-y-2">
                            <!-- Dynamic field items will be added here -->
                        </div>
                    </div>
                </form>
            </div>
            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button type="button" id="save-event-type-btn"
                    class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm">
                    Save
                </button>
                <button type="button" id="cancel-event-type-btn"
                    class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none sm:mt-0 sm:w-auto sm:text-sm">
                    Cancel
                </button>
            </div>
        </div>
    </div>
</div>
```

**JavaScript** (add to existing script section):

```javascript
// Add to existing variables
let orgEventTypes = [];
let editingEventTypeId = null;
let eventTypeFields = [];  // Temp storage for fields being added

// Add to init() function
await loadOrgEventTypes();

// Functions to add
async function loadOrgEventTypes() {
    try {
        orgEventTypes = await api.getOrganizationEventTypes(organizationId);
        renderOrgEventTypes();
    } catch (error) {
        showError('Failed to load event types: ' + error.message);
    } finally {
        document.getElementById('org-event-types-loading').classList.add('hidden');
        document.getElementById('org-event-types-content').classList.remove('hidden');
    }
}

function renderOrgEventTypes() {
    const tbody = document.getElementById('org-event-types-tbody');
    const emptyDiv = document.getElementById('org-event-types-empty');
    const table = document.getElementById('org-event-types-table');

    if (orgEventTypes.length === 0) {
        emptyDiv.classList.remove('hidden');
        table.classList.add('hidden');
        return;
    }

    emptyDiv.classList.add('hidden');
    table.classList.remove('hidden');

    tbody.innerHTML = orgEventTypes.map(eventType => {
        const fieldsCount = eventType.fields ? eventType.fields.length : 0;
        const fieldsSummary = fieldsCount > 0
            ? `${fieldsCount} field${fieldsCount !== 1 ? 's' : ''}`
            : 'No fields';

        const actionsHtml = canManage ? `
            <button onclick="openEditEventTypeModal('${eventType.id}')" class="text-blue-600 hover:underline mr-2">Edit</button>
            <button onclick="deleteEventType('${eventType.id}')" class="text-red-600 hover:underline">Delete</button>
        ` : '<span class="text-gray-400">View only</span>';

        return `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${eventType.event_name}</td>
                <td class="px-6 py-4 text-sm text-gray-600">${eventType.description || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${fieldsSummary}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">${actionsHtml}</td>
            </tr>
        `;
    }).join('');
}

function openAddEventTypeModal() {
    editingEventTypeId = null;
    eventTypeFields = [];
    document.getElementById('event-type-modal-title').textContent = 'Add Organization Event Type';
    document.getElementById('event-type-form').reset();
    document.getElementById('event-type-fields-list').innerHTML = '';
    document.getElementById('event-type-modal').classList.remove('hidden');
}

function openEditEventTypeModal(eventTypeId) {
    const eventType = orgEventTypes.find(et => et.id === eventTypeId);
    if (!eventType) return;

    editingEventTypeId = eventTypeId;
    eventTypeFields = eventType.fields || [];

    document.getElementById('event-type-modal-title').textContent = 'Edit Organization Event Type';
    document.getElementById('event-type-name').value = eventType.event_name;
    document.getElementById('event-type-description').value = eventType.description || '';
    document.getElementById('event-type-order').value = eventType.display_order || 0;

    renderEventTypeFields();
    document.getElementById('event-type-modal').classList.remove('hidden');
}

function renderEventTypeFields() {
    const container = document.getElementById('event-type-fields-list');
    container.innerHTML = eventTypeFields.map((field, index) => `
        <div class="flex items-center gap-2 p-2 bg-gray-50 rounded">
            <span class="flex-1 text-sm">${field.field_name} (${field.field_type}${field.is_required ? ', required' : ''})</span>
            <button type="button" onclick="removeEventTypeField(${index})" class="text-red-600 hover:underline text-sm">Remove</button>
        </div>
    `).join('');
}

function addFieldToEventType() {
    // Open a sub-modal or inline form to add field details
    // For simplicity, use prompt() or create another modal
    const fieldName = prompt('Field name:');
    if (!fieldName) return;

    const fieldType = prompt('Field type (string or number):');
    if (!fieldType || !['string', 'number'].includes(fieldType.toLowerCase())) {
        alert('Invalid field type');
        return;
    }

    const isRequired = confirm('Is this field required?');

    eventTypeFields.push({
        field_name: fieldName,
        field_type: fieldType.toLowerCase(),
        is_required: isRequired,
        display_order: eventTypeFields.length
    });

    renderEventTypeFields();
}

function removeEventTypeField(index) {
    eventTypeFields.splice(index, 1);
    renderEventTypeFields();
}

async function saveEventType() {
    const eventTypeData = {
        event_name: document.getElementById('event-type-name').value,
        description: document.getElementById('event-type-description').value,
        display_order: parseInt(document.getElementById('event-type-order').value) || 0,
        fields: eventTypeFields
    };

    try {
        if (editingEventTypeId) {
            await api.updateOrganizationEventType(organizationId, editingEventTypeId, eventTypeData);
            showSuccess('Event type updated successfully');
        } else {
            await api.createOrganizationEventType(organizationId, eventTypeData);
            showSuccess('Event type created successfully');
        }
        closeEventTypeModal();
        await loadOrgEventTypes();
    } catch (error) {
        showError('Failed to save event type: ' + error.message);
    }
}

async function deleteEventType(eventTypeId) {
    if (!confirm('Are you sure you want to delete this event type?')) {
        return;
    }

    try {
        await api.deleteOrganizationEventType(organizationId, eventTypeId);
        showSuccess('Event type deleted successfully');
        await loadOrgEventTypes();
    } catch (error) {
        showError('Failed to delete event type: ' + error.message);
    }
}

function closeEventTypeModal() {
    document.getElementById('event-type-modal').classList.add('hidden');
    document.getElementById('event-type-form').reset();
    editingEventTypeId = null;
    eventTypeFields = [];
}

// Add event listeners
document.getElementById('add-org-event-type-btn').addEventListener('click', openAddEventTypeModal);
document.getElementById('cancel-event-type-btn').addEventListener('click', closeEventTypeModal);
document.getElementById('save-event-type-btn').addEventListener('click', saveEventType);
document.getElementById('add-field-to-type-btn').addEventListener('click', addFieldToEventType);

// Show button if can manage
if (canManage) {
    document.getElementById('add-org-event-type-btn').classList.remove('hidden');
}
```

---

## 7. Frontend UI - Project Page

**File**: `frontend/project.html`

**Location**: Add after the "Accessions" section, before "Accession Custom Fields"

**Implementation**: Nearly identical to org-admin.html event types section, with these changes:

1. Change all IDs: `org-event-types-*` → `project-event-types-*`
2. Change API calls: `api.getOrganizationEventTypes()` → `api.getProjectEventTypes(organizationId, projectId)`
3. Update section title: "Project Event Types"
4. Update description: "Event types available only to plants in this project"

---

## 8. Frontend UI - Plant Page

**File**: `frontend/plant.html`

This is the most complex UI addition.

**Location**: Add after plant details, before footer

**HTML Structure**:

```html
<!-- Events Section -->
<div class="bg-white rounded-lg shadow-md p-6 mt-6">
    <div class="flex justify-between items-center mb-4">
        <div>
            <h3 class="text-xl font-semibold text-gray-800">Events</h3>
            <p class="text-sm text-gray-600 mt-1">Timeline of events for this plant</p>
        </div>
        <button id="add-event-btn" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
            Add Event
        </button>
    </div>

    <div id="events-loading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-2 text-gray-600">Loading events...</p>
    </div>

    <div id="events-content" class="hidden">
        <div id="events-empty" class="text-center py-8 text-gray-600 hidden">
            No events recorded yet.
        </div>

        <div id="events-timeline" class="space-y-4 hidden">
            <!-- Events will be rendered here as timeline items -->
        </div>
    </div>
</div>

<!-- Add/Edit Event Modal -->
<div id="event-modal" class="hidden fixed z-10 inset-0 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75"></div>
        <div class="inline-block bg-white rounded-lg overflow-hidden shadow-xl transform transition-all sm:my-8 sm:max-w-lg sm:w-full">
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <h3 id="event-modal-title" class="text-lg font-medium mb-4">Add Event</h3>

                <form id="event-form">
                    <!-- Event Type Dropdown -->
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Event Type *</label>
                        <select id="event-type-select" required
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">Select event type...</option>
                        </select>
                    </div>

                    <!-- Event Date -->
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Event Date *</label>
                        <input type="datetime-local" id="event-date" required
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>

                    <!-- Dynamic Fields Container -->
                    <div id="event-dynamic-fields" class="mb-4">
                        <!-- Fields will be dynamically added based on selected event type -->
                    </div>

                    <!-- Notes -->
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                        <textarea id="event-notes" rows="3"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
                    </div>
                </form>
            </div>
            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button type="button" id="save-event-btn"
                    class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 sm:ml-3 sm:w-auto sm:text-sm">
                    Save
                </button>
                <button type="button" id="cancel-event-btn"
                    class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:w-auto sm:text-sm">
                    Cancel
                </button>
            </div>
        </div>
    </div>
</div>
```

**JavaScript**:

```javascript
// Add to existing variables
let events = [];
let availableEventTypes = [];  // Combination of org and project event types
let selectedEventType = null;
let editingEventId = null;

// Add to init()
await loadAvailableEventTypes();
await loadPlantEvents();

// Functions
async function loadAvailableEventTypes() {
    try {
        // Get org-level event types
        const orgTypes = await api.getOrganizationEventTypes(organizationId);

        // Get project-level event types for each project this plant's accession belongs to
        const accession = plant.accession;  // Assuming plant object has accession
        const projectTypes = [];

        if (accession && accession.projects) {
            for (const project of accession.projects) {
                const types = await api.getProjectEventTypes(organizationId, project.id);
                projectTypes.push(...types);
            }
        }

        // Combine and deduplicate
        availableEventTypes = [...orgTypes, ...projectTypes];

        // Populate dropdown
        const select = document.getElementById('event-type-select');
        select.innerHTML = '<option value="">Select event type...</option>' +
            availableEventTypes.map(et =>
                `<option value="${et.id}">${et.event_name}</option>`
            ).join('');

    } catch (error) {
        showError('Failed to load event types: ' + error.message);
    }
}

async function loadPlantEvents() {
    try {
        events = await api.getPlantEvents(organizationId, speciesId, accessionId, plantId);
        renderPlantEvents();
    } catch (error) {
        showError('Failed to load events: ' + error.message);
    } finally {
        document.getElementById('events-loading').classList.add('hidden');
        document.getElementById('events-content').classList.remove('hidden');
    }
}

function renderPlantEvents() {
    const timeline = document.getElementById('events-timeline');
    const emptyDiv = document.getElementById('events-empty');

    if (events.length === 0) {
        emptyDiv.classList.remove('hidden');
        timeline.classList.add('hidden');
        return;
    }

    emptyDiv.classList.add('hidden');
    timeline.classList.remove('hidden');

    // Sort by event_date DESC
    events.sort((a, b) => new Date(b.event_date) - new Date(a.event_date));

    timeline.innerHTML = events.map(event => {
        const eventDate = formatDate(event.event_date);
        const fieldValues = event.field_values || [];

        return `
            <div class="border-l-4 border-green-500 pl-4 pb-4">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="text-lg font-semibold text-gray-800">${event.event_type_name}</h4>
                        <p class="text-sm text-gray-500">${eventDate}</p>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="openEditEventModal('${event.id}')" class="text-blue-600 hover:underline text-sm">Edit</button>
                        <button onclick="deleteEvent('${event.id}')" class="text-red-600 hover:underline text-sm">Delete</button>
                    </div>
                </div>

                ${fieldValues.length > 0 ? `
                    <dl class="mt-2 grid grid-cols-2 gap-2 text-sm">
                        ${fieldValues.map(fv => `
                            <dt class="font-medium text-gray-700">${fv.field_name}:</dt>
                            <dd class="text-gray-600">${fv.value || '-'}</dd>
                        `).join('')}
                    </dl>
                ` : ''}

                ${event.notes ? `
                    <p class="mt-2 text-sm text-gray-600 italic">${event.notes}</p>
                ` : ''}
            </div>
        `;
    }).join('');
}

function openAddEventModal() {
    editingEventId = null;
    document.getElementById('event-modal-title').textContent = 'Add Event';
    document.getElementById('event-form').reset();

    // Set default date to now
    const now = new Date();
    const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);
    document.getElementById('event-date').value = localDateTime;

    document.getElementById('event-dynamic-fields').innerHTML = '';
    document.getElementById('event-modal').classList.remove('hidden');
}

function openEditEventModal(eventId) {
    const event = events.find(e => e.id === eventId);
    if (!event) return;

    editingEventId = eventId;
    document.getElementById('event-modal-title').textContent = 'Edit Event';

    // Set event type
    document.getElementById('event-type-select').value = event.event_type_id;
    selectedEventType = availableEventTypes.find(et => et.id === event.event_type_id);

    // Set date
    const eventDate = new Date(event.event_date);
    const localDateTime = new Date(eventDate.getTime() - eventDate.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);
    document.getElementById('event-date').value = localDateTime;

    // Set notes
    document.getElementById('event-notes').value = event.notes || '';

    // Render dynamic fields with values
    renderDynamicFields(event.field_values);

    document.getElementById('event-modal').classList.remove('hidden');
}

// Event type selection changed
document.getElementById('event-type-select').addEventListener('change', (e) => {
    const eventTypeId = e.target.value;
    selectedEventType = availableEventTypes.find(et => et.id === eventTypeId);
    renderDynamicFields();
});

function renderDynamicFields(existingValues = []) {
    const container = document.getElementById('event-dynamic-fields');

    if (!selectedEventType || !selectedEventType.fields) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = selectedEventType.fields
        .sort((a, b) => a.display_order - b.display_order)
        .map(field => {
            const existingValue = existingValues.find(v => v.field_id === field.id);
            const value = existingValue ? existingValue.value : '';

            const inputType = field.field_type === 'number' ? 'number' : 'text';
            const requiredAttr = field.is_required ? 'required' : '';

            return `
                <div class="mb-3">
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        ${field.field_name} ${field.is_required ? '*' : ''}
                    </label>
                    <input
                        type="${inputType}"
                        id="field-${field.id}"
                        data-field-id="${field.id}"
                        data-field-type="${field.field_type}"
                        value="${value}"
                        ${requiredAttr}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                </div>
            `;
        }).join('');
}

async function saveEvent() {
    if (!selectedEventType) {
        alert('Please select an event type');
        return;
    }

    // Collect field values
    const fieldValues = [];
    const fieldInputs = document.querySelectorAll('#event-dynamic-fields input[data-field-id]');

    for (const input of fieldInputs) {
        const fieldId = input.dataset.fieldId;
        const fieldType = input.dataset.fieldType;
        let value = input.value;

        if (value) {
            // Convert to appropriate type
            if (fieldType === 'number') {
                value = parseFloat(value);
            }

            fieldValues.push({
                field_id: fieldId,
                value: value
            });
        } else if (input.required) {
            alert(`Please fill in required field: ${input.previousElementSibling.textContent}`);
            return;
        }
    }

    const eventData = {
        event_type_id: selectedEventType.id,
        event_date: new Date(document.getElementById('event-date').value).toISOString(),
        notes: document.getElementById('event-notes').value || null,
        field_values: fieldValues
    };

    try {
        if (editingEventId) {
            await api.updatePlantEvent(organizationId, speciesId, accessionId, plantId, editingEventId, eventData);
            showSuccess('Event updated successfully');
        } else {
            await api.createPlantEvent(organizationId, speciesId, accessionId, plantId, eventData);
            showSuccess('Event created successfully');
        }
        closeEventModal();
        await loadPlantEvents();
    } catch (error) {
        showError('Failed to save event: ' + error.message);
    }
}

async function deleteEvent(eventId) {
    if (!confirm('Are you sure you want to delete this event?')) {
        return;
    }

    try {
        await api.deletePlantEvent(organizationId, speciesId, accessionId, plantId, eventId);
        showSuccess('Event deleted successfully');
        await loadPlantEvents();
    } catch (error) {
        showError('Failed to delete event: ' + error.message);
    }
}

function closeEventModal() {
    document.getElementById('event-modal').classList.add('hidden');
    document.getElementById('event-form').reset();
    editingEventId = null;
    selectedEventType = null;
}

// Event listeners
document.getElementById('add-event-btn').addEventListener('click', openAddEventModal);
document.getElementById('cancel-event-btn').addEventListener('click', closeEventModal);
document.getElementById('save-event-btn').addEventListener('click', saveEvent);
```

---

## Testing Checklist

After implementation, test in this order:

1. **Database Migration**:
   ```bash
   make upgrade  # Apply migration
   ```

2. **Org Event Types**:
   - Create org-level event type with 2 fields
   - Edit event type
   - Delete event type

3. **Project Event Types**:
   - Create project-level event type with 2 fields
   - Verify it only shows for plants in that project

4. **Plant Events**:
   - View plant page
   - Check dropdown shows both org and project event types
   - Create event with field values
   - Verify event appears in timeline
   - Edit event
   - Delete event

5. **Validation**:
   - Test required fields
   - Test field type validation (string vs number)
   - Test backdating events

6. **Permissions**:
   - As regular user: can view, can create events
   - As admin: can manage event types
   - As non-member: cannot access

---

## Common Issues & Solutions

### Issue: Migration fails
**Solution**: Check model relationships are bidirectional. Ensure all ForeignKey references exist.

### Issue: Event type fields not showing in dropdown
**Solution**: Check that `fields` relationship is eager-loaded in the query. Use `.options(joinedload(EventType.fields))`.

### Issue: Field validation not working
**Solution**: Implement validation logic in the route before creating EventFieldValue. Reference `app/core/field_validation.py` for patterns.

### Issue: Project event types showing for wrong plants
**Solution**: In `get_accessible_event_types()`, verify the plant's accession's projects are correctly queried.

### Issue: Date timezone issues
**Solution**: Always store UTC in database. Frontend should add 'Z' suffix and convert to local using `formatDate()` from `utils.js`.

---

## Quick Start Commands

```bash
# Apply migration
make upgrade

# Start dev server
make run

# Check for errors
make check

# If you need to rollback
make downgrade
```

---

## Next Steps

1. Implement backend routes (start with organization_event_types.py)
2. Test routes with API docs at http://localhost:8000/docs
3. Implement frontend API methods
4. Add UI sections one at a time
5. Test end-to-end flow

Good luck! The foundation is solid - you're implementing a clean EAV pattern that matches the existing codebase architecture.
