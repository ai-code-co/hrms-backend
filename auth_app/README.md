ADMIN
  │
  ├── POST /auth/login/ (JWT)
  │
  ├── POST /auth/users/
  │        ↓
  │   User created (inactive, unverified)
  │        ↓
  │   Verification email sent
  │
USER
  │
  ├── GET /auth/verify-email/<token>/
  │        ↓
  │   Account activated + verified
  │        ↓
  │   Redirect → frontend /set-password?token=XYZ
  │
  ├── POST /auth/set-password/
  │        ↓
  │   Password set
  │
  ├── POST /auth/login/
  │        ↓
  │   JWT issued
  │
  ├── POST /auth/change-password/ (logged in)
  │
  └── POST /auth/forgot-password/
           ↓
      Email reset link
           ↓
      POST /auth/set-password/
