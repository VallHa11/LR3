from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import SignUpForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import stripe
from .models import CartItem
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'myapp/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')
            else:
                messages.error(request, 'Неправильное имя пользователя или пароль.')
        else:
            messages.error(request, 'Неправильное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    return render(request, 'myapp/login.html', {'form': form})

@login_required(login_url='signup')
def profile_view(request):
    return render(request, 'myapp/profile.html', {
        'user': request.user
    })
def door_detail(request, door_id):
    return render(request, 'myapp/door_detail.html', {'door_id': door_id})

def search_doors(request, query):

    return render(request, 'myapp/search_results.html', {'query': query})

def index(request):
    return render(request, 'myapp/index.html')

def contact(request):
    return render(request, 'myapp/contact.html')

def doors(request):
    products = Product.objects.all()
    return render(request, 'myapp/doors.html', {'products': products})




@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')


@login_required
def cart_view(request):
    # Получение всех элементов корзины для текущего пользователя
    cart_items = CartItem.objects.filter(user=request.user)
    # Подсчёт общей суммы
    total_price = sum(item.get_total_price() for item in cart_items)

    # Отправка контекста в шаблон
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    }
    return render(request, 'myapp/cart.html', context)

import json

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            total_price = data.get('total_price', 0) * 100  # Преобразование в центы

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'Ваши товары'
                            },
                            'unit_amount': int(total_price),
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri('/success/'),
                cancel_url=request.build_absolute_uri('/cancel/'),
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)
from django.shortcuts import render

def payment_success(request):
    return render(request, 'myapp/payment_success.html')

def payment_cancel(request):
    return render(request, 'myapp/payment_cancel.html')

@require_POST
def remove_from_cart(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')  #


