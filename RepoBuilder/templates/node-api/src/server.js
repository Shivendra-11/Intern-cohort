'use strict';

const { createApp } = require('./app');

const port = process.env.PORT || 3000;
createApp().listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Ledger API listening on http://127.0.0.1:${port}`);
});
