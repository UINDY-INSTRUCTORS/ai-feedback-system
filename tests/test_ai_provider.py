"""
Tests for ai_provider.py - multi-provider abstraction layer.

Tests cover:
- Provider config resolution (env vars > global config > repo config > defaults)
- Message format conversion (OpenAI -> Anthropic, OpenAI -> Gemini)
- Image stripping fallback
- call_ai routing to correct provider
- No real API calls - all network calls are mocked
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from ai_provider import (
    resolve_provider_config,
    _convert_message_to_anthropic,
    _convert_message_to_gemini,
    _strip_images_from_messages,
    call_ai,
    print_provider_info,
    PROVIDER_ENDPOINTS,
    PROVIDER_DEFAULT_MODELS,
    PROVIDER_KEY_ENVVARS,
)


# ============================================================================
# resolve_provider_config
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestResolveProviderConfig:
    """Tests for provider configuration resolution."""

    @patch('ai_provider.load_global_config', return_value={})
    def test_defaults_when_no_config(self, mock_global):
        """Defaults to github_models + gpt-4o when nothing is configured."""
        with patch.dict('os.environ', {}, clear=True):
            # Need GITHUB_TOKEN for default provider
            result = resolve_provider_config()
        assert result['provider'] == 'github_models'
        assert result['model'] == 'gpt-4o'
        assert result['api_base'] == PROVIDER_ENDPOINTS['github_models']

    @patch('ai_provider.load_global_config', return_value={})
    def test_env_vars_override_everything(self, mock_global):
        """Environment variables take highest priority."""
        env = {
            'AI_PROVIDER': 'openai',
            'AI_MODEL': 'gpt-4-turbo',
            'AI_FALLBACK_MODEL': 'gpt-3.5-turbo',
            'AI_API_BASE': 'https://custom.api.com',
            'OPENAI_API_KEY': 'sk-test',
        }
        with patch.dict('os.environ', env, clear=True):
            result = resolve_provider_config({'provider': 'github_models'})

        assert result['provider'] == 'openai'
        assert result['model'] == 'gpt-4-turbo'
        assert result['fallback'] == 'gpt-3.5-turbo'
        assert result['api_base'] == 'https://custom.api.com'
        assert result['api_key'] == 'sk-test'

    @patch('ai_provider.load_global_config', return_value={
        'provider': 'anthropic',
        'model': {'primary': 'claude-sonnet-4-20250514'},
        'api_key': 'sk-ant-test',
    })
    def test_global_config_used(self, mock_global):
        """Global config is used when env vars are not set."""
        with patch.dict('os.environ', {}, clear=True):
            result = resolve_provider_config()

        assert result['provider'] == 'anthropic'
        assert result['model'] == 'claude-sonnet-4-20250514'
        assert result['api_key'] == 'sk-ant-test'

    @patch('ai_provider.load_global_config', return_value={})
    def test_repo_config_used(self, mock_global):
        """Repo config is used when no env vars or global config."""
        repo = {
            'provider': 'gemini',
            'model': {'primary': 'gemini-2.5-flash'},
        }
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'gkey'}, clear=True):
            result = resolve_provider_config(repo)

        assert result['provider'] == 'gemini'
        assert result['model'] == 'gemini-2.5-flash'

    @patch('ai_provider.load_global_config', return_value={'provider': 'openrouter'})
    def test_provider_key_envvar_mapping(self, mock_global):
        """Correct env var is used for API key based on provider."""
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'or-key'}, clear=True):
            result = resolve_provider_config()

        assert result['api_key'] == 'or-key'

    @patch('ai_provider.load_global_config', return_value={})
    def test_ai_api_key_fallback(self, mock_global):
        """AI_API_KEY env var works as fallback for any provider."""
        with patch.dict('os.environ', {'AI_PROVIDER': 'openai', 'AI_API_KEY': 'generic-key'}, clear=True):
            result = resolve_provider_config()

        assert result['api_key'] == 'generic-key'

    @patch('ai_provider.load_global_config', return_value={})
    def test_default_model_per_provider(self, mock_global):
        """Each provider has its own default model."""
        for provider, expected_model in PROVIDER_DEFAULT_MODELS.items():
            with patch.dict('os.environ', {'AI_PROVIDER': provider}, clear=True):
                result = resolve_provider_config()
            assert result['model'] == expected_model, f"Wrong default model for {provider}"

    @patch('ai_provider.load_global_config', return_value={})
    def test_deterministic_resolution(self, mock_global):
        """Config resolution is deterministic."""
        repo = {'provider': 'openai', 'model': {'primary': 'gpt-4o'}}
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'k'}, clear=True):
            r1 = resolve_provider_config(repo)
            r2 = resolve_provider_config(repo)
        assert r1 == r2


# ============================================================================
# Message conversion: OpenAI -> Anthropic
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestConvertMessageToAnthropic:
    """Tests for OpenAI -> Anthropic message conversion."""

    def test_simple_text_message(self):
        """Simple text message passthrough."""
        msg = {"role": "user", "content": "Hello"}
        result = _convert_message_to_anthropic(msg)
        assert result == {"role": "user", "content": "Hello"}

    def test_multipart_text_only(self):
        """Multi-part message with text only."""
        msg = {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
        result = _convert_message_to_anthropic(msg)
        assert result["role"] == "user"
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "Hello"

    def test_multipart_with_base64_image(self):
        """Multi-part message with base64 image."""
        msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBOR"}}
            ]
        }
        result = _convert_message_to_anthropic(msg)
        assert len(result["content"]) == 2
        assert result["content"][0]["type"] == "text"
        assert result["content"][1]["type"] == "image"
        assert result["content"][1]["source"]["type"] == "base64"
        assert result["content"][1]["source"]["media_type"] == "image/png"
        assert result["content"][1]["source"]["data"] == "iVBOR"

    def test_multipart_with_url_image(self):
        """Multi-part message with URL image."""
        msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "See image"},
                {"type": "image_url", "image_url": {"url": "https://example.com/img.png"}}
            ]
        }
        result = _convert_message_to_anthropic(msg)
        assert result["content"][1]["type"] == "image"
        assert result["content"][1]["source"]["type"] == "url"
        assert result["content"][1]["source"]["url"] == "https://example.com/img.png"


# ============================================================================
# Message conversion: OpenAI -> Gemini
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestConvertMessageToGemini:
    """Tests for OpenAI -> Gemini message conversion."""

    def test_simple_text_message(self):
        """Simple text message conversion."""
        msg = {"role": "user", "content": "Hello"}
        result = _convert_message_to_gemini(msg)
        assert result["role"] == "user"
        assert result["parts"] == [{"text": "Hello"}]

    def test_assistant_becomes_model(self):
        """Assistant role maps to 'model' in Gemini."""
        msg = {"role": "assistant", "content": "Response"}
        result = _convert_message_to_gemini(msg)
        assert result["role"] == "model"

    def test_multipart_with_base64_image(self):
        """Multi-part with base64 image converts to inlineData."""
        msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j"}}
            ]
        }
        result = _convert_message_to_gemini(msg)
        assert len(result["parts"]) == 2
        assert result["parts"][0] == {"text": "Describe"}
        assert result["parts"][1]["inlineData"]["mimeType"] == "image/jpeg"
        assert result["parts"][1]["inlineData"]["data"] == "/9j"


# ============================================================================
# _strip_images_from_messages
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestStripImagesFromMessages:
    """Tests for image stripping fallback."""

    def test_strips_images(self):
        """Removes image_url items from multipart content."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": [
                {"type": "text", "text": "Look at this"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
            ]}
        ]
        result = _strip_images_from_messages(messages)
        assert result is not None
        user_content = result[1]["content"]
        assert len(user_content) == 1
        assert user_content[0]["type"] == "text"

    def test_returns_none_when_no_images(self):
        """Returns None when there are no images to strip."""
        messages = [
            {"role": "user", "content": "Just text"},
        ]
        result = _strip_images_from_messages(messages)
        assert result is None

    def test_preserves_system_message(self):
        """System message is not altered."""
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": [
                {"type": "text", "text": "Q"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,x"}},
            ]}
        ]
        result = _strip_images_from_messages(messages)
        assert result[0] == {"role": "system", "content": "Be helpful"}


# ============================================================================
# call_ai routing
# ============================================================================

@pytest.mark.unit
class TestCallAiRouting:
    """Tests that call_ai routes to the correct provider backend."""

    def _make_provider_config(self, provider, api_key='test-key'):
        return {
            'provider': provider,
            'model': 'test-model',
            'api_key': api_key,
            'api_base': PROVIDER_ENDPOINTS.get(provider, 'https://example.com'),
            'fallback': 'test-model',
            'extractor': 'test-model',
        }

    def test_raises_without_api_key(self):
        """Raises ValueError when API key is missing."""
        cfg = self._make_provider_config('openai', api_key=None)
        with pytest.raises(ValueError, match="No API key"):
            call_ai([{"role": "user", "content": "hi"}], "gpt-4o", {}, provider_config=cfg)

    @patch('ai_provider._call_openai_compatible')
    def test_routes_github_models(self, mock_fn):
        """github_models routes to _call_openai_compatible."""
        mock_fn.return_value = ("text", {}, {})
        cfg = self._make_provider_config('github_models')
        call_ai([{"role": "user", "content": "hi"}], "gpt-4o", {}, provider_config=cfg)
        mock_fn.assert_called_once()

    @patch('ai_provider._call_openai_compatible')
    def test_routes_openrouter(self, mock_fn):
        """openrouter routes to _call_openai_compatible with extra headers."""
        mock_fn.return_value = ("text", {}, {})
        cfg = self._make_provider_config('openrouter')
        call_ai([{"role": "user", "content": "hi"}], "model", {}, provider_config=cfg)
        mock_fn.assert_called_once()
        # Check extra_headers were passed
        _, kwargs = mock_fn.call_args
        assert kwargs.get('extra_headers') is not None

    @patch('ai_provider._call_openai_compatible')
    def test_routes_openai(self, mock_fn):
        """openai routes to _call_openai_compatible."""
        mock_fn.return_value = ("text", {}, {})
        cfg = self._make_provider_config('openai')
        call_ai([{"role": "user", "content": "hi"}], "gpt-4o", {}, provider_config=cfg)
        mock_fn.assert_called_once()

    @patch('ai_provider._call_anthropic')
    def test_routes_anthropic(self, mock_fn):
        """anthropic routes to _call_anthropic."""
        mock_fn.return_value = ("text", {}, {})
        cfg = self._make_provider_config('anthropic')
        call_ai([{"role": "user", "content": "hi"}], "claude", {}, provider_config=cfg)
        mock_fn.assert_called_once()

    @patch('ai_provider._call_gemini')
    def test_routes_gemini(self, mock_fn):
        """gemini routes to _call_gemini."""
        mock_fn.return_value = ("text", {}, {})
        cfg = self._make_provider_config('gemini')
        call_ai([{"role": "user", "content": "hi"}], "gemini", {}, provider_config=cfg)
        mock_fn.assert_called_once()

    def test_unknown_provider_raises(self):
        """Unknown provider raises ValueError."""
        cfg = self._make_provider_config('unknown_provider')
        with pytest.raises(ValueError, match="Unknown provider"):
            call_ai([{"role": "user", "content": "hi"}], "m", {}, provider_config=cfg)


# ============================================================================
# print_provider_info (smoke test)
# ============================================================================

@pytest.mark.unit
class TestPrintProviderInfo:
    """Smoke test for print_provider_info."""

    def test_prints_without_error(self, capsys):
        cfg = {
            'provider': 'openai',
            'model': 'gpt-4o',
            'api_base': 'https://api.openai.com/v1',
            'api_key': 'sk-test',
        }
        print_provider_info(cfg)
        captured = capsys.readouterr()
        assert 'openai' in captured.out
        assert 'gpt-4o' in captured.out
        assert 'set' in captured.out

    def test_prints_missing_key(self, capsys):
        cfg = {
            'provider': 'openai',
            'model': 'gpt-4o',
            'api_base': 'https://api.openai.com/v1',
            'api_key': None,
        }
        print_provider_info(cfg)
        captured = capsys.readouterr()
        assert 'MISSING' in captured.out
