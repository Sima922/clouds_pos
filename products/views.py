from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import F
from .models import Product, Category
from .forms import ProductForm

def get_user_subscription(user):
    """
    Return the ClientSubscription for this user, whether
    they're a member or the owner.
    """
    if hasattr(user, 'subscription') and user.subscription:
        return user.subscription
    return getattr(user, 'owned_subscription', None)


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/list.html'
    paginate_by = 20

    def get_queryset(self):
        sub = get_user_subscription(self.request.user)
        # if no subscription, return empty
        if not sub:
            return Product.objects.none()

        qs = Product.objects.filter(subscription=sub)

        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(name__icontains=search)

        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)

        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()

        sub = get_user_subscription(self.request.user)
        if sub:
            context['low_stock'] = Product.objects.filter(
                subscription=sub,
                stock__lte=F('reorder_level')
            )
        else:
            context['low_stock'] = Product.objects.none()

        return context


class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/manage.html'
    success_url = reverse_lazy('product-list')

    def test_func(self):
        return self.request.user.role in ['owner', 'admin']

    def form_valid(self, form):
        user = self.request.user
        sub = get_user_subscription(user)
        form.instance.created_by = user
        form.instance.subscription = sub
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/manage.html'
    success_url = reverse_lazy('product-list')

    def test_func(self):
        prod = self.get_object()
        sub = get_user_subscription(self.request.user)
        return (
            self.request.user.role in ['owner', 'admin'] and
            sub is not None and
            prod.subscription == sub
        )


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = 'products/confirm_delete.html'
    success_url = reverse_lazy('product-list')

    def test_func(self):
        prod = self.get_object()
        sub = get_user_subscription(self.request.user)
        return (
            self.request.user.role in ['owner', 'admin'] and
            sub is not None and
            prod.subscription == sub
        )
