import math
import json
from flask import Flask, render_template, request, redirect
from twilio.rest import Client

app = Flask(__name__)

# Iron men locations
iron_men = [
    {"name": "Rajapalayam Bus Stand", "lat": 9.42724, "lon": 77.53035},
    {"name": "Rajapalayam Railway Station", "lat": 9.4248, "lon": 77.5530},
    {"name": "Government Hospital Rajapalayam", "lat": 9.4510, "lon": 77.5600},
    {"name": "PACR Area", "lat": 9.4342, "lon": 77.5676},
    {"name": "Rajapalayam Town Center", "lat": 9.45296, "lon": 77.55556}
]

PRICE_PER_SHIRT = 15
DELIVERY_PER_KM = 10

# Twilio config
ACCOUNT_SID = "ACea2318dc8015a889ced5588acc1093a6"
AUTH_TOKEN = "ad7977430cb5b7424736af627cf76133"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
ADMIN_WHATSAPP_NUMBER = "whatsapp:+918248005899"


def load_orders():
    orders = []
    try:
        with open("orders.json", "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    orders.append(json.loads(line))
    except FileNotFoundError:
        pass
    return orders


def save_orders(orders):
    with open("orders.json", "w") as f:
        for order in orders:
            f.write(json.dumps(order) + "\n")


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


def send_whatsapp_message(body, to_number):
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=body,
            to=to_number
        )
    except Exception as e:
        print("WhatsApp send error:", e)


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
        total_price = (shirts * PRICE_PER_SHIRT) + (distance * DELIVERY_PER_KM)

        orders = load_orders()

        data = {
            "id": len(orders) + 1,
            "name": request.form["name"],
            "phone": request.form["phone"],
            "address": request.form["address"],
            "shirts": shirts,
            "distance": round(distance, 2),
            "total_price": round(total_price, 2),
            "status": "Order Placed",
            "assigned_to": nearest_person["name"]
        }

        orders.append(data)
        save_orders(orders)

        # Admin notification
        admin_message = f"""📦 New Order!

Customer: {data['name']}
Phone: {data['phone']}
Address: {data['address']}
Shirts: {data['shirts']}
Assigned To: {data['assigned_to']}
Distance: {data['distance']} KM
Total: ₹{data['total_price']}
"""
        send_whatsapp_message(admin_message, ADMIN_WHATSAPP_NUMBER)

        return f"✅ Order placed! Assigned to {nearest_person['name']} | ₹{round(total_price, 2)}"

    return render_template("index.html")


@app.route("/admin")
def admin():
    orders = load_orders()
    return render_template("admin.html", orders=orders)


@app.route("/update_status/<int:order_id>/<status>")
def update_status(order_id, status):
    orders = load_orders()

    for order in orders:
        if order["id"] == order_id:
            order["status"] = status

            status_message = f"""📦 Order Update

Status: {order['status']}
Customer: {order['name']}
Assigned To: {order['assigned_to']}
"""
            send_whatsapp_message(status_message, ADMIN_WHATSAPP_NUMBER)
            break

    save_orders(orders)
    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)
