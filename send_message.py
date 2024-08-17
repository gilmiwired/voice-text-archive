import argparse
import json
import os

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_random_exponential

load_dotenv()

required_keys = [
    "GOOGLE_API_KEY",
    "NOTION_API_KEY",
]
not_set = []
for key in required_keys:
    if not os.getenv(key):
        not_set.append(key)
if len(not_set) > 0:
    fmt = ", ".join(not_set)
    raise Exception(f"Environment variables not set: {fmt}")


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""
NOTION_API_KEY = os.getenv("NOTION_API_KEY") or ""

genai.configure(api_key=GOOGLE_API_KEY)

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def get_last_block_id(page_id: str):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f'Bearer {os.getenv("NOTION_API_KEY")}',
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        blocks = response.json().get("results", [])
        if blocks:
            return blocks[-1]["id"]
    return None


def format_explanation(explanation_data):
    """Format the explanation data into a readable string."""
    formatted_explanation = ""
    for item in explanation_data:
        formatted_explanation += f"{item['word']}:\n{item['explanation']}\n\n"
    return formatted_explanation.strip()


def archive_notion(archive_data: str) -> str:
    """
    Uses Gemini API to retrieve content based on the archive_data and uploads it to a Notion page.

    Args:
        archive_data (str): Description of the data to be archived.

    Returns:
        str: Status message of the operation.
    """
    model = "gemini-1.5-pro-latest"
    google_api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={google_api_key}"
    headers = {"Content-Type": "application/json"}

    prompt_part = """
    You are the explainer. Your goal is to explain technical terms or difficult words in a given text and the images associated with those words. Specific criteria are words that are understandable at a junior high school level or higher.
You do not need to extract elements by force.
The information should be provided on a single line without line breaks. Please answer in Japanese. Exclude all other explanations.
    """
    json_schema = """
    {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "word": {"type": "string"},
                "explanation": {"type": "string"}
            },
            "required": ["word", "explanation"]
        }
    }
    """
    parts_text = f"{prompt_part}This time {archive_data} is message You have to use this JSON schema: '{json_schema}'"

    data = {
        "contents": [{"parts": [{"text": parts_text}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        return f"Failed to retrieve data: {response.status_code}, {response.text}"

    response_data = response.json()
    try:
        parts_data = json.loads(response_data["candidates"][0]["content"]["parts"][0]["text"])
        content = format_explanation(parts_data)
    except json.JSONDecodeError:
        content = response_data["candidates"][0]["content"]["parts"][0]["text"]


    page_id = "a88cbcd8ead44afab62ef9a0ea05b132"
    block_id = get_last_block_id(page_id)
    if not block_id:
        return "Failed to find the last block in the page."

    notion_api_key = os.getenv("NOTION_API_KEY")
    blocks_url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    notion_headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    blocks_data = {
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "読み上げ"}}]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": archive_data}}]
                },
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "解説"}}]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                },
            },
        ]
    }

    notion_response = requests.patch(
        blocks_url, headers=notion_headers, json=blocks_data
    )

    if not notion_response.ok:
        error_data = notion_response.json()
        raise Exception(
            f"Failed to add content to Notion page: {notion_response.status_code} {notion_response.reason} - {json.dumps(error_data)}"
        )

    return "Data archived successfully"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get chat completion from OpenAI.")
    parser.add_argument(
        "--input",
        help="Input message to send to the chat model.",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    try:
        completion = archive_notion(args.input)

    except Exception as e:
        print(f"Error: {e.__class__.__name__}, {e}")
