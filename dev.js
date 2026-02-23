#!/usr/bin/env node
/**
 * Local dev server - frontend test karne ke liye
 * Run: node dev.js
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

// Vercel jaise res.status() aur res.json() add karo
function patchRes(res) {
  res.status = (code) => { res.statusCode = code; return res; };
  res.json   = (data) => {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(data));
  };
  return res;
}

const tokenHandler = require('./api/token');

const server = http.createServer(async (req, res) => {
  patchRes(res);

  const url = req.url.split('?')[0];

  if (url === '/api/token') {
    return await tokenHandler(req, res);
  }

  // Baaki sab: index.html serve karo
  const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
});

const PORT = 3000;
server.listen(PORT, () => {
  console.log('\n  Dev server ready!');
  console.log(`  Open: http://localhost:${PORT}\n`);
});
