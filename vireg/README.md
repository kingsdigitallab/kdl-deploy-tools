# Visual Regression Toolkit (vireg)

This script automates [visual regression testing](https://www.browserstack.com/percy/visual-regression-testing) for web pages. 
It generates screenshots of URLs from a CSV file, 
compares them with baseline images, 
and reports differences in an HTML format.

## Usage

1. **Install Dependencies**: Ensure you have Node.js installed. Install the required packages using npm:
   ```bash
   npm ci
   ```

2. **Configure References**: Update `refs.csv` with URLs to test.

3. **Actions**:

    ```bash
    npm run ACTION
    ```

    Possible ACTION:
    * **fetch**: fetch URLs from CSV file and save screenshots.
    * **diff**: compare screenshots against baseline and generate HTML report.
    * **report**: generate HTML report of all test results.
    * **test**: runs fetch, diff and report actions in sequence
    * **accept**: accept current screenshots as baseline for future comparisons
    * **urls**: list all urls from the CSV file

## Notes

- Screenshots are saved in `screenshots/latest`, `screenshots/accepted`, and `screenshots/diff`.
- The script compares images based on pixel differences, ignoring text flow.
- Remove baseline screenshots before accepting new ones: `node vireg/vireg.mjs accept`.

## Dependencies

* [playwright](https://github.com/microsoft/playwright): for loading a page in a headless browser and taking screenshots
* [pixelmatch](https://github.com/mapbox/pixelmatch): for comparing images
* [csv-parser](https://github.com/mafintosh/csv-parser): for parsing CSV files
