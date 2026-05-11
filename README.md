# IP Geolocation MCP Server

[![Smithery](https://smithery.ai/badge/ip-geolocation-mcp)](https://smithery.ai/server/ip-geolocation-mcp)

An MCP (Model Context Protocol) server that provides IP geolocation data using [ipinfo.io](https://ipinfo.io) (free tier — no API key required, 50,000 lookups/month).

## Tools

### `ip_lookup(ip)`

Look up geolocation data for a specific IP address.

**Parameters:**
| Name | Type   | Required | Description                                      |
|------|--------|----------|--------------------------------------------------|
| `ip` | string | yes      | IPv4 or IPv6 address (e.g. `"8.8.8.8"`)         |

**Returns:** city, region, country, org (ISP), timezone, postal code, latitude, longitude.

### `ip_lookup_own()`

Get geolocation data for your own public IP address. No arguments needed.

### `ip_batch(ips)`

Batch lookup up to 10 IP addresses at once.

**Parameters:**
| Name | Type         | Required | Description                          |
|------|--------------|----------|--------------------------------------|
| `ips`| string[]     | yes      | Array of IPs (max 10)               |

**Returns:** Array of geolocation objects, one per IP.

## Usage

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ip-geolocation": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {}
    }
  }
}
```

Or via **uv** (recommended for dependency management):

```json
{
  "mcpServers": {
    "ip-geolocation": {
      "command": "uv",
      "args": [
        "--directory", "path/to/ip-geolocation-mcp",
        "run", "server.py"
      ]
    }
  }
}
```

### Any MCP Client

```bash
pip install -r requirements.txt
python server.py
```

## Pricing

| Tier      | Price     | Lookups/month |
|-----------|-----------|---------------|
| Free      | $0        | 50,000        |
| Pro       | $19/month | Unlimited     |

[Subscribe to Pro](https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m)

## Deployment

### Smithery

This server is compatible with [Smithery.ai](https://smithery.ai). See `smithery.yaml` for configuration.

## Data Fields

Each lookup returns:

| Field       | Description                | Example             |
|-------------|----------------------------|---------------------|
| `ip`        | Queried IP address         | `8.8.8.8`           |
| `city`      | City name                  | `Mountain View`     |
| `region`    | Region/state               | `California`        |
| `country`   | 2-letter ISO country code  | `US`                |
| `org`       | ISP/Organization           | `AS15169 Google LLC`|
| `timezone`  | IANA timezone              | `America/Los_Angeles`|
| `postal`    | Postal/ZIP code            | `94043`             |
| `latitude`  | Latitude                   | `37.4056`           |
| `longitude` | Longitude                  | `-122.0775`         |
| `loc`       | Raw "lat,lon" string       | `37.4056,-122.0775` |

## License

MIT
