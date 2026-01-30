const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto('http://localhost:80/visor.html');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'visor_home_btn.png' });

  await browser.close();
})();
