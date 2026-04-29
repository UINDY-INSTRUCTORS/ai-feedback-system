#!/usr/bin/env python3
"""
AI Provider abstraction for multi-provider support.

Built-in providers (with sensible defaults):
  - github_models: GitHub Models API (default in Actions, uses GITHUB_TOKEN)
  - openrouter:    OpenRouter (OpenAI-compatible, uses OPENROUTER_API_KEY)
  - anthropic:     Anthropic Claude API (uses ANTHROPIC_API_KEY)
  - gemini:        Google Gemini API (uses GEMINI_API_KEY)
  - openai:        OpenAI directly (uses OPENAI_API_KEY)
  - vertex:        Google Vertex AI (uses ADC via gcloud / GOOGLE_APPLICATION_CREDENTIALS)

Custom providers can be added in config without editing source — set 'provider' to any name
and set 'api' to one of the supported protocols: openai, anthropic, gemini, vertex.

All providers return the same (text, response_data, request_payload) tuple.

Configuration priority:
  1. Environment variables (AI_PROVIDER, AI_MODEL, AI_API, etc.)
  2. Global config file (~/.ai-feedback/config.yml)
  3. Per-repo .github/config.yml
  4. Defaults (github_models + gpt-4o)

Vertex AI config:
  project:  GCP project ID (GOOGLE_CLOUD_PROJECT env var or 'project' in config)
  location: GCP region     (GOOGLE_CLOUD_LOCATION env var or 'location' in config, default: us-central1)
  Auth is handled automatically via Application Default Credentials (run: gcloud auth application-default login)
"""

import os
import json
import random
import sys
import time
import yaml
import requests
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Provider endpoint defaults (vertex is computed dynamically from project/location)
PROVIDER_ENDPOINTS = {
    'github_models': 'https://models.inference.ai.azure.com',
    'openrouter':    'https://openrouter.ai/api/v1',
    'openai':        'https://api.openai.com/v1',
    'anthropic':     'https://api.anthropic.com',
    'gemini':        'https://generativelanguage.googleapis.com',
    'vertex':        None,
}

# Maps known provider name -> env var for API key
PROVIDER_KEY_ENVVARS = {
    'github_models': 'GITHUB_TOKEN',
    'openrouter':    'OPENROUTER_API_KEY',
    'openai':        'OPENAI_API_KEY',
    'anthropic':     'ANTHROPIC_API_KEY',
    'gemini':        'GEMINI_API_KEY',
}

# Maps api protocol -> default env var for API key (fallback for unknown provider names)
API_KEY_ENVVARS = {
    'openai':     'OPENAI_API_KEY',
    'anthropic':  'ANTHROPIC_API_KEY',
    'gemini':     'GEMINI_API_KEY',
}

# APIs that use ADC/service-account auth instead of an API key
APIS_WITHOUT_API_KEY = {'vertex'}

# Default api protocol per known provider name
PROVIDER_DEFAULT_API = {
    'github_models': 'openai',
    'openrouter':    'openai',
    'openai':        'openai',
    'anthropic':     'anthropic',
    'gemini':        'gemini',
    'vertex':        'vertex',
}

# Default models per provider
PROVIDER_DEFAULT_MODELS = {
    'github_models': 'gpt-4o',
    'openrouter':    'openai/gpt-4o',
    'openai':        'gpt-4o',
    'anthropic':     'claude-sonnet-4-20250514',
    'gemini':        'gemini-2.5-flash',
    'vertex':        'google/gemini-2.5-flash',
}

GLOBAL_CONFIG_PATH = Path.home() / '.ai-feedback' / 'config.yml'


def load_global_config() -> dict:
    """Load global config from ~/.ai-feedback/config.yml if it exists."""
    if GLOBAL_CONFIG_PATH.exists():
        try:
            with open(GLOBAL_CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load global config: {e}", file=sys.stderr)
    return {}


def create_default_global_config():
    """Create a default global config file with documentation."""
    GLOBAL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    default_config = """# AI Feedback System - Global Configuration
# This file sets defaults for local feedback runs.
# Environment variables take precedence over this file, and this file
# takes precedence over per-repo .github/config.yml.
#
# Priority: env vars > --profile (CLI) > this file (top-level) > per-repo config > defaults

# Default active profile (overridden by --profile on the CLI or AI_PROFILE env var)
# profile: github

# Named profiles — switch with: --profile <name>
# profiles:
#   github:
#     provider: github_models
#     model:
#       primary: gpt-4o
#       fallback: gpt-4o-mini
#       extractor: gpt-4o-mini
#
#   anthropic:
#     provider: anthropic
#     model:
#       primary: claude-sonnet-4-20250514
#       fallback: claude-haiku-4-5-20251001
#       extractor: claude-haiku-4-5-20251001
#
#   openrouter-llama:
#     provider: openrouter
#     model:
#       primary: meta-llama/llama-4-scout
#       fallback: meta-llama/llama-4-scout
#       extractor: openai/gpt-4o-mini
#
#   local:
#     provider: openrouter
#     api_base: http://localhost:1234/v1
#     disable_json_mode: true
#     model:
#       primary: your-local-model-id

# Fallback top-level settings (used when no profile is active)
provider: github_models
# model:
#   primary: gpt-4o
#   fallback: gpt-4o-mini
#   extractor: gpt-4o-mini

# API keys (environment variables always take precedence)
# api_key: your-key-here

# disable_json_mode: false
"""
    with open(GLOBAL_CONFIG_PATH, 'w') as f:
        f.write(default_config)
    print(f"Created default global config: {GLOBAL_CONFIG_PATH}")


def resolve_provider_config(repo_config: dict = None, profile: str = None) -> dict:
    """
    Resolve provider configuration from all sources.
    Priority: env vars > profile > global config > repo config > defaults.

    Returns dict with keys: provider, model, fallback, extractor, api_key, api_base
    """
    global_config = load_global_config()
    repo_config = repo_config or {}

    # Resolve named profile (CLI --profile > AI_PROFILE env var > global config default)
    profile_name = profile or os.environ.get('AI_PROFILE') or global_config.get('profile')
    profile_config = {}
    if profile_name:
        profiles = global_config.get('profiles', {})
        if profile_name in profiles:
            profile_config = profiles[profile_name] or {}
        else:
            available = ', '.join(profiles.keys()) if profiles else 'none'
            print(f"Warning: profile '{profile_name}' not found. Available: {available}", file=sys.stderr)

    # Provider: env var > profile > global config > repo config > default
    provider = (
        os.environ.get('AI_PROVIDER')
        or profile_config.get('provider')
        or global_config.get('provider')
        or repo_config.get('provider')
        or 'github_models'
    )

    # API protocol: env var > profile > global config > repo config > inferred from provider
    api = (
        os.environ.get('AI_API')
        or profile_config.get('api')
        or global_config.get('api')
        or repo_config.get('api')
        or PROVIDER_DEFAULT_API.get(provider, 'openai')
    )

    # Model names: env var > profile > global config > repo config > provider default
    repo_model = repo_config.get('model', {})
    global_model = global_config.get('model', {})
    profile_model = profile_config.get('model', {})
    default_model = PROVIDER_DEFAULT_MODELS.get(provider, 'gpt-4o')

    model = (
        os.environ.get('AI_MODEL')
        or profile_model.get('primary')
        or global_model.get('primary')
        or repo_model.get('primary')
        or default_model
    )
    fallback = (
        os.environ.get('AI_FALLBACK_MODEL')
        or profile_model.get('fallback')
        or global_model.get('fallback')
        or repo_model.get('fallback')
        or model
    )
    extractor = (
        os.environ.get('AI_EXTRACTOR_MODEL')
        or profile_model.get('extractor')
        or global_model.get('extractor')
        or repo_model.get('extractor')
        or ('gpt-4o-mini' if provider == 'github_models' else model)
    )
    extractor_fallback = (
        os.environ.get('AI_EXTRACTOR_FALLBACK_MODEL')
        or profile_model.get('extractor_fallback')
        or global_model.get('extractor_fallback')
        or repo_model.get('extractor_fallback')
        or fallback
    )

    # API key: env var (provider-specific) > env var (api-based) > AI_API_KEY > config
    key_envvar = PROVIDER_KEY_ENVVARS.get(provider) or API_KEY_ENVVARS.get(api)
    api_key = (
        (os.environ.get(key_envvar) if key_envvar else None)
        or os.environ.get('AI_API_KEY')
        or profile_config.get('api_key')
        or global_config.get('api_key')
    )

    # Vertex AI project and location (only used when api == 'vertex')
    vertex_project = (
        os.environ.get('GOOGLE_CLOUD_PROJECT')
        or profile_config.get('project')
        or global_config.get('project')
        or repo_config.get('project')
    )
    vertex_location = (
        os.environ.get('GOOGLE_CLOUD_LOCATION')
        or profile_config.get('location')
        or global_config.get('location')
        or repo_config.get('location')
        or 'us-central1'
    )

    # API base URL: env var > profile > global config > provider default
    # For vertex api, compute dynamically from project + location if not overridden
    api_base = (
        os.environ.get('AI_API_BASE')
        or profile_config.get('api_base')
        or global_config.get('api_base')
        or PROVIDER_ENDPOINTS.get(provider)
    )
    if api == 'vertex' and not api_base:
        if not vertex_project:
            raise ValueError(
                "Vertex AI requires a GCP project. Set GOOGLE_CLOUD_PROJECT env var "
                "or add 'project: your-project-id' to your profile in ~/.ai-feedback/config.yml"
            )
        api_base = (
            f"https://{vertex_location}-aiplatform.googleapis.com/v1beta1"
            f"/projects/{vertex_project}/locations/{vertex_location}/endpoints/openapi"
        )

    # Disable JSON mode
    disable_json_mode = (
        os.environ.get('AI_DISABLE_JSON_MODE', '').lower() in ('true', '1', 'yes')
        or profile_config.get('disable_json_mode', False)
        or global_config.get('disable_json_mode', False)
        or repo_config.get('disable_json_mode', False)
    )

    # Request timeout: env var > profile > global config > repo config > default
    _timeout_env = os.environ.get('AI_REQUEST_TIMEOUT')
    request_timeout = (
        int(_timeout_env) if _timeout_env
        else profile_config.get('request_timeout')
        or global_config.get('request_timeout')
        or repo_config.get('request_timeout')
        or 240
    )

    # Frequency penalty (optional): profile > global config > repo config
    _fp = (
        profile_config.get('frequency_penalty')
        if profile_config.get('frequency_penalty') is not None
        else global_config.get('frequency_penalty')
        if global_config.get('frequency_penalty') is not None
        else repo_config.get('frequency_penalty')
    )

    def _first(*sources, key):
        for s in sources:
            v = s.get(key)
            if v is not None:
                return v
        return None

    return {
        'provider': provider,
        'api': api,
        'model': model,
        'fallback': fallback,
        'extractor': extractor,
        'extractor_fallback': extractor_fallback,
        'api_key': api_key,
        'api_base': api_base,
        'disable_json_mode': disable_json_mode,
        'request_timeout': request_timeout,
        'vertex_project': vertex_project,
        'vertex_location': vertex_location,
        'frequency_penalty': _fp,
        'system_prompt': _first(profile_config, global_config, repo_config, key='system_prompt'),
        'extractor_system_prompt': _first(profile_config, global_config, repo_config, key='extractor_system_prompt'),
        'extractor_max_output_tokens': _first(profile_config, global_config, repo_config, key='extractor_max_output_tokens'),
    }


def _call_openai_compatible(
    messages: list,
    model: str,
    api_key: str,
    api_base: str,
    config: dict,
    json_mode: bool = True,
    max_retries: int = 3,
    extra_headers: dict = None,
    session_id: str = None,
    disable_json_mode: bool = False,
) -> Tuple[str, dict, dict]:
    """
    Call an OpenAI-compatible chat completions endpoint.
    Works for: github_models, openrouter, openai.
    """
    endpoint = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if extra_headers:
        headers.update(extra_headers)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": config.get('max_output_tokens', 2000),
    }
    if config.get('frequency_penalty') is not None:
        payload["frequency_penalty"] = config['frequency_penalty']
    if json_mode and not disable_json_mode:
        payload["response_format"] = {"type": "json_object"}
    if session_id:
        payload["session_id"] = session_id

    timeout = config.get('request_timeout', 240)
    last_error = None

    for attempt in range(max_retries):
        try:
            print(f"   Calling {model} via {api_base}... (attempt {attempt + 1}/{max_retries})")
            response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()

            result = response.json()
            msg = result['choices'][0]['message']
            text = msg.get('content') or msg.get('reasoning') or ''

            usage = result.get('usage', {})
            print(f"   Tokens: {usage.get('total_tokens', 0)} "
                  f"(prompt: {usage.get('prompt_tokens', 0)}, "
                  f"completion: {usage.get('completion_tokens', 0)})")

            return text, result, payload

        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt + random.uniform(0, 2)
                print(f"   Request timed out. Waiting {wait:.1f}s before retry...")
                time.sleep(wait)
                continue
            raise
        except requests.exceptions.HTTPError as e:
            last_error = e
            status = e.response.status_code
            if status == 429 and attempt < max_retries - 1:
                retry_after = e.response.headers.get('Retry-After')
                if retry_after and retry_after.isdigit():
                    wait = int(retry_after) + random.uniform(0, 2)
                else:
                    wait = random.uniform(0, 2 ** (attempt + 1))
                print(f"   Rate limited (429). Waiting {wait:.1f}s...")
                time.sleep(wait)
                continue
            elif status == 413 and attempt < max_retries - 1:
                # Strip images and retry
                stripped = _strip_images_from_messages(messages)
                if stripped:
                    messages = stripped
                    payload["messages"] = messages
                    print(f"   Payload too large (413). Retrying without images...")
                    continue
                raise
            elif status == 400 and 'response_format' in payload and attempt < max_retries - 1:
                # Some models (e.g. Gemma via OpenRouter) don't support response_format
                del payload['response_format']
                print(f"   Bad request (400). Retrying without response_format...")
                continue
            else:
                raise

    if last_error:
        raise last_error


def _call_anthropic(
    messages: list,
    model: str,
    api_key: str,
    api_base: str,
    config: dict,
    json_mode: bool = True,
    max_retries: int = 3,
) -> Tuple[str, dict, dict]:
    """
    Call the Anthropic Messages API.
    Converts OpenAI-format messages to Anthropic format.
    """
    endpoint = f"{api_base}/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    # Convert OpenAI messages to Anthropic format
    system_text = ""
    anthropic_messages = []
    for msg in messages:
        if msg['role'] == 'system':
            system_text = msg['content'] if isinstance(msg['content'], str) else msg['content'][0].get('text', '')
        else:
            anthropic_messages.append(_convert_message_to_anthropic(msg))

    payload = {
        "model": model,
        "max_tokens": config.get('max_output_tokens', 2000),
        "messages": anthropic_messages,
        "temperature": 0.3,
    }
    if system_text:
        payload["system"] = system_text

    timeout = config.get('request_timeout', 240)
    last_error = None

    for attempt in range(max_retries):
        try:
            print(f"   Calling {model} via Anthropic... (attempt {attempt + 1}/{max_retries})")
            response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()

            result = response.json()
            # Anthropic returns content as a list of content blocks
            text_parts = [block['text'] for block in result.get('content', []) if block.get('type') == 'text']
            text = '\n'.join(text_parts)

            usage = result.get('usage', {})
            print(f"   Tokens: {usage.get('input_tokens', 0) + usage.get('output_tokens', 0)} "
                  f"(input: {usage.get('input_tokens', 0)}, "
                  f"output: {usage.get('output_tokens', 0)})")

            # Normalize usage to OpenAI-style keys for downstream compatibility
            normalized_usage = {
                'prompt_tokens': usage.get('input_tokens', 0),
                'completion_tokens': usage.get('output_tokens', 0),
                'total_tokens': usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
            }
            result['usage'] = normalized_usage

            return text, result, payload

        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt + random.uniform(0, 2)
                print(f"   Request timed out. Waiting {wait:.1f}s before retry...")
                time.sleep(wait)
                continue
            raise
        except requests.exceptions.HTTPError as e:
            last_error = e
            status = e.response.status_code
            if status == 429 and attempt < max_retries - 1:
                retry_after = e.response.headers.get('retry-after')
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                print(f"   Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                raise

    if last_error:
        raise last_error


def _call_gemini(
    messages: list,
    model: str,
    api_key: str,
    api_base: str,
    config: dict,
    json_mode: bool = True,
    max_retries: int = 3,
) -> Tuple[str, dict, dict]:
    """
    Call the Google Gemini API.
    Converts OpenAI-format messages to Gemini format.
    """
    endpoint = f"{api_base}/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    # Convert OpenAI messages to Gemini format
    system_text = ""
    gemini_contents = []
    for msg in messages:
        if msg['role'] == 'system':
            system_text = msg['content'] if isinstance(msg['content'], str) else msg['content'][0].get('text', '')
        else:
            gemini_contents.append(_convert_message_to_gemini(msg))

    payload = {
        "contents": gemini_contents,
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": config.get('max_output_tokens', 2000),
        }
    }
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    timeout = config.get('request_timeout', 240)
    last_error = None

    for attempt in range(max_retries):
        try:
            print(f"   Calling {model} via Gemini... (attempt {attempt + 1}/{max_retries})")
            response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()

            result = response.json()
            # Gemini returns candidates[0].content.parts[0].text
            text = result['candidates'][0]['content']['parts'][0]['text']

            usage = result.get('usageMetadata', {})
            prompt_tokens = usage.get('promptTokenCount', 0)
            completion_tokens = usage.get('candidatesTokenCount', 0)
            print(f"   Tokens: {prompt_tokens + completion_tokens} "
                  f"(prompt: {prompt_tokens}, completion: {completion_tokens})")

            # Normalize usage
            result['usage'] = {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens,
            }

            return text, result, payload

        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt + random.uniform(0, 2)
                print(f"   Request timed out. Waiting {wait:.1f}s before retry...")
                time.sleep(wait)
                continue
            raise
        except requests.exceptions.HTTPError as e:
            last_error = e
            status = e.response.status_code
            if status == 429 and attempt < max_retries - 1:
                retry_after = e.response.headers.get('retry-after')
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                print(f"   Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                raise

    if last_error:
        raise last_error


def _call_vertex(
    messages: list,
    model: str,
    api_base: str,
    config: dict,
    json_mode: bool = True,
    max_retries: int = 3,
) -> Tuple[str, dict, dict]:
    """
    Call Vertex AI Model Garden via its OpenAI-compatible endpoint.
    Auth uses Application Default Credentials (ADC) — run:
        gcloud auth application-default login
    """
    try:
        import google.auth
        import google.auth.transport.requests
    except ImportError:
        raise ImportError(
            "google-auth is required for Vertex AI. Install with: pip install google-auth"
        )

    endpoint = f"{api_base}/chat/completions"

    credentials, _ = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    auth_request = google.auth.transport.requests.Request()
    credentials.refresh(auth_request)

    def _get_headers():
        if not credentials.valid:
            credentials.refresh(auth_request)
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {credentials.token}",
        }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": config.get('max_output_tokens', 2000),
    }
    # Vertex AI does not support response_format; JSON is requested via prompt only

    timeout = config.get('request_timeout', 240)
    last_error = None

    for attempt in range(max_retries):
        try:
            print(f"   Calling {model} via Vertex AI... (attempt {attempt + 1}/{max_retries})")
            response = requests.post(endpoint, headers=_get_headers(), json=payload, timeout=timeout)
            response.raise_for_status()

            result = response.json()
            msg = result['choices'][0]['message']
            text = msg.get('content') or ''

            usage = result.get('usage', {})
            print(f"   Tokens: {usage.get('total_tokens', 0)} "
                  f"(prompt: {usage.get('prompt_tokens', 0)}, "
                  f"completion: {usage.get('completion_tokens', 0)})")

            return text, result, payload

        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt + random.uniform(0, 2)
                print(f"   Request timed out. Waiting {wait:.1f}s before retry...")
                time.sleep(wait)
                continue
            raise
        except requests.exceptions.HTTPError as e:
            last_error = e
            status = e.response.status_code
            if status == 429 and attempt < max_retries - 1:
                retry_after = e.response.headers.get('Retry-After')
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                print(f"   Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                continue
            elif status == 413 and attempt < max_retries - 1:
                stripped = _strip_images_from_messages(messages)
                if stripped:
                    messages = stripped
                    payload["messages"] = messages
                    print(f"   Payload too large (413). Retrying without images...")
                    continue
                raise
            elif status == 400 and 'response_format' in payload and attempt < max_retries - 1:
                del payload['response_format']
                print(f"   Bad request (400). Retrying without response_format...")
                continue
            else:
                raise

    if last_error:
        raise last_error


def _convert_message_to_anthropic(msg: dict) -> dict:
    """Convert an OpenAI-format message to Anthropic format."""
    role = msg['role']
    content = msg.get('content', '')

    if isinstance(content, str):
        return {"role": role, "content": content}

    # Multi-part content (text + images)
    parts = []
    for item in content:
        if item.get('type') == 'text':
            parts.append({"type": "text", "text": item['text']})
        elif item.get('type') == 'image_url':
            url = item['image_url']['url']
            # Handle base64 data URIs
            if url.startswith('data:'):
                # Parse: data:image/png;base64,AAAA...
                media_type = url.split(';')[0].split(':')[1]
                b64_data = url.split(',', 1)[1]
                parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": b64_data,
                    }
                })
            else:
                # URL-based image
                parts.append({
                    "type": "image",
                    "source": {"type": "url", "url": url}
                })
    return {"role": role, "content": parts}


def _convert_message_to_gemini(msg: dict) -> dict:
    """Convert an OpenAI-format message to Gemini format."""
    role = "user" if msg['role'] == 'user' else "model"
    content = msg.get('content', '')

    if isinstance(content, str):
        return {"role": role, "parts": [{"text": content}]}

    # Multi-part content
    parts = []
    for item in content:
        if item.get('type') == 'text':
            parts.append({"text": item['text']})
        elif item.get('type') == 'image_url':
            url = item['image_url']['url']
            if url.startswith('data:'):
                media_type = url.split(';')[0].split(':')[1]
                b64_data = url.split(',', 1)[1]
                parts.append({
                    "inlineData": {
                        "mimeType": media_type,
                        "data": b64_data,
                    }
                })
    return {"role": role, "parts": parts}


def _strip_images_from_messages(messages: list) -> list:
    """Remove image content from messages (for payload-too-large fallback)."""
    had_images = False
    stripped = []
    for msg in messages:
        content = msg.get('content', '')
        if isinstance(content, list):
            new_content = [item for item in content if item.get('type') != 'image_url']
            if len(new_content) < len(content):
                had_images = True
            stripped.append({**msg, 'content': new_content})
        else:
            stripped.append(msg)
    return stripped if had_images else None


def call_ai(
    messages: list,
    model: str,
    config: dict,
    provider_config: dict = None,
    json_mode: bool = True,
    max_retries: int = 3,
    fallback_model: str = None,
) -> Tuple[str, dict, dict]:
    """
    Unified AI call interface. Routes to the correct provider.

    Args:
        messages: OpenAI-format messages list
        model: Model name
        config: Repo config dict
        provider_config: Output of resolve_provider_config() (resolved if None)
        json_mode: Request JSON response format
        max_retries: Number of retries on rate limit
        fallback_model: Model to try if primary exhausts all retries

    Returns:
        (response_text, response_data, request_payload)
    """
    if provider_config is None:
        provider_config = resolve_provider_config(config)

    provider = provider_config['provider']
    api = provider_config['api']
    api_key = provider_config['api_key']
    api_base = provider_config['api_base']

    if not api_key and api not in APIS_WITHOUT_API_KEY:
        key_var = PROVIDER_KEY_ENVVARS.get(provider) or API_KEY_ENVVARS.get(api, 'AI_API_KEY')
        raise ValueError(
            f"No API key found for provider '{provider}' (api: {api}). "
            f"Set {key_var} environment variable, or add api_key to ~/.ai-feedback/config.yml"
        )

    session_id = os.environ.get('AI_SESSION_ID') or None
    disable_json_mode = provider_config.get('disable_json_mode', False)

    # Provider config timeout and generation params take precedence over repo config
    effective_config = {**config, 'request_timeout': provider_config['request_timeout']}
    if provider_config.get('frequency_penalty') is not None:
        effective_config['frequency_penalty'] = provider_config['frequency_penalty']

    def _call(m):
        if api == 'openai':
            extra_headers = {}
            if provider == 'openrouter':
                extra_headers = {
                    "HTTP-Referer": "https://github.com/UINDY-INSTRUCTORS/ai-feedback-system",
                    "X-Title": "AI Feedback System",
                }
            return _call_openai_compatible(
                messages, m, api_key, api_base, effective_config,
                json_mode=json_mode, max_retries=max_retries,
                extra_headers=extra_headers if extra_headers else None,
                session_id=session_id,
                disable_json_mode=disable_json_mode,
            )
        elif api == 'anthropic':
            return _call_anthropic(
                messages, m, api_key, api_base, effective_config,
                json_mode=json_mode, max_retries=max_retries,
            )
        elif api == 'gemini':
            return _call_gemini(
                messages, m, api_key, api_base, effective_config,
                json_mode=json_mode, max_retries=max_retries,
            )
        elif api == 'vertex':
            return _call_vertex(
                messages, m, api_base, effective_config,
                json_mode=json_mode, max_retries=max_retries,
            )
        else:
            raise ValueError(f"Unknown api: '{api}' for provider '{provider}'. Supported apis: openai, anthropic, gemini, vertex")

    try:
        return _call(model)
    except Exception as e:
        if fallback_model and fallback_model != model:
            print(f"   Primary model failed ({e}). Trying fallback: {fallback_model}")
            return _call(fallback_model)
        raise


def print_provider_info(provider_config: dict):
    """Print resolved provider info for debugging."""
    print(f"   Provider: {provider_config['provider']}")
    print(f"   API:      {provider_config['api']}")
    print(f"   Model:    {provider_config['model']}")
    print(f"   Base URL: {provider_config['api_base']}")
    if provider_config['api'] == 'vertex':
        print(f"   Project:  {provider_config.get('vertex_project', 'MISSING')}")
        print(f"   Location: {provider_config.get('vertex_location', 'us-central1')}")
        print(f"   Auth:     ADC (gcloud application-default)")
    else:
        has_key = "set" if provider_config['api_key'] else "MISSING"
        print(f"   API Key:  {has_key}")


def print_configured_profiles(active_profile: str = None):
    """Print all named profiles and defaults from ~/.ai-feedback/config.yml."""
    global_config = load_global_config()
    profiles = global_config.get('profiles', {})
    default_profile = global_config.get('profile')

    print(f"\nAI configuration  ({GLOBAL_CONFIG_PATH})\n")

    top_provider = global_config.get('provider', 'github_models')
    top_model_cfg = global_config.get('model', {})
    top_model = (top_model_cfg.get('primary') if isinstance(top_model_cfg, dict) else top_model_cfg) \
                or PROVIDER_DEFAULT_MODELS.get(top_provider, 'gpt-4o')
    print(f"  Default (no profile): provider={top_provider}  model={top_model}")
    if default_profile:
        print(f"  Active profile:       {default_profile}")
    print()

    if not profiles:
        print("  No named profiles configured.")
        print(f"  To add profiles, edit {GLOBAL_CONFIG_PATH}")
        print(f"  (or run: python run-local-feedback.py --init-config)")
        print()
        return

    active = active_profile or os.environ.get('AI_PROFILE') or default_profile
    source = ('--profile arg' if active_profile
              else 'AI_PROFILE env var' if os.environ.get('AI_PROFILE')
              else 'config default' if default_profile
              else None)

    col = {'name': 25, 'provider': 16, 'model': 42, 'fallback': 36}
    hdr = (f"  {'Profile':<{col['name']}}  {'Provider':<{col['provider']}}"
           f"  {'Primary model':<{col['model']}}  Fallback")
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))

    for name, cfg in profiles.items():
        cfg = cfg or {}
        marker = '* ' if name == active else '  '
        provider = cfg.get('provider', top_provider)
        mcfg = cfg.get('model', {})
        if isinstance(mcfg, dict):
            model    = mcfg.get('primary')   or PROVIDER_DEFAULT_MODELS.get(provider, '?')
            fallback = mcfg.get('fallback')  or model
        else:
            model = fallback = mcfg or PROVIDER_DEFAULT_MODELS.get(provider, '?')
        fb_str = '' if fallback == model else fallback
        print(f"  {marker}{name:<{col['name']}}  {provider:<{col['provider']}}"
              f"  {model:<{col['model']}}  {fb_str}")

    if active and source:
        print(f"\n  (* = active via {source})")
    print()
    print("  Select with:  --profile <name>")
    print("  Override with: --model <model-id>")
    print()


def list_openai_compatible_models(api_base: str, api_key: str = None, timeout: int = 10) -> List[str]:
    """
    Query an OpenAI-compatible endpoint for available models.
    Works with LM Studio, OpenRouter, OpenAI, etc.

    Args:
        api_base: The base URL (e.g., http://localhost:1234/v1)
        api_key: Optional API key (some providers require it)
        timeout: Request timeout in seconds

    Returns:
        List of model identifiers, sorted
    """
    endpoint = f"{api_base}/models"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        print(f"Querying {endpoint}...")
        response = requests.get(endpoint, headers=headers, timeout=timeout)
        response.raise_for_status()

        result = response.json()
        models = [m['id'] for m in result.get('data', [])]
        return sorted(models)

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Failed to query models from {api_base}: {e}\n"
            f"Make sure LM Studio is running locally (default: http://localhost:1234/v1)"
        )
