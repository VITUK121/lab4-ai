from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
import plotly.express as px
import pandas as pd
from .models import Passenger, Cashier, Trip, Ticket
from .repositories import RepositoryManager

repo = RepositoryManager()

# Головна сторінка
def home(request):
    return render(request, 'tickets/home.html')

def dashboard_view(request):
    analytics_qs = repo.get_complex_analytics()
    min_revenue_filter = request.GET.get('min_revenue')
    graphs = {}

    # === ГРАФІК 1: Прибуток (Bar) ===
    df1 = pd.DataFrame(list(analytics_qs['revenue_by_trip'].values(
        'start_station', 'end_station', 'total_revenue'
    )))
    df1 = df1.fillna(0)

    if not df1.empty:
        # Конвертуємо Decimal -> float
        df1['total_revenue'] = df1['total_revenue'].astype(float) 

        if min_revenue_filter:
            try:
                val = float(min_revenue_filter)
                df1 = df1[df1['total_revenue'] >= val]
            except ValueError:
                pass 

        df1['route'] = df1['start_station'] + " - " + df1['end_station']
        fig1 = px.bar(df1, x='route', y='total_revenue', title="1. Прибуток рейсів", color='total_revenue')
        graphs['g1'] = fig1.to_html(full_html=False)

    # === ГРАФІК 2: Касири (Pie) ===
    df2 = pd.DataFrame(list(analytics_qs['cashier_performance'].values(
        'first_name', 'last_name', 'total_sales'
    )))
    df2 = df2.fillna(0)
    
    if not df2.empty:
        df2['total_sales'] = df2['total_sales'].astype(float) # Конвертація

        df2['cashier'] = df2['first_name'] + " " + df2['last_name']
        fig2 = px.pie(df2, values='total_sales', names='cashier', title="2. Доля продажів касирів")
        graphs['g2'] = fig2.to_html(full_html=False)

    # === ГРАФІК 3: Завантаженість (Bar) ===
    df3 = pd.DataFrame(list(analytics_qs['trip_occupancy'].values(
        'start_station', 'end_station', 'occupancy_rate'
    )))
    df3 = df3.fillna(0)

    if not df3.empty:
        df3['occupancy_rate'] = df3['occupancy_rate'].astype(float) # Конвертація

        df3['route'] = df3['start_station'] + "-" + df3['end_station']
        fig3 = px.bar(df3, x='route', y='occupancy_rate', title="3. Заповненість потягів (%)", 
                      range_y=[0, 100], color='occupancy_rate')
        graphs['g3'] = fig3.to_html(full_html=False)

    # === ГРАФІК 4: Типи потягів (Scatter) ===
    # САМЕ ТУТ БУЛА ПОМИЛКА
    df4 = pd.DataFrame(list(analytics_qs['train_type_stats'].values(
        'train_type', 'avg_passenger_age', 'max_ticket_price'
    )))
    df4 = df4.fillna(0)

    if not df4.empty:
        # Plotly вимагає float для 'size', Decimal не підходить
        df4['max_ticket_price'] = df4['max_ticket_price'].astype(float)
        df4['avg_passenger_age'] = df4['avg_passenger_age'].astype(float)

        fig4 = px.scatter(df4, x='avg_passenger_age', y='max_ticket_price', 
                          size='max_ticket_price', # Тепер це float, помилки не буде
                          color='train_type', 
                          title="4. Типи потягів: Вік vs Ціна (Bubble Chart)", 
                          size_max=60)
        graphs['g4'] = fig4.to_html(full_html=False)

    # === ГРАФІК 5: Продажі по місяцях (Line) ===
    df5 = pd.DataFrame(list(analytics_qs['sales_by_month'].values(
        'month', 'tickets_sold'
    )))
    df5 = df5.fillna(0)

    if not df5.empty:
        fig5 = px.line(df5, x='month', y='tickets_sold', markers=True, title="5. Продажі по місяцях")
        graphs['g5'] = fig5.to_html(full_html=False)

    # === ГРАФІК 6: Топ Пасажири (Bar) ===
    df6 = pd.DataFrame(list(analytics_qs['top_passengers'].values(
        'first_name', 'last_name', 'total_spent'
    )))
    df6 = df6.fillna(0)

    if not df6.empty:
        df6['total_spent'] = df6['total_spent'].astype(float) # Конвертація
        
        df6['person'] = df6['first_name'] + " " + df6['last_name']
        fig6 = px.bar(df6, x='total_spent', y='person', orientation='h', title="6. VIP Клієнти")
        graphs['g6'] = fig6.to_html(full_html=False)

    return render(request, 'tickets/dashboard.html', {'graphs': graphs})


# --- Passenger ---
class PassengerListView(ListView):
    model = Passenger
    template_name = 'tickets/passenger_list.html'
    context_object_name = 'passengers'
    
    def get_queryset(self):
        # Використовуємо репозиторій
        return repo.passengers.all()

class PassengerCreateView(CreateView):
    model = Passenger
    template_name = 'tickets/passenger_form.html'
    fields = ['first_name', 'last_name', 'passport', 'age']
    success_url = reverse_lazy('passenger_list')

class PassengerUpdateView(UpdateView):
    model = Passenger
    template_name = 'tickets/passenger_form.html'
    fields = ['first_name', 'last_name', 'passport', 'age']
    success_url = reverse_lazy('passenger_list')

class PassengerDeleteView(DeleteView):
    model = Passenger
    template_name = 'tickets/passenger_confirm_delete.html'
    success_url = reverse_lazy('passenger_list')

# --- Cashier ---
class CashierListView(ListView):
    model = Cashier
    template_name = 'tickets/cashier_list.html'
    context_object_name = 'cashiers'

    def get_queryset(self):
        return repo.cashiers.all()

# --- Trip ---
class TripListView(ListView):
    model = Trip
    template_name = 'tickets/trip_list.html'
    context_object_name = 'trips'

    def get_queryset(self):
        return repo.trips.all()

# --- Ticket ---
class TicketsListView(ListView):
    model = Ticket
    template_name = 'tickets/tickets_list.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        qs = repo.tickets.all()
        # if repo returns a Django QuerySet of Ticket objects, try to eager-load relations
        try:
            return qs.select_related('trip', 'passenger', 'cashier')
        except Exception:
            # repo may return plain objects or lists — return as-is (list) so we can attach related objects later
            return list(qs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tickets = list(ctx.get('tickets', []))

        # collect ids from tickets (supports both ORM objects and plain objects with *_id attrs)
        trip_ids = {getattr(t, 'trip_id', None) for t in tickets if getattr(t, 'trip_id', None) is not None}
        passenger_ids = {getattr(t, 'passenger_id', None) for t in tickets if getattr(t, 'passenger_id', None) is not None}
        cashier_ids = {getattr(t, 'cashier_id', None) for t in tickets if getattr(t, 'cashier_id', None) is not None}

        if trip_ids:
            trips = Trip.objects.in_bulk(trip_ids)
        else:
            trips = {}

        if passenger_ids:
            passengers = Passenger.objects.in_bulk(passenger_ids)
        else:
            passengers = {}

        if cashier_ids:
            cashiers = Cashier.objects.in_bulk(cashier_ids)
        else:
            cashiers = {}

        # attach related objects so templates can use ticket.trip, ticket.passenger, ticket.cashier
        for t in tickets:
            # prefer existing related object if present, otherwise set from in_bulk map
            if not getattr(t, 'trip', None):
                setattr(t, 'trip', trips.get(getattr(t, 'trip_id', None)))
            if not getattr(t, 'passenger', None):
                setattr(t, 'passenger', passengers.get(getattr(t, 'passenger_id', None)))
            if not getattr(t, 'cashier', None):
                setattr(t, 'cashier', cashiers.get(getattr(t, 'cashier_id', None)))

        ctx['tickets'] = tickets
        return ctx
    
class TicketsDetailsView(DetailView):
    model = Ticket
    template_name = 'tickets/ticket_details.html'
    context_object_name = 'ticket' # Однина, бо це один квиток

    def get_object(self, queryset=None):
        """
        Замість get_queryset (для списку), DetailView використовує get_object.
        Ми беремо ID з URL (self.kwargs['pk']) і питаємо репо.
        """
        ticket_id = self.kwargs.get('pk')
        
        # Отримуємо об'єкт з репозиторія
        # Припускаємо, що get_by_id повертає один об'єкт або None
        obj = repo.tickets.get_by_id(ticket_id) 
        
        if not obj:
            raise Http404("Квиток не знайдено")
            
        return obj

    def get_context_data(self, **kwargs):
        """
        Тут ми вручну додаємо зв'язки (Trip, Passenger), 
        оскільки репозиторій може повертати "голий" об'єкт без ORM-зв'язків.
        """
        ctx = super().get_context_data(**kwargs)
        ticket = ctx['ticket'] # Це наш об'єкт, отриманий в get_object

        # 1. Підтягуємо Рейс (Trip)
        trip_id = getattr(ticket, 'trip_id', None)
        if trip_id:
             # Використовуємо filter().first(), щоб не було помилки, якщо ID битий
            ticket.trip = Trip.objects.filter(pk=trip_id).first()

        # 2. Підтягуємо Пасажира (Passenger)
        passenger_id = getattr(ticket, 'passenger_id', None)
        if passenger_id:
            ticket.passenger = Passenger.objects.filter(pk=passenger_id).first()

        # 3. Підтягуємо Касира (Cashier)
        cashier_id = getattr(ticket, 'cashier_id', None)
        if cashier_id:
            ticket.cashier = Cashier.objects.filter(pk=cashier_id).first()

        return ctx
    
class TicketsAddView(CreateView):
    model = Ticket
    template_name = 'tickets/ticket_form.html'
    fields = ['trip', 'passenger', 'cashier', 'base_price_id', 'payment_method']
    success_url = reverse_lazy('tickets_list')

    def get_queryset(self):
        return repo.tickets.all()
    
class TicketsEditView(UpdateView):
    model = Ticket
    template_name = 'tickets/ticket_form.html'
    fields = ['trip', 'passenger', 'cashier', 'base_price_id', 'payment_method']
    success_url = reverse_lazy('tickets_list')

class TicketsDeleteView(DeleteView):
    model = Ticket
    template_name = 'tickets/ticket_confirm_delete.html'
    success_url = reverse_lazy('tickets_list')