/*
TODO:
* better image comparison that takes text flow into account
* parametrise DOMAIN
D screenshots of all urls found in refs.csv
D screenshot of the full web page length, no truncation
D screenshots of urls created from book and page columns in refs
D report: generate a html with all the differences
D test: fetch+diff+report
D remove content of diff folder at the start of the diff action
D delay before screenshot
*/

import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import csvParser from 'csv-parser';
import {PNG} from 'pngjs';
import pixelmatch from 'pixelmatch';

// const VIEWPORT = {width: 1920, height: 2000}
const DOMAIN = 'http://localhost:8082';
const VIEWPORT = {width: 1280, height: 2000}
const URLS_CSV_PATH = 'urls.csv';
const STYLESHEET_PATH = 'vireg.css'
const SCREENSHOTS_BASELINE_PATH = 'screenshots/accepted';
const SCREENSHOTS_LATEST_PATH = 'screenshots/latest';
const SCREENSHOTS_DIFF_PATH = 'screenshots/diff';
const REPORT_FILE_PATH = 'report.html';
const __dirname = import.meta.dirname;

class VisualRegressionToolkit {
  constructor() {
    this.rows = [];
    this.urls = [];
  }

  async init() {
    console.log('initialisation');
    
    this.urls = await this.readUrls()

    this.styleSheetContent = this.readStyleSheet()

    this.browser = await chromium.launch({ headless: true });
    const context = await this.browser.newContext();
    this.webPage = await context.newPage();
    await this.webPage.setViewportSize(VIEWPORT);

    // ensure diff directory exists
    if (!fs.existsSync(SCREENSHOTS_DIFF_PATH)) {
      fs.mkdirSync(SCREENSHOTS_DIFF_PATH, { recursive: true });
    }
  }

  async uninit() {
    await this.browser.close()
  }

  async run() {
    const args = process.argv.slice(2);

    if (args.length > 0) {
      const action = args[0];

      await this.init()

      switch (action) {
        case 'fetch':
          await this.actionFetch();
          break;
        case 'accept':
          await this.actionAccept();
          break;
        case 'diff':
          await this.actionDiff();
          break;
        case 'report':
          await this.actionReport();
          break;
        case 'test':
          await this.actionTest();
          break;
        case 'urls':
          await this.actionUrls();
          break;
        default:
          console.log(`Unknown action: ${action}`);
          break;
      }

      await this.uninit()

    } else {
      console.log('No action specified. Please provide an action as the first argument.');
    }
  }

  async actionTest() {
    await this.actionFetch()
    await this.actionDiff()
    await this.actionReport()
  }

  async actionFetch() {
    await this.removeScreenshots(SCREENSHOTS_LATEST_PATH)

    for (const url of this.urls) {
      await this.takeScreenshot(`${DOMAIN}${url}`)
    }
  }

  async actionAccept() {
    if (!fs.existsSync(SCREENSHOTS_BASELINE_PATH)) {
      fs.mkdirSync(SCREENSHOTS_BASELINE_PATH, { recursive: true });
    }

    await this.removeScreenshots(SCREENSHOTS_BASELINE_PATH)

    if (fs.existsSync(SCREENSHOTS_LATEST_PATH)) {
      fs.readdirSync(SCREENSHOTS_LATEST_PATH).forEach(file => {
        if (file.endsWith('.png')) {
          const sourcePath = path.join(SCREENSHOTS_LATEST_PATH, file);
          const destinationPath = path.join(SCREENSHOTS_BASELINE_PATH, file);
          fs.copyFileSync(sourcePath, destinationPath);
        }
      });
    } else {
      console.log('No latest screenshots found.');
    }
  }

  async actionDiff() {
    let comparedPairs = 0;
    let differentPairs = 0;

    await this.removeScreenshots(SCREENSHOTS_DIFF_PATH)

    if (fs.existsSync(SCREENSHOTS_LATEST_PATH) && fs.existsSync(SCREENSHOTS_BASELINE_PATH)) {
      const latestFiles = new Set(fs.readdirSync(SCREENSHOTS_LATEST_PATH));
      const baselineFiles = new Set(fs.readdirSync(SCREENSHOTS_BASELINE_PATH));

      for (const file of latestFiles) {
        if (file.endsWith('.png') && baselineFiles.has(file)) {
          const screenshotPath1 = path.join(SCREENSHOTS_LATEST_PATH, file);
          const screenshotPath2 = path.join(SCREENSHOTS_BASELINE_PATH, file);
          const diffScreenshotPath = path.join(SCREENSHOTS_DIFF_PATH, file);

          const result = await this.compareScreenshots(screenshotPath1, screenshotPath2, diffScreenshotPath);

          console.log(`${result ? 'SAME' : 'DIFF'} ${file}`);
          comparedPairs++;
          if (!result) {
            differentPairs++;
          }
        }
      }

      console.log(`Compared pairs: ${comparedPairs}`);
      console.log(`Different pairs: ${differentPairs}`);

    } else {
      console.log('Either latest or baseline screenshots not found.');
    }
  }

  async compareScreenshots(imagePath1, imagePath2, diffImagePath) {
    const image1 = fs.readFileSync(imagePath1);
    const image2 = fs.readFileSync(imagePath2);

    const img1 = PNG.sync.read(image1);
    const img2 = PNG.sync.read(image2);

    if (img1.width !== img2.width || img1.height !== img2.height) {
      console.log('Images have different dimensions.');
      return false;
    }

    const diffImg = new PNG({ width: img1.width, height: img1.height });

    const diffCount = pixelmatch(img1.data, img2.data, diffImg.data, img1.width, img1.height, { threshold: 0.1 });

    if (diffCount > 0) {
      fs.writeFileSync(diffImagePath, PNG.sync.write(diffImg));
      return false;
    }

    return true;
  }

  async takeScreenshot(url) {
    let screenshotPath = SCREENSHOTS_LATEST_PATH + '/' + this.getScreenshotFilenameFromURL(url);
    console.log(`Screenshot: ${url} -> ${screenshotPath}`);

    await this.webPage.goto(url)
    await this.webPage.waitForLoadState('networkidle')
    await this.webPage.waitForLoadState('domcontentloaded')
    await this.webPage.waitForTimeout(10)

    await this.webPage.screenshot({ 
      path: screenshotPath, 
      animations: 'disabled', 
      style: this.styleSheetContent
    });
  }

  readStyleSheet() {
    let ret = null
    if (fs.existsSync(STYLESHEET_PATH)) {
      ret = fs.readFileSync(STYLESHEET_PATH).toString()
      console.log(`Found stylesheet (${STYLESHEET_PATH}).`)
    }
    return ret;
  }

  getScreenshotFilenameFromURL(url) {
    const relativeUrl = url.replace(DOMAIN, '');
    const validFileName = 's__' + relativeUrl.replace(/[^a-z0-9]/gi, '_').toLowerCase().replace(/^_+|_+$/g, '');
    return `${validFileName}.png`;
  }

  async removeScreenshots(path) {
    // remove all latest screenshots
    // SCREENSHOTS_LATEST_PATH
    if (fs.existsSync(path)) {
        fs.readdirSync(path).forEach(file => {
            if (file.endsWith('.png')) {
                fs.unlinkSync(`${path}/${file}`);
            }
        })
    }
  }

  async actionUrls() {
    for (let i = 0; i < this.urls.length; i++) {
      console.log(`${i}: ${this.urls[i]}`)
    }
    console.log(this.urls.length)
  }

  async readUrls() {
    let ret = []
    let rows = await this.readCSVFile(URLS_CSV_PATH);
    // let row = { 
    //   url: '/{v1}/{v2}/{v3}',
    //   v1: 'a|bb',
    //   v2: 'e|f',
    //   v3: 'y|z'
    // }
    // console.log(this.interpolateUrl(row))

    for (const row of rows) {
      ret.push(...this.interpolateUrl(row))
    }

    return ret
  }

  interpolateUrl(row) {
    /*
    Returns a list or URLs generated by substituting variables from row.url with values from the row object.
    Variables in row.url are wrapped in curly braces.
    Any key in the row object can contain mutliple values separated by a pipe '|'.
    Example:
    row = { url: "https://example.com/{var1}/{var2}", var1: "A|B", var2: "Z" }
    The resulting URLs will be [
      "https://example.com/A/Z",
      "https://example.com/B/Z"
    ]
    */
    let ret = []

    if (!row.url) return ret;

    // find variables used in the template
    let varNames = row.url.match(/\{([^}]+)\}/g)
    if (!varNames) return [row.url];
    varNames = varNames.map(m => m.replace(/[{}]/g, ''))
    
    let combis = [{}]
    
    // first combination is made of the first value of each variable
    for (const varName of varNames) {
      const values = row[varName]
      // console.log(varName, values)
      combis[0][varName] = values.split('|')[0]
    }

    // add combinations for each variable
    for (const varName of varNames) {
      const values = row[varName].split('|')
      let lastIndex = combis.length
      for (let v of values.slice(1)) {
        // apply this value to all previous combinations
        for (let i = 0; i < lastIndex; i++) {
          let combi = {...combis[i]}
          combi[varName] = v
          combis.push(combi)
        }
      }
    }

    for (let combi of combis) {
      ret.push(row.url.replace(/\{([^}]+)\}/g, v => combi[v.replace(/[{}]/g, '')]))
    }

    return ret
  }
  async readCSVFile(filePath) {
    return new Promise((resolve, reject) => {
      const results = [];

      fs.createReadStream(filePath)
        .pipe(csvParser())
        .on('data', (row) => {
          results.push(row);
        })
        .on('end', () => {
          this.rows = results;
          resolve(results);
        })
        .on('error', (err) => {
          reject(err);
        });      
    });
  }

  async actionReport() {
    let reportContent = `
      <html>
      <head>
        <title>Visual Regression Report</title>
        <style>
          table { width: 100%; border-collapse: collapse; }
          th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
          img { max-width: 100%; height: auto; }
        </style>
      </head>
      <body>
        <h1>Visual Regression Report</h1>
        <table>
          <tr>
            <th>URL</th>
            <th>Accepted Image</th>
            <th>Latest Screenshot</th>
            <th>Difference Image</th>
          </tr>
    `;

    const diffFiles = new Set(fs.readdirSync(SCREENSHOTS_DIFF_PATH));

    for (let relativeUrl of this.urls) {
      let url = `${DOMAIN}${relativeUrl}`;
      const validFileName = this.getScreenshotFilenameFromURL(relativeUrl);

      if (diffFiles.has(`${validFileName}`)) {
        reportContent += `
          <tr>
            <td><a href="${url}" target="_blank">${url}</a></td>
            <td><img src="${SCREENSHOTS_BASELINE_PATH}/${validFileName}" alt="Accepted Image"></td>
            <td><img src="${SCREENSHOTS_LATEST_PATH}/${validFileName}" alt="Latest Screenshot"></td>
            <td><img src="${SCREENSHOTS_DIFF_PATH}/${validFileName}" alt="Difference Image"></td>
          </tr>
        `;
      }
    }

    reportContent += `
        </table>
      </body>
      </html>
    `;

    fs.writeFileSync(REPORT_FILE_PATH, reportContent);
    console.log(`Report generated: ${REPORT_FILE_PATH}`);
  }
}

let vr = new VisualRegressionToolkit()
vr.run()

