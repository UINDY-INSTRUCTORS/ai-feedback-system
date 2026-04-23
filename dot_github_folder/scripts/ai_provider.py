#!/usr/bin/env python3
"""
AI Provider abstraction for multi-provider support.

Supports:
  - github_models: GitHub Models API (default in Actions, uses GITHUB_TOKEN)
  - openrouter:    OpenRouter (OpenAI-compatible, uses OPENROUTER_API_KEY)
  - anthropic:     Anthropic Claude API (uses ANTHROPIC_API_KEY)
  - gemini:        Google Gemini API (uses GEMINI_API_KEY)
  - openai:        OpenAI directly (uses OPENAI_API_KEY)
  - vertex:        Google Vertex AI (uses ADC via gcloud / GOOGLE_APPLICATION_CREDENTIALS)

All providers return the same (text, response_data, request_payload) tuple.

Configuration priority:
  1. Environment variables (AI_PROVIDER, AI_MODEL, etc.)
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

# Maps provider -> env var name for API key (vertex uses ADC, no key needed)
PROVIDER_KEY_ENVVARS = {
    'github_models': 'GITHUB_TOKEN',
    'openrouter':    'OPENROUTER_API_KEY',
    'openai':        'OPENAI_API_KEY',
    'anthropic':     'ANTHROPIC_API_KEY',
    'gemini':        'GEMINI_API_KEY',
}

# Providers that use ADC/service-account auth instead of an API key
PROVIDERS_WITHOUT_API_KEY = {'vertex'}

# Default models per provider
PROVIDER_DEFAULT_MODELS = {
    'github_models': 'gpt-4o',
    'openrouter':    'openai/gpt-4o',
    'openai':        'gpt-4o',
    'anthropic':     'claude-sonnet-4-20250514',
    'gemini':        'gemini-2.5-flash',
    'vertex':        'google/gemini-2.5-flash-001',
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

    # API key: env var > profile > global config
    key_envvar = PROVIDER_KEY_ENVVARS.get(provider, 'GITHUB_TOKEN')
    api_key = (
        os.environ.get(key_envvar)
        or os.environ.get('AI_API_KEY')
        or profile_config.get('api_key')
        or global_config.get('api_key')
    )

    # Vertex AI project and location (only used when provider == 'vertex')
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
    # For vertex, compute dynamically from project + location if not overridden
    api_base = (
        os.environ.get('AI_API_BASE')
        or profile_config.get('api_base')
        or global_config.get('api_base')
        or PROVIDER_ENDPOINTS.get(provider)
    )
    if provider == 'vertex' and not api_base:
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

    return {
        'provider': provider,
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
    is_local = 'localhost' in api_base or '127.0.0.1' in api_base
    if json_mode and not disable_json_mode and not is_local:
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
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

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
    api_key = provider_config['api_key']
    api_base = provider_config['api_base']

    if not api_key and provider not in PROVIDERS_WITHOUT_API_KEY:
        key_var = PROVIDER_KEY_ENVVARS.get(provider, 'AI_API_KEY')
        raise ValueError(
            f"No API key found for provider '{provider}'. "
            f"Set {key_var} environment variable, or add api_key to ~/.ai-feedback/config.yml"
        )

    session_id = os.environ.get('AI_SESSION_ID') or None
    disable_json_mode = provider_config.get('disable_json_mode', False)

    # Provider config timeout takes precedence over repo config (already resolved through priority chain)
    effective_config = {**config, 'request_timeout': provider_config['request_timeout']}

    def _call(m):
        if provider in ('github_models', 'openrouter', 'openai'):
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
        elif provider == 'anthropic':
            return _call_anthropic(
                messages, m, api_key, api_base, effective_config,
                json_mode=json_mode, max_retries=max_retries,
            )
        elif provider == 'gemini':
            return _call_gemini(
                messages, m, api_key, api_base, effective_config,
                json_mode=json_mode, max_retries=max_retries,
            )
        elif provider == 'vertex':
            return _call_vertex(
                messages, m, api_base, effective_config,
                json_mode=json_mode, max_retries=max_retries,
            )
        else:
            raise ValueError(f"Unknown provider: {provider}. Supported: {', '.join(PROVIDER_ENDPOINTS.keys())}")

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
    print(f"   Model:    {provider_config['model']}")
    print(f"   Base URL: {provider_config['api_base']}")
    if provider_config['provider'] == 'vertex':
        print(f"   Project:  {provider_config.get('vertex_project', 'MISSING')}")
        print(f"   Location: {provider_config.get('vertex_location', 'us-central1')}")
        print(f"   Auth:     ADC (gcloud application-default)")
    else:
        has_key = "set" if provider_config['api_key'] else "MISSING"
        print(f"   API Key:  {has_key}")


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
