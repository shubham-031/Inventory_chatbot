from datetime import datetime, timezone, timedelta

OWNER = "jadhavshubham9718@gmail.com"

def get_expiring_products(db, days=30):
    """
    Returns products expiring within next X days
    """

    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=days)

    products = list(db.products.find({
        "owner": OWNER,
        "expirationDate": {
            "$gte": now,
            "$lte": future_date
        }
    }))

    if not products:
        return "✅ No products expiring in next 30 days."

    response = "⏳ Products Expiring Soon:\n\n"

    for product in products:
        days_left = (product["expirationDate"] - now).days
        response += (
            f"• {product['name']} \n"
            f"  Category: {product['category']}\n"
            f"  Quantity: {product['quantity']}\n"
            f"  Expires in: {days_left} days\n\n"
        )

    return response