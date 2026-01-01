import cv2
import base64
import requests
import time

# CONFIG
API_URL = "http://127.0.0.1:8000/auth/verify-face/"
TOKEN = "PUT_YOUR_TOKEN_HERE"  # احصل على التوكن من /auth/login/
ROOM_CODE = "1234"             # اختياري: كود القاعة

headers = {
    "Authorization": f"Token {TOKEN}"
}

def capture_and_send(cap):
    ret, frame = cap.read()
    if not ret:
        return None
    # encode jpg
    _, jpg = cv2.imencode('.jpg', frame)
    b64 = base64.b64encode(jpg.tobytes()).decode('utf-8')
    # send as form-data file:
    files = {'image': ('capture.jpg', jpg.tobytes(), 'image/jpeg')}
    data = {'room_code': ROOM_CODE}
    # If your API expects token in header, use headers, else pass data
    resp = requests.post(API_URL, files=files, headers=headers, data=data, timeout=10)
    return resp

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    print("Camera opened. Press q to quit. Press s to snap & send.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Camera (press s to send)", frame)
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break
        if k == ord('s'):
            print("Sending snapshot...")
            resp = capture_and_send(cap)
            if resp is not None:
                try:
                    print("Response:", resp.status_code, resp.json())
                except Exception:
                    print("Response text:", resp.text)
            else:
                print("No response")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
