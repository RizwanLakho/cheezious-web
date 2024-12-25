import random

from django.conf import settings
from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.utils import timezone

# class CustomUser(AbstractUser):
#     mobile_number = models.CharField(max_length=15, unique=True)


class OTP(models.Model):
    mobile_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.otp = str(random.randint(100000, 999999))  # 6-digit OTP
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Item(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to="items/", null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="items"
    )
    has_starting_price = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    # user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total(self):
        return sum(item.get_total() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total(self):
        return self.item.price * self.quantity


# class Order(models.Model):
#     PENDING = "pending"
#     COMPLETED = "completed"
#     FAILED = "failed"
#     STATUS_CHOICES = [
#         (PENDING, "Pending"),
#         (COMPLETED, "Completed"),
#         (FAILED, "Failed"),
#     ]

#     user = models.ForeignKey(
#         "auth.User", on_delete=models.CASCADE, null=True, blank=True
#     )
#     full_name = models.CharField(max_length=255)
#     email = models.EmailField()
#     phone = models.CharField(max_length=20)
#     address = models.TextField()
#     city = models.CharField(max_length=100)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
#     payment_id = models.CharField(max_length=100, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Order #{self.id} - {self.full_name}"


class Order(models.Model):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]

    # user = models.ForeignKey(
    #     "auth.User", on_delete=models.SET_NULL, null=True, blank=True
    # )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    full_name = models.CharField(max_length=255, default="")
    email = models.EmailField(default="")
    phone = models.CharField(max_length=20, default="")
    address = models.TextField(default="")
    city = models.CharField(max_length=100, default="")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


class OrderStatus(models.Model):
    order = models.ForeignKey(
        "Order", related_name="status_updates", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ("processing", "Processing"),
            ("confirmed", "Confirmed"),
            ("shipped", "Shipped"),
            ("out_for_delivery", "Out for Delivery"),
            ("delivered", "Delivered"),
        ],
    )
    location = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp"]


# def get_or_create_cart(request):
#     session_id = request.session.session_key or request.session.create()
#     cart = Cart.objects.filter(session_id=session_id).first()
#     if not cart:
#         cart = Cart.objects.create(session_id=session_id)
#     return cart


# # Add this to your view that renders the header (likely base.html)
# def base_context(request):
#     cart = get_or_create_cart(request)
#     return {"cart": cart}
