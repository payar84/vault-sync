# vault-sync

> CLI tool to sync secrets from HashiCorp Vault to local `.env` files with namespace support.

---

## Installation

```bash
pip install vault-sync
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install vault-sync
```

---

## Usage

Authenticate and pull secrets from a Vault namespace into a local `.env` file:

```bash
vault-sync pull \
  --addr https://vault.example.com \
  --token s.xxxxxxxx \
  --namespace production \
  --path secret/myapp \
  --output .env
```

Push local `.env` values back to Vault:

```bash
vault-sync push --path secret/myapp --input .env
```

**Example `.env` output:**

```
DATABASE_URL=postgres://user:pass@localhost/db
API_KEY=abc123
DEBUG=false
```

Run `vault-sync --help` to see all available commands and options.

---

## Requirements

- Python 3.8+
- A running [HashiCorp Vault](https://www.vaultproject.io/) instance
- A valid Vault token or supported auth method

---

## License

This project is licensed under the [MIT License](LICENSE).