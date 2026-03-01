#!/usr/bin/env node

/**
 * Automated test script for POS Perfume Frontend
 * Tests the application flow at http://localhost:3000
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const SCREENSHOTS_DIR = path.join(__dirname, 'pos-test-screenshots');

// Create screenshots directory
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function takeScreenshot(page, name, step) {
  const filepath = path.join(SCREENSHOTS_DIR, `${step}-${name}.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`   📸 Screenshot saved: ${filepath}`);
  return filepath;
}

async function testPOSFrontend() {
  console.log('='.repeat(80));
  console.log('POS PERFUME FRONTEND TEST');
  console.log('='.repeat(80));
  
  let browser;
  
  try {
    // Launch browser
    console.log('\n🚀 Launching browser...');
    browser = await puppeteer.launch({
      headless: false, // Set to false to see the browser
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      defaultViewport: { width: 1920, height: 1080 }
    });
    
    const page = await browser.newPage();
    
    // Enable console logging
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error') {
        console.log(`   ❌ Console Error: ${text}`);
      } else if (type === 'warning') {
        console.log(`   ⚠️  Console Warning: ${text}`);
      }
    });
    
    // Enable error logging
    page.on('pageerror', error => {
      console.log(`   ❌ Page Error: ${error.message}`);
    });
    
    // STEP 1: Navigate to the page
    console.log('\n' + '─'.repeat(80));
    console.log('STEP 1: Navigate to http://localhost:3000');
    console.log('─'.repeat(80));
    
    try {
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle0', timeout: 10000 });
      console.log('✅ Page loaded successfully');
      
      const title = await page.title();
      console.log(`   Page Title: ${title}`);
      
      await takeScreenshot(page, 'initial-load', '01');
      
      // Check for loading spinner
      const hasSpinner = await page.$('[class*="spinner"], [class*="loading"]');
      if (hasSpinner) {
        console.log('   🔄 Loading spinner detected');
      }
      
      // Check for errors
      const errorElement = await page.$('[class*="error"], [class*="Error"]');
      if (errorElement) {
        const errorText = await page.evaluate(el => el.textContent, errorElement);
        console.log(`   ⚠️  Error detected: ${errorText}`);
      }
    } catch (err) {
      console.log(`❌ Failed to load page: ${err.message}`);
      throw err;
    }
    
    // STEP 2: Wait for data to load
    console.log('\n' + '─'.repeat(80));
    console.log('STEP 2: Wait 3-5 seconds for setup data to load');
    console.log('─'.repeat(80));
    
    await sleep(5000);
    await takeScreenshot(page, 'after-data-load', '02');
    
    // Check for pricelist
    const pricelistSelect = await page.$('select:has(option)');
    if (pricelistSelect) {
      const options = await page.$$eval('select option', opts => 
        opts.map(opt => opt.textContent)
      );
      console.log('✅ Pricelist dropdown found');
      console.log(`   Options: ${options.join(', ')}`);
    } else {
      console.log('⚠️  Pricelist dropdown not found');
    }
    
    // Check for user/session info
    const pageContent = await page.content();
    console.log('   Checking page content for loaded data...');
    
    // STEP 3: Search for customer
    console.log('\n' + '─'.repeat(80));
    console.log('STEP 3: Search for customer with "a"');
    console.log('─'.repeat(80));
    
    try {
      const customerInput = await page.$('input[placeholder*="customer" i], input[placeholder*="Customer" i], input[placeholder*="Search" i]');
      
      if (customerInput) {
        console.log('✅ Customer search field found');
        await customerInput.click();
        await customerInput.type('a', { delay: 100 });
        console.log('   Typed "a" in search field');
        
        await sleep(1000);
        await takeScreenshot(page, 'customer-search', '03');
        
        // Check for dropdown
        const dropdown = await page.$('[class*="dropdown"], [role="listbox"], [class*="menu"]');
        if (dropdown) {
          console.log('✅ Dropdown appeared');
          const items = await page.$$eval('[role="option"], [class*="item"]', items => 
            items.map(item => item.textContent?.trim()).filter(Boolean).slice(0, 5)
          );
          if (items.length > 0) {
            console.log(`   Customers shown: ${items.join(', ')}`);
          }
        } else {
          console.log('⚠️  No dropdown appeared');
        }
        
        // Clear the search
        await customerInput.click({ clickCount: 3 });
        await page.keyboard.press('Backspace');
      } else {
        console.log('❌ Customer search field not found');
      }
    } catch (err) {
      console.log(`❌ Error in customer search: ${err.message}`);
    }
    
    // STEP 4: Change pricelist
    console.log('\n' + '─'.repeat(80));
    console.log('STEP 4: Try changing the pricelist');
    console.log('─'.repeat(80));
    
    try {
      const pricelistSelects = await page.$$('select');
      if (pricelistSelects.length > 0) {
        const select = pricelistSelects[0];
        const options = await page.evaluate(sel => {
          const opts = Array.from(sel.options);
          return opts.map(opt => ({ value: opt.value, text: opt.text }));
        }, select);
        
        console.log('✅ Pricelist dropdown found');
        console.log(`   Available options: ${options.map(o => o.text).join(', ')}`);
        
        await takeScreenshot(page, 'pricelist-options', '04');
      } else {
        console.log('⚠️  No select elements found');
      }
    } catch (err) {
      console.log(`❌ Error checking pricelist: ${err.message}`);
    }
    
    // STEP 5: Click "New" button
    console.log('\n' + '─'.repeat(80));
    console.log('STEP 5: Click "New" button to create order');
    console.log('─'.repeat(80));
    
    try {
      const newButton = await page.$('button:has-text("New"), button:has-text("new"), button:has-text("NEW")');
      
      if (!newButton) {
        // Try alternative selectors
        const buttons = await page.$$('button');
        let foundNew = false;
        for (const btn of buttons) {
          const text = await page.evaluate(b => b.textContent, btn);
          if (text && text.toLowerCase().includes('new')) {
            console.log(`✅ Found "New" button with text: ${text}`);
            await btn.click();
            foundNew = true;
            break;
          }
        }
        
        if (!foundNew) {
          console.log('⚠️  "New" button not found');
        }
      } else {
        await newButton.click();
        console.log('✅ Clicked "New" button');
      }
      
      await sleep(1000);
      await takeScreenshot(page, 'after-new-order', '05');
      
      // Check for order number
      const orderInput = await page.$('input[value*="Order"], input[value*="order"], input[placeholder*="Order"]');
      if (orderInput) {
        const orderValue = await page.evaluate(input => input.value, orderInput);
        console.log(`   Order created: ${orderValue}`);
      }
    } catch (err) {
      console.log(`❌ Error clicking New button: ${err.message}`);
    }
    
    // STEP 6: Open product search modal
    console.log('\n' + '─'.repeat(80));
    console.log('STEP 6: Try to open product search modal');
    console.log('─'.repeat(80));
    
    try {
      // Try clicking in the table/rows area
      const table = await page.$('table, [class*="table"], [class*="grid"]');
      if (table) {
        await table.click();
        console.log('   Clicked in table area');
      }
      
      await sleep(500);
      
      // Check for modal
      const modal = await page.$('[role="dialog"], [class*="modal"], [class*="Modal"]');
      if (modal) {
        console.log('✅ Modal opened');
        await takeScreenshot(page, 'modal-opened', '06');
      } else {
        console.log('⚠️  Modal did not open, trying alternative approach...');
        
        // Try clicking a search button or icon
        const searchButton = await page.$('button:has-text("Search"), button[title*="search" i], button svg[class*="search"]');
        if (searchButton) {
          await searchButton.click();
          console.log('   Clicked search button');
          await sleep(500);
          await takeScreenshot(page, 'modal-attempt', '06');
        }
      }
    } catch (err) {
      console.log(`❌ Error opening modal: ${err.message}`);
    }
    
    // STEP 7: Search for product
    console.log('\n' + '─'.repeat(80));
    console.log('STEP 7: Search for "test" in product search');
    console.log('─'.repeat(80));
    
    try {
      // Find search input in modal or page
      const searchInputs = await page.$$('input[type="text"], input[type="search"]');
      
      let productSearchInput = null;
      for (const input of searchInputs) {
        const placeholder = await page.evaluate(i => i.placeholder, input);
        if (placeholder && (placeholder.toLowerCase().includes('product') || placeholder.toLowerCase().includes('search'))) {
          productSearchInput = input;
          break;
        }
      }
      
      if (productSearchInput) {
        await productSearchInput.click();
        await productSearchInput.type('test', { delay: 100 });
        console.log('   Typed "test" in search field');
        
        await sleep(2000);
        await takeScreenshot(page, 'product-search', '07');
        
        // Check for products
        const productItems = await page.$$('[class*="product"], [role="listitem"], tr');
        if (productItems.length > 0) {
          console.log(`✅ Found ${productItems.length} potential product items`);
          
          const productTexts = [];
          for (let i = 0; i < Math.min(5, productItems.length); i++) {
            const text = await page.evaluate(el => el.textContent?.trim().substring(0, 100), productItems[i]);
            if (text) productTexts.push(text);
          }
          console.log(`   Products: ${productTexts.join(' | ')}`);
        } else {
          console.log('⚠️  No products found');
        }
      } else {
        console.log('⚠️  Product search input not found');
      }
    } catch (err) {
      console.log(`❌ Error searching products: ${err.message}`);
    }
    
    // STEP 8: Add product to order
    console.log('\n' + '─'.repeat(80));
    console.log('STEP 8: Click on a product to add to order');
    console.log('─'.repeat(80));
    
    try {
      const productItems = await page.$$('[class*="product"], [role="listitem"], tr');
      if (productItems.length > 0) {
        await productItems[0].click();
        console.log('✅ Clicked on first product');
        
        await sleep(1000);
        await takeScreenshot(page, 'after-product-add', '08');
        
        // Check for order lines
        const orderLines = await page.$$('table tbody tr, [class*="order-line"]');
        console.log(`   Order lines count: ${orderLines.length}`);
        
        if (orderLines.length > 0) {
          console.log('✅ Product added to order');
        } else {
          console.log('⚠️  No order lines detected');
        }
      } else {
        console.log('⚠️  No products to click');
      }
    } catch (err) {
      console.log(`❌ Error adding product: ${err.message}`);
    }
    
    // STEP 9: Final screenshot
    console.log('\n' + '─'.repeat(80));
    console.log('STEP 9: Take final screenshot of POS interface');
    console.log('─'.repeat(80));
    
    await takeScreenshot(page, 'final-pos-interface', '09');
    console.log('✅ Final screenshot captured');
    
    console.log('\n' + '='.repeat(80));
    console.log('TEST COMPLETED');
    console.log('='.repeat(80));
    console.log(`\n📁 Screenshots saved to: ${SCREENSHOTS_DIR}`);
    console.log('\nPlease review the screenshots to see the actual state of the application.');
    
  } catch (error) {
    console.error('\n❌ Fatal error during testing:', error.message);
    console.error(error.stack);
  } finally {
    if (browser) {
      await sleep(2000); // Keep browser open for a moment
      await browser.close();
      console.log('\n🔚 Browser closed');
    }
  }
}

// Run the test
testPOSFrontend().catch(console.error);
