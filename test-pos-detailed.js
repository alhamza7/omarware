#!/usr/bin/env node

/**
 * Detailed POS Frontend Test with Precise Timing
 * This script follows the exact steps requested with careful waits and screenshots
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const SCREENSHOTS_DIR = path.join(__dirname, 'pos-detailed-test');

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function takeScreenshot(page, name, step) {
  const filepath = path.join(SCREENSHOTS_DIR, `${step}-${name}.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`   📸 Screenshot: ${filepath}`);
  return filepath;
}

async function detailedPOSTest() {
  console.log('='.repeat(80));
  console.log('DETAILED POS FRONTEND TEST - EXACT STEPS');
  console.log('='.repeat(80));
  
  let browser;
  
  try {
    console.log('\n🚀 Launching browser...');
    browser = await puppeteer.launch({
      headless: false,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      defaultViewport: { width: 1920, height: 1080 },
      slowMo: 100 // Slow down actions for visibility
    });
    
    const page = await browser.newPage();
    
    // Console and error logging
    page.on('console', msg => {
      const type = msg.type();
      if (type === 'error') console.log(`   ❌ Console: ${msg.text()}`);
      else if (type === 'warning') console.log(`   ⚠️  Console: ${msg.text()}`);
    });
    
    page.on('pageerror', err => console.log(`   ❌ Page Error: ${err.message}`));
    
    // ========================================================================
    // STEP 1: Initial screenshot
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 1: Navigate and take initial screenshot');
    console.log('═'.repeat(80));
    
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
    console.log('✅ Page loaded');
    
    await sleep(2000);
    await takeScreenshot(page, 'initial-state', 'step1');
    
    const title = await page.title();
    console.log(`   Page title: ${title}`);
    
    // ========================================================================
    // STEP 2: Customer search with "ad"
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 2: Customer search - type "ad" slowly');
    console.log('═'.repeat(80));
    
    // Find customer input by placeholder
    const customerInput = await page.$('input[placeholder*="customer" i]');
    
    if (customerInput) {
      console.log('✅ Found customer search input');
      
      // Click to focus
      await customerInput.click();
      console.log('   Clicked on customer input');
      await sleep(500);
      
      // Type "a" and wait
      await page.keyboard.type('a');
      console.log('   Typed "a"');
      await sleep(1000);
      
      // Type "d" and wait
      await page.keyboard.type('d');
      console.log('   Typed "d" (full text: "ad")');
      await sleep(2000);
      
      await takeScreenshot(page, 'after-customer-search', 'step2');
      
      // Check for dropdown
      const dropdownSelectors = [
        '[role="listbox"]',
        '[class*="dropdown"]',
        '[class*="autocomplete"]',
        '[class*="suggestions"]',
        '[class*="menu"]',
        'ul[class*="list"]',
        '.suggestion-list',
        '[data-radix-popper-content-wrapper]'
      ];
      
      let dropdownFound = false;
      for (const selector of dropdownSelectors) {
        const dropdown = await page.$(selector);
        if (dropdown) {
          const isVisible = await page.evaluate(el => {
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          }, dropdown);
          
          if (isVisible) {
            console.log(`✅ Dropdown found with selector: ${selector}`);
            dropdownFound = true;
            
            // Try to get dropdown items
            const items = await page.$$eval(
              `${selector} [role="option"], ${selector} li, ${selector} div[class*="item"]`,
              elements => elements.map(el => el.textContent?.trim()).filter(Boolean).slice(0, 5)
            );
            
            if (items.length > 0) {
              console.log(`   Customer options: ${items.join(', ')}`);
            } else {
              console.log('   Dropdown is visible but no items found');
            }
            break;
          }
        }
      }
      
      if (!dropdownFound) {
        console.log('❌ No dropdown appeared after typing "ad"');
        console.log('   Possible reasons:');
        console.log('   - No customers matching "ad"');
        console.log('   - Minimum character requirement not met');
        console.log('   - API not responding');
      }
      
      // Clear the input for next tests
      await customerInput.click({ clickCount: 3 });
      await page.keyboard.press('Backspace');
      await sleep(500);
      
    } else {
      console.log('❌ Customer search input not found');
    }
    
    // ========================================================================
    // STEP 3: Click "New" button
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 3: Click green "New" button');
    console.log('═'.repeat(80));
    
    // Multiple strategies to find the New button
    let newButtonClicked = false;
    
    // Strategy 1: Look for green button with "New" text
    const buttons = await page.$$('button');
    for (const btn of buttons) {
      const text = await page.evaluate(el => el.textContent?.trim(), btn);
      const bgColor = await page.evaluate(el => 
        window.getComputedStyle(el).backgroundColor, btn
      );
      
      if (text && text.toLowerCase() === 'new') {
        console.log(`✅ Found "New" button with text: "${text}"`);
        await btn.click();
        newButtonClicked = true;
        console.log('   Clicked "New" button');
        break;
      }
    }
    
    if (!newButtonClicked) {
      console.log('❌ Could not find "New" button, trying alternative selectors...');
      const altSelectors = [
        'button:has-text("New")',
        'button[class*="green"]',
        'button:nth-last-of-type(1)', // Last button
      ];
      
      for (const selector of altSelectors) {
        try {
          await page.click(selector);
          console.log(`✅ Clicked button with selector: ${selector}`);
          newButtonClicked = true;
          break;
        } catch (e) {
          // Continue to next selector
        }
      }
    }
    
    await sleep(3000);
    await takeScreenshot(page, 'after-new-button', 'step3');
    
    // Check for order number
    const orderInputs = await page.$$('input[value*="Order" i], input[placeholder*="Order" i]');
    if (orderInputs.length > 0) {
      const orderValue = await page.evaluate(el => el.value, orderInputs[0]);
      console.log(`✅ Order field value: "${orderValue}"`);
    } else {
      console.log('⚠️  No order number field found');
    }
    
    // Check if interface changed
    const currentScreenText = await page.evaluate(() => document.body.innerText);
    console.log(`   Interface state: ${currentScreenText.includes('New Order') ? 'Changed' : 'No visible change'}`);
    
    // ========================================================================
    // STEP 4: Click on "Click to search product..." row
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 4: Click on order row to open product search');
    console.log('═'.repeat(80));
    
    // Find rows with "Click to search product..."
    const productRows = await page.$$('td, div');
    let clickedRow = false;
    
    for (const row of productRows) {
      const text = await page.evaluate(el => el.textContent?.trim(), row);
      if (text && text.includes('Click to search product')) {
        console.log(`✅ Found product row with text: "${text}"`);
        await row.click();
        clickedRow = true;
        console.log('   Clicked on product row');
        break;
      }
    }
    
    if (!clickedRow) {
      console.log('⚠️  Could not find "Click to search product" text, clicking first table row...');
      const firstRow = await page.$('tbody tr');
      if (firstRow) {
        await firstRow.click();
        console.log('   Clicked first table row');
      }
    }
    
    await sleep(1000);
    await takeScreenshot(page, 'after-row-click', 'step4');
    
    // Check if modal opened
    const modalSelectors = [
      '[role="dialog"]',
      '[class*="modal" i]',
      '[class*="Modal" i]',
      'div[class*="fixed"][class*="inset"]',
      '[data-radix-dialog-content]'
    ];
    
    let modalFound = false;
    let modalElement = null;
    
    for (const selector of modalSelectors) {
      modalElement = await page.$(selector);
      if (modalElement) {
        const isVisible = await page.evaluate(el => {
          const rect = el.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0;
        }, modalElement);
        
        if (isVisible) {
          console.log(`✅ Product Search modal opened (selector: ${selector})`);
          modalFound = true;
          
          // Get modal title
          const modalTitle = await page.evaluate(() => {
            const titleEl = document.querySelector('h2, h3, [class*="title"]');
            return titleEl ? titleEl.textContent : 'No title found';
          });
          console.log(`   Modal title: ${modalTitle}`);
          break;
        }
      }
    }
    
    if (!modalFound) {
      console.log('❌ Product Search modal did not open');
    }
    
    // ========================================================================
    // STEP 5: Search for "test" in product modal
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 5: Type "test" in product search modal');
    console.log('═'.repeat(80));
    
    if (modalFound) {
      // Find search input in modal
      const searchInput = await page.$('input[type="text"]:not([placeholder*="customer" i]), input[type="search"]');
      
      if (searchInput) {
        console.log('✅ Found search input in modal');
        await searchInput.click();
        await sleep(300);
        
        // Clear any existing text
        await page.keyboard.down('Control');
        await page.keyboard.press('A');
        await page.keyboard.up('Control');
        await page.keyboard.press('Backspace');
        await sleep(300);
        
        // Type "test" character by character
        const chars = ['t', 'e', 's', 't'];
        for (const char of chars) {
          await page.keyboard.type(char);
          console.log(`   Typed "${char}"`);
          await sleep(500);
        }
        
        console.log('   Full search term: "test"');
        await sleep(2000);
        
        await takeScreenshot(page, 'after-product-search', 'step5');
        
        // Check for products in table
        const productRows = await page.$$('table tbody tr, [class*="product-row"], [class*="result"]');
        console.log(`   Found ${productRows.length} potential product rows`);
        
        if (productRows.length > 0) {
          console.log('✅ Products found!');
          
          // Get first few product details
          const products = [];
          for (let i = 0; i < Math.min(5, productRows.length); i++) {
            const rowText = await page.evaluate(el => el.textContent?.trim(), productRows[i]);
            if (rowText && rowText.length > 10) {
              products.push(rowText.substring(0, 100));
            }
          }
          
          if (products.length > 0) {
            console.log('   Product details:');
            products.forEach((p, i) => console.log(`   ${i + 1}. ${p}`));
          }
        } else {
          console.log('❌ No products found for "test"');
          
          // Check for "no results" message
          const noResultsMsg = await page.evaluate(() => {
            const body = document.body.innerText;
            if (body.includes('No products') || body.includes('not found') || body.includes('0 results')) {
              return 'No results message displayed';
            }
            return null;
          });
          
          if (noResultsMsg) {
            console.log(`   ${noResultsMsg}`);
          }
        }
        
      } else {
        console.log('❌ Search input not found in modal');
      }
      
      // ========================================================================
      // STEP 6: Click on first product
      // ========================================================================
      console.log('\n' + '═'.repeat(80));
      console.log('STEP 6: Click first product to add to order');
      console.log('═'.repeat(80));
      
      const productRows = await page.$$('table tbody tr');
      
      if (productRows.length > 0) {
        const firstRow = productRows[0];
        const rowText = await page.evaluate(el => el.textContent?.trim(), firstRow);
        console.log(`   Clicking on: ${rowText?.substring(0, 80)}`);
        
        await firstRow.click();
        console.log('✅ Clicked first product row');
        
        await sleep(2000);
        await takeScreenshot(page, 'after-product-add', 'step6');
        
        // Check if product was added to order
        const orderTable = await page.$('table');
        if (orderTable) {
          const orderRows = await page.$$eval('table tbody tr', rows => {
            return rows.map(row => {
              const cells = Array.from(row.querySelectorAll('td'));
              return cells.map(cell => cell.textContent?.trim()).join(' | ');
            }).filter(text => text && !text.includes('Click to search product'));
          });
          
          if (orderRows.length > 0) {
            console.log('✅ Product added to order!');
            console.log('   Order lines:');
            orderRows.forEach((line, i) => {
              console.log(`   ${i + 1}. ${line.substring(0, 100)}`);
            });
          } else {
            console.log('⚠️  No products in order lines table (still showing "Click to search product...")');
          }
        }
        
        // Check if modal closed
        const modalStillOpen = await page.$('[role="dialog"]');
        if (modalStillOpen) {
          const visible = await page.evaluate(el => {
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          }, modalStillOpen);
          
          if (visible) {
            console.log('   Modal is still open');
          } else {
            console.log('   Modal closed');
          }
        } else {
          console.log('   Modal closed');
        }
        
      } else {
        console.log('❌ No products to click - search returned no results');
      }
      
    } else {
      console.log('⚠️  Skipping steps 5 & 6 - modal was not opened');
    }
    
    // ========================================================================
    // Final screenshot
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('FINAL: Complete interface screenshot');
    console.log('═'.repeat(80));
    
    await takeScreenshot(page, 'final-state', 'step7-final');
    
    console.log('\n' + '='.repeat(80));
    console.log('✅ DETAILED TEST COMPLETED');
    console.log('='.repeat(80));
    console.log(`\n📁 Screenshots saved to: ${SCREENSHOTS_DIR}`);
    console.log('\nPlease review the screenshots for exact visual confirmation.');
    
    // Keep browser open for a moment
    await sleep(3000);
    
  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    console.error(error.stack);
  } finally {
    if (browser) {
      await browser.close();
      console.log('\n🔚 Browser closed');
    }
  }
}

// Run the test
detailedPOSTest().catch(console.error);
