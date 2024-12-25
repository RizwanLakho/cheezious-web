import json

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import OTP, Cart, CartItem, Category, Item, Order, OrderItem

# Create your views here.


def home(request):
    return render(request, "web/home.html")


# def menu(request):
#     # Get selected category from URL parameter, if any
#     category_id = request.GET.get("category")

#     # Get all categories for the filter
#     categories = Category.objects.all()

#     # Filter items by category if selected
#     if category_id:
#         items = Item.objects.filter(category_id=category_id).select_related("category")
#     else:
#         items = Item.objects.all().select_related("category")

#     context = {
#         "items": items,
#         "categories": categories,
#         "selected_category": category_id,
#     }
#     return render(request, "web/menu.html", context)


def menu(request):
    # Get all categories and their items
    categories = Category.objects.all().prefetch_related("items")
    context = {
        "categories": categories,
    }
    return render(request, "web/menu.html", context)


def item(request):
    return render(request, "web/item.html")


def branches(request):
    return render(request, "web/branches.html")


def blog(request):
    return render(request, "web/blog.html")


def privacy(request):
    return render(request, "web/privacy.html")


def login(request):
    return render(request, "auth/login.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")

        user = authenticate(username=email, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            return redirect("home")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "auth/login_auth.html")


def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirmation = request.POST.get("password_confirmation")

        if password != password_confirmation:
            messages.error(request, "Passwords do not match.")
            return render(request, "auth/signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, "auth/signup.html")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name.split()[0],
            last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "",
        )

        login(request)
        return redirect("home")

    return render(request, "auth/signup.html")


# def get_or_create_cart(request):
#     if request.user.is_authenticated:
#         cart, created = Cart.objects.get_or_create(user=request.user)
#     else:
#         session_id = request.session.get("cart_id")
#         if session_id:
#             cart = Cart.objects.filter(session_id=session_id).first()
#             if not cart:
#                 cart = Cart.objects.create(session_id=session_id)
#         else:
#             cart = Cart.objects.create()
#             request.session["cart_id"] = cart.session_id
#     return cart


def get_or_create_cart(request):
    session_id = request.session.session_key or request.session.create()
    cart = Cart.objects.filter(session_id=session_id).first()
    if not cart:
        cart = Cart.objects.create(session_id=session_id)
    return cart


def add_to_cart(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        if not item_id:
            return JsonResponse(
                {"status": "error", "message": "No item ID provided"}, status=400
            )

        item = get_object_or_404(Item, id=item_id)
        cart = get_or_create_cart(request)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, item=item, defaults={"quantity": 1}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return JsonResponse(
            {
                "status": "success",
                "message": "Item added to cart",
                "cart_total": cart.get_total(),
                "cart_items_count": cart.items.count(),
            }
        )

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


def cart_view(request):
    cart = get_or_create_cart(request)
    context = {"cart": cart, "cart_items": cart.items.all()}
    return render(request, "web/cart.html", context)


def update_cart_item(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        action = request.POST.get("action")
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, cart=cart, item_id=item_id)

        if action == "increase":
            cart_item.quantity += 1
        elif action == "decrease":
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart_item.delete()
                return JsonResponse(
                    {
                        "status": "removed",
                        "cart_total": cart.get_total(),
                        "cart_items_count": cart.items.count(),
                    }
                )

        cart_item.save()
        return JsonResponse(
            {
                "status": "success",
                "item_total": cart_item.get_total(),
                "cart_total": cart.get_total(),
                "cart_items_count": cart.items.count(),
            }
        )

    return JsonResponse({"status": "error"}, status=400)


def remove_from_cart(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, cart=cart, item_id=item_id)
        cart_item.delete()

        return JsonResponse(
            {
                "status": "success",
                "cart_total": cart.get_total(),
                "cart_items_count": cart.items.count(),
            }
        )

    return JsonResponse({"status": "error"}, status=400)


def checkout(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        return redirect("cart")

    if request.method == "POST":
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=request.POST.get("full_name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            address=request.POST.get("address"),
            city=request.POST.get("city"),
            total_amount=cart.get_total(),
            status=Order.PENDING,
        )

        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                item=cart_item.item,
                quantity=cart_item.quantity,
                price=cart_item.item.price,
            )

        # Clear cart
        cart.items.all().delete()

        # Simulate payment success
        order.status = Order.COMPLETED
        order.payment_id = f"PAY-{order.id}-{hash(order.created_at)}"
        order.save()

        messages.success(request, "Order placed successfully!")
        return redirect("order_success", order_id=order.id)

    return render(request, "web/checkout.html", {"cart": cart})


def order_success(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, "web/order_success.html", {"order": order})


# views.py
def track_order(request):
    if request.method == "POST":
        tracking_number = request.POST.get("tracking_number")
        try:
            order = Order.objects.get(tracking_number=tracking_number)
            return render(request, "web/order_tracking.html", {"order": order})
        except Order.DoesNotExist:
            messages.error(request, "Invalid tracking number")
    return render(request, "web/track_order.html")
