# 🚌 Bus Ticket Booking System

A full-stack web application for booking bus tickets online. Features user authentication, real-time seat availability, and secure booking management.

## 📌 Project Overview

This is a **full-stack MERN-like application** (Django REST + React) that enables users to:
- Browse available buses with routes and timings
- View real-time seat availability
- Book and cancel tickets
- Manage personal bookings
- User authentication and authorization

## 🏗️ Architecture

```
┌─────────────────┐          ┌──────────────────┐
│  React Frontend │◄────────►│  Django REST API │
│  (Vite + Axios) │ (HTTP)   │  (PostgreSQL)    │
└─────────────────┘          └──────────────────┘
```

### Backend Structure
- **Framework**: Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: Token-based (Django REST Token Auth)
- **CORS**: Enabled for frontend communication

### Frontend Structure
- **Framework**: React 19
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **Routing**: React Router v7
- **Styling**: Tailwind CSS

## 🚀 Features

### ✨ Core Features
- **User Management**
  - User registration and login
  - Token-based authentication
  - Personal booking history

- **Bus Management**
  - Browse available buses
  - Filter by route, time, and price
  - View bus features and seat types

- **Seat Management**
  - Real-time seat availability
  - Window and aisle seat options
  - Visual seat layout

- **Booking System**
  - Book multiple seats at once
  - Atomic transactions (all-or-nothing)
  - Prevent double-booking with database locks
  - Cancel bookings and free up seats

### 🔒 Advanced Features
- **Transaction Safety**: Uses database transactions to prevent race conditions
- **Concurrency Control**: `select_for_update()` ensures seat locking during booking
- **Input Validation**: Comprehensive error handling for invalid requests
- **Authorization**: Users can only view/manage their own bookings

## 📊 Database Models

```python
Bus
├── bus_name, bus_number (unique)
├── origin, destination
├── features, start_time, reach_time
├── no_of_seats, price
└── Related: seats, bookings

Seat
├── bus_id (FK → Bus)
├── seat_number, row, column
├── is_booked (Boolean)
├── seat_type (Window/Aisle)
└── Related: bookings

Booking
├── user_id (FK → User)
├── bus_id (FK → Bus)
├── seat_id (FK → Seat)
└── booking_time (auto_now_add)
```

## 🛠️ Tech Stack

### Backend
```
Django==6.1.1
djangorestframework==3.18.1
django-cors-headers==4.9.0
psycopg==3.3.5 (PostgreSQL driver)
python-dotenv==1.2.3
```

### Frontend
```
React==19.2.8
Vite==8.2.2
Tailwind CSS==4.3.3
Axios==1.20.0
React Router==7.18.3
```

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/suhasgp2003/Bus_Ticket_Booking-Backend-.git
   cd Bus_Ticket_Booking-Backend-
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file
   touch .env
   ```
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://user:password@localhost:5432/bus_booking
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Setup database**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser  # For admin panel
   ```

6. **Run the server**
   ```bash
   python manage.py runserver
   ```
   API will be available at `http://localhost:8000/`

### Frontend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/suhasgp2003/Bus_Ticket_Booking-React-.git
   cd Bus_Ticket_Booking-React-
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure API URL**
   ```bash
   # Create .env.local
   VITE_API_URL=http://localhost:8000/api
   ```

4. **Run development server**
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:5173/`

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login user |

### Buses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/buses/` | List all buses |
| POST | `/api/buses/` | Create bus (Admin) |
| GET | `/api/buses/{id}/` | Get bus details |
| PUT | `/api/buses/{id}/` | Update bus |
| DELETE | `/api/buses/{id}/` | Delete bus |

### Bookings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookings/` | Create booking |
| DELETE | `/api/bookings/cancel/` | Cancel booking |
| GET | `/api/bookings/user/{user_id}/` | Get user's bookings |

### Seats
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/seats/?bus_id=1` | Get bus seats |

## 📝 Example API Usage

### Register User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password"
  }'
```

### Book Tickets
```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Authorization: Token your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "seats": [1, 2, 3]
  }'
```

### Cancel Booking
```bash
curl -X DELETE http://localhost:8000/api/bookings/cancel/ \
  -H "Authorization: Token your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "seats": [1, 2]
  }'
```

## 🎯 Key Implementation Highlights

### 1. **Atomic Transactions**
```python
with transaction.atomic():
    seats = Seat.objects.select_for_update().filter(id__in=seat_ids)
    # Book seats safely without race conditions
```

### 2. **Authorization**
```python
class BookingView(APIView):
    permission_classes = [IsAuthenticated]
    # Only authenticated users can book
```

### 3. **Input Validation**
```python
# Validates duplicate seats, existence, and availability
if len(seat_ids) != len(set(seat_ids)):
    return Response({"error": "Duplicate seat IDs"})
```

### 4. **CORS Integration**
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]
```

## 📚 Learning Outcomes

This project demonstrates:
- ✅ Full-stack web development
- ✅ RESTful API design
- ✅ Database modeling and relationships
- ✅ Authentication and authorization
- ✅ Transaction management & concurrency control
- ✅ Frontend-backend integration
- ✅ Error handling and validation
- ✅ CORS and HTTP communication

## 🐛 Known Limitations & Future Improvements

### Current Limitations
- [ ] Payment integration
- [ ] Email notifications
- [ ] Advanced filtering (date range, price range)
- [ ] User reviews and ratings
- [ ] Admin dashboard
- [ ] Unit tests and integration tests
- [ ] Deployment configuration

### Planned Features
- 🔄 Payment gateway (Razorpay/Stripe)
- 📧 Email confirmations
- 📊 Analytics dashboard
- 🗺️ Map integration for routes
- ⭐ User ratings and reviews
- 📱 Mobile app

## 🧪 Testing

### Run Tests (Backend)
```bash
python manage.py test
```

### Run Linting (Frontend)
```bash
npm run lint
```

## 📂 Project Structure

### Backend
```
Bus_Ticket_Booking-Backend-/
├── TransportNetwork/       # Project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── bookings/               # Main app
│   ├── models.py          # DB Models: Bus, Seat, Booking
│   ├── views.py           # API Views
│   ├── serializers.py     # DRF Serializers
│   ├── urls.py            # URL routing
│   └── admin.py           # Admin configuration
├── manage.py
└── requirements.txt
```

### Frontend
```
Bus_Ticket_Booking-React-/
├── src/
│   ├── components/        # React components
│   ├── pages/            # Page components
│   ├── services/         # API service layer
│   ├── App.jsx
│   └── main.jsx
├── public/
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

**Suhas GP**
- GitHub: [@suhasgp2003](https://github.com/suhasgp2003)
- Portfolio: [View all projects](https://github.com/suhasgp2003?tab=repositories)

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Contact via email or GitHub profile

---

**Made with ❤️ | Last Updated: 2026**
