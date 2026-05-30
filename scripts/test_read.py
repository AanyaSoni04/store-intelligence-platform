import cv2

cap = cv2.VideoCapture('c:/Users/sonir/Downloads/CCTV Footage/CAM 5.mp4')
print('Looping...')
count = 0
while cap.isOpened():
    ret, f = cap.read()
    if not ret:
        print("Read returned False. Stopping.")
        break
    count += 1
print(f'Read {count} frames.')
