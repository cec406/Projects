# Local-first shop operations

GrizzWorks was built for shops that need to manage jobs, quotes, inventory, and billing on their own hardware. This standalone reference sample isolates one design decision: post an invoice and its payment as balanced entries in a local database that needs no internet connection.

## Try it

From this directory, run `python demo.py` with Python 3. Expect cash of 12500 cents, receivables of 0, and revenue of -12500 (credits use negative signs). To see repeatable imports, run `python demo.py --db demo.sqlite` twice; the synthetic event IDs prevent duplicate postings.

This sample uses SQLite and fixed synthetic input. The original application uses a Node server and live LAN updates; this sample is not that application or a production accounting system.
