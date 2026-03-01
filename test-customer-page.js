#!/usr/bin/env node

/**
 * Script to test the CRM customer page and API
 * This will help diagnose what's happening on the customers page
 */

const http = require('http');

// Helper to make HTTP requests
function makeRequest(options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });
    
    req.on('error', reject);
    
    if (postData) {
      req.write(postData);
    }
    
    req.end();
  });
}

async function testCustomerAPI() {
  console.log('='.repeat(60));
  console.log('Testing CRM Customer Page API');
  console.log('='.repeat(60));
  
  try {
    // Test 1: Check if the frontend is running
    console.log('\n1. Checking if frontend is accessible...');
    const frontendResponse = await makeRequest({
      hostname: 'localhost',
      port: 5173,
      path: '/',
      method: 'GET'
    });
    console.log(`   ✓ Frontend is running (Status: ${frontendResponse.statusCode})`);
    
    // Test 2: Try to call the customer list API (without auth - expecting 401)
    console.log('\n2. Testing /api/crm/customers/list endpoint (no auth)...');
    const payload = JSON.stringify({
      page: 1,
      per_page: 50,
      search: null,
      stage_id: null,
      branch_id: null,
      vip_only: false
    });
    
    const apiResponse = await makeRequest({
      hostname: 'localhost',
      port: 5173,
      path: '/api/crm/customers/list',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    }, payload);
    
    console.log(`   Status: ${apiResponse.statusCode}`);
    console.log(`   Response: ${apiResponse.body}`);
    
    const parsedResponse = JSON.parse(apiResponse.body);
    if (parsedResponse.result) {
      if (parsedResponse.result.success === false) {
        console.log(`   ⚠ API returned error: ${parsedResponse.result.error}`);
        console.log('   This is expected if not authenticated yet.');
      } else if (parsedResponse.result.success === true) {
        const { items = [], total = 0 } = parsedResponse.result.data || {};
        console.log(`   ✓ API returned successfully`);
        console.log(`   Total customers: ${total}`);
        console.log(`   Items in response: ${items.length}`);
        
        if (total === 0) {
          console.log('\n   💡 No customers found in database.');
          console.log('   The UI should show a sync banner asking to import from Odoo.');
        } else {
          console.log(`\n   ✓ Found ${total} customers in the database.`);
          console.log('   The UI should display customer cards in the kanban view.');
        }
      }
    }
    
    // Test 3: Check if Odoo backend is accessible
    console.log('\n3. Checking if Odoo backend is accessible...');
    try {
      const odooResponse = await makeRequest({
        hostname: 'localhost',
        port: 8070,
        path: '/web',
        method: 'GET',
        timeout: 3000
      });
      console.log(`   ✓ Odoo backend is running (Status: ${odooResponse.statusCode})`);
    } catch (err) {
      console.log(`   ✗ Odoo backend is not accessible: ${err.message}`);
      console.log('   Customer sync from Odoo will not work.');
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('MANUAL TESTING STEPS:');
    console.log('='.repeat(60));
    console.log('\n1. Open http://localhost:5173 in your browser');
    console.log('2. Login with username: admin, password: admin');
    console.log('3. Click on "العملاء" (Customers) in the sidebar');
    console.log('4. Open Developer Tools (F12)');
    console.log('5. Check the Console tab for JavaScript errors');
    console.log('6. Check the Network tab for /api/crm/customers/list request');
    console.log('\nEXPECTED BEHAVIORS:');
    console.log('─'.repeat(60));
    console.log('If customers table is empty:');
    console.log('  → Should show sync banner with "استيراد من أودو" button');
    console.log('\nIf customers exist:');
    console.log('  → Should show kanban board with customer cards');
    console.log('\nIf API fails:');
    console.log('  → Should show error message in red box');
    console.log('\nIf loading:');
    console.log('  → Should show "جاري التحميل..." message');
    console.log('='.repeat(60));
    
  } catch (error) {
    console.error('\n✗ Error during testing:', error.message);
  }
}

// Run the test
testCustomerAPI();
