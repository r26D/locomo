import numpy as np
import json
import time
import sys
import os

import google.generativeai as genai
from anthropic import Anthropic
from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError, InternalServerError

_openai_client = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.environ["LOCOMO_OPENAI_API_KEY"])
    return _openai_client


def _default_chat_model() -> str:
    return os.environ.get("LOCOMO_OPENAI_CHAT_MODEL", "gpt-4o-mini")


def _default_chat_model_16k() -> str:
    return os.environ.get("LOCOMO_OPENAI_CHAT_MODEL_16K", _default_chat_model())


def _default_embedding_model() -> str:
    return os.environ.get("LOCOMO_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def get_openai_embedding(texts, model=None):
    if model is None:
        model = _default_embedding_model()
    texts = [text.replace("\n", " ") for text in texts]
    client = _get_openai_client()
    resp = client.embeddings.create(input=texts, model=model)
    return np.array([d.embedding for d in resp.data])


def set_anthropic_key():
    pass


def set_gemini_key():

    # Or use `os.getenv('GOOGLE_API_KEY')` to fetch an environment variable.
    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])


def set_openai_key():
    global _openai_client
    _openai_client = OpenAI(api_key=os.environ['LOCOMO_OPENAI_API_KEY'])


def run_json_trials(query, num_gen=1, num_tokens_request=1000, 
                model='davinci', use_16k=False, temperature=1.0, wait_time=1, examples=None, input=None):

    run_loop = True
    counter = 0
    while run_loop:
        try:
            if examples is not None and input is not None:
                output = run_chatgpt_with_examples(query, examples, input, num_gen=num_gen, wait_time=wait_time,
                                                   num_tokens_request=num_tokens_request, use_16k=use_16k, temperature=temperature).strip()
            else:
                output = run_chatgpt(query, num_gen=num_gen, wait_time=wait_time, model=model,
                                                   num_tokens_request=num_tokens_request, use_16k=use_16k, temperature=temperature)
            output = output.replace('json', '') # this frequently happens
            facts = json.loads(output.strip())
            run_loop = False
        except json.decoder.JSONDecodeError:
            counter += 1
            time.sleep(1)
            print("Retrying to avoid JsonDecodeError, trial %s ..." % counter)
            print(output)
            if counter == 10:
                print("Exiting after 10 trials")
                sys.exit()
            continue
    return facts


def run_claude(query, max_new_tokens, model_name):

    if model_name == 'claude-sonnet':
        model_name = os.environ.get("LOCOMO_CLAUDE_SONNET_MODEL", "claude-3-5-sonnet-20241022")
    elif model_name == 'claude-haiku':
        model_name = os.environ.get("LOCOMO_CLAUDE_HAIKU_MODEL", "claude-3-5-haiku-20241022")

    client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )
    message = client.messages.create(
        max_tokens=max_new_tokens,
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ],
        model=model_name,
    )
    print(message.content)
    return message.content[0].text


def run_gemini(model, content: str, max_tokens: int = 0):

    try:
        response = model.generate_content(content)
        return response.text
    except Exception as e:
        print(f'{type(e).__name__}: {e}')
        return None


def run_chatgpt(query, num_gen=1, num_tokens_request=1000, 
                model='chatgpt', use_16k=False, temperature=1.0, wait_time=1):

    client = _get_openai_client()
    completion = None
    while completion is None:
        wait_time = wait_time * 2
        try:
            if model == 'chatgpt':
                messages = [
                        {"role": "system", "content": query}
                    ]
                completion = client.chat.completions.create(
                    model=_default_chat_model(),
                    temperature=temperature,
                    max_tokens=num_tokens_request,
                    n=num_gen,
                    messages=messages
                )
            else:
                completion = client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    max_tokens=num_tokens_request,
                    n=num_gen,
                    messages=[
                        {"role": "user", "content": query}
                    ]
                )
        except APIError as e:
            print(f"OpenAI API returned an API Error: {e}; waiting for {wait_time} seconds")
            time.sleep(wait_time)
            pass
        except APIConnectionError as e:
            print(f"Failed to connect to OpenAI API: {e}; waiting for {wait_time} seconds")
            time.sleep(wait_time)
            pass
        except RateLimitError as e:
            print(f"OpenAI API request exceeded rate limit: {e}")
            pass
        except InternalServerError as e:
            print(f"OpenAI API service error: {e}; waiting for {wait_time} seconds")
            time.sleep(wait_time)
            pass

    return completion.choices[0].message.content


def run_chatgpt_with_examples(query, examples, input, num_gen=1, num_tokens_request=1000, use_16k=False, wait_time = 1, temperature=1.0):

    client = _get_openai_client()
    completion = None

    messages = [
        {"role": "system", "content": query}
    ]
    for inp, out in examples:
        messages.append(
            {"role": "user", "content": inp}
        )
        messages.append(
            {"role": "system", "content": out}
        )
    messages.append(
        {"role": "user", "content": input}
    )

    chat_model = _default_chat_model_16k() if use_16k else _default_chat_model()

    while completion is None:
        wait_time = wait_time * 2
        try:
            completion = client.chat.completions.create(
                model=chat_model,
                temperature=temperature,
                max_tokens=num_tokens_request,
                n=num_gen,
                messages=messages
            )
        except APIError as e:
            print(f"OpenAI API returned an API Error: {e}; waiting for {wait_time} seconds")
            time.sleep(wait_time)
            pass
        except APIConnectionError as e:
            print(f"Failed to connect to OpenAI API: {e}; waiting for {wait_time} seconds")
            time.sleep(wait_time)
            pass
        except RateLimitError as e:
            print(f"OpenAI API request exceeded rate limit: {e}")
            pass
        except InternalServerError as e:
            print(f"OpenAI API service error: {e}; waiting for {wait_time} seconds")
            time.sleep(wait_time)
            pass

    return completion.choices[0].message.content
