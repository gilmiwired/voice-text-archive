import io
import os
import threading
import wave

import numpy as np
import requests
import sounddevice as sd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

samplerate = 16000  # Whisperモデル推奨のサンプリングレート
channels = 1
dtype = "int16"
duration = 30


def record_audio(
    duration: int, samplerate: int, channels: int, dtype: str
) -> np.ndarray:
    """指定したパラメータで音声を録音します。

    Args:
        duration (int): 録音時間 (秒)
        samplerate (int): サンプリングレート
        channels (int): チャンネル数
        dtype (str): データ型

    Returns:
        np.ndarray: 録音された音声データ
    """
    recording = sd.rec(
        int(samplerate * duration),
        samplerate=samplerate,
        channels=channels,
        dtype=dtype,
    )
    sd.wait()
    return recording


def send_to_api(text: str) -> None:
    """テキストデータをAPIに送信します。

    Args:
        text (str): 送信するテキスト
    """
    url = "http://127.0.0.1:8000/archive"
    headers = {"Content-Type": "application/json"}
    data = {"message": text}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("Text successfully sent to the API.")
    else:
        print("Error sending text to API:", response.status_code, response.text)


def convert_to_wav(
    data: np.ndarray, samplerate: int, channels: int, dtype: str
) -> io.BytesIO:
    """NumPy配列の音声データをWAV形式に変換します。

    Args:
        data (np.ndarray): 音声データ
        samplerate (int): サンプリングレート
        channels (int): チャンネル数
        dtype (str): データ型

    Returns:
        io.BytesIO: WAV形式の音声データ
    """
    byte_io = io.BytesIO()
    with wave.open(byte_io, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(np.dtype(dtype).itemsize)
        wav_file.setframerate(samplerate)
        wav_file.writeframes(data.astype(np.int16).tobytes())
    byte_io.seek(0)
    return byte_io


def transcribe_audio(audio_stream: io.BytesIO) -> None:
    """音声データをテキストに変換し、結果をAPIに送信します。

    Args:
        audio_stream (io.BytesIO): WAV形式の音声データ
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    files = {"file": ("temp_audio.wav", audio_stream, "audio/wav")}
    data = {"model": "whisper-1"}
    response = requests.post(
        "https://api.openai.com/v1/audio/transcriptions",
        headers=headers,
        data=data,
        files=files,
    )
    if response.status_code == 200:
        text = response.json()["text"]
        print(text)
        threading.Thread(target=send_to_api, args=(text,)).start()
    else:
        print("Error:", response.status_code, response.json())


def process_audio(data: np.ndarray) -> None:
    """音声データを処理して、テキスト変換とAPI送信を行います。

    Args:
        data (np.ndarray): 録音された音声データ
    """
    audio_stream = convert_to_wav(data, samplerate, channels, dtype)
    threading.Thread(target=transcribe_audio, args=(audio_stream,)).start()


def main():
    """アプリケーションのメインループです。ユーザーが中断するまで繰り返し音声を録音し、処理します。"""
    while True:
        audio_data = record_audio(duration, samplerate, channels, dtype)
        process_audio(audio_data)


if __name__ == "__main__":
    main()
