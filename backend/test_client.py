import requests

API_URL = "http://localhost:8000/api/analyze"

def test_analyze():
    # テスト用のダミー画像（真っ黒な画像などでもエラーが起きないか確認）
    from PIL import Image
    import io

    # ダミー画像をオンメモリで作成
    img = Image.new('RGB', (200, 200), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    files = {"file": ("test_image.jpg", img_byte_arr, "image/jpeg")}
    print("Calling API...")
    
    try:
        response = requests.post(API_URL, files=files)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(response.json())
    except Exception as e:
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    test_analyze()
