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

2. **Configure References**: Update `urls.csv` with URLs to test. Only use webpath, leave out the domain.

3. **Actions**:

    ```bash
    npm run ACTION
    ```

    Possible ACTION:
    * **init**: remove all screenshots, take new ones (fetch) and accept them (accept)
    * **fetch**: fetch URLs from CSV file and save screenshots
    * **diff**: compare screenshots against baseline and generate HTML report
    * **report**: generate a HTML report (report.html) of all test results
    * **test**: runs fetch, diff and report actions in sequence
    * **accept**: accept current screenshots as baseline for future comparisons
    * **urls**: list all urls from the CSV file

4. **Typical workflow**:

    1. Before your first test on a site: `npm run init`.
    2. Then make changes to the site.
    3. Run `npm run test` to take new screenshots and report difference
    4. Open/reload report.html in your browser to see the differences
    5. If there are any unwanted differences, return to step 2
    6. Otherwise, if you are happy with the new screenshots, run `npm run accept` to save them as the new baseline.

## Notes

- Screenshots are saved in `screenshots/latest`, `screenshots/accepted`, and `screenshots/diff`.
- The script compares images based on pixel differences, ignoring text flow.
- Default browser is Chromium, but in principle Firefox and Safari engines could be used.
- Default viewport is set to 1080x2000.
- Add vireg.css to your project to style the pages before screenshots. It is useful to make dynamic (e.g. date) or animated elements invisible so they won't appear as a difference.

## Dependencies

* [playwright](https://github.com/microsoft/playwright): for loading a page in a headless browser and taking screenshots
* [pixelmatch](https://github.com/mapbox/pixelmatch): for comparing images
* [csv-parser](https://github.com/mafintosh/csv-parser): for parsing CSV files
