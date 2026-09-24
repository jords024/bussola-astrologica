// Isolated browser check. The go() test hook is injected only into the intercepted
// response, never into the shipped quiz. API calls and external tracking are blocked.
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
(async()=>{
 const browser = await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const context = await browser.newContext({viewport:{width:390,height:844}});
 const page = await context.newPage();
 const errors=[]; const media=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(r.url().endsWith('.mp4'))media.push(r.url());});
 await context.route('**/*',async route=>{
  const u = new URL(route.request().url());
  if(u.origin!=='http://127.0.0.1:8841') return route.abort();
  if(u.pathname.startsWith('/api/'))return route.fulfill({status:204});
  if(u.pathname==='/'){
   let html=fs.readFileSync(path.join(__dirname,'../publico/index.html'),'utf8');
   html=html.replace('  const FLUXO_ATIVO =','  window.__quizGo = go;\n  const FLUXO_ATIVO =');
   return route.fulfill({contentType:'text/html',body:html});
  }
  return route.continue();
 });
 await page.goto('http://127.0.0.1:8841/?t=1&utm_source=qa');
 assert.equal(await page.locator('#ofertaVideo').getAttribute('src'),null);
 assert.equal(media.length,0,'video must not download on initial quiz screen');
 await page.evaluate(()=>window.__quizGo(7));
 await page.locator('#passoGo').click();
 await page.locator('#notaPular').click();
 await page.waitForSelector('[data-s="10"].on');
 assert.equal(await page.locator('#pct').textContent(),'100%');
 await page.waitForFunction(()=>document.querySelector('#ofertaVideo').readyState>=1);
 assert(Math.abs(await page.locator('#ofertaVideo').evaluate(v=>v.duration)-280.4)<.1);
 await page.locator('#ofertaVideo').evaluate(v=>v.play());
 await page.waitForFunction(()=>document.querySelector('#ofertaVideo').currentTime>.2);
 await page.screenshot({path:path.join(__dirname,'vsl-mobile.png'),fullPage:true});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'mobile overflow');
 await page.locator('#back').click();
 assert(await page.locator('[data-s="7"]').evaluate(e=>e.classList.contains('on')));
 assert(await page.locator('#ofertaVideo').evaluate(v=>v.paused));
 await page.evaluate(()=>window.__quizGo(8));
 assert(await page.locator('[data-s="10"]').evaluate(e=>e.classList.contains('on')));
 await page.locator('#ofertaVideo').evaluate(v=>v.dispatchEvent(new Event('error')));
 assert(await page.locator('#ofertaVideoErro').isVisible());
 await page.locator('#ofertaVideoRetry').click();
 await page.waitForFunction(()=>document.querySelector('#ofertaVideo').readyState>=2);
 await page.setViewportSize({width:1440,height:1000});
 await page.evaluate(()=>scrollTo(0,0));
 await page.screenshot({path:path.join(__dirname,'vsl-desktop.png'),fullPage:true});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 const [request] = await Promise.all([
  page.waitForRequest(r=>r.url().startsWith('https://pay.hotmart.com/')),
  page.locator('#buy').click()
 ]);
 assert.equal(new URL(request.url()).pathname,'/Q107238351O');
 assert.equal(new URL(request.url()).searchParams.get('utm_source'),'qa');
 assert.deepEqual(errors,[]);
 console.log('PASS: lazy media, letter -> VSL, playback, exact duration, back/pause, skipped stages, retry, mobile/desktop, checkout + UTM; no JS errors.');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
