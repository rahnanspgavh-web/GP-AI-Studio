# GP AI Studio - API Manager

Version: 1.0

---

# Goal

The API Manager is responsible for securely managing all AI providers used by GP AI Studio.

No module should directly store or access API keys.

Every module must communicate with AI providers through the API Manager.

---

# Supported Providers

## Google AI Studio

Purpose

- Research
- Script Generation
- Prompt Generation
- Image Prompt Generation
- Video Prompt Generation

Status

Enabled

---

## Claude

Purpose

- Research
- Long-form Writing
- Script Generation

Status

Optional

---

## OpenAI

Purpose

- Script Generation
- Automation
- Future AI features

Status

Optional

---

# Future Providers

The architecture must allow additional providers without modifying existing modules.

Example

- Provider A
- Provider B

The API Manager must be provider-independent.

---

# Folder Structure

config/

    api_keys.json

modules/

    api_manager/

        api_manager.py

tests/

    test_api_manager.py

---

# api_keys.json

Example

{
    "google": {
        "enabled": true,
        "api_key": "",
        "default_model": "gemini-2.5-pro"
    },

    "claude": {
        "enabled": false,
        "api_key": "",
        "default_model": ""
    },

    "openai": {
        "enabled": false,
        "api_key": "",
        "default_model": ""
    }
}

---

# Responsibilities

The API Manager shall

- load API keys
- save API keys
- validate providers
- return provider status
- return default model
- update default model
- enable provider
- disable provider
- test API configuration

No other module shall directly read api_keys.json.

---

# Public Functions

load_api_keys()

save_api_keys()

get_provider()

set_provider()

enable_provider()

disable_provider()

validate_provider()

list_enabled_providers()

get_default_model()

set_default_model()

---

# Security Rules

API keys must never be hardcoded.

API keys must never appear in logs.

API keys must never be committed to GitHub.

If api_keys.json is missing

Create it automatically.

If corrupted

Restore default structure.

---

# Validation Rules

Google

API key must not be empty.

Claude

API key must not be empty.

OpenAI

API key must not be empty.

Return clear error messages.

---

# Error Handling

Missing configuration

Invalid JSON

Missing provider

Disabled provider

Invalid model

Invalid key

All errors should raise meaningful exceptions.

---

# Logging

Log

Provider loaded

Provider enabled

Provider disabled

Validation success

Validation failure

Never log API keys.

---

# Unit Tests

Verify

Load configuration

Save configuration

Create default configuration

Enable provider

Disable provider

Validate configuration

Missing configuration recovery

Corrupted JSON recovery

---

# Future Enhancements

Encrypted API key storage

Usage statistics

Automatic model updates

Rate limit tracking

Token usage tracking

Multiple API keys per provider

Automatic provider fallback