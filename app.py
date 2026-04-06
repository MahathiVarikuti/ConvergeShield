"""
ConvergeShield: AI-Assisted IT-OT Security Monitoring System
Main application entry point

Run with: python app.py
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("="*60)
    print("ConvergeShield - AI-Assisted IT-OT Security Monitoring")
    print("="*60)
    print("\nStarting server...")
    print("Dashboard:  http://127.0.0.1:5000/")
    print("Incidents:  http://127.0.0.1:5000/incidents")
    print("Analytics:  http://127.0.0.1:5000/analytics")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
