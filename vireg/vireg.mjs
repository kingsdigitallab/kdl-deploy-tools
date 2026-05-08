/*
TODO:
* better image comparison that takes text flow into account
* multi-project mode, with one folder per project, which contains urls.csv, reports.html and the screenshots
D screenshots of all urls found in refs.csv
D screenshot of the full web page length, no truncation
D screenshots of urls created from book and page columns in refs
D report: generate a html with all the differences
D test: fetch+diff+report
D remove content of diff folder at the start of the diff action
D delay before screenshot
*/

import 'dotenv/config';
import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { Liquid } from 'liquidjs';
import csvParser from 'csv-parser';
import {PNG} from 'pngjs';
import pixelmatch from 'pixelmatch';

const __dirname = import.meta.dirname;

const TEMPLATE_DIR = path.join(__dirname, 'projects', 'TEMPLATE');

// const VIEWPORT = {width: 1920, height: 2000}
const VIREG_PROJECT = process.env.VIREG_PROJECT || 'default';
const PROJECT_ROOT = path.join(__dirname, 'projects', VIREG_PROJECT);
const VIEWPORT = {width: 1280, height: 2000}
const URLS_CSV_PATH = path.join(PROJECT_ROOT, 'urls.csv');
const STYLESHEET_PATH = path.join(PROJECT_ROOT, 'vireg.css');
const SCREENSHOTS_BASELINE_PATH = path.join(PROJECT_ROOT, 'screenshots/accepted');
const SCREENSHOTS_LATEST_PATH = path.join(PROJECT_ROOT, 'screenshots/latest');
const SCREENSHOTS_DIFF_PATH = path.join(PROJECT_ROOT, 'screenshots/diff');
const REPORT_FILE_PATH = path.join(PROJECT_ROOT, 'report.html');
const REPORT_TEMPLATE_PATH = path.join(__dirname, 'report-template.liquid');
const CAPTURE_FULL_PAGE = true;
const PRE_SCREENSHOT_DELAY = 1000;

class VisualRegressionToolkit {
  constructor() {
    this.rows = [];
    this.urls = [];
  }

  resolveDomain() {
    const envDomain = process.env.VIREG_DOMAIN;

    const configPath = path.join(PROJECT_ROOT, 'config.json');
    if (!fs.existsSync(configPath)) {
      return envDomain || 'http://localhost:8082';
    }

    let config;
    try {
      config = JSON.parse(fs.readFileSync(configPath).toString());
    } catch (err) {
      console.error('Failed to parse config.json:', err.message);
      return envDomain || 'http://localhost:8082';
    }

    const domains = config && config.domains ? config.domains : null;
    if (!domains) {
      return envDomain || 'http://localhost:8082';
    }

    if (envDomain && domains[envDomain]) {
      return domains[envDomain];
    }

    if (envDomain) {
      return envDomain;
    }

    const defaultAlias = config.domain || null;
    if (defaultAlias && domains[defaultAlias]) {
      return domains[defaultAlias];
    }

    return 'http://localhost:8082';
  }

  async init() {
    console.log('initialisation');
    
    if (!fs.existsSync(PROJECT_ROOT)) {
      fs.mkdirSync(PROJECT_ROOT, { recursive: true });
      this.copyTemplateFiles();
    }

    this.domain = this.resolveDomain();
    console.log(`Using domain: ${this.domain}`);

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

  copyTemplateFiles() {
    if (!fs.existsSync(TEMPLATE_DIR)) {
      return;
    }
    fs.readdirSync(TEMPLATE_DIR).forEach(file => {
      const src = path.join(TEMPLATE_DIR, file);
      const dest = path.join(PROJECT_ROOT, file);
      if (fs.statSync(src).isFile()) {
        fs.copyFileSync(src, dest);
        console.log(`Created default ${file} for project ${VIREG_PROJECT}`);
      }
    });
  }

  async run() {
    const args = process.argv.slice(2);

    if (args.length > 0) {
      const action = args[0];

      await this.init()

      switch (action) {
        case 'init':
          await this.actionInit();
          break;
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

  async actionInit() {
    await this.actionFetch()
    await this.actionAccept()
    await this.actionDiff()
  }

  async actionTest() {
    await this.actionFetch()
    await this.actionDiff()
    await this.actionReport()
  }

  async actionFetch() {
    this.removeScreenshots(SCREENSHOTS_LATEST_PATH)

    for (const urlConfig of this.urls) {
      await this.takeScreenshot(urlConfig)
    }
  }

  async actionAccept() {
    if (!fs.existsSync(SCREENSHOTS_BASELINE_PATH)) {
      fs.mkdirSync(SCREENSHOTS_BASELINE_PATH, { recursive: true });
    }

    this.removeScreenshots(SCREENSHOTS_BASELINE_PATH)

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

    this.removeScreenshots(SCREENSHOTS_DIFF_PATH)

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
      const maxWidth = Math.max(img1.width, img2.width);
      const maxHeight = Math.max(img1.height, img2.height);
      const overlapWidth = Math.min(img1.width, img2.width);
      const overlapHeight = Math.min(img1.height, img2.height);

      const diffImg = new PNG({ width: maxWidth, height: maxHeight });
      const RED = [255, 0, 0, 255];

      function fillRect(data, imgWidth, x, y, w, h, color) {
        for (let row = y; row < y + h; row++) {
          for (let col = x; col < x + w; col++) {
            const idx = (row * imgWidth + col) * 4;
            data[idx] = color[0];
            data[idx + 1] = color[1];
            data[idx + 2] = color[2];
            data[idx + 3] = color[3];
          }
        }
      }

      if (maxWidth > img1.width) {
        fillRect(diffImg.data, maxWidth, img1.width, 0, maxWidth - img1.width, img1.height, RED);
      }
      if (maxHeight > img1.height) {
        fillRect(diffImg.data, maxWidth, 0, img1.height, maxWidth, maxHeight - img1.height, RED);
      }
      if (maxWidth > img2.width) {
        fillRect(diffImg.data, maxWidth, img2.width, 0, maxWidth - img2.width, img2.height, RED);
      }
      if (maxHeight > img2.height) {
        fillRect(diffImg.data, maxWidth, 0, img2.height, maxWidth, maxHeight - img2.height, RED);
      }

      if (overlapWidth > 0 && overlapHeight > 0) {
        const crop1 = Buffer.alloc(overlapWidth * overlapHeight * 4);
        const crop2 = Buffer.alloc(overlapWidth * overlapHeight * 4);
        const overlapDiff = Buffer.alloc(overlapWidth * overlapHeight * 4);

        for (let y = 0; y < overlapHeight; y++) {
          const srcRowStart = y * img1.width * 4;
          const dstRowStart = y * overlapWidth * 4;
          crop1.set(img1.data.subarray(srcRowStart, srcRowStart + overlapWidth * 4), dstRowStart);
        }
        for (let y = 0; y < overlapHeight; y++) {
          const srcRowStart = y * img2.width * 4;
          const dstRowStart = y * overlapWidth * 4;
          crop2.set(img2.data.subarray(srcRowStart, srcRowStart + overlapWidth * 4), dstRowStart);
        }

        const diffCount = pixelmatch(crop1, crop2, overlapDiff, overlapWidth, overlapHeight, { threshold: 0.1 });

        for (let y = 0; y < overlapHeight; y++) {
          const srcRowStart = y * overlapWidth * 4;
          const dstRowStart = y * maxWidth * 4;
          diffImg.data.set(overlapDiff.subarray(srcRowStart, srcRowStart + overlapWidth * 4), dstRowStart);
        }
      }

      fs.writeFileSync(diffImagePath, PNG.sync.write(diffImg));
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

  async takeScreenshot(urlConfig) {
    const { url, delay, waitFor } = urlConfig;
    const fullUrl = `${this.domain}${url}`;
    let screenshotPath = path.join(SCREENSHOTS_LATEST_PATH, this.getScreenshotFilenameFromURL(fullUrl));

    // Apply delay (per-URL or default)
    const actualDelay = delay || PRE_SCREENSHOT_DELAY;

    console.log(`Screenshot: ${fullUrl} (delay: ${actualDelay}ms${waitFor ? ', waitFor: ' + waitFor : ''}) -> ${screenshotPath}`);

    try {
      const TIMEOUT_DEFAULT_MILISECS = 10000
      await this.webPage.goto(fullUrl, { timeout: TIMEOUT_DEFAULT_MILISECS })
      if (actualDelay > 0) {
        await this.webPage.waitForTimeout(actualDelay);
      }
      await this.webPage.waitForLoadState('networkidle', { timeout: TIMEOUT_DEFAULT_MILISECS })
      await this.webPage.waitForLoadState('domcontentloaded', { timeout: TIMEOUT_DEFAULT_MILISECS })
      
      // Wait for specific selector if configured
      if (waitFor) {
        try {
          await this.webPage.waitForSelector(waitFor, { timeout: TIMEOUT_DEFAULT_MILISECS });
          console.log(`  Waited for selector: ${waitFor}`);
        } catch (err) {
          console.warn(`  Selector '${waitFor}' not found, falling back to delay`);
        }
      }
      

      await this.webPage.screenshot({
        path: screenshotPath,
        animations: 'disabled',
        style: this.styleSheetContent,
        fullPage: CAPTURE_FULL_PAGE,
        timeout: 30000
      });
    } catch (error) {
      console.error(`Failed to screenshot ${fullUrl}: ${error.message}`);
    }
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
    const relativeUrl = url.replace(this.domain, '');
    const validFileName = 's__' + relativeUrl.replace(/[^a-z0-9]/gi, '_').toLowerCase().replace(/^_+|_+$/g, '');
    return `${validFileName}.png`;
  }

  removeScreenshots(dirPath) {
    // remove all latest screenshots
    if (fs.existsSync(dirPath)) {
        fs.readdirSync(dirPath).forEach(file => {
            if (file.endsWith('.png')) {
                fs.unlinkSync(path.join(dirPath, file));
            }
        })
    }
  }

  async actionUrls() {
    for (let i = 0; i < this.urls.length; i++) {
      const config = this.urls[i];
      const extra = config.delay || config.waitFor 
        ? ` (delay: ${config.delay || PRE_SCREENSHOT_DELAY}ms${config.waitFor ? ', waitFor: ' + config.waitFor : ''})` 
        : '';
      console.log(`${i}: ${config.url}${extra}`)
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
    Returns a list of URL config objects generated by substituting variables from row.url with values from the row object.
    Each config object is: { url: string, delay: number|null, waitFor: string|null }
    Variables in row.url are wrapped in curly braces.
    Any key in the row object can contain mutliple values separated by a pipe '|'.
    Example:
    row = { url: "https://example.com/{var1}/{var2}", var1: "A|B", var2: "Z", delay: "2000", waitFor: ".loaded" }
    The resulting configs will be [
      { url: "https://example.com/A/Z", delay: 2000, waitFor: ".loaded" },
      { url: "https://example.com/B/Z", delay: 2000, waitFor: ".loaded" }
    ]
    */
    let ret = []

    if (!row.url) return ret;

    // Extract config from row (preserved across all interpolated URLs)
    const delay = row.delay ? parseInt(row.delay, 10) : null;
    const waitFor = row.waitFor || null;

    // find variables used in the template
    let varNames = row.url.match(/\{([^}]+)\}/g)
    if (!varNames) return [{ url: row.url, delay, waitFor }];
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
      const interpolatedUrl = row.url.replace(/\{([^}]+)\}/g, v => combi[v.replace(/[{}]/g, '')])
      ret.push({ url: interpolatedUrl, delay, waitFor })
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
    let diffs = [];

    const diffFiles = new Set(fs.readdirSync(SCREENSHOTS_DIFF_PATH));

    for (const urlConfig of this.urls) {
      const relativeUrl = urlConfig.url;
      let url = `${this.domain}${relativeUrl}`;
      const validFileName = this.getScreenshotFilenameFromURL(url);

      if (diffFiles.has(`${validFileName}`)) {
        diffs.push({
          relativeUrl,
          url,
          validFileName,
          baseline: `${SCREENSHOTS_BASELINE_PATH}/${validFileName}`,
          latest: `${SCREENSHOTS_LATEST_PATH}/${validFileName}`,
          diff: `${SCREENSHOTS_DIFF_PATH}/${validFileName}`
        });
      }
    }

    const engine = new Liquid();
    
    if (!fs.existsSync(REPORT_TEMPLATE_PATH)) {
      console.error(`Template not found: ${REPORT_TEMPLATE_PATH}`);
      return;
    }

    const templateContent = fs.readFileSync(REPORT_TEMPLATE_PATH).toString();
    
    const reportContent = await engine.parseAndRender(templateContent, {
      diffCount: diffs.length,
      diffs: diffs
    });

    fs.writeFileSync(REPORT_FILE_PATH, reportContent);
    console.log(`Report generated: ${REPORT_FILE_PATH}`);
  }
}

let vr = new VisualRegressionToolkit()
vr.run()
