# BlackShield AuditSource

Internal Governance, Risk & Compliance (GRC) audit tool for BlackShield HQ.

## Features

- Two-stage workpaper workflow (Contributor → Auditor)
- Role-based access control (Admin, Auditor, Contributor)
- Evidence and workpaper file management
- Acceptance gatekeeper (requires workpaper + test notes)
- Automatic locking after acceptance
- Comprehensive audit trail with sign-offs

## Tech Stack

- Backend: Python 3.11, Django 5.x
- Frontend: Django Templates + Bootstrap 5
- Database: SQLite (development), PostgreSQL-ready
- Authentication: Django Auth

## Installation & Setup

### 1. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Create User Groups (Optional but Recommended)

Run the Django shell and create groups:

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import Group

Group.objects.get_or_create(name='Admin')
Group.objects.get_or_create(name='Auditor')
Group.objects.get_or_create(name='Contributor')
```

Assign users to groups via Django admin panel at `/admin/auth/user/`.

### 6. Run Development Server

**Local Access Only:**
```bash
python manage.py runserver
```
Access at: `http://127.0.0.1:8000/`

**Access from Other Devices on Same Network:**
```bash
python manage.py runserver 0.0.0.0:8000
```

To find your local IP address:
- **Mac/Linux:** `ifconfig | grep "inet " | grep -v 127.0.0.1`
- **Windows:** `ipconfig` (look for IPv4 Address)

Then access from other devices using: `http://YOUR_IP_ADDRESS:8000/`

**Example:** If your IP is `192.168.1.100`, access at `http://192.168.1.100:8000/`

Access Django admin at: `http://YOUR_IP_ADDRESS:8000/admin/`

## Usage

### Workflow

1. **Admin** creates an Engagement and Control Requirements
2. **Contributor** uploads evidence files
3. **Auditor** reviews evidence, uploads workpaper, and writes test notes
4. **Auditor** accepts the request (only if workpaper + test notes exist)
5. System automatically locks the request and stamps sign-off
6. **Admin** can unlock if needed

### Roles

- **Admin**: Full access, can create engagements/controls, unlock requests
- **Auditor**: Can review, upload workpapers, write test notes, accept/return requests
- **Contributor**: Can upload evidence files only

### Dashboard

The main dashboard displays all controls in a table with the following columns:

1. Control ID
2. Control Description
3. Request (Evidence) - Upload/download evidence
4. Documents (Workpaper) - Upload/download workpapers
5. Test Performed - View/add test notes
6. Status - Current request status
7. Sign-Offs - Review information
8. Actions - Accept/Return/Unlock buttons

## Database

- Development: SQLite (`db.sqlite3`)
- Production: PostgreSQL (configure in `settings.py`)

## File Storage

Uploaded files are stored in the `media/` directory:
- Evidence files: `media/evidence/YYYY/MM/DD/`
- Workpaper files: `media/workpapers/YYYY/MM/DD/`

## Production Deployment

1. Set `DEBUG = False` in `settings.py`
2. Update `SECRET_KEY` with a secure value
3. Configure `ALLOWED_HOSTS`
4. Set up PostgreSQL database
5. Configure static files serving
6. Set up media files serving
7. Use a production WSGI server (e.g., Gunicorn)
8. Set up reverse proxy (e.g., Nginx)

## License

Internal use only - BlackShield HQ
