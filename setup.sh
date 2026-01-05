#!/bin/bash
# Quick setup script for BlackShield AuditSource

echo "Setting up BlackShield AuditSource..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create groups
echo "Creating user groups..."
python manage.py shell << EOF
from django.contrib.auth.models import Group
Group.objects.get_or_create(name='Admin')
Group.objects.get_or_create(name='Auditor')
Group.objects.get_or_create(name='Contributor')
print("Groups created successfully!")
EOF

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a superuser: python manage.py createsuperuser"
echo "2. Run the server: python manage.py runserver"
echo "3. Access the application at: http://127.0.0.1:8000/"
echo "4. Access admin at: http://127.0.0.1:8000/admin/"
