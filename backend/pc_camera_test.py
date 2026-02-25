import cv2
import requests
import json
import io
import time

API_URL = "http://localhost:8000/api/analyze"

def capture_and_analyze():
    print("カメラを起動しています...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("エラー: カメラを開けませんでした。")
        return

    print("スペースキーを押して撮影、'q'を押して終了します。")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("フレームを取得できませんでした。")
            break
            
        cv2.imshow("Vintage AI Shop Assistant - Camera Test", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):  # スペースキーで撮影
            print("撮影しました！AIに送信中...")
            cv2.destroyAllWindows()
            
            # 画像をエンコードして送信
            success, encoded_image = cv2.imencode('.jpg', frame)
            if success:
                files = {"file": ("capture.jpg", encoded_image.tobytes(), "image/jpeg")}
                try:
                    start_time = time.time()
                    response = requests.post(API_URL, files=files)
                    elapsed = time.time() - start_time
                    
                    print(f"--- APIレスポンス ({elapsed:.2f}秒) ---")
                    if response.status_code == 200:
                        data = response.json()
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    else:
                        print(f"Error Code: {response.status_code}")
                        print(response.text)
                except Exception as e:
                    print(f"通信エラー: {e}")
            else:
                print("画像のエンコードに失敗しました。")
                
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_and_analyze()
