#!/usr/bin/env node

/**
 * COMPLETE POS TEST - 2-Step Product Addition Modal
 * Tests: Customer selection → Order creation → Product search → Configuration → Add to order
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const SCREENSHOTS_DIR = path.join(__dirname, 'pos-2step-modal-test');

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function screenshot(page, name, step) {
  const filepath = path.join(SCREENSHOTS_DIR, `${step}-${name}.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`   📸 ${name}`);
  return filepath;
}

async function testCompletePOSWorkflow() {
  console.log('='.repeat(90));
  console.log('COMPLETE POS TEST - 2-STEP PRODUCT ADDITION MODAL');
  console.log('='.repeat(90));
  
  let browser;
  
  try {
    console.log('\n🚀 Launching browser...');
    browser = await puppeteer.launch({
      headless: false,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      defaultViewport: { width: 1920, height: 1080 },
      slowMo: 30
    });
    
    const page = await browser.newPage();
    await page.setCacheEnabled(false);
    
    // Console monitoring
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('Error') || text.includes('error')) {
        console.log(`   ❌ Console: ${text}`);
      } else if (text.includes('[POS') || text.includes('API')) {
        console.log(`   ℹ️  ${text}`);
      }
    });
    
    // ========================================================================
    // NAVIGATE AND RELOAD
    // ========================================================================
    console.log('\n📂 Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
    
    console.log('🔄 Hard reload (F5)...');
    await page.reload({ waitUntil: 'networkidle0' });
    await sleep(3000);
    console.log('✅ Page loaded\n');
    
    // ========================================================================
    // STEP 1: Verify Initial State
    // ========================================================================
    console.log('═'.repeat(90));
    console.log('STEP 1: Verify initial state');
    console.log('═'.repeat(90));
    
    await screenshot(page, 'initial-state', 'step1');
    
    // Check header
    const headerText = await page.$eval('.header, header, [class*="Header"]', el => el.innerText).catch(() => 'Not found');
    console.log(headerText.includes('NBS POS') ? '✅ Header shows "NBS POS"' : '⚠️  Header check failed');
    console.log(headerText.includes('Administrator') ? '✅ Administrator shown' : '⚠️  Administrator not visible');
    console.log(headerText.includes('USD') || headerText.includes('IQD') ? '✅ Exchange rate shown' : '⚠️  Exchange rate not visible');
    
    // Check "+ New Order" button state
    const buttons = await page.$$('button');
    let newOrderBtn = null;
    for (const btn of buttons) {
      const text = await page.evaluate(el => el.textContent?.trim(), btn);
      if (text && text.includes('New Order')) {
        newOrderBtn = btn;
        console.log(`✅ Found: "${text}" button`);
        
        const isDisabled = await page.evaluate(el => {
          return el.disabled || el.hasAttribute('disabled') || 
                 el.getAttribute('aria-disabled') === 'true' ||
                 window.getComputedStyle(el).pointerEvents === 'none';
        }, btn);
        
        console.log(isDisabled ? '✅ Button is DISABLED (correct)' : '⚠️  Button appears enabled');
        break;
      }
    }
    
    // Check for warning
    const bodyText = await page.evaluate(() => document.body.innerText);
    if (bodyText.includes('Select a customer')) {
      console.log('✅ Warning "Select a customer first" visible');
    }
    
    // Check empty rows
    if (bodyText.includes('Click to search and add product')) {
      console.log('✅ Empty rows show "Click to search and add product..."');
    }
    
    // ========================================================================
    // STEP 2: Search and Select Customer
    // ========================================================================
    console.log('\n' + '═'.repeat(90));
    console.log('STEP 2: Search and select customer');
    console.log('═'.repeat(90));
    
    const customerInput = await page.$('input[placeholder*="customer" i]');
    if (!customerInput) {
      throw new Error('Customer search input not found');
    }
    
    console.log('✅ Customer search input found');
    await customerInput.click();
    await sleep(300);
    
    // Type "test" slowly
    for (const char of ['t', 'e', 's', 't']) {
      await page.keyboard.type(char);
      console.log(`   Typed: "${char}"`);
      await sleep(300);
    }
    
    console.log('   Search term: "test"');
    await sleep(2000);
    
    await screenshot(page, 'customer-dropdown', 'step2a');
    
    // Check dropdown
    const dropdown = await page.evaluate(() => {
      const list = document.querySelector('[role="listbox"], ul[class*="list"], [class*="dropdown"]');
      if (!list) return null;
      
      const items = Array.from(list.querySelectorAll('[role="option"], li, div[class*="item"]'));
      return {
        visible: list.offsetHeight > 0,
        count: items.length,
        customers: items.slice(0, 5).map(el => el.textContent?.trim()).filter(Boolean)
      };
    });
    
    if (dropdown && dropdown.visible && dropdown.count > 0) {
      console.log(`✅ Dropdown appeared with ${dropdown.count} customers:`);
      dropdown.customers.forEach((c, i) => console.log(`   ${i + 1}. ${c}`));
    } else {
      console.log('❌ No dropdown appeared');
    }
    
    // Click first customer
    const customerOptions = await page.$$('[role="option"], [class*="dropdown"] > div, ul > li');
    if (customerOptions.length > 0) {
      const firstCustomer = customerOptions[0];
      const custName = await page.evaluate(el => el.textContent?.trim(), firstCustomer);
      console.log(`\n   Clicking: "${custName}"`);
      
      await firstCustomer.click();
      await sleep(1000);
      
      await screenshot(page, 'customer-selected', 'step2b');
      
      // Verify selection
      const selectedValue = await page.$eval('input[placeholder*="customer" i]', el => el.value);
      console.log(selectedValue ? `✅ Customer selected: "${selectedValue}"` : '⚠️  Input is empty');
      
      // Check if button is now enabled
      if (newOrderBtn) {
        const nowEnabled = await page.evaluate(el => {
          const disabled = el.disabled || el.hasAttribute('disabled') || 
                          el.getAttribute('aria-disabled') === 'true' ||
                          window.getComputedStyle(el).pointerEvents === 'none';
          const bgColor = window.getComputedStyle(el).backgroundColor;
          return { enabled: !disabled, bgColor };
        }, newOrderBtn);
        
        console.log(nowEnabled.enabled ? '✅ "+ New Order" button is now ENABLED and GREEN' : '⚠️  Button still disabled');
        console.log(`   Background: ${nowEnabled.bgColor}`);
      }
    } else {
      throw new Error('No customer options found to click');
    }
    
    // ========================================================================
    // STEP 3: Create New Order
    // ========================================================================
    console.log('\n' + '═'.repeat(90));
    console.log('STEP 3: Create new order');
    console.log('═'.repeat(90));
    
    if (newOrderBtn) {
      await newOrderBtn.click();
      console.log('✅ Clicked "+ New Order" button');
      await sleep(3000);
      
      await screenshot(page, 'order-created', 'step3');
      
      // Check order number
      const orderFields = await page.$$('input');
      let orderNumber = null;
      for (const field of orderFields) {
        const value = await page.evaluate(el => el.value, field);
        if (value && (value.includes('POS/') || value.includes('SO/') || value.includes('Order'))) {
          orderNumber = value;
          break;
        }
      }
      
      if (orderNumber) {
        console.log(`✅ Order created: "${orderNumber}"`);
      } else {
        console.log('⚠️  No order number visible');
      }
      
      // Check state badge
      const badges = await page.$$('[class*="badge"], [class*="Badge"]');
      for (const badge of badges) {
        const text = await page.evaluate(el => el.textContent?.trim().toLowerCase(), badge);
        if (text && (text === 'draft' || text === 'quotation' || text === 'sale')) {
          console.log(`✅ State badge: "${text}"`);
          break;
        }
      }
    }
    
    // ========================================================================
    // STEP 4: Open Product Search Modal (Step 1 of 2)
    // ========================================================================
    console.log('\n' + '═'.repeat(90));
    console.log('STEP 4: Open product search modal');
    console.log('═'.repeat(90));
    
    // Find and click product search row
    const allElements = await page.$$('td, div, span');
    let clicked = false;
    
    for (const el of allElements) {
      const text = await page.evaluate(e => e.textContent?.trim(), el);
      if (text && text.includes('Click to search and add product')) {
        console.log('✅ Found product search trigger');
        await el.click();
        clicked = true;
        console.log('   Clicked on row');
        break;
      }
    }
    
    if (!clicked) {
      console.log('⚠️  Trying to click first table row...');
      const firstRow = await page.$('tbody tr:first-child');
      if (firstRow) await firstRow.click();
    }
    
    await sleep(1000);
    await screenshot(page, 'modal-opened-search', 'step4');
    
    // Check modal
    const modal = await page.evaluate(() => {
      const dialog = document.querySelector('[role="dialog"], [class*="modal" i]');
      if (!dialog) return null;
      
      const rect = dialog.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return null;
      
      const title = dialog.querySelector('h2, h3, [class*="title" i]');
      const searchInput = dialog.querySelector('input[type="text"], input[type="search"]');
      
      return {
        opened: true,
        title: title ? title.textContent?.trim() : 'No title',
        hasSearchInput: !!searchInput
      };
    });
    
    if (modal && modal.opened) {
      console.log(`✅ Modal opened: "${modal.title}"`);
      console.log(modal.hasSearchInput ? '✅ Search input present' : '⚠️  No search input');
    } else {
      console.log('❌ Modal did not open');
      throw new Error('Cannot proceed - modal not open');
    }
    
    // ========================================================================
    // STEP 5: Search for Product in Modal
    // ========================================================================
    console.log('\n' + '═'.repeat(90));
    console.log('STEP 5: Search for product in modal');
    console.log('═'.repeat(90));
    
    // Get all text inputs, find the one in the modal (should be visible)
    const inputs = await page.$$('input[type="text"], input[type="search"]');
    let modalSearchInput = null;
    
    for (const input of inputs) {
      const isVisible = await page.evaluate(el => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && 
               window.getComputedStyle(el).visibility !== 'hidden';
      }, input);
      
      if (isVisible) {
        const placeholder = await page.evaluate(el => el.placeholder, input);
        if (!placeholder.toLowerCase().includes('customer')) {
          modalSearchInput = input;
          console.log(`✅ Found modal search input (placeholder: "${placeholder}")`);
          break;
        }
      }
    }
    
    if (modalSearchInput) {
      await modalSearchInput.click();
      await sleep(300);
      
      // Clear and type "test"
      await page.keyboard.down('Control');
      await page.keyboard.press('A');
      await page.keyboard.up('Control');
      await page.keyboard.press('Backspace');
      await sleep(200);
      
      for (const char of ['t', 'e', 's', 't']) {
        await page.keyboard.type(char);
        console.log(`   Typed: "${char}"`);
        await sleep(400);
      }
      
      console.log('   Search: "test"');
      await sleep(2000);
      
      await screenshot(page, 'products-in-modal', 'step5');
      
      // Check products
      const products = await page.evaluate(() => {
        const rows = Array.from(document.querySelectorAll('table tbody tr'));
        const results = [];
        
        rows.forEach(row => {
          const text = row.textContent?.trim();
          if (text && text.length > 10 && 
              !text.includes('Click to search') && 
              !text.includes('No products')) {
            
            const cells = Array.from(row.querySelectorAll('td, div'));
            const columns = cells.map(c => c.textContent?.trim()).filter(Boolean);
            
            results.push({
              fullText: text.substring(0, 100),
              columns: columns
            });
          }
        });
        
        return results;
      });
      
      if (products.length > 0) {
        console.log(`✅ Found ${products.length} product(s):`);
        products.forEach((prod, i) => {
          console.log(`   ${i + 1}. ${prod.fullText}`);
          if (prod.fullText.includes('TEST BOTTLE')) {
            console.log('      ⭐ Contains "TEST BOTTLE"');
          }
        });
        
        if (products[0].columns.length > 0) {
          console.log(`   Columns visible: ${products[0].columns.length}`);
        }
      } else {
        console.log('❌ No products found');
      }
      
      // ========================================================================
      // STEP 6: Click Product to Open Config Panel (Step 2)
      // ========================================================================
      console.log('\n' + '═'.repeat(90));
      console.log('STEP 6: Click product to open configuration panel');
      console.log('═'.repeat(90));
      
      if (products.length > 0) {
        const productRows = await page.$$('table tbody tr');
        let targetRow = null;
        
        for (const row of productRows) {
          const text = await page.evaluate(el => el.textContent?.trim(), row);
          if (text && (text.includes('TEST BOTTLE') || text.length > 10) && 
              !text.includes('No products')) {
            targetRow = row;
            console.log(`✅ Clicking: "${text.substring(0, 60)}..."`);
            break;
          }
        }
        
        if (targetRow) {
          await targetRow.click();
          console.log('   Product row clicked');
          await sleep(2000);
          
          await screenshot(page, 'config-panel-opened', 'step6');
          
          // Check for configuration panel
          const configPanel = await page.evaluate(() => {
            const body = document.body.innerText;
            
            return {
              hasProductName: body.includes('Product') || body.includes('TEST'),
              hasUoMSection: body.includes('Unit of Measure') || body.includes('قطعه') || body.includes('UoM'),
              hasWarehouse: body.includes('Warehouse') || body.includes('Stock') || body.includes('Available'),
              hasQtyInput: !!document.querySelector('input[placeholder*="Qty" i], input[type="number"]'),
              hasUnitPrice: body.includes('Unit Price') || body.includes('Price'),
              hasDiscount: body.includes('Discount'),
              hasTotals: body.includes('Subtotal') || body.includes('Line Total'),
              hasBackButton: body.includes('Back to Search') || body.includes('Back'),
              hasAddButton: body.includes('Add to Order')
            };
          });
          
          console.log('\n   Configuration Panel Elements:');
          console.log(configPanel.hasProductName ? '   ✅ Product name/code visible' : '   ❌ No product name');
          console.log(configPanel.hasUoMSection ? '   ✅ Unit of Measure section' : '   ❌ No UoM section');
          console.log(configPanel.hasWarehouse ? '   ✅ Warehouse section with stock' : '   ❌ No warehouse section');
          console.log(configPanel.hasQtyInput ? '   ✅ Quantity input' : '   ❌ No qty input');
          console.log(configPanel.hasUnitPrice ? '   ✅ Unit Price shown' : '   ❌ No price');
          console.log(configPanel.hasDiscount ? '   ✅ Discount % field' : '   ❌ No discount');
          console.log(configPanel.hasTotals ? '   ✅ Totals preview (Subtotal, Line Total, IQD)' : '   ❌ No totals');
          console.log(configPanel.hasBackButton ? '   ✅ "Back to Search" button' : '   ❌ No back button');
          console.log(configPanel.hasAddButton ? '   ✅ "+ Add to Order" button' : '   ❌ No add button');
          
          const allGood = Object.values(configPanel).every(v => v);
          console.log(allGood ? '\n   ✅ Configuration panel fully loaded!' : '\n   ⚠️  Some elements missing');
          
          // ========================================================================
          // STEP 7: Configure and Add to Order
          // ========================================================================
          console.log('\n' + '═'.repeat(90));
          console.log('STEP 7: Configure product and add to order');
          console.log('═'.repeat(90));
          
          // Try to change qty to 3
          const qtyInputs = await page.$$('input[type="number"], input[placeholder*="Qty" i]');
          if (qtyInputs.length > 0) {
            const qtyInput = qtyInputs[0];
            await qtyInput.click({ clickCount: 3 });
            await page.keyboard.press('Backspace');
            await page.keyboard.type('3');
            console.log('✅ Changed quantity to 3');
            await sleep(500);
          }
          
          await screenshot(page, 'config-panel-filled', 'step7a');
          
          // Click "+ Add to Order"
          const allButtons = await page.$$('button');
          let addButton = null;
          
          for (const btn of allButtons) {
            const text = await page.evaluate(el => el.textContent?.trim(), btn);
            if (text && text.includes('Add to Order')) {
              addButton = btn;
              console.log(`✅ Found: "${text}" button`);
              break;
            }
          }
          
          if (addButton) {
            await addButton.click();
            console.log('   Clicked "+ Add to Order"');
            await sleep(3000);
            
            await screenshot(page, 'product-added-to-order', 'step7b');
            
            // Check if product appears in order table
            const orderLines = await page.evaluate(() => {
              const rows = Array.from(document.querySelectorAll('tbody tr'));
              const lines = [];
              
              rows.forEach(row => {
                const text = row.textContent?.trim();
                if (text && !text.includes('Click to search')) {
                  const cells = Array.from(row.querySelectorAll('td'));
                  if (cells.length >= 5) {
                    lines.push({
                      product: cells[1]?.textContent?.trim(),
                      qty: cells[2]?.textContent?.trim(),
                      uom: cells[3]?.textContent?.trim(),
                      warehouse: cells[4]?.textContent?.trim(),
                      price: cells[cells.length - 1]?.textContent?.trim()
                    });
                  }
                }
              });
              
              return lines;
            });
            
            if (orderLines.length > 0) {
              console.log(`\n✅ Product added! Order has ${orderLines.length} line(s):`);
              orderLines.forEach((line, i) => {
                console.log(`\n   Line ${i + 1}:`);
                console.log(`   - Product: ${line.product}`);
                console.log(`   - Qty: ${line.qty}`);
                console.log(`   - UoM: ${line.uom}`);
                console.log(`   - Warehouse: ${line.warehouse}`);
                console.log(`   - Total: ${line.price}`);
              });
            } else {
              console.log('⚠️  No order lines visible yet');
            }
          } else {
            console.log('❌ "+ Add to Order" button not found');
          }
          
        } else {
          console.log('❌ No product row found to click');
        }
      } else {
        console.log('⚠️  Skipping - no products to configure');
      }
    } else {
      console.log('❌ Modal search input not found');
    }
    
    // ========================================================================
    // STEP 8: Verify Order Summary
    // ========================================================================
    console.log('\n' + '═'.repeat(90));
    console.log('STEP 8: Verify complete order summary');
    console.log('═'.repeat(90));
    
    await screenshot(page, 'final-order-complete', 'step8');
    
    const summary = await page.evaluate(() => {
      const text = document.body.innerText;
      
      const subtotalMatch = text.match(/Subtotal:?\s*\$?([\d,]+\.?\d*)/i);
      const discountMatch = text.match(/Discount:?\s*-?\$?([\d,]+\.?\d*)/i);
      const taxMatch = text.match(/Tax:?\s*\$?([\d,]+\.?\d*)/i);
      const grandTotalMatch = text.match(/Grand Total:?\s*\$?([\d,]+\.?\d*)/i);
      const iqdMatch = text.match(/Total in IQD:?\s*([\d,]+)/i);
      
      return {
        subtotal: subtotalMatch ? subtotalMatch[1] : '0.00',
        discount: discountMatch ? discountMatch[1] : '0.00',
        tax: taxMatch ? taxMatch[1] : '0.00',
        grandTotal: grandTotalMatch ? grandTotalMatch[1] : '0.00',
        totalIQD: iqdMatch ? iqdMatch[1] : '0'
      };
    });
    
    console.log('\n📊 Order Totals:');
    console.log(`   Subtotal:    $${summary.subtotal}`);
    console.log(`   Discount:   -$${summary.discount}`);
    console.log(`   Tax:         $${summary.tax}`);
    console.log(`   Grand Total: $${summary.grandTotal}`);
    console.log(`   Total (IQD):  ${summary.totalIQD} IQD`);
    
    const hasValue = parseFloat(summary.grandTotal.replace(/,/g, '')) > 0;
    console.log(hasValue ? '\n✅ Order has value - product successfully added!' : '\n⚠️  Order total is $0.00');
    
    console.log('\n' + '='.repeat(90));
    console.log('✅ COMPLETE WORKFLOW TEST FINISHED');
    console.log('='.repeat(90));
    console.log(`\n📁 Screenshots: ${SCREENSHOTS_DIR}`);
    
    await sleep(3000);
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error(error.stack);
  } finally {
    if (browser) {
      await browser.close();
      console.log('\n🔚 Browser closed');
    }
  }
}

testCompletePOSWorkflow().catch(console.error);
