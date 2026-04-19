import math
import json
import requests
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Iron men locations - Rajapalayam area
iron_men = [
    {"name": "Rajapalayam Bus Stand", "lat": 9.42724, "lon": 77.53035},
    {"name": "Rajapalayam Railway Station", "lat": 9.4248, "lon": 77.5530},
    {"name": "Government Hospital Rajapalayam", "lat": 9.4510, "lon": 77.5600},
    {"name": "PACR Area", "lat": 9.4342, "lon": 77.5676},
    {"name": "Rajapalayam Town Center", "lat": 9.45296, "lon": 77.55556}
]

PRICE_PER_SHIRT = 15
DELIVERY_PER_KM = 10

# Telegram config
TELEGRAM_BOT_TOKEN = "YOUR_NEW_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"


def load_orders():
    orders = []
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    orders.append(json.loads(line))
    except FileNotFoundError:
        pass
    return orders


def save_orders(orders):
    with open("orders.json", "w", encoding="utf-8") as f:
        for order in orders:
            f.write(json.dumps(order, ensure_ascii=False) + "\n")


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)

    a = (
        math.sin(dLat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dLon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearest_ironman(user_lat, user_lon):
    nearest = None
    min_distance = float("inf")

    for person in iron_men:
        dist = calculate_distance(user_lat, user_lon, person["lat"], person["lon"])
        if dist < min_distance:
            min_distance = dist
            nearest = person

    return nearest, min_distance


def send_telegram_message(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        }
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram Error:", e)


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            shirts = int(request.form["shirts"])
            user_lat = float(request.form["lat"])
            user_lon = float(request.form["lon"])
        except (ValueError, KeyError):
            return "Invalid input. Please allow location and enter valid details."

        nearest_person, distance = find_nearest_ironman(user_lat, user_lon)

        # Delivery charge cap = ₹50 max
        delivery_charge = min(round(distance * DELIVERY_PER_KM, 2), 50)
        total_price = (shirts * PRICE_PER_SHIRT) + delivery_charge

        orders = load_orders()

        data = {
            "id": len(orders) + 1,
            "name": request.form["name"],
            "phone": request.form["phone"],
            "address": request.form["address"],
            "shirts": shirts,
            "distance": round(distance, 2),
            "delivery_charge": round(delivery_charge, 2),
            "total_price": round(total_price, 2),
            "status": "Order Placed",
            "assigned_to": nearest_person["name"],
            "payment_status": "Pending"
        }

        orders.append(data)
        save_orders(orders)

        # Telegram notification
        admin_message = f"""📦 New Order!

Customer: {data['name']}
Phone: {data['phone']}
Address: {data['address']}
Shirts: {data['shirts']}
Assigned To: {data['assigned_to']}
Distance: {data['distance']} KM
Delivery Charge: ₹{data['delivery_charge']}
Total: ₹{data['total_price']}
Payment: {data['payment_status']}
"""
        send_telegram_message(admin_message)

        return redirect(f"/payment/{data['id']}")

    return render_template("index.html")


@app.route("/admin")
def admin():
    orders = load_orders()
    return render_template("admin.html", orders=orders)


@app.route("/payment/<int:order_id>")
def payment(order_id):
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            return render_template(
                "payment.html",
                total_price=order["total_price"],
                order_id=order["id"]
            )

    return "Order not found"


@app.route("/update_payment/<int:order_id>")
def update_payment(order_id):
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            order["payment_status"] = "Paid"

            payment_message = f"""💳 Payment Update

Customer: {order['name']}
Order ID: {order['id']}
Payment Status: {order['payment_status']}
Total: ₹{order['total_price']}
"""
            send_telegram_message(payment_message)
            break

    save_orders(orders)
    return redirect("/admin")


@app.route("/update_status/<int:order_id>/<status>")
def update_status(order_id, status):
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            order["status"] = status

            status_message = f"""📦 Order Update

Status: {order['status']}
Customer: {order['name']}
Assigned To: {order['assigned_to']}
Payment: {order.get('payment_status', 'Pending')}
"""
            send_telegram_message(status_message)
            break

    save_orders(orders)
    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)
