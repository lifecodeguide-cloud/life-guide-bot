from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

# ===== НАСТРОЙКИ =====
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_API_BASE = "https://api-m.paypal.com"   # LIVE
PRICE = "4.99"


# ===== ГЛАВНАЯ СТРАНИЦА =====
@app.route("/")
def home():
    return render_template_string("""
    <!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Оплата доступа</title>
    <script src="https://www.paypal.com/sdk/js?client-id={{ client_id }}&currency=USD"></script>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f7f7f7;
            margin: 0;
            padding: 10px 10px;
            display: flex;
            justify-content: center;
        }

        .box {
            width: 100%;
            max-width: 100%;
            background: white;
            border-radius: 20px;
            padding: 20px 14px;
            margin-top: 0;
            box-shadow: none;
            text-align: center;
        }

        h1 {
            font-size: 34px;
            margin-bottom: 18px;
        }

        .text {
            font-size: 32px;
            line-height: 1.5;
            margin-bottom: 22px;
        }

        .price {
            font-weight: bold;
            font-size: 40px;
        }

        #paypal-button-container {
            margin-top: 20px;
            max-width: 420px; 
            margin-left: auto; 
            margin-right: auto;                                                              
        }

        @media (max-width: 600px) {
            .text {
                font-size: 42px;
                line-height: 1.35;                  
            }
            .price {
                font-size: 58px;
            }                                                                  
                                  
            h1 {
                font-size: 48px !impotant;
            }

           #paypal-button-container {
            max-width: 100%;
            transform: scale (1.18); 
            transform-origin: top center; 
            margin-top: 28px;
            }                                             
        }
    </style>
</head>
<body>
    <div class="box">
        <h1 style="font-size: 42px; margin-botton: 18px;">Life Guide ✨</h1>

        <div class="text">
            Чтобы получить полный разбор,<br>
            оплатите доступ за <span class="price">4.99 $</span>
        </div>

        <div id="paypal-button-container"></div>
    </div>

    <script>
        paypal.Buttons({
            createOrder: function(data, actions) {
                return fetch('/create-order', {
                    method: 'post'
                })
                .then(res => res.json())
                .then(data => data.id);
            },

            onApprove: function(data, actions) {
                return fetch('/capture-order', {
                    method: 'post',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        orderID: data.orderID
                    })
                })
                .then(res => res.json())
                .then(data => {
                    window.location.href = "/success";
                });
            }
        }).render('#paypal-button-container');
    </script>
</body>
</html>
    """, client_id=PAYPAL_CLIENT_ID)


# ===== ПОЛУЧИТЬ ACCESS TOKEN =====
def get_paypal_access_token():
    response = requests.post(
        f"{PAYPAL_API_BASE}/v1/oauth2/token",
        headers={
            "Accept": "application/json",
            "Accept-Language": "en_US"
        },
        data={"grant_type": "client_credentials"},
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    )
    return response.json()["access_token"]


# ===== СОЗДАТЬ ЗАКАЗ =====
@app.route("/create-order", methods=["POST"])
def create_order():
    access_token = get_paypal_access_token()

    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": PRICE
                    }
                }
            ]
        }
    )

    return response.json()


# ===== ПОДТВЕРДИТЬ ОПЛАТУ =====
@app.route("/capture-order", methods=["POST"])
def capture_order():
    order_id = request.json.get("orderID")
    access_token = get_paypal_access_token()

    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )

    data = response.json()
    print("PAYMENT CAPTURED:", data)

    return data


# ===== СТРАНИЦА УСПЕХА =====
@app.route("/success")
def success():
    return """
    <h1 style='font-family:Arial; text-align:center; margin-top:80px;'>
    Оплата прошла успешно ✅<br><br>
    Возвращаем вас в Telegram...
    </h1>

    <script>
    setTimeout(function() {
        window.location.href = "https://t.me/Life_Guide?start=paid";
    }, 2000);
    </script>
    """


# ===== PAYPAL WEBHOOK =====
@app.route("/paypal-webhook", methods=["POST"])
def paypal_webhook():
    data = request.json
    print("PAYPAL WEBHOOK RECEIVED:", data)
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
