# Configuration

Configuration is loaded from environment variables:

| Variable                | Default     | Description                        |
| ----------------------- | ----------- | ---------------------------------- |
| `URL_SHORTENER_HOST`    | `localhost` | Server bind address                |
| `URL_SHORTENER_PORT`    | `8000`      | Server port                        |
| `URL_SHORTENER_WORKERS` | `1`         | Number of workers                  |
| `URL_SHORTENER_STORAGE` | `memory`    | Storage type: `memory` or `sqlite` |
| `URL_SHORTENER_DB_PATH` | `:memory:`  | SQLite database path               |

**Example with SQLite persistence:**

```bash
URL_SHORTENER_STORAGE=sqlite \
URL_SHORTENER_DB_PATH=./urls.db \
uv run python -m url_shortener
```
