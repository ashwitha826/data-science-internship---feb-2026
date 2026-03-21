from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field
import math

app = FastAPI()

# -------------------- DATA --------------------

menu = [
    {"id": 1, "name": "Pizza", "price": 350, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Burger", "price": 150, "category": "Burger", "is_available": True},
    {"id": 3, "name": "Chicken briyani", "price": 200, "category": "Briyani", "is_available": False},
    {"id": 4, "name": "Thumbup", "price": 100, "category": "Drink", "is_available": True},
    {"id": 5, "name": "Cake", "price": 250, "category": "Dessert", "is_available": True},
    {"id": 6, "name": "Pasta", "price": 149, "category": "Pizza", "is_available": False}
]

orders = []
order_counter = 1
cart = []

# -------------------- HELPERS --------------------

def find_menu_item(item_id):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None


def calculate_bill(price, quantity, order_type="delivery"):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total


def filter_menu_logic(category=None, max_price=None, is_available=None):
    result = menu
    if category is not None:
        result = [i for i in result if i["category"].lower() == category.lower()]
    if max_price is not None:
        result = [i for i in result if i["price"] <= max_price]
    if is_available is not None:
        result = [i for i in result if i["is_available"] == is_available]
    return result


# -------------------- MODELS --------------------

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=10)
    order_type: str = "delivery"


class NewMenuItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    is_available: bool = True


class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# -------------------- DAY 1 --------------------

@app.get("/")
def home():
    return {"message": "Welcome to QuickBite Food Delivery"}


@app.get("/menu")
def get_menu():
    return {"total": len(menu), "menu": menu}


@app.get("/menu/summary")
def menu_summary():
    total = len(menu)
    available = sum(1 for i in menu if i["is_available"])
    categories = list(set(i["category"] for i in menu))

    return {
        "total": total,
        "available": available,
        "unavailable": total - available,
        "categories": categories
    }

#  STATIC ROUTES FIRST

@app.get("/menu/filter")
def filter_menu(category: str = None, max_price: int = None, is_available: bool = None):
    filtered = filter_menu_logic(category, max_price, is_available)
    return {"count": len(filtered), "items": filtered}


@app.get("/menu/search")
def search_menu(keyword: str):
    result = [i for i in menu if keyword.lower() in i["name"].lower() or keyword.lower() in i["category"].lower()]
    if not result:
        return {"message": "No items found"}
    return {"count": len(result), "items": result}


@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "category"]:
        return {"error": "Invalid sort field"}
    reverse = True if order == "desc" else False
    sorted_data = sorted(menu, key=lambda x: x[sort_by], reverse=reverse)
    return {"sorted_by": sort_by, "order": order, "items": sorted_data}


@app.get("/menu/page")
def paginate(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    total = len(menu)
    total_pages = math.ceil(total / limit)
    return {
        "page": page,
        "total_pages": total_pages,
        "items": menu[start:start + limit]
    }

 

@app.get("/menu/browse")
def browse(
    keyword: str = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    result = menu
    if keyword:
        result = [i for i in result if keyword.lower() in i["name"].lower()]
    reverse = True if order == "desc" else False
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)
    start = (page - 1) * limit
    total = len(result)
    return {
        "total": total,
        "page": page,
        "items": result[start:start + limit]
    }

 
@app.get("/menu/{item_id}")
def get_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        return {"error": "Item not found"}
    return item


@app.get("/orders")
def get_orders():
    return {"total_orders": len(orders), "orders": orders}


# -------------------- DAY 2 & 3 --------------------

@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter
    item = find_menu_item(order.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item["is_available"]:
        raise HTTPException(status_code=400, detail="Item not available")
    total = calculate_bill(item["price"], order.quantity, order.order_type)
    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item": item["name"],
        "quantity": order.quantity,
        "total_price": total
    }
    orders.append(new_order)
    order_counter += 1
    return new_order


# -------------------- DAY 4 --------------------

@app.post("/menu", status_code=201)
def add_menu(item: NewMenuItem):
    for i in menu:
        if i["name"].lower() == item.name.lower():
            raise HTTPException(status_code=400, detail="Duplicate item")
    new_item = item.dict()
    new_item["id"] = len(menu) + 1
    menu.append(new_item)
    return new_item


@app.put("/menu/{item_id}")
def update_menu(item_id: int, price: int = None, is_available: bool = None):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if price is not None:
        item["price"] = price
    if is_available is not None:
        item["is_available"] = is_available
    return item


@app.delete("/menu/{item_id}")
def delete_menu(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    menu.remove(item)
    return {"message": f"{item['name']} deleted"}


# -------------------- DAY 5 --------------------

@app.post("/cart/add")
def add_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)
    if not item or not item["is_available"]:
        raise HTTPException(status_code=400, detail="Invalid item")
    for c in cart:
        if c["item_id"] == item_id:
            c["quantity"] += quantity
            return {"message": "Updated cart", "cart": cart}
    cart.append({"item_id": item_id, "name": item["name"], "quantity": quantity})
    return {"message": "Added to cart", "cart": cart}


@app.get("/cart")
def view_cart():
    total = 0
    for c in cart:
        item = find_menu_item(c["item_id"])
        total += item["price"] * c["quantity"]
    return {"cart": cart, "grand_total": total}


@app.delete("/cart/{item_id}")
def remove_cart(item_id: int):
    for c in cart:
        if c["item_id"] == item_id:
            cart.remove(c)
            return {"message": "Removed"}
    return {"error": "Not found"}


@app.post("/cart/checkout", status_code=201)
def checkout(data: CheckoutRequest):
    global order_counter
    if not cart:
        raise HTTPException(status_code=400, detail="Cart empty")
    new_orders = []
    total = 0
    for c in cart:
        item = find_menu_item(c["item_id"])
        cost = item["price"] * c["quantity"]
        order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "item": item["name"],
            "quantity": c["quantity"],
            "total_price": cost
        }
        orders.append(order)
        new_orders.append(order)
        total += cost
        order_counter += 1
    cart.clear()
    return {"orders": new_orders, "grand_total": total}