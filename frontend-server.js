#!/usr/bin/env node
/**
 * Simple frontend server - frontend.html ko serve karne ke liye
 * Run: node frontend-server.js
 */

// .env.local manually load karo (dotenv ki zaroorat nahi)
const fs_env = require('fs');
if (fs_env.existsSync('.env.local')) {
  fs_env.readFileSync('.env.local', 'utf8')
    .split('\n')
    .forEach(line => {
      const [key, ...val] = line.split('=');
      if (key && !key.startsWith('#')) {
        process.env[key.trim()] = val.join('=').trim();
      }
    });
}

const http = require('http');
const fs   = require('fs');
const path = require('path');

// token.js ko res.status() aur res.json() chahiye (Express-style)
function patchRes(res) {
  res.status = (code) => { res.statusCode = code; return res; };
  res.json   = (data) => {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(data));
  };
  return res;
}

// Token API import karo
const tokenHandler = require('./api/token');

const server = http.createServer(async (req, res) => {
  patchRes(res);

  // CORS headers for LiveKit
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');

  const url = req.url.split('?')[0];

  // /api/token route handle karo
  if (url === '/api/token') {
    return await tokenHandler(req, res);
  }
  
  // Serve frontend.html
  const htmlPath = path.join(__dirname, 'frontend.html');
  
  if (fs.existsSync(htmlPath)) {
    const html = fs.readFileSync(htmlPath, 'utf8');
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(html);
    console.log(`[${new Date().toLocaleTimeString()}] Served frontend.html`);
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('frontend.html not found');
    console.error(`[${new Date().toLocaleTimeString()}] frontend.html not found`);
  }
});

const PORT = 3001;
server.listen(PORT, () => {
  console.log('\n' + '='.repeat(60));
  console.log('  Frontend Server Ready!');
  console.log('='.repeat(60));
  console.log(`\n  Open: http://localhost:${PORT}\n`);
  console.log('  Steps:');
  console.log('  1. Generate token: uv run python generate_token.py');
  console.log('  2. Copy the URL and Token');
  console.log('  3. Paste in the form and click Connect');
  console.log('  4. Start speaking!\n');
  console.log('='.repeat(60) + '\n');
});
