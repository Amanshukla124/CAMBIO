# Cambio – AI-Powered Voucher Exchange Platform

Cambio is a full-stack web application that allows users to exchange unused vouchers for credits and redeem vouchers they actually need.

<img width="1920" height="991" alt="Screenshot 2026-03-19 at 1 14 10 PM" src="https://github.com/user-attachments/assets/c67a73d4-e911-45fc-a0e3-7d2de1850355" />


Built using:
- Python (Flask)
- SQLite
- HTML5
- Tailwind CSS
- JavaScript

---

## 💡 Project Idea

Many users receive vouchers that:
- They don’t need
- Are brand-specific
- Expire unused

Cambio solves this by converting vouchers into **Cambio Credits**, which can be used to redeem other vouchers in the marketplace.

---

## 🧠 AI Valuation Engine (Rule-Based)

Cambio uses a rule-based valuation system to calculate voucher credits.

<img width="1920" height="993" alt="Screenshot 2026-03-19 at 1 14 28 PM" src="https://github.com/user-attachments/assets/714598af-4df5-4744-89cc-894d952e7190" />

Factors considered:

- Voucher value (50% base conversion)
- Brand tier boost
- Expiry-based penalty

### Tier System

| Tier      | Criteria |
|-----------|----------|
| Premium   | Top brands (Amazon, Apple, Nike, Flipkart) |
| Gold      | Mid-tier brands (Zara, Puma, Myntra) |
| Standard  | Default category |
| Basic     | Near expiry vouchers (<30 days) |

Points are dynamically calculated and added to the user's wallet.

---

## 🔐 Features

### 👤 Authentication
- User Signup
- Login
- Logout
- Secure password hashing
- Session-based authentication

### 💳 Credit Wallet
- Dynamic credit balance
- Auto-update on upload
- Auto-deduct on redemption

### 🎟 Voucher Upload
- Brand
- Value
- Expiry date
- Image upload
- AI-based points calculation
- Tier assignment

### 🛒 Marketplace
- View vouchers from other users
- Redeem using credits
- Automatic credit deduction
- Voucher status management

---

## 🗂 Project Structure

