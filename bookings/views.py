from django.shortcuts import render
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status,generics
from rest_framework.views import APIView
from .serializers import UserRegisterSerializer, BusSerializer, BookingSerializer, SeatSerializer
from rest_framework.response import Response
from .models import Bus, Seat, Booking
from django.db import transaction

# Create your views here.
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        username=request.data.get('username')
        password=request.data.get('password')
        user=authenticate(username=username,password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user_id': user.id}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)    

class BusListCreateView(generics.ListCreateAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

class BusDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer



class BookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        seat_ids = request.data.get("seats", [])

        if not isinstance(seat_ids, list) or not seat_ids:
            return Response(
                {"error": "Provide at least one seat in 'seats'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(seat_ids) != len(set(seat_ids)):
            return Response(
                {"error": "Duplicate seat IDs are not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            seats = list(
                Seat.objects.select_for_update().filter(id__in=seat_ids)
            )

            if len(seats) != len(seat_ids):
                return Response(
                    {"error": "One or more seats do not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            booked_seats = [seat.seat_number for seat in seats if seat.is_booked]
            if booked_seats:
                return Response(
                    {"error": "Some seats are already booked.", "seats": booked_seats},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for seat in seats:
                seat.is_booked = True
                seat.save(update_fields=["is_booked"])

            bookings = Booking.objects.bulk_create([
                Booking(user=request.user, bus=seat.bus, seat=seat)
                for seat in seats
            ])

        return Response(
            BookingSerializer(bookings, many=True).data,
            status=status.HTTP_201_CREATED,
        )
class UserBookingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,user_id):
        if request.user.id != user_id:
            return Response({'error': 'You can only view your own bookings'}, status=status.HTTP_403_FORBIDDEN)

        booking=Booking.objects.filter(user_id=user_id)
        serializer=BookingSerializer(booking,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)