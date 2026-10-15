import {chromium} from 'playwright';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true});
fs.mkdirSync('test-artifacts',{recursive:true});
const errors=[];
for(const [name,width,height] of [['paper-desktop',1440,1000],['paper-mobile',390,844]]){
 const page=await browser.newPage({viewport:{width,height}});
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(process.env.TEST_BASE_URL || 'http://localhost:3000/',{waitUntil:'networkidle'});
 await page.evaluate(()=>document.fonts.ready);
 assert.equal(await page.getByRole('button',{name:'已复原香方',exact:true}).count(),1);
 assert.equal(await page.locator('.vermilion-seal').count(),1);
 assert.match(await page.locator('.research-lab').evaluate(e=>getComputedStyle(e).backgroundImage),/paper-hd/);
 assert.ok(await page.locator('.vermilion-seal').evaluate(e=>e.naturalWidth>=1024));
 await page.screenshot({path:`test-artifacts/${name}-home.png`});
 for(const [hash,title] of [['archive','已复原香方'],['restore','复原'],['library','资料库'],['method','方法']]){
  await page.evaluate(hash=>location.hash=hash,hash);
  await page.getByRole('heading',{name:title,exact:true}).waitFor();
  const folio=page.locator('.material-folio');await folio.scrollIntoViewIfNeeded();
  assert.ok(await folio.locator('img').evaluateAll(imgs=>imgs.every(i=>i.complete&&i.naturalWidth>0)),`${hash}: images load`);
  const caption=page.locator('.material-caption>span').first();const before=await caption.textContent();
  await folio.click();assert.notEqual(await caption.textContent(),before);
  await page.locator('.material-controls button').first().click();assert.equal(await caption.textContent(),before);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${name} ${hash} overflow`);
  if(hash==='archive')assert.equal(await page.locator('.formula-item').count(),91);
  if(hash==='method'){
   assert.equal(await page.locator('.research-table').count(),2);
   assert.match(await page.locator('.research-reading').textContent(),/0.394/);
   await page.locator('.theory-details').first().locator('summary').click();
   assert.ok(await page.locator('.math-line').first().isVisible());
  }
  if(hash==='restore'){await page.getByRole('button',{name:'生成候选香方'}).click();await page.getByRole('heading',{name:'候选香方',exact:true}).waitFor();}
  await page.evaluate(()=>scrollTo(0,0));
  await page.screenshot({path:`test-artifacts/${name}-${hash}.png`,fullPage:hash!=='archive'});
 }
 await page.emulateMedia({reducedMotion:'reduce'});
 assert.equal(await page.locator('.material-print').first().evaluate(e=>getComputedStyle(e).transitionDuration),'0s');
 await page.close();
}
await browser.close();assert.deepEqual(errors,[]);console.log('Paper, seal, renamed navigation, 4 image folios, prediction, 91 records, mobile, reduced motion: passed.');
