from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login", views.login, name="login"),
    path("menu", views.menu, name="menu"),
    path("branches", views.branches, name="branches"),
    path("blog", views.blog, name="blog"),
    path("privacy-policy", views.privacy, name="privacy-policy"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/", views.update_cart_item, name="update_cart_item"),
    path("cart/remove/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/success/<int:order_id>/", views.order_success, name="order_success"),
    path("track/", views.track_order, name="track_order"),
    path("signup/", views.signup_view, name="signup"),
    path("signin/", views.login_view, name="signin"),
]
