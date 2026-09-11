# Finance: A Stock Trading Simulator

A web app that lets users manage a simulated stock portfolio: register an account, get a set amount of fake cash, look up real stock prices, and buy and sell shares against a live market feed.

## Setup and Installation

### 1. Clone the repository

```
git clone https://github.com/YOUR_USERNAME/finance.git
cd finance
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Get a free API key

This app pulls live stock prices from [Alpha Vantage](https://www.alphavantage.co/support/#api-key). Go to that link, enter your email, and it issues a free key instantly, no credit card required. The free tier allows 25 requests per day.

### 4. Set the API key as an environment variable

The app reads your key from an environment variable called `API_KEY`. It's never stored in any file, which is intentional, so it never ends up committed to a public repo like this one.

**Windows (PowerShell):**
```
$env:API_KEY="your_key_here"
```

**macOS/Linux:**
```
export API_KEY="your_key_here"
```

This only lasts for your current terminal session. You'll need to set it again each time you open a new terminal.

### 5. Run the app

**Windows (PowerShell):**
```
$env:FLASK_APP="app.py"
python -m flask run
```

**macOS/Linux:**
```
export FLASK_APP=app.py
flask run
```

Then open **http://127.0.0.1:5000** in your browser.

## About This Project

I wanted real practice with two things I hadn't done much of before: building a web app from scratch in Python, and dealing with actual user accounts, logins, passwords, sessions, instead of scripts that only I ever touch. A stock trading simulator forces you into a real database, a real external API, and logic that actually has to be correct (balances, transactions, validation), not something purely cosmetic.

This started as a project for Harvard's CS50 course. I came back to it later to fix bugs I found in my own original code and to migrate it off a price API that no longer exists, both of which I get into below. But the bigger reason I'm including it here is what it led to. Once I actually understood how to structure a Flask app, handle a database properly, and wire up an external API, I went and built something of my own: an app that automates construction cost estimates for calculistas in Mexico, where a lot of that work still gets done by hand. This project is where that ability came from.

## Features

- User registration and login with hashed passwords and session-based authentication
- Real-time(ish) stock quote lookups via an external API
- Buying and selling shares, with cash balance tracked per user
- A running portfolio view showing current holdings, current value, and total net worth

## Design & Technical Decisions

**Transaction ledger instead of a mutable holdings table.** Rather than storing "user X owns Y shares of Z" as a single row that gets updated in place, every buy and sell is stored as its own row in a `transactions` table (positive shares for a buy, negative for a sell). Current holdings are derived on the fly with `SUM(shares) ... GROUP BY symbol HAVING SUM(shares) > 0`. This keeps a full audit trail of every trade for free, and it's the same pattern real accounting and trading systems use for exactly this reason.

**Parameterized SQL throughout.** Every query uses placeholders (`:id`, `?`) rather than string-formatting user input directly into SQL, which is what prevents SQL injection.

**Session-based auth with hashed passwords.** Passwords are hashed with Werkzeug's `generate_password_hash`/`check_password_hash` rather than stored in plain text, and routes that require login are protected with a `login_required` decorator rather than repeating the same check in every function.

**Migrating off IEX Cloud to Alpha Vantage.** This project used to rely on IEX Cloud for stock price data. IEX Cloud shut down permanently in August 2024, which meant the app's core feature, looking up a real stock price, simply stopped working. I rewrote `lookup()` in `helpers.py` to use Alpha Vantage's `GLOBAL_QUOTE` endpoint instead. This came with its own tradeoff: Alpha Vantage's free tier doesn't return a company name with a quote the way IEX did, only ticker/price/volume data. Fetching the company name separately would cost a second API call per lookup, and the free tier is capped at 25 requests/day, so I chose to just display the ticker symbol instead of spending twice the quota on a cosmetic detail.

**Plain-text error pages instead of external images.** The original `apology()` error handler built a custom meme image via a third-party service (memegen.link) for every error. I replaced this with a simple styled text message, removing an external network dependency from the error path, which is the one place in an app where you least want something else to be able to fail.

## Known Limitations / What I'd Build Next

- **Transaction history isn't implemented yet.** The `/history` route is a stub. I'd build it as a simple query against the `transactions` table, ordered by timestamp, showing each buy/sell with its symbol, share count, price, and date.
- **Alpha Vantage's free tier is rate-limited** (25 requests/day, 5/minute), a real constraint for a live demo. The app doesn't currently do any caching to reduce redundant lookups, which would be the natural next step if this were going into real use.
- **No company names in quotes**, as explained above, a tradeoff made to conserve API quota rather than a technical limitation.

## Project Structure

```
finance/
├── app.py                 # Routes and application logic
├── helpers.py              # apology(), login_required(), lookup(), usd()
├── requirements.txt        # Python dependencies
├── static/                 # CSS
└── templates/               # HTML templates (Jinja2)
```

## Acknowledgments

The base structure of this project, some starter templates and helper functions, originated from Harvard's CS50x course. Since then, I've rewritten the price-lookup integration to use a different API entirely, fixed several logic bugs in the buy/sell flow, and reworked the error-handling page to remove an external dependency. The application logic, the database design, and everything under Design & Technical Decisions above are my own work.
