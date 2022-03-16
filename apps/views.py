from django.shortcuts import render, redirect
from django.forms import inlineformset_factory
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Product, Customer, Order
from .forms import CustomerForm, OrderForm, MyUserCreationForm
from .filters import OrderFilter
from .decorators import unauthenticated_user, allowed_users, admin_only


@unauthenticated_user
def register_page(request):
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(
                request, f'Account was created for user "{username}"')
            return redirect('login')
    context = {'form': form}
    return render(request, 'apps/register.html', context)


@unauthenticated_user
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home', )
        else:
            messages.info(request, 'Username or password incorrect')
    return render(request, 'apps/login.html')


@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def user_page(request):
    orders = request.user.customer.order_set.all()
    total_orders = orders.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'delivered': delivered,
        'pending': pending,
    }
    return render(request, 'apps/user.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def account_settings(request):
    user = request.user.customer
    form = CustomerForm(instance=user)
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
    context = {'form': form}
    return render(request, 'apps/account_settings.html', context)


def logout_page(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
@admin_only
def home(request):
    customers = Customer.objects.all()
    orders = Order.objects.all()
    total_orders = orders.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    context = {
        'customers': customers,
        'orders': orders,
        'total_orders': total_orders,
        'delivered': delivered,
        'pending': pending,
    }
    return render(request, 'apps/dashboard.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['administrator'])
def product(request):
    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'apps/products.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['administrator'])
def customer(request, pk):
    customer = Customer.objects.get(id=pk)
    orders = customer.order_set.all()
    total_orders = orders.count()
    my_filter = OrderFilter(request.GET, queryset=orders)
    orders = my_filter.qs
    context = {
        'customer': customer,
        'orders': orders,
        'total_orders': total_orders,
        'my_filter': my_filter,
    }
    return render(request, 'apps/customers.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['administrator'])
def create_order(request):
    form = OrderForm()
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    context = {'form': form}
    return render(request, 'apps/order_form.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['administrator'])
def update_order(request, pk):
    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('/')
    context = {'form': form}
    return render(request, 'apps/order_form.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['administrator'])
def delete_order(request, pk):
    order = Order.objects.get(id=pk)
    context = {'item': order}
    if request.method == 'POST':
        order.delete()
        return redirect('/')
    return render(request, 'apps/delete_form.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['administrator'])
def create_order_from_customer(request, pk):
    OrderFormSet = inlineformset_factory(
        Customer, Order, fields=('product', 'status'), extra=5)
    customer = Customer.objects.get(id=pk)
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
    if request.method == 'POST':
        formset = OrderFormSet(request.POST, instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect(f'/customer/{customer.id}')
    context = {'formset': formset}
    return render(request, 'apps/order_form_from_customer.html', context)
