import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    rows = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
    if not rows:
        return apology("Missing User")
    cash = rows[0]["cash"]
    total = cash

    stocks = db.execute("SELECT symbol, SUM(shares) AS shares FROM transactions WHERE user_id=:user_id GROUP BY symbol HAVING SUM(shares) > 0", user_id=session["user_id"])

    for stock in stocks:
        quote = lookup(stock["symbol"])
        if not quote:
            return apology(f"Could not fetch current price for {stock['symbol']}")
        stock["name"] = quote["name"]
        stock["price"] = quote["price"]
        total += stock["shares"] * quote["price"]

    return render_template("index.html", stocks=stocks, cash=cash, total=total)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Missing symbol")
        if not request.form.get("shares"):
            return apology("Missing amount")
        elif not request.form.get("shares").isdigit():
            return apology("Input is not an integer")

        shares = int(request.form.get("shares"))

        quote = lookup(request.form.get("symbol"))

        if not quote:
            return apology("No quote for such symbol")

        cost = shares * quote["price"]

        rows = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])

        if not rows:
            return apology("Missing User")

        cash = rows[0]["cash"]

        if cash < cost:
            return apology("Insufficient Funds")


        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)", user_id = session["user_id"], symbol=quote["symbol"], shares=shares, price=quote["price"])
        db.execute("UPDATE users SET cash = cash - :cost WHERE id = :id", cost=cost, id=session["user_id"])



        flash("Purchase Successful")
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Missing symbol")
        quote = lookup(request.form.get("symbol"))

        if not quote:
            return apology("No quote for such symbol")

        return render_template("quoted.html", quote=quote)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    #POST
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Missing username")
        elif not request.form.get("password"):
            return apology("Missing password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Incorrect password")

        try:
            id = db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
        except ValueError:
            return apology("Username is taken")

        session["user_id"] = id

        flash("Registered!")
        return redirect("/")
    #GET
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
            if not request.form.get("symbol"):
                return apology("Missing symbol")
            if not request.form.get("shares"):
                return apology("Missing amount")
            elif not request.form.get("shares").isdigit():
                return apology("Input is not an integer")

            shares = int(request.form.get("shares"))

            if shares <= 0:
                return apology("Shares must be positive")

            quote = lookup(request.form.get("symbol"))
            
            if not quote:
                return apology("No quote for such symbol")

            owned = db.execute(
            "SELECT SUM(shares) AS total FROM transactions WHERE user_id = :user_id AND symbol = :symbol",
            user_id=session["user_id"], symbol=quote["symbol"])
            owned_shares = owned[0]["total"] or 0

            if shares > owned_shares:
                return apology("Too many shares")

            cost = shares * quote["price"]

            rows = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])

            if not rows:
                return apology("Missing User")

            cash = rows[0]["cash"]


            db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)", user_id = session["user_id"], symbol=quote["symbol"], shares=-shares, price=quote["price"])
            db.execute("UPDATE users SET cash = cash + :cost WHERE id = :id", cost=cost, id=session["user_id"])



            flash("Sell Successful")
            return redirect("/")

    else:
        return render_template("sell.html")

