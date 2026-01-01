# University Attendance System Using Face Recognition

##  Project Overview
This project presents a network-based software architecture for managing university attendance using **Face Recognition (ArcFace)** technology.  
The system aims to automate attendance verification securely and efficiently within lecture halls and laboratories.

##  Core Technologies
- **Backend:** Django (Python)
- **Face Recognition:** ArcFace (ONNX)
- **Face Detection:** MediaPipe + OpenCV (fallback)
- **Database:** SQLite (development)
- **Frontend:** HTML, CSS, JavaScript
- **Security:** Device Key Authorization

##  System Architecture
The system follows a modular architecture consisting of:
- Authentication & Authorization Module
- Face Recognition Service
- Attendance Management Module
- Web Interface (Enrollment & Verification Pages)

##  Project Structure
UNIVERSITY_ATTENDANCE_SYSTEM/
├── auth_app/
├── face_service/
├── frontend/
├── project/
├── manage.py
├── requirements.txt
├── README.md




##  Features
- Student face enrollment
- Real-time face verification
- Room-based authorization
- Attendance logging with confidence score
- Secure device-based access

##  Installation
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
