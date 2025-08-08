import { createRequire } from "module";
const require = createRequire(import.meta.url);

const {program} = require('commander');
import puppeteer from 'puppeteer';

program
  .version('1.0.0', '-v, --version')
  .usage('[OPTIONS]...')
  .option('-u, --url <url>', "URL to render")
  .option('-w, --width <width>', "Width of the viewport")
  .option('-h, --height <height>', "Height of the viewport")
  .option('-p, --path <path>', "Path to save the file to")
  .option('-b, --browser <browser>', "Browser to use (firefox or chrome, must be installed with `npx puppeteer browsers install <browser>`)")
  .parse(process.argv);

const options = program.opts();

const browserConfig = {browser: options.browser}

if (options.browser == 'firefox') {
  browserConfig.extraPrefsFirefox = {
    'gfx.text.disable-aa': true,
    'gfx.font_rendering.cleartype_params.cleartype_level': 0,
    'gfx.font_rendering.cleartype_params.pixel_structure': 0,
    'gfx.font_rendering.cleartype_params.rendering_mode': 1,
  };
}

if (options.browser == 'chrome') {
  browserConfig.args = [
    '--no-sandbox --disable-gpu'
  ];
}

const browser = await puppeteer.launch(browserConfig);
const page = await browser.newPage();
await page.setViewport({
    width: parseInt(options.width),
    height: parseInt(options.height),
    deviceScaleFactor: 1,
    isMobile: true,
});
await page.goto(options.url, {waitUntil: 'networkidle2'});
await page.screenshot({path: options.path});
await browser.close();