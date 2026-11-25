// Money tests. The engine (shared/records.js + shared/erp.js) is the only
// place business rules live, so these run it directly on plain objects —
// no server, no DOM, no disk. If any of these fail, the books are wrong and
// nothing else matters. Run with: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeEngine } from '../shared/records.js';
import { buildSeed } from '../shared/seed.js';
import * as erp from '../shared/erp.js';
import { docTotals } from '../shared/schema.js';
import { makeLocalDb, memoryStorage, STORAGE_KEY } from '../public/js/localdb.js';

function freshDb() {
  const db = buildSeed();
  const engine = makeEngine(db, {});
  return { db, engine };
}

function ledgerBalance(db) {
  let debit = 0;
  let credit = 0;
  for (const e of db.ledger) {
    for (const l of e.lines) { debit += l.debit; credit += l.credit; }
  }
  const diff = Math.round((debit - credit) * 100) / 100;
  return diff === 0 ? 0 : diff; // never -0
}

function accountBalance(db, code) {
  const account = erp.accountByCode(db, code);
  let sum = 0;
  for (const e of db.ledger) {
    for (const l of e.lines) {
      if (l.accountId !== account.id) continue;
      if (['Asset', 'Expense'].includes(account.type)) sum += l.debit - l.credit;
      else sum += l.credit - l.debit;
    }
  }
  return Math.round(sum * 100) / 100;
}

// ---------------------------------------------------------------------------
test('seeded sample business posts clean: every journal entry balances', () => {
  const { db } = freshDb();
  assert.equal(ledgerBalance(db), 0, 'debits = credits across the whole journal');
  assert.ok(db.ledger.length > 0, 'seeded invoices posted');
  assert.ok(db.accounts.length >= 10, 'chart of accounts seeded');
});

test('seeded invoices derive paid/status from payments (partial + paid)', () => {
  const { db } = freshDb();
  const byNumber = Object.fromEntries(db.invoices.map((i) => [i.number, i]));
  assert.equal(byNumber['INV-1001'].status, 'Paid', 'fully-paid seed invoice');
  assert.equal(byNumber['INV-1002'].status, 'Partial', 'partially-paid seed invoice');
  assert.ok(byNumber['INV-1002'].total - byNumber['INV-1002'].paid > 0, 'open balance on the partial invoice');
  // AR reflects the open balance, cash reflects collections.
  assert.ok(accountBalance(db, '1100') > 0, 'AR carries the open balance');
  assert.ok(accountBalance(db, '1000') > 0, 'Cash carries the payments');
});

test('part quantities survive seeding+posting: stock moves land exactly on current qty', () => {
  const { db } = freshDb();
  // The seed stores qty = desired + sold (so posting the seeded invoices lands
  // back on the desired numbers). Verify the hose: desired 2, sold 6.
  const hose = db.parts.find((p) => p.sku === 'HOSE-34-48');
  assert.equal(hose.qty, 2, 'hose on hand is the desired number after seeded sales');
  const saleMoves = db.stockmoves.filter((m) => m.partId === hose.id && m.reason === 'Sale');
  assert.equal(saleMoves.reduce((s, m) => s + m.qty, 0), -6, 'six hoses moved out for the seeded invoice');
});

test('invoice lifecycle: draft → send posts AR/income/tax + COGS + stock', () => {
  const { db, engine } = freshDb();
  const part = db.parts.find((p) => p.sku === 'BAT-G31'); // cost 189
  const qtyBefore = part.qty;
  const lines = [
    { kind: 'part', partId: part.id, description: 'Battery', qty: 2, unitPrice: 229, taxable: true },
    { kind: 'labor', description: 'Install', qty: 1, unitPrice: 110, taxable: false },
  ];
  const t = docTotals(lines, 6); // 458 parts + 110 labor = 568; tax 6% of 458 = 27.48
  assert.equal(t.subtotal, 568);
  assert.equal(t.taxAmount, 27.48);
  assert.equal(t.total, 595.48);

  const inv = engine.create('invoices', { customerId: 'cus-bigsky', lines, taxRate: 6 }, 'tester');
  assert.ok(inv.number.startsWith('INV-'), 'number assigned');
  assert.equal(inv.status, 'Draft');
  assert.equal(inv.total, 595.48);
  assert.equal(inv.paid, 0);

  const arBefore = accountBalance(db, '1100');
  engine.op('invoices', inv.id, 'send', {}, 'tester');
  assert.equal(inv.status, 'Sent');
  assert.equal(ledgerBalance(db), 0, 'journal still balances after posting');
  assert.equal(Math.round((accountBalance(db, '1100') - arBefore) * 100) / 100, 595.48, 'AR increased by the invoice total');
  assert.equal(part.qty, qtyBefore - 2, 'stock decremented by the part line');
  assert.ok(accountBalance(db, '5000') > 0, 'COGS posted');
  assert.ok(accountBalance(db, '1200') >= 0, 'inventory not negative');
});

test('payments: full payment closes the invoice and zeroes AR; partial stays open', () => {
  const { db, engine } = freshDb();
  const inv = db.invoices.find((i) => i.number === 'INV-1003'); // sent, unpaid counter sale
  const arBefore = accountBalance(db, '1100');
  const cashBefore = accountBalance(db, '1000');

  const partial = engine.create('payments', { invoiceId: inv.id, amount: 50, date: '2026-01-01', method: 'Cash' }, 'tester');
  assert.equal(inv.status, 'Partial');
  engine.create('payments', { invoiceId: inv.id, amount: inv.total - 50, date: '2026-01-02', method: 'Cash' }, 'tester');
  assert.equal(inv.status, 'Paid');
  assert.equal(Math.round((inv.total - inv.paid) * 100) / 100, 0, 'nothing left open');
  assert.ok(Math.abs((accountBalance(db, '1100') - arBefore) + inv.total) < 0.005, 'AR decreased by the full total');
  assert.ok(accountBalance(db, '1000') > cashBefore, 'Cash went up');

  // Deleting a payment reverses it and re-derives status.
  engine.remove('payments', partial.id, 'tester');
  assert.equal(inv.status, 'Partial', 'back to partial after the payment is deleted');
  assert.ok(Math.abs((accountBalance(db, '1100') - arBefore) + (inv.total - 50)) < 0.005);
  assert.ok(ledgerBalance(db) === 0);
});

test('payment guardrails: overpay blocked, draft/void invoices blocked', () => {
  const { db, engine } = freshDb();
  const inv = db.invoices.find((i) => i.number === 'INV-1003');
  assert.throws(() => engine.create('payments', { invoiceId: inv.id, amount: inv.total + 1 }, 'tester'), /outstanding balance/i);
  const draft = engine.create('invoices', { customerId: 'cus-bigsky', lines: [{ kind: 'item', description: 'x', qty: 1, unitPrice: 10 }] }, 'tester');
  assert.throws(() => engine.create('payments', { invoiceId: draft.id, amount: 10 }, 'tester'), /send .* before/i);
  engine.op('invoices', draft.id, 'send', {}, 'tester');
  engine.op('invoices', draft.id, 'void', {}, 'tester');
  assert.throws(() => engine.create('payments', { invoiceId: draft.id, amount: 10 }, 'tester'), /void/i);
});

test('posted documents are locked; void posts reversals and returns stock', () => {
  const { db, engine } = freshDb();
  const part = db.parts.find((p) => p.sku === 'BLT-F550');
  const qtyBefore = part.qty;
  const inv = engine.create('invoices', { customerId: 'cus-bozeman', lines: [{ kind: 'part', partId: part.id, description: 'belt', qty: 3, unitPrice: 48 }] }, 'tester');
  const arBefore = accountBalance(db, '1100'); // before send (draft posts nothing)
  engine.op('invoices', inv.id, 'send', {}, 'tester');

  assert.throws(() => engine.update('invoices', inv.id, { notes: 'sneaky edit' }, 'tester'), /locked/i);
  assert.throws(() => engine.remove('invoices', inv.id, 'tester'), /void/i);

  const entriesBefore = db.ledger.length;
  engine.op('invoices', inv.id, 'void', {}, 'tester');
  assert.equal(inv.status, 'Void');
  assert.ok(db.ledger.length > entriesBefore, 'reversal entries appended (history kept)');
  assert.equal(ledgerBalance(db), 0, 'reversals balance');
  assert.equal(accountBalance(db, '1100'), arBefore, 'AR returned to its pre-send level');
  assert.equal(part.qty, qtyBefore, 'stock returned');
});

test('quotes convert: accept creates a draft invoice with the same lines and totals', () => {
  const { db, engine } = freshDb();
  const quote = db.quotes.find((q) => q.number === 'QUO-1001');
  const before = db.invoices.length;
  const { created } = engine.op('quotes', quote.id, 'accept', {}, 'tester');
  assert.ok(created, 'an invoice was created');
  assert.equal(db.invoices.length, before + 1);
  assert.equal(created.status, 'Draft');
  assert.ok(created.number.startsWith('INV-'));
  assert.equal(created.total, quote.total, 'same money');
  assert.deepEqual(created.lines.map((l) => [l.qty, l.unitPrice]), quote.lines.map((l) => [l.qty, l.unitPrice]));
  assert.ok(created.number !== quote.number, 'invoice has its own number');
});

test('purchasing: receive posts Inventory/GRIR and moves avg cost; bill clears GRIR; vendor payment closes it', () => {
  const { db, engine } = freshDb();
  const part = db.parts.find((p) => p.sku === 'TOOTH-320');
  const qtyBefore = part.qty;
  const avgBefore = part.avgCost;
  const po = engine.create('purchaseorders', {
    vendorId: 'ven-under',
    lines: [{ kind: 'part', partId: part.id, description: 'teeth', qty: 10, unitPrice: 80 }],
  }, 'tester');
  engine.op('purchaseorders', po.id, 'order', {}, 'tester');
  const lineId = po.lines[0].id;
  engine.op('purchaseorders', po.id, 'receive', { lines: [{ lineId, qty: 10 }] }, 'tester');
  assert.equal(po.status, 'Received');
  assert.equal(part.qty, qtyBefore + 10);
  assert.equal(part.avgCost, Math.round(((qtyBefore * avgBefore + 10 * 80) / (qtyBefore + 10)) * 100) / 100, 'moving average blended');
  assert.equal(ledgerBalance(db), 0);
  const grirAfterReceive = accountBalance(db, '1300');
  assert.ok(grirAfterReceive > 0, 'GRIR liability for received-not-invoiced');

  // Bill it: GRIR clears, AP appears.
  const bill = engine.create('bills', { vendorId: 'ven-under', poId: po.id, lines: [{ kind: 'part', partId: part.id, description: 'teeth', qty: 10, unitPrice: 80 }] }, 'tester');
  engine.op('bills', bill.id, 'record', {}, 'tester');
  assert.equal(bill.status, 'Unpaid');
  assert.ok(accountBalance(db, '1300') < grirAfterReceive, 'GRIR cleared by the bill');
  assert.ok(accountBalance(db, '2000') > 0, 'AP carried');
  assert.equal(po.receivedValue, 0, 'PO receipt pool consumed');

  engine.create('vendorpayments', { billId: bill.id, amount: bill.total, date: '2026-01-05' }, 'tester');
  assert.equal(bill.status, 'Paid');
  assert.equal(ledgerBalance(db), 0);
});

test('manual stock adjustments are recorded as moves, never silently', () => {
  const { db, engine } = freshDb();
  const part = db.parts.find((p) => p.sku === 'DEF-25');
  const movesBefore = db.stockmoves.length;
  engine.update('parts', part.id, { qty: 99 }, 'tester');
  assert.equal(part.qty, 99);
  assert.equal(db.stockmoves.length, movesBefore + 1, 'an adjustment move exists');
  const move = db.stockmoves[0];
  assert.ok(move.reason === 'Adjustment' && move.qty !== 0, 'move records the delta');
});

test('document numbering is sequential and survives restarts (meta.seq)', () => {
  const { db, engine } = freshDb();
  const a = engine.create('invoices', { customerId: 'cus-bigsky', lines: [{ kind: 'item', description: 'x', qty: 1, unitPrice: 1 }] }, 'tester');
  const b = engine.create('invoices', { customerId: 'cus-bigsky', lines: [{ kind: 'item', description: 'y', qty: 1, unitPrice: 1 }] }, 'tester');
  const n1 = Number(a.number.split('-')[1]);
  const n2 = Number(b.number.split('-')[1]);
  assert.equal(n2, n1 + 1);
  assert.ok(db.meta.seq.invoice >= 5, 'counter advanced past the seeded invoices');
});

test('reports: aging buckets, P&L and job costing compute off the ledger', () => {
  const { db } = freshDb();
  const ar = erp.arAging(db);
  assert.ok(ar.total > 0, 'AR total');
  assert.ok(ar.rows.length > 0);
  const ap = erp.apAging(db);
  assert.ok(ap.total > 0, 'AP total (unpaid vendor bills)');
  const pnl = erp.pnl(db, 12);
  assert.ok(pnl.totals.income > 0 && pnl.totals.expense > 0, 'income and expense both present');
  assert.equal(pnl.net, Math.round((pnl.totals.income - pnl.totals.expense) * 100) / 100);
  const jobs = erp.jobCosting(db);
  const fleet = jobs.find((r) => r.job.title.includes('Big Sky'));
  assert.ok(fleet, 'job costing rows exist');
  assert.ok(fleet.labor > 0, 'labor cost from time entries');
  assert.ok(fleet.invoiced > 0, 'invoiced per job');
});

test('catchUp is idempotent: booting twice never double-posts', () => {
  const { db } = freshDb();
  const entries = db.ledger.length;
  const moves = db.stockmoves.length;
  erp.catchUp(db);
  erp.catchUp(db);
  assert.equal(db.ledger.length, entries, 'no duplicate journal entries');
  assert.equal(db.stockmoves.length, moves, 'no duplicate stock moves');
});

test('append-only discipline: the journal cannot be edited or deleted', () => {
  const { db, engine } = freshDb();
  const entry = db.ledger[0];
  assert.throws(() => engine.remove('ledger', entry.id, 'tester'), /append-only/i);
  assert.throws(() => engine.remove('stockmoves', db.stockmoves[0].id, 'tester'), /append-only/i);
});

// ---- the money gate ---------------------------------------------------------
test('gate: sanitizeSettings strips the hash and exposes adminPinSet', async () => {
  const { sanitizeSettings } = await import('../shared/gate.js');
  const s = sanitizeSettings({ shopName: 'X', adminPinHash: 'abc' });
  assert.equal(s.adminPinHash, undefined, 'hash never leaves the server');
  assert.equal(s.adminPinSet, true);
  assert.equal(sanitizeSettings({}).adminPinSet, false);
});

test('gate: locked snapshots withhold money documents and pay rates', async () => {
  const { redactSnapshot } = await import('../shared/gate.js');
  const { db } = freshDb();
  const snap = {
    collections: {
      invoices: db.invoices, payments: db.payments, bills: db.bills,
      quotes: db.quotes, purchaseorders: db.purchaseorders, vendorpayments: db.vendorpayments,
      ledger: db.ledger, stockmoves: db.stockmoves,
      people: db.people, parts: db.parts, jobs: db.jobs,
    },
    settings: { adminPinHash: 'h', defaultTaxRate: 6 },
  };
  const locked = redactSnapshot(snap, false);
  assert.equal(locked.collections.invoices.length, 0, 'invoices withheld');
  assert.equal(locked.collections.ledger.length, 0, 'journal withheld');
  assert.ok(locked.collections.people.every((p) => p.payRate === null), 'pay rates withheld');
  assert.equal(locked.collections.parts.length, db.parts.length, 'inventory is planning data, not billing data');
  assert.equal(locked.settings.adminPinHash, undefined);
  assert.equal(locked.settings.adminPinSet, true);

  const open = redactSnapshot(snap, true);
  assert.equal(open.collections.invoices.length, db.invoices.length, 'money visible when unlocked');
  assert.equal(open.settings.adminPinHash, undefined, 'hash stripped even when unlocked');
});

test('gate: demo mode blocks money until the PIN is entered', async () => {
  const storage = memoryStorage();
  const ldb = makeLocalDb(storage, STORAGE_KEY);
  const { sha256Hex } = await import('../shared/gate.js');
  ldb.updateSettings({ adminPinHash: await sha256Hex('1357') }, 'tester');

  // Locked: money hidden and mutations blocked.
  assert.equal(ldb.snapshot().collections.invoices.length, 0);
  assert.equal(ldb.snapshot().settings.adminPinSet, true);
  assert.equal(ldb.snapshot().settings.adminPinHash, undefined);
  assert.throws(() => ldb.create('invoices', { customerId: null, lines: [] }, 't'), /locked/i);
  assert.throws(() => ldb.updateSettings({ shopName: 'x' }, 't'), /unlock/i);
  await assert.rejects(() => ldb.unlock('0000'), /Wrong PIN/);

  await ldb.unlock('1357');
  assert.ok(ldb.snapshot().collections.invoices.length > 0, 'money visible after unlock');
  assert.equal(ldb.snapshot().settings.adminPinHash, undefined);

  ldb.lockNow();
  assert.equal(ldb.snapshot().collections.invoices.length, 0, 're-locked');
});

// ---- the browser demo runs the same engine ---------------------------------
test('demo mode (localStorage) posts money exactly like the server', () => {
  const storage = memoryStorage();
  const ldb = makeLocalDb(storage, STORAGE_KEY);
  const db = ldb._db();

  const inv = ldb.create('invoices', {
    customerId: 'cus-bigsky',
    taxRate: 0,
    lines: [{ kind: 'part', partId: db.parts[0].id, description: 'part', qty: 1, unitPrice: 50 }],
  }, 'tester');
  ldb.op('invoices', inv.id, 'send', {}, 'tester');
  assert.equal(inv.status, 'Sent');
  assert.ok(db.ledger.some((e) => e.refId === inv.id), 'invoice posted in demo mode');
  ldb.create('payments', { invoiceId: inv.id, amount: 50, date: '2026-01-01' }, 'tester');
  assert.equal(inv.status, 'Paid', 'demo payment closes the invoice');
  assert.equal(ledgerBalance(db), 0, 'demo books balance');
  assert.ok(JSON.parse(storage.getItem(STORAGE_KEY)).ledger.length > 0, 'demo ledger persisted');
});
