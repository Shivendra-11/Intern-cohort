const express = require('express');
const app = express();

app.get('/health', (req, res) => res.json({ ok: true }));
app.post('/transactions', (req, res) => res.json({ created: true }));

module.exports = app;
