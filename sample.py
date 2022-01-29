import stripe
from flask import *

stripe_keys = {
  'secret_key': 'sk_test_51KNC34FNBNxpmKdvci0jGDT7KLMzkO0nt8ihmUYltHZZ1pDs6qWaR8XdDVvlobpCxXvYL7mwaPjvqyrNojaS4LKe00WXZZjtFM',
  'publishable_key': 'pk_test_51KNC34FNBNxpmKdv9xNRrTuitoi8r6ZA2Yx0SNCUT9Smi5t2bFn4ZfCqTxcSd2VMzwf1typaxdjuvhbLX16jsKqM00N7zb5ZBR',
}

stripe.api_key = stripe_keys['secret_key']

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', key=stripe_keys['publishable_key'])

@app.route('/charge', methods=['POST'])
def charge():
    # Amount in cents
    amount = 500

    customer = stripe.Customer.create(
        email='2landadvanture@gmail.com',
        source=request.form['stripeToken']
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='usd',
        description='Flask Charge'
    )
    print('Done')

    return render_template('charge.html', amount=amount)

if __name__ == '__main__':
    app.run(debug=True)