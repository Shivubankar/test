#!/bin/bash
# Run Django server accessible from network devices

echo "Starting BlackShield AuditSource server on network..."
echo ""
echo "Finding your IP address..."

# Try to get IP address
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

if [ -z "$IP" ]; then
    echo "Could not automatically detect IP. Please find your IP address manually:"
    echo "  Mac/Linux: ifconfig | grep 'inet '"
    echo "  Windows: ipconfig"
    echo ""
    IP="YOUR_IP_ADDRESS"
else
    echo "Your IP address appears to be: $IP"
    echo ""
fi

echo "Starting server on 0.0.0.0:8000..."
echo "Access the application from other devices at:"
echo "  http://$IP:8000/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 manage.py runserver 0.0.0.0:8000
