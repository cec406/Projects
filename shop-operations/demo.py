"""Run a synthetic invoice-to-payment workflow in a local SQLite database."""
import argparse
import sqlite3
from contextlib import closing


def run(path):
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('''CREATE TABLE IF NOT EXISTS entries (
            event TEXT, account TEXT, cents INTEGER NOT NULL,
            PRIMARY KEY (event, account)
        )''')
        for event, debit, credit, cents in (
            ('DEMO-INVOICE', 'Receivables', 'Revenue', 12500),
            ('DEMO-PAYMENT', 'Cash', 'Receivables', 12500),
        ):
            db.executemany('INSERT OR IGNORE INTO entries VALUES (?, ?, ?)',
                           [(event, debit, cents), (event, credit, -cents)])
        return dict(db.execute('SELECT account, SUM(cents) FROM entries GROUP BY account ORDER BY account'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=':memory:', help='Optional SQLite file for the demo')
    for account, cents in run(parser.parse_args().db).items():
        print(f'{account}: {cents} cents')
