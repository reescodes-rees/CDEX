# Jules' CDEX Development Checklist & Roadmap

This document tracks the development progress of the CDEX application, suggestions, and future goals. It will be updated by Jules based on user feedback and development milestones.

## Core Infrastructure & User System (Completed)

- [x] Backend: Django project setup (`cdex_project`).
- [x] Core App: `accounts` app created for user management.
- [x] User Model: Django's `User` model extended with `UserProfile` (for bio, etc.) via one-to-one link and signals.
- [x] Authentication System (`django-allauth`):
    - [x] Local email/password registration and login.
    - [x] Configuration for Google Sign-In (requires admin to add API keys).
- [x] API Authentication (`dj-rest-auth` with JWT):
    - [x] API endpoints for registration, login, logout.
    - [x] JWT Cookie Authentication configured.
- [x] User Profile API:
    - [x] Endpoint for authenticated users to retrieve/update their own `UserProfile` (`/api/accounts/profile/`).
- [x] Basic Frontend UI (Django Templates + `django-allauth`):
    - [x] Web pages for login, signup using `allauth` templates.
    - [x] Basic web page for users to view/edit their profile bio, interacting with the API.
- [x] Testing:
    - [x] Unit/integration tests for user models, signals, auth APIs, profile API, and profile UI views.
- [ ] **CAPTCHA Integration (`django-recaptcha`)**:
    - [x] Code and configuration implemented.
    - [ ] Runtime `ModuleNotFoundError` for `captcha` in initial development environment. Currently disabled in `settings.py`. Needs revisit/resolution in a compatible environment to activate.

## Phase 1 / Initial Demo Features (In Progress / To Do)

- [ ] **Live Value Tracking (Core)**:
    - [ ] Track sales data for specific, graded cards (e.g., "Derek Jeter rookie PSA 9").
    - [ ] Implement backend logic to ingest and process this sales data.
- [ ] **Order Book Recording (Core)**:
    - [ ] Record buy/sell orders or listings that contribute to value tracking.
- [ ] **Card Listings**:
    - [ ] Allow users to list their cards for sale or trade.
    - [ ] Develop API endpoints for creating, viewing, and managing listings.
    - [ ] Basic frontend UI for listing and viewing cards.
- [ ] **Auction Functionality**:
    - [ ] Allow users to auction cards (e.g., Pokémon cards as an example focus).
    - [ ] Bidding system.
    - [ ] API endpoints and UI for auctions.
- [ ] **Value Change Graphs**:
    - [ ] Display historical value changes for cards.
    - [ ] API endpoints to provide data for graphs.
    - [ ] Frontend components to render graphs.
- [ ] **Grading Information**:
    - [ ] Store and display grading information (PSA, Beckett, etc.) for cards.
- [ ] **Support for "All Cards"**:
    - [ ] Ensure models and systems are flexible enough to accommodate diverse card types.
- [ ] **Facilitated Direct Payments (Phase 1 Method)**:
    - [ ] Allow users to specify preferred direct payment methods (CashApp, Venmo, PayPal.Me) on their profiles.
    - [ ] Display this information on listings or to transaction partners.

## Future Goals & Enhancements (Post Phase 1 / Demo)

- [ ] **Platform-Mediated Secure Online Transactions**:
    - [ ] Integrate payment gateways (e.g., Stripe, PayPal) for secure on-platform transactions.
    - [ ] Possible escrow-like features.
- [ ] **Advanced Search & Filtering**: For cards, listings, users.
- [ ] **Direct User-to-User Messaging**: Secure in-app communication.
- [ ] **User Reputation & Feedback System**: For traders and sellers.
- [ ] **Advanced Value Tracking Tools**: More sophisticated analytics, alerts, portfolio tracking.
- [ ] **Mobile Application (Google Play)**: Native Android app.
- [ ] **Full CAPTCHA Activation**: Resolve any environment issues and enable CAPTCHA for signups.
- [ ] **Refine Allauth Deprecation Warnings**: Update settings to align with latest `django-allauth` best practices.

## Jules' Suggestions & Notes

*(This section will be populated by Jules with specific suggestions or notes as development progresses)*

- *Initial Note (Date of creation): The `ModuleNotFoundError` for the `captcha` app during earlier development stages should be investigated in the target deployment or a full development environment. The code is present but the feature is currently bypassed in `settings.py`.*
- *Suggestion (Date of creation): Consider separating Django URL configurations more distinctly, e.g., `accounts.api_urls` and `accounts.web_urls`, for better organization as the project grows. (Partially addressed by having `/api/` prefix for most API routes).*

- **Recommendation (2025-06-20):** Prioritize resolving the `captcha` module environment issue to enable CAPTCHA on registration. This is important for preventing bot signups.
- **Recommendation (2025-06-20):** For Phase 1, clearly distinguish in the UI which features are fully implemented versus those that are mockups or placeholders for the demo (e.g., value graphs if data isn't fully live yet).
- **Recommendation (2025-06-20):** Start planning for robust data backup and security measures, especially as live financial data (even if just user payment handles) and personal information are stored.
- **Recommendation (2025-06-20):** When implementing card listings and auctions, consider early integration of a background task queue (e.g., Celery with Redis/RabbitMQ) for handling potentially long-running processes like auction expirations, notifications, or image processing if card images are uploaded.
- **Recommendation (2025-06-20):** Refactor Django URL configurations to separate web UI paths from API paths more clearly (e.g., `accounts/web/profile` vs `api/v1/accounts/profile`). This improves organization. (Partially noted before, reiterating for clarity).
- **Recommendation (2025-06-20):** Address the `django-allauth` deprecation warnings in `settings.py` at the next convenient opportunity to ensure long-term compatibility and adherence to best practices.

- **Operational Suggestion (2025-06-20):** Jules (the AI assistant) should, as a standard procedure or if technically feasible in future versions, read the `juleschecklist.md` file at the beginning of new chat sessions. This will ensure Jules is always informed of the latest project status, completed tasks, and active goals for the CDEX project.
