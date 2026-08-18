<a href="https://avishay.co.il" target="_blank" rel="noopener">
  <img src=".github/brand/hero.png" alt="Avishay Bar — Security // AI // Engineering. Secure the AI you build, and the AI you run." width="100%" />
</a>

---


# RAG History Search Home Assistant Integration

[![Validate](https://github.com/avishayil/rag-search-homeassistant/actions/workflows/validate.yml/badge.svg)](https://github.com/avishayil/rag-search-homeassistant/actions/workflows/validate.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

## Overview

The **RAG History Search** integration lets you query Home Assistant's entity
history and generate natural-language answers about it using OpenAI. It is a
Retrieval-Augmented Generation (RAG) tool that combines recorded entity states
with a large language model to answer questions about your home.

## Features

- Retrieves Home Assistant entity history within a specified time range.
- Sends that history to the OpenAI API to generate an answer to your question.
- UI-based setup (config flow) with the OpenAI API key stored securely by Home
  Assistant, not in plaintext `configuration.yaml`.
- Configurable model, allowed entity scope, and maximum number of history items.
- Timeout and automatic retry with backoff around the OpenAI call.
- Exposes a `rag_search.search_history` service.

## Installation (HACS)

This integration is distributed as a HACS **custom repository**.

1. In Home Assistant, open **HACS**.
2. Click the **three-dot menu** (top right) and choose **Custom repositories**.
3. Enter the repository URL `https://github.com/avishayil/rag-search-homeassistant`,
   select **Integration** as the category, and click **Add**.
4. Find **HomeAssistant RAG Search** in the HACS list and click **Download**.
5. **Restart Home Assistant.**

> Once a versioned release/tag is published, HACS will offer it under the
> normal download/update flow.

### Manual installation (alternative)

Copy the `custom_components/rag_search` folder into your Home Assistant
`config/custom_components/` directory and restart Home Assistant.

## Configuration

After installation, add the integration from the UI:

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **RAG Search**.
3. Enter your **OpenAI API key** and, optionally, the model, allowed entities,
   and maximum history items.

Your API key is stored in Home Assistant's encrypted-at-rest config storage,
not in `configuration.yaml`.

### Options

| Option           | Description                                                        | Default       |
| ---------------- | ------------------------------------------------------------------ | ------------- |
| `openai_api_key` | Your OpenAI API key.                                               | _(required)_  |
| `openai_model`   | The OpenAI model used for completions.                             | `gpt-4o-mini` |
| `entity_scope`   | List of entity IDs allowed for history searches.                   | `[]`          |
| `max_items`      | Maximum number of history items to fetch per query.                | `50`          |

Model, entity scope, and max items can be changed later via the integration's
**Configure** (options) dialog.

### YAML (deprecated, back-compat)

Existing YAML configuration is still imported automatically on startup and then
migrated into secure storage. New installs should use the UI flow above.

```yaml
rag_search:
  openai_api_key: "your_openai_api_key_here"
  openai_model: "gpt-4o-mini"
  entity_scope:
    - "sensor.temperature"
    - "light.living_room"
  max_items: 50
```

After the first restart, you can remove this block from `configuration.yaml`.

## Usage

Call the `rag_search.search_history` service:

```yaml
service: rag_search.search_history
data:
  entity_id: "sensor.temperature"
  start_time: "2024-10-01T00:00:00Z"
  end_time: "2024-10-10T23:59:59Z"
  num_items: 30  # Optional, overrides max_items for this call
  query: "What were the notable temperature changes?"
```

The generated answer is written to the `rag_search.last_query_result` state.

### Parameters

- **entity_id**: The entity ID to search for (must be in the configured scope).
- **start_time**: Start of the history window (ISO 8601).
- **end_time**: End of the history window (ISO 8601).
- **num_items**: Optional. Items to fetch, capped by `max_items`.
- **query**: The natural-language question appended to the entity history.

## Logging

```yaml
logger:
  default: info
  logs:
    custom_components.rag_search: debug
```

## Security Considerations

- The OpenAI API key is stored securely by Home Assistant (config entry
  storage) and is no longer required in plaintext `configuration.yaml`.
- Be mindful of the data sent to OpenAI, especially if entity history could
  contain sensitive information. Use `entity_scope` to restrict which entities
  can be queried.

## Development / Testing

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.test.txt
pytest
```

CI runs HACS validation, Home Assistant `hassfest`, and the pytest suite on
every push and pull request (see `.github/workflows/validate.yml`).

## License

This project is licensed under the [MIT License](LICENSE).

## Contributions

Contributions are welcome! Please open an issue or submit a pull request.
