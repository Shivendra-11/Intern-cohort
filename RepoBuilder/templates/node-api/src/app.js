'use strict';

// A small transaction-ledger API built with Express.
// Mirrors the FastAPI example: POST /transactions, GET /transactions, GET /balance.
// State is kept in memory to stay self-contained.

const express = require('express');

const VALID_TYPES = new Set(['credit', 'debit']);

function createApp() {
  const app = express();
  app.use(express.json());

  // Per-app state so each created app (and each test) is isolated.
  const transactions = [];
  let nextId = 1;

  // Validate input; return an error string or null if valid.
  function validate(body) {
    if (body == null || typeof body !== 'object') return 'body must be a JSON object';
    const { amount, type } = body;
    if (typeof amount !== 'number' || Number.isNaN(amount)) return 'amount must be a number';
    if (amount <= 0) return 'amount must be greater than 0';
    if (!VALID_TYPES.has(type)) return "type must be 'credit' or 'debit'";
    if (body.description != null && typeof body.description !== 'string') {
      return 'description must be a string';
    }
    return null;
  }

  app.post('/transactions', (req, res) => {
    const error = validate(req.body);
    if (error) return res.status(422).json({ error });

    const tx = {
      id: nextId++,
      amount: req.body.amount,
      type: req.body.type,
      description: req.body.description ?? null,
    };
    transactions.push(tx);
    return res.status(201).json(tx);
  });

  app.get('/transactions', (_req, res) => {
    res.json(transactions);
  });

  app.get('/balance', (_req, res) => {
    const credits = transactions
      .filter((t) => t.type === 'credit')
      .reduce((sum, t) => sum + t.amount, 0);
    const debits = transactions
      .filter((t) => t.type === 'debit')
      .reduce((sum, t) => sum + t.amount, 0);
    res.json({ balance: credits - debits, credits, debits, count: transactions.length });
  });

  return app;
}

module.exports = { createApp };
