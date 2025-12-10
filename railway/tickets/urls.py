from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('passengers/', views.PassengerListView.as_view(), name='passenger_list'),
    path('passenger/add/', views.PassengerCreateView.as_view(), name='passenger_add'),
    path('passenger/<int:pk>/edit/', views.PassengerUpdateView.as_view(), name='passenger_edit'),
    path('passenger/<int:pk>/delete/', views.PassengerDeleteView.as_view(), name='passenger_delete'),
    
    path('cashiers/', views.CashierListView.as_view(), name='cashier_list'),
    path('trips/', views.TripListView.as_view(), name='trip_list'),
    path('tickets/', views.TicketsListView.as_view(), name='tickets_list'),
    path('tickets/add/', views.TicketsAddView.as_view(), name='ticket_add'),
    path('tickets/<int:pk>/edit/', views.TicketsEditView.as_view(), name='ticket_edit'),
    path('tickets/<int:pk>/details/', views.TicketsDetailsView.as_view(), name='ticket_details'),
    path('tickets/<int:pk>/delete/', views.TicketsDeleteView.as_view(), name='ticket_delete'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/v2/', views.dashboard_bokeh_view, name='dashboard_bokeh'),
    path('performance/', views.performance_view, name='performance'),
]
