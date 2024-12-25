def base_context(request):
    from .views import get_or_create_cart

    cart = get_or_create_cart(request)
    return {"cart": cart}
