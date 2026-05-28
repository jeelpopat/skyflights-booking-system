# ✈️ Skyflights Booking System

Welcome to the **Skyflights Booking System**! This is a full-stack web application built with Python and Flask that allows users to search for real-time flights, book tickets, manage their reservations, and download dynamically generated PDF e-tickets. 

**🌍 Live Demo:** [https://skyflights-booking-system.onrender.com/](https://skyflights-booking-system.onrender.com/)

---

## ✨ Features

- 🔍 **Real-Time Flight Search:** Integrated with SerpApi (Google Flights Engine) to fetch live flight schedules, airlines, and pricing.
- 🔐 **User Authentication:** Secure user registration and login system with password hashing. Includes a "Forgot Password" feature that sends a secure password reset link via email.
- 🎫 **Flight Booking & Checkout:** Users can select flights, input passenger details (name, passport, age, gender), and proceed through a simulated checkout process.
- 📄 **Automated PDF E-Tickets:** Generates downloadable, customized PDF flight tickets complete with passenger details and a scannable QR code using `ReportLab` and `qrcode`.
- 🗂️ **Booking Management:** A user dashboard to view booking history, download confirmed e-tickets, and cancel pending/confirmed bookings.
- ✉️ **Contact Form:** A built-in contact page that saves user messages directly to the database.

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite (using Flask-SQLAlchemy)
- **External APIs:** SerpApi (for live flight data)
- **Libraries:** - `Flask-Mail` (Email services for password resets)
  - `ReportLab` & `qrcode[pil]` (PDF & QR code generation)
  - `Werkzeug` & `itsdangerous` (Security and secure token generation)
  - `requests` (API calls)
- **Deployment:** Render (with Gunicorn)
