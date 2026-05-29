import json
import os
import requests

def call_llm(prompt: str, max_tokens: int = 1000) -> str:
    payload = {"model": "claude-sonnet-4-6",
               "max_tokens": max_tokens,
               "messages": [{"role": "user", "content": prompt}]}

    response = requests.post("https://api.anthropic.com/v1/messages",
                             json= payload,
                             headers={"anthropic-version": "2023-06-01",
                                      "x-api-key": os.environ.get("ANTHROPIC_API_KEY", "")}, timeout=30)

    response.raise_for_status()
    data = response.json()
    return data["content"][0]["text"].strip()

def decompose_goal_with_llm(goal: str, context: dict) -> list[str]:
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": (
                f"Decompose this goal into 2-4 concrete subtasks.\n"
                f"Goal: {goal}\n"
                f"Context: {context}\n"
                f"Reply with ONLY a JSON array of strings. Example:\n"
                f'["subtask_one", "subtask_two", "subtask_three"]\n'
                f"No explanation. No markdown. Just the array."
            )
        }]
    }

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        json=payload,
        headers={
            "anthropic-version": "2023-06-01",
            "x-api-key": os.environ.get("ANTHROPIC_API_KEY", "")
        },
        timeout=30
    )

    response.raise_for_status()
    data = response.json()
    text = data["content"][0]["text"].strip()
    return json.loads(text)