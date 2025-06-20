# CDEX - Card Index: The Ultimate Hub for Trading Card Collectors & Traders

## Project Vision

CDEX aims to be the definitive online platform for enthusiasts of all physical trading cards – from sports legends and iconic gaming cards (like Pokémon, Magic: The Gathering) to unique, self-designed collectibles. We're building a comprehensive ecosystem that supports:

*   **Live Value Tracking:** Understand the market value of your cards based on real-time sales data and order book information, especially for graded items.
*   **Dynamic Listings & Auctions:** Easily list your cards for sale, trade, or put them up for auction.
*   **Flexible Transactions:** Connect with other users for direct trades (card-for-card, card-for-currency), supporting both local meetups and global shipping.
*   **Community & Insights:** Track value changes with graphs, manage your collection with grading information, and connect with a passionate community.

## Current Status & Phase 1 Demo Goals

CDEX is under active development. Here's a snapshot of our progress:

**Foundation (Implemented & Tested):**

*   **User Accounts:** Secure registration using email/password, with Google Sign-In integration ready (pending admin configuration of API keys).
*   **User Profiles:** Editable user bios to personalize your trading identity.
*   **Robust API Backend:** Built with Django and Django REST Framework, providing secure JWT-based authentication for future client applications.
*   **Basic Web Interface:** Initial web pages for user login, registration, and profile editing.

**Phase 1 / Initial Demo (Actively Developing):**

We are currently focused on delivering a demo showcasing these core functionalities:

*   **Live Value Tracking (Graded Cards):** Initial implementation for tracking sales data and values for specific graded cards (e.g., "Derek Jeter rookie PSA 9").
*   **Order Book Recording:** System to log buy/sell orders, contributing to value metrics.
*   **Card Listing System:** Functionality for users to list their cards for sale or trade.
*   **Auction Mechanism:** Platform to host and participate in card auctions (e.g., for Pokémon cards).
*   **Value Change Graphs:** Visual representation of historical card value trends.
*   **Grading Information Management:** Ability to associate and display card grading details (PSA, Beckett, etc.).
*   **Facilitated Direct Payments:** User profiles will allow specifying preferred direct payment methods (e.g., CashApp, Venmo, PayPal.Me) to settle transactions peer-to-peer.

## Key Features (Evolving with Development)

*   **Comprehensive Card Support:** Designed for all types of trading cards.
*   **User-Centric Transactions:** Empowers users to connect and transact directly, offering flexibility for local exchanges or global shipping (user-managed).
*   **Data-Driven Value Insights:** Providing tools to understand card values.
*   **(Future) Secure On-Platform Transactions:** Planned integration for secure payment processing directly within CDEX.

## Disclaimer

**Important:** CDEX and its operating LLC function as a platform to connect users and provide information. We are **not liable** for any issues, losses, disputes, or damages arising from personal trades, local transactions, or items mailed/shipped between users. All transaction details, including shipping terms, payment, and final agreements for direct peer-to-peer payments, are the sole responsibility of the participating users. Users assume all risks associated with their transactions.

## Technology Stack

*   **Backend:** Python, Django, Django REST Framework
*   **Authentication:** `django-allauth`, `dj-rest-auth` (JWT)
*   **Database:** SQLite (for current development), PostgreSQL (planned for production)
*   **(Frontend - Evolving):** Initial views via Django Templates; future development may involve a dedicated JavaScript framework.

## Contributing & Future Development

We welcome collaboration and ideas! Our roadmap beyond Phase 1 includes:

*   Platform-mediated secure online payment gateway integration.
*   Advanced search, filtering, and collection management tools.
*   Direct user-to-user messaging.
*   User reputation and feedback systems.
*   Native mobile applications.

For a detailed checklist of completed items, current work, and future goals, please see [`juleschecklist.md`](juleschecklist.md).
