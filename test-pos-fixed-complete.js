#!/usr/bin/env node

/**
 * Complete POS Test - AFTER FIXES with Hard Reload
 * Tests the full workflow: customer selection → order creation → product add
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const SCREENSHOTS_DIR = path.join(__dirname, 'pos-fixed-test');

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function takeScreenshot(page, name, step) {
  const filepath = path.join(SCREENSHOTS_DIR, `${step}-${name}.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`   📸 Screenshot: ${name}`);
  return filepath;
}

async function testFixedPOS() {
  console.log('='.repeat(80));
  console.log('TESTING FIXED POS - COMPLETE WORKFLOW');
  console.log('='.repeat(80));
  
  let browser;
  
  try {
    console.log('\n🚀 Launching browser with cache disabled...');
    browser = await puppeteer.launch({
      headless: false,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-cache',
        '--disable-application-cache',
        '--disable-offline-load-stale-cache',
        '--disk-cache-size=0'
      ],
      defaultViewport: { width: 1920, height: 1080 },
      slowMo: 50
    });
    
    const page = await browser.newPage();
    
    // Disable cache at page level
    await page.setCacheEnabled(false);
    
    // Console logging
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error') console.log(`   ❌ Console Error: ${text}`);
      else if (type === 'warning') console.log(`   ⚠️  Warning: ${text}`);
      else if (text.includes('[POS') || text.includes('API')) {
        console.log(`   ℹ️  ${text}`);
      }
    });
    
    page.on('pageerror', err => console.log(`   ❌ Page Error: ${err.message}`));
    
    // Navigate with hard reload
    console.log('\n📂 Navigating to http://localhost:3000 with hard reload...');
    await page.goto('http://localhost:3000', {
      waitUntil: 'networkidle0',
      timeout: 15000
    });
    
    // Additional hard reload simulation
    await page.evaluate(() => {
      window.location.reload(true);
    });
    await page.waitForNavigation({ waitUntil: 'networkidle0' });
    
    console.log('✅ Page loaded with cache cleared');
    await sleep(2000);
    
    // ========================================================================
    // STEP 1: Check "New Order" button state
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 1: Check "+ New Order" button initial state');
    console.log('═'.repeat(80));
    
    await takeScreenshot(page, 'initial-state-new-button-check', 'step1');
    
    // Find New Order button
    const newOrderButtons = await page.$$('button');
    let newOrderButton = null;
    let buttonText = '';
    
    for (const btn of newOrderButtons) {
      const text = await page.evaluate(el => el.textContent?.trim(), btn);
      if (text && (text.includes('New Order') || text.includes('New'))) {
        newOrderButton = btn;
        buttonText = text;
        break;
      }
    }
    
    if (newOrderButton) {
      console.log(`✅ Found button with text: "${buttonText}"`);
      
      // Check if disabled
      const isDisabled = await page.evaluate(el => {
        return el.disabled || el.classList.contains('disabled') || 
               el.getAttribute('aria-disabled') === 'true' ||
               window.getComputedStyle(el).pointerEvents === 'none';
      }, newOrderButton);
      
      const bgColor = await page.evaluate(el => window.getComputedStyle(el).backgroundColor, newOrderButton);
      const opacity = await page.evaluate(el => window.getComputedStyle(el).opacity, newOrderButton);
      
      console.log(`   Button state: ${isDisabled ? '❌ DISABLED' : '✅ ENABLED'}`);
      console.log(`   Background color: ${bgColor}`);
      console.log(`   Opacity: ${opacity}`);
      
      if (isDisabled || parseFloat(opacity) < 0.8) {
        console.log('✅ GOOD: Button is properly disabled (no customer selected)');
      } else {
        console.log('⚠️  Button appears enabled (might be a bug if no customer selected)');
      }
    } else {
      console.log('❌ New Order button not found');
    }
    
    // Check for warning message
    const warningText = await page.evaluate(() => {
      const body = document.body.innerText;
      if (body.includes('Select a customer') || body.includes('customer first')) {
        return 'Warning message found';
      }
      return null;
    });
    
    if (warningText) {
      console.log(`✅ ${warningText}`);
    }
    
    // ========================================================================
    // STEP 2: Search for customer "test"
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 2: Search for customer with "test"');
    console.log('═'.repeat(80));
    
    const customerInput = await page.$('input[placeholder*="customer" i]');
    
    if (customerInput) {
      console.log('✅ Customer search input found');
      
      await customerInput.click();
      await sleep(300);
      
      // Clear any existing text
      await page.keyboard.down('Control');
      await page.keyboard.press('A');
      await page.keyboard.up('Control');
      await page.keyboard.press('Backspace');
      await sleep(300);
      
      // Type "test" slowly
      const chars = ['t', 'e', 's', 't'];
      for (const char of chars) {
        await page.keyboard.type(char);
        console.log(`   Typed: "${char}"`);
        await sleep(400);
      }
      
      console.log('   Complete search term: "test"');
      await sleep(1500);
      
      await takeScreenshot(page, 'after-customer-search', 'step2');
      
      // Check for dropdown with specific selectors
      const dropdownVisible = await page.evaluate(() => {
        const selectors = [
          '[role="listbox"]',
          '[class*="dropdown"]',
          '[class*="popover"]',
          'ul[class*="list"]',
          '[data-radix-popper-content-wrapper]'
        ];
        
        for (const selector of selectors) {
          const element = document.querySelector(selector);
          if (element) {
            const rect = element.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
              const items = element.querySelectorAll('[role="option"], li, div[class*="item"]');
              return {
                found: true,
                selector: selector,
                itemCount: items.length,
                items: Array.from(items).slice(0, 5).map(el => el.textContent?.trim())
              };
            }
          }
        }
        return { found: false };
      });
      
      if (dropdownVisible.found) {
        console.log(`✅ Dropdown appeared (${dropdownVisible.selector})`);
        console.log(`   Items found: ${dropdownVisible.itemCount}`);
        if (dropdownVisible.items && dropdownVisible.items.length > 0) {
          console.log('   Customer options:');
          dropdownVisible.items.forEach((item, i) => {
            console.log(`     ${i + 1}. ${item}`);
          });
          
          // Check if "API Test Customer" is in the list
          const hasTestCustomer = dropdownVisible.items.some(item => 
            item && item.includes('API Test Customer')
          );
          if (hasTestCustomer) {
            console.log('   ✅ "API Test Customer" found in dropdown!');
          }
        }
      } else {
        console.log('❌ No dropdown appeared');
      }
      
    } else {
      console.log('❌ Customer search input not found');
    }
    
    // ========================================================================
    // STEP 3: Select a customer
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 3: Select customer from dropdown');
    console.log('═'.repeat(80));
    
    // Try to click on first customer option
    const customerOptions = await page.$$('[role="option"], ul li, [class*="dropdown"] div[class*="item"]');
    
    if (customerOptions.length > 0) {
      const firstOption = customerOptions[0];
      const optionText = await page.evaluate(el => el.textContent?.trim(), firstOption);
      console.log(`   Clicking on: "${optionText}"`);
      
      await firstOption.click();
      console.log('✅ Clicked on customer option');
      await sleep(1000);
      
      await takeScreenshot(page, 'after-customer-selection', 'step3');
      
      // Check if customer name appears
      const selectedCustomerText = await page.evaluate(() => {
        const input = document.querySelector('input[placeholder*="customer" i]');
        return input ? input.value : '';
      });
      
      if (selectedCustomerText && selectedCustomerText.length > 0) {
        console.log(`✅ Customer selected: "${selectedCustomerText}"`);
      } else {
        console.log('⚠️  Customer input is empty');
      }
      
      // Check for green badge
      const badges = await page.$$('[class*="badge"], [class*="chip"], [class*="tag"]');
      let foundCustomerBadge = false;
      for (const badge of badges) {
        const badgeText = await page.evaluate(el => el.textContent?.trim(), badge);
        const badgeColor = await page.evaluate(el => 
          window.getComputedStyle(el).backgroundColor, badge
        );
        
        if (badgeText && (badgeText.includes('Test') || badgeText.includes('Customer'))) {
          console.log(`✅ Badge found: "${badgeText}" (color: ${badgeColor})`);
          foundCustomerBadge = true;
          break;
        }
      }
      
      if (!foundCustomerBadge) {
        console.log('⚠️  No customer badge visible');
      }
      
      // Check if New Order button is now enabled
      if (newOrderButton) {
        const nowEnabled = await page.evaluate(el => {
          return !(el.disabled || el.classList.contains('disabled') || 
                   el.getAttribute('aria-disabled') === 'true' ||
                   window.getComputedStyle(el).pointerEvents === 'none');
        }, newOrderButton);
        
        const opacity = await page.evaluate(el => window.getComputedStyle(el).opacity, newOrderButton);
        
        console.log(`   New Order button now: ${nowEnabled && parseFloat(opacity) >= 0.8 ? '✅ ENABLED (green & clickable)' : '❌ Still disabled'}`);
      }
      
    } else {
      console.log('❌ No customer options found to click');
    }
    
    // ========================================================================
    // STEP 4: Create new order
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 4: Click "+ New Order" button');
    console.log('═'.repeat(80));
    
    if (newOrderButton) {
      try {
        await newOrderButton.click();
        console.log('✅ Clicked "+ New Order" button');
        await sleep(3000);
        
        await takeScreenshot(page, 'after-new-order-creation', 'step4');
        
        // Check for order number
        const orderNumberInput = await page.$('input[placeholder*="Order" i], input[name*="order" i]');
        if (orderNumberInput) {
          const orderValue = await page.evaluate(el => el.value, orderNumberInput);
          if (orderValue && orderValue.length > 0) {
            console.log(`✅ Order created: "${orderValue}"`);
          } else {
            console.log('⚠️  Order input exists but is empty');
          }
        } else {
          console.log('⚠️  Order number field not found');
        }
        
        // Check for state badge (draft, etc.)
        const allBadges = await page.$$('[class*="badge"]');
        for (const badge of allBadges) {
          const text = await page.evaluate(el => el.textContent?.trim().toLowerCase(), badge);
          if (text && (text.includes('draft') || text.includes('sale') || text.includes('done'))) {
            console.log(`✅ Order state badge: "${text}"`);
            break;
          }
        }
        
        // Check if interface shows active order
        const hasActiveOrder = await page.evaluate(() => {
          const body = document.body.innerText;
          return body.includes('POS/') || body.includes('SO/') || body.includes('Order #');
        });
        
        console.log(`   Active order interface: ${hasActiveOrder ? '✅ YES' : '⚠️  No indication'}`);
        
      } catch (err) {
        console.log(`❌ Error clicking New Order button: ${err.message}`);
      }
    } else {
      console.log('⚠️  Cannot proceed - New Order button reference lost');
    }
    
    // ========================================================================
    // STEP 5: Open product search modal
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 5: Click on order row to open product search');
    console.log('═'.repeat(80));
    
    // Find rows with "Click to search product"
    const allCells = await page.$$('td, div');
    let clickedProductRow = false;
    
    for (const cell of allCells) {
      const cellText = await page.evaluate(el => el.textContent?.trim(), cell);
      if (cellText && cellText.includes('Click to search product')) {
        console.log('✅ Found product search row');
        await cell.click();
        console.log('   Clicked on row');
        clickedProductRow = true;
        break;
      }
    }
    
    if (!clickedProductRow) {
      // Try clicking first row of table
      const firstRow = await page.$('tbody tr');
      if (firstRow) {
        await firstRow.click();
        console.log('   Clicked first table row');
      }
    }
    
    await sleep(1000);
    await takeScreenshot(page, 'after-row-click-modal-check', 'step5');
    
    // Check if modal opened
    const modalInfo = await page.evaluate(() => {
      const selectors = [
        '[role="dialog"]',
        '[class*="modal" i]',
        '[class*="Modal" i]',
        '[data-radix-dialog-content]'
      ];
      
      for (const selector of selectors) {
        const modal = document.querySelector(selector);
        if (modal) {
          const rect = modal.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            const title = modal.querySelector('h2, h3, [class*="title"]');
            return {
              opened: true,
              selector: selector,
              title: title ? title.textContent?.trim() : 'No title'
            };
          }
        }
      }
      return { opened: false };
    });
    
    if (modalInfo.opened) {
      console.log(`✅ Product Search modal OPENED`);
      console.log(`   Title: "${modalInfo.title}"`);
    } else {
      console.log('❌ Product Search modal DID NOT OPEN');
    }
    
    // ========================================================================
    // STEP 6: Search for product "test"
    // ========================================================================
    console.log('\n' + '═'.repeat(80));
    console.log('STEP 6: Search for product with "test"');
    console.log('═'.repeat(80));
    
    if (modalInfo.opened) {
      // Find search input in modal (not the customer search)
      const allInputs = await page.$$('input[type="text"], input[type="search"]');
      let productSearchInput = null;
      
      // Get the second input (first is customer, second should be product in modal)
      if (allInputs.length >= 2) {
        productSearchInput = allInputs[1];
      } else if (allInputs.length === 1) {
        productSearchInput = allInputs[0];
      }
      
      if (productSearchInput) {
        console.log('✅ Product search input found');
        
        await productSearchInput.click();
        await sleep(300);
        
        // Clear field
        await page.keyboard.down('Control');
        await page.keyboard.press('A');
        await page.keyboard.up('Control');
        await page.keyboard.press('Backspace');
        await sleep(300);
        
        // Type "test" slowly
        const chars = ['t', 'e', 's', 't'];
        for (const char of chars) {
          await page.keyboard.type(char);
          console.log(`   Typed: "${char}"`);
          await sleep(400);
        }
        
        console.log('   Complete search: "test"');
        await sleep(2000);
        
        await takeScreenshot(page, 'after-product-search', 'step6');
        
        // Check for products in results
        const productResults = await page.evaluate(() => {
          const rows = document.querySelectorAll('table tbody tr, [class*="product-row"]');
          const products = [];
          
          rows.forEach(row => {
            const text = row.textContent?.trim();
            if (text && text.length > 5 && 
                !text.includes('Click to search') && 
                !text.includes('No products')) {
              products.push(text.substring(0, 150));
            }
          });
          
          return products;
        });
        
        if (productResults.length > 0) {
          console.log(`✅ Found ${productResults.length} product(s):`);
          productResults.forEach((prod, i) => {
            console.log(`   ${i + 1}. ${prod}`);
            if (prod.includes('TEST BOTTLE')) {
              console.log('      ⭐ Contains "TEST BOTTLE"!');
            }
          });
        } else {
          console.log('❌ No products found');
          
          // Check for no results message
          const noResults = await page.evaluate(() => {
            return document.body.innerText.includes('No products');
          });
          if (noResults) {
            console.log('   Message: "No products found"');
          }
        }
        
        // ========================================================================
        // STEP 7: Add product to order
        // ========================================================================
        console.log('\n' + '═'.repeat(80));
        console.log('STEP 7: Click on product to add to order');
        console.log('═'.repeat(80));
        
        if (productResults.length > 0) {
          const productRows = await page.$$('table tbody tr');
          
          // Find row with "TEST BOTTLE" or just use first row
          let targetRow = productRows[0];
          for (const row of productRows) {
            const text = await page.evaluate(el => el.textContent?.trim(), row);
            if (text && text.includes('TEST BOTTLE')) {
              targetRow = row;
              console.log('   Found "TEST BOTTLE" row');
              break;
            }
          }
          
          if (targetRow) {
            const rowText = await page.evaluate(el => el.textContent?.trim().substring(0, 80), targetRow);
            console.log(`   Clicking: ${rowText}`);
            
            await targetRow.click();
            console.log('✅ Clicked on product');
            await sleep(3000);
            
            await takeScreenshot(page, 'after-product-added', 'step7');
            
            // Check if product appears in order lines
            const orderLines = await page.evaluate(() => {
              const rows = document.querySelectorAll('tbody tr');
              const lines = [];
              
              rows.forEach(row => {
                const text = row.textContent?.trim();
                if (text && !text.includes('Click to search product')) {
                  const cells = Array.from(row.querySelectorAll('td'));
                  if (cells.length > 3) {
                    const productName = cells[1]?.textContent?.trim();
                    const qty = cells[2]?.textContent?.trim();
                    const price = cells[cells.length - 1]?.textContent?.trim();
                    if (productName && productName.length > 2) {
                      lines.push({ productName, qty, price });
                    }
                  }
                }
              });
              
              return lines;
            });
            
            if (orderLines.length > 0) {
              console.log(`✅ Product(s) in order lines: ${orderLines.length}`);
              orderLines.forEach((line, i) => {
                console.log(`   ${i + 1}. ${line.productName} | Qty: ${line.qty} | Price: ${line.price}`);
              });
            } else {
              console.log('⚠️  No products in order lines table');
            }
            
            // Check order summary/totals
            const totals = await page.evaluate(() => {
              const body = document.body.innerText;
              const subtotalMatch = body.match(/Subtotal:?\s*\$?([\d,]+\.?\d*)/i);
              const taxMatch = body.match(/Tax:?\s*\$?([\d,]+\.?\d*)/i);
              const grandTotalMatch = body.match(/Grand Total:?\s*\$?([\d,]+\.?\d*)/i);
              
              return {
                subtotal: subtotalMatch ? subtotalMatch[1] : '0.00',
                tax: taxMatch ? taxMatch[1] : '0.00',
                grandTotal: grandTotalMatch ? grandTotalMatch[1] : '0.00'
              };
            });
            
            console.log('\n   📊 Order Summary:');
            console.log(`      Subtotal: $${totals.subtotal}`);
            console.log(`      Tax: $${totals.tax}`);
            console.log(`      Grand Total: $${totals.grandTotal}`);
            
            if (parseFloat(totals.grandTotal.replace(/,/g, '')) > 0) {
              console.log('      ✅ Order has value (product was added successfully)');
            } else {
              console.log('      ⚠️  Grand total is $0.00');
            }
            
          }
        } else {
          console.log('⚠️  Skipping - no products found to add');
        }
        
      } else {
        console.log('❌ Product search input not found in modal');
      }
      
    } else {
      console.log('⚠️  Skipping steps 6 & 7 - modal did not open');
    }
    
    // ========================================================================
    // FINAL SUMMARY
    // ========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('✅ TEST COMPLETE - FINAL SUMMARY');
    console.log('='.repeat(80));
    
    await takeScreenshot(page, 'final-complete-state', 'step8-final');
    
    console.log(`\n📁 All screenshots saved to: ${SCREENSHOTS_DIR}`);
    console.log('\nTest execution completed successfully!');
    
    await sleep(2000);
    
  } catch (error) {
    console.error('\n❌ Fatal error during test:', error.message);
    console.error(error.stack);
  } finally {
    if (browser) {
      await browser.close();
      console.log('\n🔚 Browser closed');
    }
  }
}

// Run the test
testFixedPOS().catch(console.error);
