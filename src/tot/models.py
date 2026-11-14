import os
import time
import openai
import requests

completion_tokens = prompt_tokens = 0

api_key = os.getenv("OPENAI_API_KEY", "")
if api_key != "":
    openai.api_key = api_key
else:
    print("Warning: OPENAI_API_KEY is not set")

def completions_with_backoff(**kwargs):
    model = kwargs.get("model", "gemini-3.8-flash")
    print(f"Calling {model}...", flush=True)
    url = "https://generativelanguage." + "googleapis.com" + f"/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": openai.api_key, "Content-Type": "application/json"}
    prompt = kwargs["messages"][0]["content"]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
              "temperature": kwargs.get("temperature", 0.7),
         "maxOutputTokens": kwargs.get("max_tokens", 1000),
         "candidateCount": kwargs.get("n", 1),
            
        }
    }
    for _ in range(6):
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code not in (429, 503):
            break
        print(f"Rate limit/busy ({res.status_code}), waiting 15s...", flush=True)
        time.sleep(15)

    if res.status_code != 200:
        raise Exception(f"API Error {res.status_code}: {res.text}")
    print("Response received!", flush=True)
    class Obj(dict):
        __getattr__ = dict.get
    data = res.json()
    choices = [Obj(message=Obj(content=c["content"]["parts"][0]["text"])) for c in data["candidates"]]
    usage = data.get("usageMetadata", {})
    return Obj(
        choices=choices,
        usage=Obj(completion_tokens=usage.get("candidatesTokenCount", 0), prompt_tokens=usage.get("promptTokenCount", 0))
    )

def gpt(prompt, model="gpt-4", temperature=0.7, max_tokens=1000, n=1, stop=None) -> list:
    messages = [{"role": "user", "content": prompt}]
    return chatgpt(messages, model=model, temperature=temperature, max_tokens=max_tokens, n=n, stop=stop)
    
def chatgpt(messages, model="gpt-4", temperature=0.7, max_tokens=1000, n=1, stop=None) -> list:
    global completion_tokens, prompt_tokens
    outputs = []
    while n > 0:
        cnt = min(n, 20)
        n -= cnt
        res = completions_with_backoff(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, n=cnt, stop=stop)
        outputs.extend([choice.message.content for choice in res.choices])
        completion_tokens += res.usage.completion_tokens
        prompt_tokens += res.usage.prompt_tokens
    return outputs
    
def gpt_usage(backend="gpt-4"):
    global completion_tokens, prompt_tokens
    cost = 0
    if backend == "gpt-4":
        cost = completion_tokens / 1000 * 0.06 + prompt_tokens / 1000 * 0.03
    elif backend == "gpt-3.5-turbo":
        cost = completion_tokens / 1000 * 0.002 + prompt_tokens / 1000 * 0.0015
    elif backend == "gpt-4o":
        cost = completion_tokens / 1000 * 0.00250 + prompt_tokens / 1000 * 0.01
    return {"completion_tokens": completion_tokens, "prompt_tokens": prompt_tokens, "cost": cost}
