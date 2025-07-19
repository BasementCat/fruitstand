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
  .parse(process.argv);

const options = program.opts();

const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.goto(options.url, {waitUntil: 'networkidle2'});
await page.setViewport({width: parseInt(options.width), height: parseInt(options.height)});
await page.screenshot({path: options.path});
await browser.close();