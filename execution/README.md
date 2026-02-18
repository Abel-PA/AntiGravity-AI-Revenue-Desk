# Execution Scripts

This directory contains **deterministic Python scripts** that do the actual work.

## Principles

- **Deterministic**: Same inputs → same outputs
- **Fast**: Optimized for performance
- **Testable**: Can be run independently
- **Repeatable**: Reliable execution every time

## Structure

Scripts should:
- Accept clear inputs (command-line args, config files, or environment variables)
- Produce clear outputs (files, API calls, database updates)
- Handle errors gracefully with meaningful messages
- Log important steps for debugging

## Dependencies

Use a `requirements.txt` file to track Python dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Scripts should load secrets from `.env` using `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('API_KEY')
```

## Testing

Scripts should be testable in isolation:

```bash
python execution/script_name.py --test-mode
```

## Guidelines

- If something runs more than once, it belongs in code
- Keep scripts focused on a single responsibility
- Use meaningful error messages
- Document complex logic with comments
