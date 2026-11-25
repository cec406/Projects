# GrizzWorks | Shop operations engine

Small equipment shops need quotes, inventory, invoices and payments to agree, even when their internet connection is down. GrizzWorks shares its business rules between a browser demo and a locally hosted shop app so both modes post transactions the same way.

This folder contains the actual shared GrizzWorks engine, its browser storage adapter, and tests with synthetic shop records. It does not include the shop server or UI.

**[Open the live GrizzWorks demo](https://grizzlyse.com/dashboard/)** to see the full interface. Use only sample data in the public demo.

## Run the tests

With Node.js 18+ installed, run `npm test` from this folder. No dependency install or network access is needed.

Start with [`tests/erp.test.js`](tests/erp.test.js) for business workflows, then read [`shared/records.js`](shared/records.js) for record transitions and [`shared/erp.js`](shared/erp.js) for ledger and inventory posting. This is a portfolio extract, not a production accounting deployment.
