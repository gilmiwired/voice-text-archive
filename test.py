import requests

def post_audio_file(url, file_path, api_key):
    """指定されたURLに音声ファイルをPOSTする関数"""
    with open(file_path, 'rb') as audio_file:
        files = {'file': audio_file}
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'audio/wav'
        }
        response = requests.post(url, files=files, headers=headers)
        return response

url = ""
api_key = ''

file_path = 'sample.wav'
response = post_audio_file(url, file_path, api_key)

print("Status Code:", response.status_code)
print("Response Body:", response.text)
