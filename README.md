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

## Usage

1. Farmers can sign up, create a profile, and list their farming products.  
2. Consumers can browse product listings, check product details, buy products and leave reviews.  
3. Admins can manage users, products, and reviews for platform integrity.  


## License

This project is licensed under the MIT License.

---

*Note: Please replace the placeholder `[Specify License Here]` with the actual license details.*
