
# RAG History Search Home Assistant Plugin

## Overview

The **RAG History Search** plugin allows users to search through Home Assistant's entity history and generate responses based on the entity states using OpenAI's GPT model. It is a Retrieval-Augmented Generation (RAG) tool that integrates entity data with AI to provide useful insights and answers to user queries.

## Features

- Retrieves Home Assistant entity history within a specified time range.
- Integrates with OpenAI API to generate responses based on entity history.
- Allows flexible configuration options, including the maximum number of history items fetched and entity scoping.
- Provides a Home Assistant service to perform searches and generate AI-based answers.

## Installation

1. Copy the plugin files (`__init__.py`, `const.py`, `search.py`, and `manifest.json`) into the custom component folder for Home Assistant (usually `config/custom_components/rag_search/`).

2. Ensure you have `aiohttp` installed as it's a requirement for the plugin. You can add it to `requirements.txt` or install via:
   ```sh
   pip install aiohttp
   ```

3. Add the plugin configuration to your `configuration.yaml` file:

   ```yaml
   rag_search:
     openai_api_key: "your_openai_api_key_here"
     openai_model: "gpt-4-turbo"  # Optional, default is gpt-4-turbo
     entity_scope:
       - "sensor.temperature"
       - "light.living_room"
     max_items: 50  # Optional, default is 50
   ```

## Configuration

- **openai_api_key**: Your API key for accessing OpenAI services.
- **openai_model**: The model to use when calling the OpenAI API (default is `gpt-4-turbo`).
- **entity_scope**: A list of entity IDs that are allowed for RAG history searches.
- **max_items**: The maximum number of history items to fetch for a given entity (default is `50`).

## Usage

Once installed and configured, you can use the service `rag_search.search_history` to perform searches. Example service call:

```yaml
service: rag_search.search_history
data:
  entity_id: "sensor.temperature"
  start_time: "2024-10-01T00:00:00Z"
  end_time: "2024-10-10T23:59:59Z"
  num_items: 30  # Optional, overrides max_items for this call
  query: "What were the notable temperature changes?"
```

### Parameters

- **entity_id**: The entity ID to search for (must be in the configured entity scope).
- **start_time**: The start time for the history query (ISO format).
- **end_time**: The end time for the history query (ISO format).
- **num_items**: Optional. The number of history items to fetch, up to the configured maximum (`max_items`).
- **query**: The query that will be appended to the entity history and used as a prompt for OpenAI.

## Logging

The plugin uses Home Assistant's logging system to provide debug and error information. Adjust the logging level in your Home Assistant configuration if you want to see more or fewer details.

```yaml
logger:
  default: info
  logs:
    custom_components.rag_search: debug
```

## Uninstallation

To uninstall the plugin:
1. Remove the `rag_search` folder from `config/custom_components/`.
2. Remove the configuration from `configuration.yaml`.
3. Restart Home Assistant.

## Security Considerations

- The OpenAI API key is stored in plain text in the Home Assistant configuration. It is advisable to keep it secure and not share your configuration file.
- Be mindful of the data you are sending to OpenAI, especially if it includes sensitive information.

## License

This plugin is released under the MIT License.

## Contributions

Contributions are welcome! Please submit a pull request or open an issue to propose changes.
