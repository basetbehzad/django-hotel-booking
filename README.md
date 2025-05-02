# 🏨 Django Hotel Booking App

A full-featured hotel booking system built with Django and Django REST Framework. This app supports user roles, booking management, payments, cancellations with refunds, income tracking, and admin analytics — all with a strong focus on backend logic and API design.

## 🔧 Technologies Used

- Django
- Django REST Framework (DRF)
- Celery + Redis (for async tasks)
- JWT Authentication
- HTML Templates for basic frontend (admin & user views)
- Git + GitHub for version control

---

## 👤 User Roles

1. **Normal User**  
   - Register/Login using email and password  
   - Create/update profile (name, phone, address)  
   - Book available places  
   - View bookings and payment status  
   - Leave and reply to comments (only if booked the place)  
   - Cancel bookings (with refund logic)

2. **Hotel Owner**  
   - Register/Login and choose role  
   - List hotels/places  
   - View bookings for their places  
   - See daily, weekly, and monthly income reports for each place  

3. **Admin (Superuser)**  
   - Full control via Django admin panel  
   - Verify hotel places before publishing  
   - Manage users, bookings, cancellations, deleted reservations, comments  
   - View analytics: total income, top users, top places

---

## 📦 Main Features

### ✅ Authentication & Profile
- JWT-based login/logout
- One-to-one profile creation on user registration
- Role-based access handling
- Session expiry after 24 hours

### 📍 Place Management
- Hotel Owners can:
  - Add new listings (with name, address, etc.)
  - See their own listings in a table view
  - Toggle booking availability
  - See income reports per place

- Admin:
  - Must verify each place
  - Can view most booked places (monthly/yearly)

### 🗓 Booking System
- Booking calendar to view availability
- Restricts overlapping bookings
- Booking duration: min 1 day, max 7 days
- Unpaid bookings expire in 10 minutes (handled via Celery)

### 💳 Payment System
- Simulated payment confirmation with "Pay Now" button
- PDF generation on successful payment
- Status reflected in UI and calendar (paid = red, unpaid = yellow)

### ❌ Cancellation & Refund
- Cancel up to 24 hours before check-in
- Refund rules:
  - < 24 hours: ❌ No refund
  - 24–72 hours: 💸 50% refund
  -  > 72 hours: ✅ Full refund
- Auto-approval if eligible; manual review by admin otherwise
- Admin can see all cancellation requests with statuses

### 💬 Commenting System
- Only users with a booking can comment/reply
- Supports nested replies
- Visible in admin panel

### ⭐ Rating System
- Purpose: Allows users to rate places they've booked.
- Permissions: Only users who have completed a paid booking for a place can submit a rating.
- Average Rating: Each place shows the average rating based on all submitted ratings.
- Integration: Rating data is used to calculate and display top-rated places in the admin panel.

### 📊 Admin Panel Enhancements
- Booking list includes:
  - Total price
  - Payment status
  - PDF download
- Income panel shows:
  - Total income from paid bookings
  - Daily/Weekly/Monthly income
- Top 3 Users by number of bookings (monthly/yearly)
- Top 3 Places with most bookings (monthly/yearly)
- Manage:
  - Users & profiles
  - Bookings & deleted reservations
  - Comments & replies
  - Cancellation requests & refunds

---

## 📂 Project Structure (Simplified)

```
booking/
├── account/                # Custom User + Profile models
├── reservation/            # Bookings, Cancellations, Income
├── place/                  # Hotel/Place listings + Comments
├── templates/              # Basic HTML views and admin overrides
├── statics/                # CSS + JS files
├── manage.py
```



## 📌 Final Notes

This project showcases a production-style backend application with:
- Clean architecture
- Scalable models and logic
- Real-world use of Celery, admin customization, and user roles
