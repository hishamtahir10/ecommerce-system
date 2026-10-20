
# E-Commerce Order Processing System
# Python Intern Real-World Assessment

products = {
    "P001": {
        "name": "Laptop",
        "price": 1200,
        "category": "Electronics",
        "stock": 10
    },
    "P002": {
        "name": "Mouse",
        "price": 25,
        "category": "Accessories",
        "stock": 50
    },
    "P003": {
        "name": "Keyboard",
        "price": 75,
        "category": "Accessories",
        "stock": 20
    },
    "P004": {
        "name": "Monitor",
        "price": 300,
        "category": "Electronics",
        "stock": 15
    }
}


orders = [
    {
        "order_id": "ORD001",
        "customer": "Ali",
        "items": [
            {"product_id": "P001", "quantity": 1},
            {"product_id": "P002", "quantity": 2}
        ],
        "payment_status": "paid"
    },
    {
        "order_id": "ORD002",
        "customer": "Ahmed",
        "items": [
            {"product_id": "P003", "quantity": 2},
            {"product_id": "P004", "quantity": 1}
        ],
        "payment_status": "paid"
    },
    {
        "order_id": "ORD003",
        "customer": "Ali",
        "items": [
            {"product_id": "P002", "quantity": 5}
        ],
        "payment_status": "pending"
    }
]


def calculate_order_subtotal(order, products):
    subtotal = 0

    for item in order.get("items", []):
        product_id = item["product_id"]
        quantity = item["quantity"]

        subtotal += products[product_id]["price"] * quantity

    return subtotal


def calculate_discount(subtotal):
    if subtotal >= 1000:
        discount_rate = 0.15
    elif subtotal >= 500:
        discount_rate = 0.10
    elif subtotal >= 200:
        discount_rate = 0.05
    else:
        discount_rate = 0

    return round(subtotal * discount_rate, 2)


# -------------------- SHIPPING FUNCTION --------------------

def calculate_shipping(subtotal):
    if subtotal >= 500:
        return 0
    else:
        return 20


# -------------------- VALIDATION FUNCTION --------------------

def validate_order(order, products, reserved_stock=None):

    if not isinstance(order, dict):
        return False, "Invalid order format"

    if not products:
        return False, "Products dictionary is empty"

    if not order.get("order_id"):
        return False, "Missing order ID"

    if not order.get("customer"):
        return False, "Missing customer name"

    if order.get("payment_status") not in ["paid", "pending"]:
        return False, "Invalid payment status"

    items = order.get("items")

    if not isinstance(items, list) or len(items) == 0:
        return False, "Order contains no items"

    reserved_stock = reserved_stock or {}
    requested_quantities = {}

    for item in items:

        if not isinstance(item, dict):
            return False, "Invalid item format"

        product_id = item.get("product_id")
        quantity = item.get("quantity")

        if product_id not in products:
            return False, f"Unknown product ID: {product_id}"

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity <= 0
        ):
            return False, f"Invalid quantity for {product_id}"

        product = products[product_id]

        if not isinstance(product.get("price"), (int, float)):
            return False, f"Invalid price for {product_id}"

        if product["price"] < 0:
            return False, f"Invalid price for {product_id}"

        stock = product.get("stock")

        if not isinstance(stock, int) or stock < 0:
            return False, f"Invalid stock for {product_id}"

        requested_quantities[product_id] = (
            requested_quantities.get(product_id, 0) + quantity
        )

    # Check stock for paid orders.
    if order["payment_status"] == "paid":

        for product_id, quantity in requested_quantities.items():

            available_stock = (
                products[product_id]["stock"]
                - reserved_stock.get(product_id, 0)
            )

            if quantity > available_stock:
                return False, f"Insufficient stock for {product_id}"

    return True, "Order is valid"


# -------------------- PROCESS ORDER FUNCTION --------------------

def process_order(order, products, *args, **kwargs):

    include_shipping = kwargs.get("include_shipping", True)
    apply_discount = kwargs.get("apply_discount", True)

    result = {
        "order_id": order.get("order_id", "UNKNOWN")
        if isinstance(order, dict) else "UNKNOWN",
        "customer": order.get("customer", "Unknown")
        if isinstance(order, dict) else "Unknown",
        "payment_status": order.get("payment_status", "invalid")
        if isinstance(order, dict) else "invalid",
        "status": "rejected",
        "message": "",
        "subtotal": 0,
        "discount": 0,
        "shipping": 0,
        "total": 0,
        "items": []
    }

    valid, message = validate_order(order, products)

    if not valid:
        result["message"] = message
        return result

    subtotal = calculate_order_subtotal(order, products)

    if apply_discount:
        discount = calculate_discount(subtotal)
    else:
        discount = 0

    if include_shipping:
        shipping = calculate_shipping(subtotal)
    else:
        shipping = 0

    total = subtotal - discount + shipping

    result["subtotal"] = subtotal
    result["discount"] = discount
    result["shipping"] = shipping
    result["total"] = round(total, 2)

    result["items"] = [
        {
            "product_id": item["product_id"],
            "product_name": products[item["product_id"]]["name"],
            "quantity": item["quantity"],
            "line_total": (
                products[item["product_id"]]["price"]
                * item["quantity"]
            )
        }
        for item in order["items"]
    ]

    # Pending orders do not change inventory.
    if order["payment_status"] == "pending":
        result["status"] = "pending"
        result["message"] = "Payment is pending"
        return result

    # Reduce stock only for successfully processed paid orders.
    for item in order["items"]:
        product_id = item["product_id"]
        products[product_id]["stock"] -= item["quantity"]

    result["status"] = "paid"
    result["message"] = "Order processed successfully"

    return result


# -------------------- CUSTOMER REPORT --------------------

def generate_customer_report(processed_orders):

    customer_totals = {}

    for order in processed_orders:

        if order["status"] == "paid":

            customer = order["customer"]

            customer_totals[customer] = (
                customer_totals.get(customer, 0) + order["total"]
            )

    if not customer_totals:
        return {
            "top_customer": "N/A",
            "customer_totals": {}
        }

    ranked_customers = sorted(
        customer_totals.items(),
        key=lambda item: (-item[1], item[0])
    )

    return {
        "top_customer": ranked_customers[0][0],
        "customer_totals": customer_totals
    }


# -------------------- PRODUCT REPORT --------------------

def generate_product_report(processed_orders, products):

    quantities_sold = {
        product_id: 0
        for product_id in products
    }

    for order in processed_orders:

        if order["status"] == "paid":

            for item in order["items"]:

                product_id = item["product_id"]

                quantities_sold[product_id] = (
                    quantities_sold.get(product_id, 0)
                    + item["quantity"]
                )

    if not quantities_sold:
        top_products = []

    else:
        highest_quantity = max(
            quantities_sold.values(),
            default=0
        )

        if highest_quantity == 0:
            top_products = []
        else:
            top_products = [
                products[product_id]["name"]
                for product_id, quantity in quantities_sold.items()
                if quantity == highest_quantity
            ]

    # Products with stock of 5 or less are considered low-stock.
    low_stock_products = [
        product["name"]
        for product in products.values()
        if product["stock"] <= 5
    ]

    unique_categories = {
        product["category"]
        for product in products.values()
    }

    return {
        "quantities_sold": quantities_sold,
        "top_products": top_products,
        "low_stock_products": low_stock_products,
        "unique_categories": unique_categories
    }


# -------------------- SALES REPORT --------------------

def generate_sales_report(processed_orders, products):

    total_orders = len(processed_orders)

    paid_orders = [
        order for order in processed_orders
        if order["status"] == "paid"
    ]

    pending_orders = [
        order for order in processed_orders
        if order["status"] == "pending"
    ]

    rejected_orders = [
        order for order in processed_orders
        if order["status"] == "rejected"
    ]

    total_revenue = sum(
        order["total"] for order in paid_orders
    )

    total_discount = sum(
        order["discount"] for order in paid_orders
    )

    total_shipping = sum(
        order["shipping"] for order in paid_orders
    )

    customer_report = generate_customer_report(processed_orders)

    product_report = generate_product_report(
        processed_orders, products
    )

    print("\n========== SALES REPORT ==========")

    print(f"Total Orders: {total_orders}")
    print(f"Paid Orders: {len(paid_orders)}")
    print(f"Pending Orders: {len(pending_orders)}")
    print(f"Rejected Orders: {len(rejected_orders)}")

    print(f"Total Revenue: ${total_revenue:.2f}")
    print(f"Total Discount: ${total_discount:.2f}")
    print(f"Total Shipping: ${total_shipping:.2f}")

    print(f"Top Customer: {customer_report['top_customer']}")

    if product_report["top_products"]:
        print(
            "Top Selling Product(s): "
            + ", ".join(product_report["top_products"])
        )
    else:
        print("Top Selling Product(s): N/A")

    print("Low Stock Products:")

    if product_report["low_stock_products"]:
        for product_name in product_report["low_stock_products"]:
            print(f"- {product_name}")
    else:
        print("- None")

    print("==================================")


# -------------------- MAIN FUNCTION --------------------

def main(orders, products):

    processed_orders = []
    reserved_stock = {}

    for order in orders:

        valid, message = validate_order(
            order, products, reserved_stock
        )

        if not valid:

            result = {
                "order_id": order.get("order_id", "UNKNOWN"),
                "customer": order.get("customer", "Unknown"),
                "payment_status": order.get("payment_status", "invalid"),
                "status": "rejected",
                "message": message,
                "subtotal": 0,
                "discount": 0,
                "shipping": 0,
                "total": 0,
                "items": []
            }

        else:

            result = process_order(
                order,
                products,
                "standard order",
                include_shipping=True,
                apply_discount=True
            )

            # Track stock allocated to successful paid orders.
            if result["status"] == "paid":

                for item in order["items"]:

                    product_id = item["product_id"]

                    reserved_stock[product_id] = (
                        reserved_stock.get(product_id, 0)
                        + item["quantity"]
                    )

        processed_orders.append(result)

        print(
            f"{result['order_id']}: "
            f"{result['status'].upper()} - "
            f"{result['message']}"
        )

    generate_sales_report(processed_orders, products)

    return processed_orders


# -------------------- RUN PROGRAM --------------------

if __name__ == "__main__":
    main(orders, products)