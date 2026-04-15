import math
from flask import Flask, render_template, request, redirect
import json

app = Flask(__name__)

# 🔹 Iron men locations
iron_men = [
    {"name": "Ravi", "lat": 9.9252, "lon": 78.1198},
    {"name": "Kumar", "lat": 9.9300, "lon": 78.1300},
    {"name": "Suresh", "lat": 9.9200, "lon": 78.1100}
]

PRICE_PER_SHIRT = 15
DELIVERY_PER_KM = 10


# 🔹 Load orders
def load_orders():
    orders = []
    try:
        with open("orders.json", "r") as f:
            for line in f:
                orders.append(json.loads(line))
    except:
        pass
    return orders


# 🔹 Save orders
def save_orders(orders):
    with open("orders.json", "w") as f:
        for order in orders:
            f.write(json.dumps(order) + "\n")


# 🔹 Distance calculation
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)

    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dLon/2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


# 🔹 Find nearest iron man
def find_nearest_ironman(user_lat, user_lon):
    nearest = None
    min_distance = float('inf')

    for person in iron_men:
        dist = calculate_distance(user_lat, user_lon, person["lat"], person["lon"])

        if dist < min_distance:
            min_distance = dist
            nearest = person

    return nearest, min_distance


# 🔹 Customer Page
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":

        shirts = int(request.form["shirts"])

        # 🔥 Get user location (from HTML hidden inputs)
        user_lat = float(request.form["lat"])
        user_lon = float(request.form["lon"])

        # 🔥 Find nearest iron man
        nearest_person, distance = find_nearest_ironman(user_lat, user_lon)

        total_price = (shirts * PRICE_PER_SHIRT) + (distance * DELIVERY_PER_KM)

        data = {
            "id": len(load_orders()) + 1,
            "name": request.form["name"],
            "phone": request.form["phone"],
            "address": request.form["address"],
            "shirts": shirts,
            "distance": round(distance, 2),
            "total_price": round(total_price, 2),
            "status": "Order Placed",
            "assigned_to": nearest_person["name"]
        }

        orders = load_orders()
        orders.append(data)

from twilio.rest import Client

client = Client("ACCOUNT_SID", "AUTH_TOKEN")

message = client.messages.create(
    from_='whatsapp:+14155238886',
    body=f"📦 New Order!\nCustomer: {data['name']}\nAssigned: {data['assigned_to']}",
    to='whatsapp:+91XXXXXXXXXX'
)

return f"✅ Order placed! Assigned to {nearest_person['name']} | ₹{round(total_price,2)}"

        return f"✅ Order placed! Assigned to {nearest_person['name']} | ₹{total_price}"

    return render_template("index.html")


# 🔹 Admin Dashboard
@app.route("/admin")
def admin():
    orders = load_orders()
    return render_template("admin.html", orders=orders)


# 🔹 Update Status
@app.route("/update_status/<int:order_id>/<status>")
def update_status(order_id, status):
    orders = load_orders()

    for order in orders:
        if order["id"] == order_id:
            order["status"] = status

    save_orders(orders)
    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)