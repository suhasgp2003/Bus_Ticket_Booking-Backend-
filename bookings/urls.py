
from django.urls import path
from .views import BookingView, BookingCancellationView, RegisterView, LoginView, BusListCreateView, UserBookingsView, BusDetailView

urlpatterns = [
    path('buses/', BusListCreateView.as_view(), name='buslist'),
    path('buses/<int:pk>/', BusDetailView.as_view(), name='bus-detail'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user/<int:user_id>/bookings/', UserBookingsView.as_view(), name='user-bookings'),
    path('booking/',BookingView.as_view(),name='bookings'),
    path('booking/cancel/', BookingCancellationView.as_view(), name='booking-cancel'),
]
