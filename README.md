# voice-text-archive

## 概要

録音した音声データをテキストデータに変換し技術用語などに補足を入れた上でNotionページにアーカイブとして残すアプリ

・[Whisper API](https://platform.openai.com/docs/guides/speech-to-text)を使った録音した音声データをテキストデータに変換する機能<br>
・[Gemini API](https://ai.google.dev/)を使った与えられたテキストデータから技術用語などに補足を入れたテキストを生成する機能<br>
・[Notion API](https://developers.notion.com/)を使ったテキストデータをNotionにアーカイブとして残す機能<br>

## how to use

環境変数を設定<br>
voice-text-archiveディレクトリ上で
```
cp .env.example .env
```
.envファイルの各APIやNotionのページIDを設定する<br>

環境変数設定後
```
poetry install
```

サーバーを起動(別のタブで)
```
poetry run uvicorn api.app:app --reload
```

アプリを起動
```
poetry run python audio_transcriber.py  
```