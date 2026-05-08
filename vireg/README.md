# Visual Regression Toolkit (vireg)

This script automates [visual regression testing](https://www.browserstack.com/percy/visual-regression-testing) for web pages.
It generates screenshots of URLs from a CSV file,
compares them with baseline images,
and reports differences in an HTML format.

## Example

![image](https://github.com/user-attachments/assets/14237b69-dcd8-49a6-87d0-ed037ff3c6d3)

## Installation

Ensure you have Node.js installed. Install the required packages:

```bash
npm ci
```

## Configuration

Settings are read from a `.env` file in the project root or from environment variables.

| Variable | Default | Description |
|----------|---------|-------------|
| `VIREG_DOMAIN` | *(see below)* | Domain alias from `config.json` or a literal URL. |
| `VIREG_PROJECT` | `default` | Name of the project folder under `projects/`. |

## Project files

Each project lives in `projects/<VIREG_PROJECT>/` and contains:

- `urls.csv` — list of URLs to screenshot (see format below).
- `vireg.css` *(optional)* — custom CSS injected before taking screenshots.
- `config.json` *(optional)* — domain aliases and default domain (see below).
- `screenshots/accepted/` — baseline screenshots.
- `screenshots/latest/` — most recently fetched screenshots.
- `screenshots/diff/` — pixel-diff images where differences were found.
- `report.html` — generated HTML report.

On the first `init` run, all **files** (but not sub-folders) from `projects/TEMPLATE/` are copied into the new project folder automatically. Edit the files in `projects/TEMPLATE/` to change what new projects start with.

### Domain configuration with `config.json`

If `config.json` exists in the project folder, the domain is resolved through its aliases:

```json
{
  "domains": {
    "local": "http://localhost:8082",
    "staging": "https://staging.example.com",
    "prod": "https://example.com"
  },
  "domain": "local"
}
```

Resolution rules:
1. If `VIREG_DOMAIN` matches a key in `domains`, that value is used.
2. If `VIREG_DOMAIN` does **not** match any key, it is treated as a literal domain URL (backward compatible).
3. If `VIREG_DOMAIN` is not set, the alias in the `domain` key is used.
4. If `config.json` is missing or invalid, the default is `http://localhost:8082`.

### urls.csv format

```
url,delay,waitFor,unused
/,,,
/about,,,
/contact,,div.loaded,
/?page={page},2000,,page=1|2|3
```

* **`url`** — Path (without domain). Supports `{variable}` interpolation.
* **`delay`** — *(optional)* Delay in milliseconds before screenshot (overrides `PRE_SCREENSHOT_DELAY`).
* **`waitFor`** — *(optional)* CSS selector to wait for before capturing.
* **other columns** — Any column can be referenced as `{column}` in `url`; pipe `|` separates multiple values.

## Actions

Run via `npm run ACTION` where `ACTION` is one of:

* **`init`** — Remove all screenshots, fetch new ones, accept them as baseline, and run diff.
* **`fetch`** — Load each URL and save a screenshot to `screenshots/latest/`.
* **`diff`** — Compare `latest/` against `accepted/` and write diff images to `screenshots/diff/`.
* **`report`** — Generate `report.html` showing all diffs for review.
* **`test`** — Run `fetch`, `diff`, and `report` in sequence.
* **`accept`** — Copy current `latest/` screenshots to `accepted/` as the new baseline.
* **`urls`** — List all resolved URLs from the CSV.

## Typical workflow

1. **First run**: `npm run init` — creates project files, takes baseline screenshots.
2. **Make changes** to the site.
3. **Test**: `npm run test` — takes new screenshots, diffs them, and opens `report.html`.
4. **Review** `report.html` in your browser.
5. If unwanted differences are found, fix the site and return to step 2.
6. **Accept** the new baseline: `npm run accept`.

## Notes

- Default viewport is **1280 × 2000**.
- Full-page screenshots are captured by default.
- The default pre-screenshot delay is **1000 ms**.
- If a `waitFor` selector is not found within 10 seconds, the screenshot falls back to the delay.
- `report.html` reads `report.js` from the toolkit root to enable the zoom overlay.

## Dependencies

- [playwright](https://github.com/microsoft/playwright) — headless browser screenshots
- [pixelmatch](https://github.com/mapbox/pixelmatch) — pixel-level image comparison
- [pngjs](https://github.com/lukeapage/pngjs) — PNG encoding/decoding
- [csv-parser](https://github.com/mafintosh/csv-parser) — CSV parsing
- [liquidjs](https://github.com/harttle/liquidjs) — HTML report templating
- [dotenv](https://github.com/motdotla/dotenv) — environment variable loading
