'use strict';

const request = require('supertest');
const { createApp } = require('../src/app');

let app;
beforeEach(() => {
  app = createApp();
});

test('creates and lists a transaction', async () => {
  const created = await request(app)
    .post('/transactions')
    .send({ amount: 100, type: 'credit' });
  expect(created.status).toBe(201);
  expect(created.body.id).toBe(1);
  expect(created.body.amount).toBe(100);

  const listed = await request(app).get('/transactions');
  expect(listed.status).toBe(200);
  expect(listed.body).toHaveLength(1);
});

test('rejects invalid input with 422', async () => {
  const negative = await request(app)
    .post('/transactions')
    .send({ amount: -5, type: 'credit' });
  expect(negative.status).toBe(422);

  const badType = await request(app)
    .post('/transactions')
    .send({ amount: 5, type: 'wat' });
  expect(badType.status).toBe(422);

  const missing = await request(app).post('/transactions').send({ amount: 5 });
  expect(missing.status).toBe(422);
});

test('computes balance as credits minus debits', async () => {
  await request(app).post('/transactions').send({ amount: 100, type: 'credit' });
  await request(app).post('/transactions').send({ amount: 30, type: 'debit' });
  await request(app).post('/transactions').send({ amount: 10, type: 'debit' });

  const res = await request(app).get('/balance');
  expect(res.body.credits).toBe(100);
  expect(res.body.debits).toBe(40);
  expect(res.body.balance).toBe(60);
  expect(res.body.count).toBe(3);
});
