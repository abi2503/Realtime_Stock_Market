import yfinance as yf
from flask import request, render_template, jsonify, Flask,redirect,url_for


app = Flask(__name__, template_folder='templates')






@app.route('/')
def index():
    return render_template('index.html')


# Sample portfolio data (replace this with your actual data)
portfolio_data = []

@app.route('/sell/<ticker>', methods=['GET'])
def Sell_Stock(ticker):
    stock = yf.Ticker(ticker)
    
    try:
        data = stock.history(period='1d')
        if data.empty:
            raise ValueError("No data available for the specified ticker: " + ticker)

        current_price = data['Close'].iloc[-1] if 'Close' in data else 'N/A'
        open_price = data['Open'].iloc[-1] if 'Open' in data else 'N/A'
        previous_close = data['Close'].iloc[-1] if 'Close' in data else 'N/A'

        info = stock.info
        context = {
            'ticker': ticker.upper(),
            'currentPrice': current_price,
            'openPrice': open_price,
            'previousClose': previous_close,
            'marketCap': info.get('marketCap', 'N/A'),
            'logo_url': info.get('logo_url', '/static/default-logo.png'),
            'companyName': info.get('shortName', ticker),
            'sector': info.get('sector', 'N/A'),
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(context)  # Return JSON if it's an AJAX request

         
        return render_template('Sell_Stock.html', **context)

    except ValueError as ve:
        print(f"ValueError: {ve}")
        return render_template('error.html', error=str(ve))
    except Exception as e:
        print(f"Unexpected error: {e}")
        return render_template('error.html', error="An unexpected error occurred, please try again later.")

@app.route('/buy/<ticker>', methods=['GET'])
def Buy_Stock(ticker):
    stock = yf.Ticker(ticker)
    
    try:
        data = stock.history(period='1d')
        if data.empty:
            raise ValueError("No data available for the specified ticker: " + ticker)

        current_price = data['Close'].iloc[-1] if 'Close' in data else 'N/A'
        open_price = data['Open'].iloc[-1] if 'Open' in data else 'N/A'
        previous_close = data['Close'].iloc[-1] if 'Close' in data else 'N/A'

        info = stock.info
        context = {
            'ticker': ticker.upper(),
            'currentPrice': current_price,
            'openPrice': open_price,
            'previousClose': previous_close,
            'marketCap': info.get('marketCap', 'N/A'),
            'logo_url': info.get('logo_url', '/static/default-logo.png'),
            'companyName': info.get('shortName', ticker),
            'sector': info.get('sector', 'N/A'),
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(context)  # Return JSON if it's an AJAX request

         # Assuming you have a template named 'buy.html' in your 'templates' folder
        return render_template('Buy_Stock.html', **context)

    except ValueError as ve:
        print(f"ValueError: {ve}")
        return render_template('error.html', error=str(ve))
    except Exception as e:
        print(f"Unexpected error: {e}")
        return render_template('error.html', error="An unexpected error occurred, please try again later.")

@app.route('/add_to_portfolio', methods=['POST'])
def add_to_portfolio():
    if request.method == 'POST':
        ticker = request.form['ticker']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])

    # Check if the stock already exists in the portfolio
    stock_exists = False
    for stock in portfolio_data:
        if stock['ticker'] == ticker:
            stock_exists = True
            prev_quantity = stock['quantity']
            stock['quantity'] += quantity
            stock['average_price'] = round((prev_quantity * stock['average_price'] + quantity * price) / stock['quantity'],2)
            val=price * quantity
            stock['Cost_Basis'] += round(val,2)
            break

    # If the stock doesn't exist, add it to the portfolio
    if not stock_exists:
        val=price * quantity
        portfolio_data.append({
            'ticker': ticker,
            'quantity': quantity,
            'Cost_Basis': round(val,2),
            'average_price': round(price,2)
        })

    # Redirect back to the portfolio page after adding the stock
    return redirect(url_for('portfolio'))

@app.route('/remove_from_portfolio', methods=['POST'])
def remove_from_portfolio():
    if request.method == 'POST':
        ticker = request.form['ticker']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        
        # Check if the stock exists in the portfolio
        stock_index = None
        for i, stock in enumerate(portfolio_data):
            if stock['ticker'] == ticker:
                stock_index = i
                break
        
        if stock_index is None:
            return "Cannot execute sell order: Stock is not in the portfolio"
        
        # Check if the quantity to sell is greater than available quantity
        if quantity > portfolio_data[stock_index]['quantity']:
            return "Cannot execute sell order: Quantity to sell exceeds available quantity"
        
        # If the quantity to sell matches the available quantity, delete the item from the table
        if quantity == portfolio_data[stock_index]['quantity']:
            del portfolio_data[stock_index]
        else:
            # Reduce the quantity and update the average price
            prev_quantity = portfolio_data[stock_index]['quantity']
            portfolio_data[stock_index]['quantity'] -= quantity
            portfolio_data[stock_index]['average_price'] = round(((prev_quantity * portfolio_data[stock_index]['average_price']) - (quantity * price)) / portfolio_data[stock_index]['quantity'], 2)
            portfolio_data[stock_index]['Cost_Basis'] = round(portfolio_data[stock_index]['Cost_Basis'] - (price * quantity), 2)
        
    # Redirect back to the portfolio page after selling the stock
    return redirect(url_for('portfolio'))


@app.route('/portfolio')
def portfolio():
  
    return render_template('portfolio.html', portfolio_data=portfolio_data)
    #return portfolio_data
@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    data = request.get_json()
    ticker = data.get('ticker')
    if ticker:  # Ensure that ticker is not an empty string
        stock = yf.Ticker(ticker)
        try:
            # Fetch data, if available
            data = stock.history(period='1y')
            if data.empty:
                raise ValueError('No data available for this ticker.')
            
            # Send the response with the needed data
            return jsonify({
                'currentPrice': data.iloc[-1].Close,
                'openPrice': data.iloc[-1].Open
            })
        except Exception as e:
            # Log the error and send a response indicating failure
            print(f"Error fetching data for {ticker}: {e}")
            response = jsonify({
                'error': 'Could not retrieve stock data.',
                'details': str(e)
            })
            response.status_code = 500
            return response
    else:
        # Handle the case where no ticker is provided
        return jsonify({'error': 'No ticker symbol provided'}), 400

@app.route('/stock/<ticker>', methods=['GET'])
def stock_detail(ticker):
    stock = yf.Ticker(ticker)
    
    try:
        data = stock.history(period='1d')
        if data.empty:
            raise ValueError("No data available for the specified ticker: " + ticker)

        current_price = data['Close'].iloc[-1] if 'Close' in data else 'N/A'
        open_price = data['Open'].iloc[-1] if 'Open' in data else 'N/A'
        previous_close = data['Close'].iloc[-1] if 'Close' in data else 'N/A'

        info = stock.info
        context = {
            'ticker': ticker.upper(),
            'currentPrice': current_price,
            'openPrice': open_price,
            'previousClose': previous_close,
            'marketCap': info.get('marketCap', 'N/A'),
            'logo_url': info.get('logo_url', '/static/default-logo.png'),
            'companyName': info.get('shortName', ticker),
            'sector': info.get('sector', 'N/A'),
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(context)  # Return JSON if it's an AJAX request

        return render_template('stock_detail.html', **context)

    except ValueError as ve:
        print(f"ValueError: {ve}")
        return render_template('error.html', error=str(ve))
    except Exception as e:
        print(f"Unexpected error: {e}")
        return render_template('error.html', error="An unexpected error occurred, please try again later.")




if __name__ == '__main__':
    app.run(debug=True)
