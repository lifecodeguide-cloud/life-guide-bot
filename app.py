from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

# ===== НАСТРОЙКИ =====
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_API_BASE = "https://api-m.paypal.com"
PRICE = "4.99"


# ===== ГЛАВНАЯ СТРАНИЦА ОПЛАТЫ =====
@app.route("/")
def home():
    user_id = request.args.get("user_id")

    if not user_id:
        return "Ошибка: user_id не передан"

    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Оплата доступа</title>

    <script src="https://www.paypal.com/sdk/js?client-id={{ client_id }}&currency=USD"></script>
</head>

<body style="font-family:Arial; text-align:center; margin-top:50px;">

    <h1>Life Guide ✨</h1>
    <p style="font-size:20px;">
        Чтобы получить полный разбор,<br>
        оплатите доступ за <b>4.99 $</b>
    </p>

    <div id="paypal-button-container"></div>

    <script>
        const USER_ID = "{{ user_id }}";

        paypal.Buttons({

            createOrder: function(data, actions) {
                return fetch('/create-order?user_id=' + USER_ID, {
                    method: 'post'
                })
                .then(res => res.json())
                .then(data => data.id);
            },

            onApprove: function(data, actions) {
                return fetch('/capture-order?user_id=' + USER_ID, {
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
                    window.location.href = "/success?user_id=" + USER_ID;
                });
            }

        }).render('#paypal-button-container');
    </script>

</body>
</html>
    """, client_id=PAYPAL_CLIENT_ID, user_id=user_id)


# ===== PAYPAL TOKEN =====
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
    response.raise_for_status()
    return response.json()["access_token"]


# ===== СОЗДАТЬ ЗАКАЗ =====
@app.route("/create-order", methods=["POST"])
def create_order():
    user_id = request.args.get("user_id")
    access_token = get_paypal_access_token()

    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "intent": "CAPTURE",
            "application_context": {
                "return_url": f"https://life-guide-pay-2026.onrender.com/success?user_id={user_id}",
                "cancel_url": f"https://life-guide-pay-2026.onrender.com/?user_id={user_id}"
            },
            
            "purchase_units": [
                {
                    "custom_id": user_id,
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
    user_id = request.args.get("user_id")
    order_id = request.json.get("orderID")

    access_token = get_paypal_access_token()

    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )

    print("PAID USER_ID:", user_id)

    return response.json()


# ===== УСПЕХ =====
@app.route("/success")
def success():
    user_id = request.args.get("user_id")

    if not user_id:
        return "Ошибка: user_id не передан"

    return f"""
    <h1 style='font-family:Arial; text-align:center; margin-top:80px;'>
    Оплата прошла успешно ✅<br><br>
    Возвращаем вас в Telegram...
    </h1>

    <script>
    setTimeout(function() {{
        window.location.href = "https://t.me/Life_Guide?start=paid_{user_id}";
    }}, 1500);
    </script>
    """


# ===== ЗАПУСК =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
