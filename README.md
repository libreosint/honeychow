# Honey Chow

A fast, asynchronous username enumeration tool.

Search for usernames across 705+ websites simultaneously to identify where accounts exist online.

## Installation

```bash
pip install honeychow
```

Requires Python 3.13+

## Usage

```bash
# Basic search
honeychow <username>

# Limit to specific sites
honeychow <username> -s GitHub Twitter Instagram

# Search specific categories
honeychow <username> -c social gaming

# Export results to CSV
honeychow <username> -o results.csv

# Adjust concurrency and timeout
honeychow <username> -w 50 -t 20
```

## Options

| Option                  | Description                              |
|-------------------------|------------------------------------------|
| `-s, --sites`           | Check specific sites only                |
| `-c, --categories`      | Search specific categories               |
| `-t, --timeout`         | Request timeout in seconds (default: 15) |
| `-w, --workers`         | Max concurrent requests (default: 100)   |
| `-o, --output`          | Export results to CSV                    |
| `-T, --table`           | Display results in table format          |
| `-N, --not-found`       | Show sites where username wasn't found   |
| `-f, --failed`          | Show failed checks                       |
| `-q, --quiet`           | Summary only, no live output             |
| `-S, --list-sites`      | List all available sites                 |
| `-C, --list-categories` | List all categories                      |
| `-d, --database`        | Load sites from local JSON file          |

## Database

By default, honeychow fetches the sites database
from [/data/honeychow-sites.json](https://github.com/libreosint/honeychow/blob/master/data/honeychow-sites.json) in this
repository. You can use a local database instead with the `-d/--database` option:

```bash
honeychow <username> -d /path/to/sites.json
```

The local file must follow the same structure as the remote database.

## Honey Chow?

So there's this song called *Different Drum* by Linda Ronstadt & The Stone Poneys (1967). At some point she sings "You
cry and moan and say it will work out. But **honey child** I've got my doubts" but my brain decided that was "**honey
chow**"
instead. I have no idea what a 'honey chow' would even be. A sweet dog breed? Some kind of food? (I recently found out
there's an
Indian-South African fast-food called **Bunny Chow**) Anyway, I needed a
project name and here we are.

## License

MIT License. See [choosealicense.com](https://choosealicense.com/licenses/mit/) for details.
