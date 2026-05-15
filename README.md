# Socaily (Django)

A full-featured Socaily social media web application built using **Django**.
Users can create profiles, upload posts, follow other users, like and comment on posts, receive notifications, and send private messages.

---

## 🚀 Live Project

You can view the live deployed project here:

https://insta-clone-0u0p.onrender.com/

---

## Features

### User Authentication

* User registration and login
* Secure authentication using Django's built-in User model
* Logout functionality

### User Profiles

* Custom profile linked to each user
* Bio section
* Profile picture upload
* Private account option

### Posts

* Upload image posts
* Add captions and location
* View posts in feed
* Timestamp for each post

### Save Posts

* Users can save posts
* Saved posts stored per user

### Follow System

* Follow and unfollow users
* Track followers and following lists

### Private Account Requests

* Send follow requests to private accounts
* Accept or reject requests

### Likes

* Like posts
* Track who liked a post
* Like notifications

### Comments

* Comment on posts
* View comments under each post

### Notifications

Users receive notifications for:

* Likes
* Comments
* New followers
* Follow requests

### Messaging System

* Send private messages between users
* Read / unread message tracking
* Messages ordered by time

---

## Tech Stack

**Backend**

* Python
* Django

**Frontend**

* HTML
* CSS
* JavaScript

**Database**

* SQLite

**Media Storage**

* Cloudinary

**Deployment**

* Render

---

## Installation

Clone the repository

git clone https://github.com/shejaan/socaily.git

Go to project folder

cd socaily

Create virtual environment

python -m venv venv

Activate environment

pip install -r requirements.txt

Run migrations

python manage.py migrate

Start development server

python manage.py runserver

---

## Project Structure

insta_clone
│
├── config
├── core
├── templates
├── manage.py
├── requirements.txt
└── README.md

---

## Author

Shejaan Khan
