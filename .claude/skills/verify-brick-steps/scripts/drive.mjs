#!/usr/bin/env node
// Drive a served Brick Steps site in a real browser engine and record evidence.
//   node drive.mjs JOURNEY --base URL --out DIR [--slug SLUG] [--engine chromium|webkit] [--url URL]
//   JOURNEY: gallery | manual-steps | step-3d | cables-missions | shot
// Every journey starts in a fresh browser profile (empty localStorage) on an iPad Mini screen.
// Writes DIR/<journey>-<engine>/: numbered .png and .aria.txt pairs, console.log, result.json.
// Exits 0 only when every check passed and no page threw an uncaught error.
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const require = createRequire(import.meta.url);
function playwright() {
  try {
    return require("playwright");
  } catch {
    return require(path.join(execSync("npm root -g").toString().trim(), "playwright"));
  }
}
const { webkit, chromium, devices } = playwright();

const argv = process.argv.slice(2);
const journey = argv[0];
const opt = (name, fallback) => {
  const i = argv.indexOf(`--${name}`);
  return i > 0 ? argv[i + 1] : fallback;
};
const base = (opt("base", "") || "").replace(/\/?$/, "/");
const slug = opt("slug", "tank-1");
const engineName = opt("engine", "chromium");
const outRoot = opt("out");
const JOURNEYS = { gallery, "manual-steps": manualSteps, "step-3d": step3d, "cables-missions": cablesMissions, shot };
if (!JOURNEYS[journey] || !outRoot || (journey !== "shot" && !opt("base"))) {
  console.error(fs.readFileSync(new URL(import.meta.url)).toString().split("\n").slice(1, 4).join("\n"));
  process.exit(2);
}
const dir = path.join(outRoot, `${journey}-${engineName}`);
fs.mkdirSync(dir, { recursive: true });

const checks = [];
const log = [];
let shots = 0;
let page;

function check(label, ok, detail = "") {
  checks.push({ label, ok: Boolean(ok), detail });
  console.log(`${ok ? "ok  " : "FAIL"} ${label}${detail ? ` (${detail})` : ""}`);
}

async function capture(label) {
  const name = `${String(++shots).padStart(2, "0")}-${label}`;
  await page.screenshot({ path: path.join(dir, `${name}.png`) });
  const aria = await page.locator("body").ariaSnapshot();
  fs.writeFileSync(path.join(dir, `${name}.aria.txt`), `${page.url()}\n${aria}\n`);
  return path.join(dir, `${name}.png`);
}

async function visible(selector, timeout = 10000) {
  try {
    await page.locator(selector).first().waitFor({ state: "visible", timeout });
    return true;
  } catch {
    return false;
  }
}

// The manual shows one card at a time: the current card carries the class "on".
async function current() {
  return page.evaluate(() => document.querySelector("#deck .card.on")?.id ?? null);
}

async function gallery() {
  await page.goto(base);
  check("map shows a stop per ready model", await visible(".map a.stop[data-name]"));
  await capture("map");
  const stop = page.locator(`.map a.stop[href="${slug}/"]`);
  check(`map has a stop for ${slug}`, (await stop.count()) === 1, "a draft model has no stop; it is in the lab");
  if ((await stop.count()) !== 1) return;
  const name = await stop.getAttribute("data-name");
  await stop.click();
  check("tapping the stop opens the sheet", await visible(".sheet.on .name"));
  check("sheet names the model", (await page.locator(".sheet .name").textContent()) === name, name);
  check("sheet shows parts and steps", /부품 \d+개 · \d+단계/.test(await page.locator(".sheet .meta").textContent()));
  await capture("sheet");
  await page.locator(".sheet .go").click();
  await page.waitForURL(`**/${slug}/**`);
  check("'만들기 시작' opens the manual on its cover", await visible("#cover h1"));
  check("cover title matches", (await page.locator("#cover h1").textContent()) === name);
  await capture("manual-cover");
  await page.goto(base);
  await visible(".site-head .brand");
  for (let k = 0; k < 5; k++) await page.locator(".site-head .brand").click();
  await page.waitForURL("**/lab/**", { timeout: 5000 }).catch(() => {});
  check("five taps on the logo open the lab", /\/lab\/$/.test(new URL(page.url()).pathname), page.url());
  check("lab heading reads 실험실", (await page.locator("h1").first().textContent())?.includes("실험실"));
  await capture("lab");
}

async function manualSteps() {
  await page.goto(`${base}${slug}/`);
  check("manual opens on the cover", await visible("#cover.on"));
  check("next button reads 시작하기", (await page.locator(".pager .next").textContent()) === "시작하기 ›");
  check("previous button is disabled on the cover", await page.locator(".pager .prev").isDisabled());
  await capture("cover");
  await page.locator(".pager .next").click();
  check("next shows step 1", (await current()) === "step-1");
  check("address shows #step-1", new URL(page.url()).hash === "#step-1");
  // The 3D view replaces the rendered picture when WebGL works; either one is what the child sees.
  const shown = await page
    .waitForFunction(() => {
      const fig = document.querySelector("#step-1 .step-img");
      const img = fig?.querySelector("img");
      return fig?.querySelector(".stage3d canvas") || (img && img.naturalWidth > 0 && img.offsetWidth > 0);
    }, null, { timeout: 15000 })
    .then(() => true, () => false);
  check("step 1 shows its 3D view or picture", shown);
  check("step 1 lists the parts it needs", (await page.locator("#step-1 .tray li").count()) > 0);
  await capture("step-1");
  await page.locator(".pager .next").click();
  check("next again shows step 2", (await current()) === "step-2");
  await page.keyboard.press("ArrowLeft");
  check("left arrow goes back to step 1", (await current()) === "step-1");
  await page.goto(`${base}${slug}/`);
  check("reopening resumes at the last card", (await current()) === "step-1");
  await page.locator(".chapters .toc").click();
  check("contents button opens the contents", await visible("dialog.contents[open]"));
  await capture("contents");
  await page.locator('dialog.contents a[href="#done"]').first().click();
  check("contents jumps to the finished card", (await current()) === "done");
  await capture("done");
  const last = await page.evaluate(() => [...document.querySelectorAll("#deck .card")].pop().id);
  for (let k = 0; k < 10 && (await current()) !== last; k++) await page.locator(".pager .next").click();
  check(`last card (${last}) offers 처음으로`, (await page.locator(".pager .next").textContent()) === "처음으로");
  await page.locator(".pager .next").click();
  check("처음으로 returns to the cover", (await current()) === "cover");
  await page.goto(base);
  const stop = page.locator(`.map a.stop[href="${slug}/"]`);
  if (await stop.count()) {
    await visible(".map a.stop");
    check("gallery marks the model as built", await stop.evaluate((a) => a.classList.contains("built")));
    await capture("map-built");
  }
}

async function step3d() {
  await page.goto(`${base}${slug}/#step-1`);
  check("step 1 is shown", (await current()) === "step-1");
  check("3D view replaces the picture", await visible("#step-1 figure.has-3d .stage3d canvas", 30000));
  await page.waitForTimeout(1500); // the step's parts drop in for 600 ms; let them land
  const canvas = page.locator("#step-1 .stage3d canvas");
  const before = await canvas.screenshot({ path: path.join(dir, "3d-before.png") });
  await capture("3d-step-1");
  const box = await canvas.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 160, box.y + box.height / 2 + 30, { steps: 12 });
  await page.mouse.up();
  await page.waitForTimeout(300);
  check("dragging hides the hint", await page.locator("#step-1 .stage3d .hint").evaluate((p) => p.classList.contains("gone")));
  const after = await canvas.screenshot({ path: path.join(dir, "3d-after-drag.png") });
  check("dragging turns the model", !before.equals(after), "canvas pixels changed");
  await capture("3d-dragged");
  await page.locator("#step-1 .stage3d .home").click();
  await page.waitForTimeout(300);
  await capture("3d-home");
}

async function cablesMissions() {
  await page.goto(`${base}${slug}/#cables`);
  if ((await current()) === "cables") {
    const ports = await page.locator("#cables .port").allTextContents();
    check("cable card lists the ports", ports.length > 0, ports.join(" "));
    await capture("cables");
  } else {
    check("cable card exists", false, `${slug} has no #cables card`);
  }
  await page.goto(`${base}${slug}/#mission-1`);
  check("mission 1 is shown", (await current()) === "mission-1");
  const blocks = await page.locator("#mission-1 [data-block]").evaluateAll((els) => els.map((e) => e.dataset.block));
  check("mission 1 shows its word blocks", blocks.length > 0, blocks.join(" "));
  await capture("mission-1");
}

async function shot() {
  await page.goto(opt("url", base));
  await page.waitForLoadState("networkidle");
  await capture("page");
}

const engine = engineName === "webkit" ? webkit : chromium;
let browser;
try {
  browser = await engine.launch();
  const context = await browser.newContext({ ...devices["iPad Mini"], locale: "ko-KR" });
  page = await context.newPage();
  page.setDefaultTimeout(15000);
  page.on("console", (m) => log.push(`[${m.type()}] ${m.text()}`));
  page.on("pageerror", (e) => {
    log.push(`[pageerror] ${e.message}`);
    check("no uncaught page error", false, e.message);
  });
  await JOURNEYS[journey]();
} catch (e) {
  check("journey ran to the end", false, e.message.replace(/\s+/g, " ").slice(0, 300));
  if (page) await capture("at-error").catch(() => {});
} finally {
  fs.writeFileSync(path.join(dir, "console.log"), log.join("\n") + "\n");
  const result = { journey, engine: engineName, slug, base, checks, ok: checks.length > 0 && checks.every((c) => c.ok) };
  fs.writeFileSync(path.join(dir, "result.json"), JSON.stringify(result, null, 2) + "\n");
  if (browser) await browser.close();
  console.log(`${result.ok ? "PASS" : "FAIL"} ${journey} on ${engineName}: ${dir}`);
  process.exitCode = result.ok ? 0 : 1;
}
