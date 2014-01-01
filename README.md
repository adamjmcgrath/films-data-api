# Films data api

This is an App Engine application that indexes films from the Freebase API and makes them available as a using the
App Engine Search API.

It can be used for autocomplete as the film titles are tokenized and can be searched using partial queries.

The search results are ranked by gross revenue, when available, then release date.

## Example

`GET /api?q=potter`

```json
[
  {
    "year": 2010,
    "rank": 956399711,
    "key": "/en/harry_potter_and_the_deathly_hallows_part_i",
    "title": "Harry Potter and the Deathly Hallows - Part I"
  },
  {
    "year": 2009,
    "rank": 934416487,
    "key": "/en/harry_potter_and_the_half_blood_prince_2008",
    "title": "Harry Potter and the Half-Blood Prince"
  },
  ...
]
```

## Usage

To use, you need your own Freebase API key. Copy `secrets.py.example` to `secrets.py` and add your API key.
