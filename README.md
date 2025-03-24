# Farmer Project

Welcome to the Farmer Project repository! This project connects farmers and consumers, enabling farmers to showcase their natural farming products while allowing consumers to explore and review them.

## Features

- **Farmer Profiles** – Farmers can create and manage their profiles with personal details, farm information, and available products.  
- **Product Listings** – Farmers can list their natural farming products with images, descriptions, and real-time stock updates.  
- **Verified Listings & Reviews** – Products are verified with certification status, and consumers can leave reviews to ensure crop quality and build trust.  
- **Trust-Building System** – Verified purchase badges help establish credibility for farmers.  
- **Django REST Framework APIs** – APIs for authentication, product listings, reviews, and user interactions.  
- **User Authentication** – Secure sign-up and login system for both farmers and consumers.  
- **SQLite Database Integration** – Efficient data management using SQLite as the backend database.
- **Multi-Language Assistance** – Webpages can be translated to any langauge suitable to user.

## Project Structure

The repository is organized as follows:

- `core/`: Contains core application logic and settings.
- `farm_core/`: Handles farmer-related functionality.
- `farmconnect/`: Manages interactions between farmers and consumers.
- `static/`: Stores static files like CSS, JavaScript, and images.
- `db.sqlite3`: The SQLite database file storing project data.
- `manage.py`: Django's command-line utility for project management.

## Tech-Stack Used

- **Frontend**: HTML/CSS/JavaScript
- **Backend**: Python (Django Framework)
- **Database**: SQLite

## Getting Started

To get a local copy up and running, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/msiddharthbansal/farmerproject.git
   ```
2. **Navigate to the project directory:**
   ```bash
   cd farmerproject
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```
5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```
   
## Screenshots

### Login & Sign Up Page  
<p align="center">
    <img src="![Screenshot from 2025-03-24 15-11-04](https://github.com/user-attachments/assets/28226b5e-bb6f-4b97-8151-2528d07fb01f)
" width="45%" alt="Login Page">
    <img src="![Screenshot from 2025-03-24 15-09-56](https://github.com/user-attachments/assets/88953375-f02e-4672-99d7-6de95e07d67b)
" width="45%" alt="Sign Up Page">
</p>

### Consumer Interface (Product Listings)
![Consumer Interface](![Screenshot from 2025-03-24 15-11-41](https://github.com/user-attachments/assets/ed593117-778b-42e0-a25e-14ab7f0b9cab)
)

### Farmer Interface (Add Product Page)
![Farmer Interface](![Screenshot from 2025-03-24 15-12-21](https://github.com/user-attachments/assets/b8af3b38-1692-48aa-bc01-92d0c605a63c)
)

### Order Placed Page
![Order Placed](![Screenshot from 2025-03-24 15-12-54](https://github.com/user-attachments/assets/49338654-00eb-4f1d-a208-3e0058f354d5)
)

## Usage

1. Farmers can sign up, create a profile, and list their farming products.  
2. Consumers can browse product listings, check product details, buy products and leave reviews.  
3. Admins can manage users, products, and reviews for platform integrity.  


## License

This project is licensed under the MIT License.

---

*Note: Please replace the placeholder `[Specify License Here]` with the actual license details.*
