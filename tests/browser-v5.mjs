import {chromium} from 'playwright';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true});
fs.mkdirSync('test-artifacts',{recursive:true});
const errors=[];
for(const [name,width,height] of [['desktop',1440,1000],['mobile',390,844],['user-2372',2372,1150]]){
 const page=await browser.newPage({viewport:{width,height},reducedMotion:'reduce'});
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(process.env.TEST_BASE_URL || 'http://localhost:3000/',{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
 await page.screenshot({path:`test-artifacts/${name}.png`,fullPage:true});
 assert.equal(await page.getByRole('heading',{name:'香迹',exact:true}).count(),1);
 await page.getByRole('button',{name:'复原香方',exact:true}).click();
 await page.getByRole('button',{name:'生成候选香方'}).click();
 await page.getByRole('heading',{name:'候选香方',exact:true}).waitFor();
 assert.ok(await page.locator('.composition-row').count()>=3);
 await page.screenshot({path:`test-artifacts/${name}-restore.png`,fullPage:true});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await page.getByRole('button',{name:'已复原香方',exact:true}).click();
 assert.equal(await page.locator('.formula-item').count(),91);
 await page.locator('.formula-summary').first().click();
 await page.screenshot({path:`test-artifacts/${name}-archive.png`,fullPage:true});
 await page.getByRole('button',{name:'方法',exact:true}).click();
 await page.screenshot({path:`test-artifacts/${name}-method.png`,fullPage:true});
 await page.close();
}
await browser.close();assert.deepEqual(errors,[]);console.log('All 3 viewports: navigation, prediction, 91-source archive, no overflow, no runtime errors.');
