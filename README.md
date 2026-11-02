# Microsoft Foundry Non-Agent Code Samples
This repository contains a collection of Python code samples that use the OpenAI v1 API in 
Microsoft Foundry.

## Samples

- **chat-completions-notebook/** — Basic chat completions using the OpenAI v1 API.
- **responses-notebook/** — Responses API, including multi-turn conversations, server-side storage, the conversations API, and tool use (MCP).
- **batch-notebook/** — Batch processing of chat completions using the batch API.

## Setup

1. Create a Python virtual environment and install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env-sample` to `.env` and fill in your own values (tenant ID, service principal credentials, endpoints, deployment names).
3. Open any notebook and run the cells in order.

## Notes

- `.env` is gitignored — never commit real credentials.
- Each notebook folder also has its own `requirements.txt` for sample-specific dependencies.

