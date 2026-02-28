"""
Enterprise Level Sample Data Generator
Creates 3 months realistic grocery shop data
"""
  
import sys
import os
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db.mongo_client import mongo_client

OWNER = "jadhavshubham9718@gmail.com"

CATEGORIES = [
    "Dairy", "Bakery", "Grains", "Snacks",
    "Beverages", "Personal Care", "Household",
    "Frozen", "Meat", "Groceries"
]

SUPPLIERS = [
    "Amul", "Britannia", "Parle", "Nestle",
    "ITC", "Tata", "Local Farms", "Fortune",
    "Mother Dairy", "Patanjali"
]

PRODUCT_NAMES = [
    "Milk 1L", "Bread", "Rice 5kg", "Yogurt",
    "Butter", "Paneer", "Ice Cream", "Cold Drink",
    "Sugar", "Salt", "Tea Powder", "Coffee",
    "Biscuits", "Chips", "Maggi", "Chocolate",
    "Toothpaste", "Shampoo", "Soap", "Detergent",
    "Eggs", "Chicken 1kg", "Mutton 1kg",
    "Cooking Oil", "Flour 1kg", "Wheat 10kg"
]


def generate_products(db):
    print("📦 Generating Products...")

    products = []

    for i in range(60):
        name = random.choice(PRODUCT_NAMES) + f" #{i}"
        category = random.choice(CATEGORIES)
        actual = random.randint(10, 300)
        selling = actual + random.randint(10, 100)

        expiry_days = random.randint(-10, 365)

        products.append({
            "owner": OWNER,
            "name": name,
            "category": category,
            "actualPrice": actual,
            "sellingPrice": selling,
            "quantity": random.randint(5, 200),
            "reorderLevel": random.randint(5, 30),
            "supplier": random.choice(SUPPLIERS),
            "expirationDate": datetime.now(timezone.utc) + timedelta(days=expiry_days),
            "dateAdded": datetime.now(timezone.utc),
            "dateUpdated": datetime.now(timezone.utc)
        })

    db.products.insert_many(products)
    print("✅ 60 Products Created")


def generate_customers(db):
    print("👥 Generating Customers...")

    customers = []

    for i in range(100):
        customers.append({
            "owner": OWNER,
            "customerName": f"Customer {i+1}",
            "phoneNumber": f"9{random.randint(100000000, 999999999)}",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        })

    db.customers.insert_many(customers)
    print("✅ 100 Customers Created")


def generate_suppliers(db):
    print("🏭 Generating Suppliers...")

    suppliers = []

    for name in SUPPLIERS:
        suppliers.append({
            "owner": OWNER,
            "supplierName": name,
            "totalPayment": random.randint(50000, 500000),
            "depositAmount": random.randint(10000, 100000),
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        })

    db.suppliers.insert_many(suppliers)
    print("✅ Suppliers Created")


def generate_bills(db):
    print("🧾 Generating 90 Days Bills...")

    products = list(db.products.find({"owner": OWNER}))
    customers = list(db.customers.find({"owner": OWNER}))

    bills = []
    now = datetime.now(timezone.utc)

    for day in range(90):
        bill_date = now - timedelta(days=day)

        for _ in range(random.randint(8, 15)):  # daily 8-15 bills
            items = []
            total = 0

            for _ in range(random.randint(1, 5)):
                product = random.choice(products)
                qty = random.randint(1, 4)
                line_total = product["sellingPrice"] * qty
                total += line_total

                items.append({
                    "productName": product["name"],
                    "quantity": qty,
                    "price": product["sellingPrice"],
                    "total": line_total
                })

            bills.append({
                "owner": OWNER,
                "customerName": random.choice(customers)["customerName"],
                "billNumber": f"BILL-{bill_date.strftime('%Y%m%d')}-{random.randint(1000,9999)}",
                "date": bill_date,
                "items": items,
                "grandTotal": total
            })

    db.bills.insert_many(bills)
    print(f"✅ {len(bills)} Bills Created (90 Days)")


def insert_sample_data():
    mongo_client.connect()
    db = mongo_client.db

    print("\n⚠ Clearing Old Data...")
    db.products.delete_many({"owner": OWNER})
    db.bills.delete_many({"owner": OWNER})
    db.suppliers.delete_many({"owner": OWNER})
    db.customers.delete_many({"owner": OWNER})

    generate_products(db)
    generate_customers(db)
    generate_suppliers(db)
    generate_bills(db)

    print("\n🎉 FULL ENTERPRISE DATA READY!")
    print("Now run: streamlit run app.py\n")


if __name__ == "__main__":
    insert_sample_data()