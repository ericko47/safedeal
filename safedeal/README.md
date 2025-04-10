# 🛡️ SafeDeal - Secure Escrow and Delivery Platform

SafeDeal is a web-based platform designed to reduce fraud in small-scale online transactions by integrating escrow services and strict user verification measures. Built with Django (Python), the system emphasizes security, transparency, and user trust.

## 🚀 Features

- User authentication & registration (with National ID & profile photo)
- Escrow service for secure transactions
- Browse & view items
- Post items for sale
- Profile management
- Admin dashboard (to be added)
- Strict terms of service and privacy policy enforcement

## 📂 Project Structure

safedeal/ ├── core/ # Django app │ ├── templates/ # HTML templates │ ├── models.py # Custom user and data models │ ├── views.py # Core views ├── media/ # Uploaded images (profile pics, ID photos) ├── static/ # CSS, JS, images ├── db.sqlite3 # Local dev database ├── requirements.txt # Python dependencies └── manage.py # Django management scrip
## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/ericko47/safedeal.git
cd safedeal

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start the server
python manage.py runserver
✅ Requirements
Python 3.11+

Django 5.x

dj-rest-auth

django-allauth

Pillow (for image handling)

🔐 Disclaimer
⚠️ Do Not Copy or Redistribute
This project is the original work of @ericko47 and is strictly not open-source.
Unauthorized use, replication, or distribution in part or whole is prohibited.
This includes copying code, design, or ideas for commercial or personal use without explicit permission.

📌 License
This project is proprietary and not licensed for public use.

vbnet
Copy
Edit
