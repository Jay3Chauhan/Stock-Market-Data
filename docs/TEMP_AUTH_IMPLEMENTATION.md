# Firebase Authentication & Push Notification Implementation

## 📋 Implementation Progress

### ✅ Completed

#### 1. Firebase Configuration & Services
- [x] `Utils/firebase_config.py` - Firebase Admin SDK initialization
- [x] `Services/firebase_auth.py` - Core authentication service (verify token, decode token)
- [x] `Services/push_notification.py` - FCM push notification service

#### 2. User Management
- [x] `Utils/user_db.py` - MongoDB user CRUD operations
- [x] `API/Controller/user_controller.py` - User business logic (register, login, update FCM)

#### 3. Authentication Middleware
- [x] `Utils/auth_middleware.py` - FastAPI dependency for protected routes
  - `get_current_user` - Extracts and verifies Firebase token
  - `get_current_user_optional` - Optional auth for public endpoints

#### 4. API Router
- [x] `API/Router/auth_router.py` - Authentication endpoints
  - `POST /auth/register` - Register new user with phone
  - `POST /auth/login` - Login existing user
  - `POST /auth/verify-token` - Verify Firebase token
  - `GET /auth/me` - Get current user profile
  - `PUT /auth/fcm-token` - Update FCM token
  - `POST /auth/send-notification` - Send push notification (admin)

#### 5. Configuration
- [x] Updated `config.ini` - Added Firebase section
- [x] Updated `requirements.txt` - Added `firebase-admin`
- [x] Updated `requirements.lite.txt` - Added `firebase-admin`

#### 6. Integration
- [x] Updated `Loader/server.py` - Registered auth router with proper tags

---

## 🔥 Firebase Setup

### Prerequisites
1. **Firebase Admin SDK JSON file** (you'll provide this)
   - Place it at: `firebase-admin-sdk.json` in project root
   - Or specify custom path in `config.ini`

2. **Firebase Project Configuration**
   - Enable Authentication in Firebase Console
   - Enable Phone Authentication provider
   - Enable Cloud Messaging (FCM)

### Configuration (`config.ini`)

```ini
[FIREBASE]
# Firebase Admin SDK service account JSON file path (relative to project root)
ADMIN_SDK_PATH = firebase-admin-sdk.json

# Enable/disable Firebase authentication
ENABLED = True

# FCM notification settings
FCM_ENABLED = True
```

---

## 📱 MongoDB User Schema

**Collection**: `users`

```json
{
  "_id": ObjectId("..."),
  "uid": "firebase_uid_here",
  "phone_number": "+919876543210",
  "email": "user@example.com",
  "display_name": "John Doe",
  "photo_url": "https://...",
  "fcm_token": "fcm_device_token_here",
  "is_active": true,
  "created_at": "2026-01-26T10:30:00+05:30",
  "updated_at": "2026-01-26T10:30:00+05:30",
  "last_login": "2026-01-26T10:30:00+05:30",
  "metadata": {
    "device_info": "...",
    "app_version": "1.0.0"
  }
}
```

**Indexes**:
- `uid` (unique)
- `phone_number` (unique, sparse)
- `email` (unique, sparse)

---

## 🔐 API Endpoints

### Public Endpoints (No Auth Required)

#### 1. Register User
```http
POST /auth/register
Content-Type: application/json

{
  "firebase_token": "eyJhbGciOiJSUzI1...",
  "phone_number": "+919876543210",
  "fcm_token": "fcm_device_token_here"
}
```

**Response**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": {
      "uid": "firebase_uid",
      "phone_number": "+919876543210",
      "email": null,
      "display_name": null
    }
  },
  "timestamp": "2026-01-26T10:30:00+05:30"
}
```

#### 2. Login User
```http
POST /auth/login
Content-Type: application/json

{
  "firebase_token": "eyJhbGciOiJSUzI1...",
  "fcm_token": "fcm_device_token_here"
}
```

**Response**: Same as register

#### 3. Verify Token
```http
POST /auth/verify-token
Content-Type: application/json

{
  "firebase_token": "eyJhbGciOiJSUzI1..."
}
```

**Response**:
```json
{
  "success": true,
  "message": "Token is valid",
  "data": {
    "uid": "firebase_uid",
    "phone_number": "+919876543210",
    "email": "user@example.com"
  }
}
```

---

### Protected Endpoints (Requires Firebase Token)

**Add header to all protected requests**:
```http
Authorization: Bearer <firebase_token>
```

#### 1. Get Current User
```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJSUzI1...
```

**Response**:
```json
{
  "success": true,
  "data": {
    "uid": "firebase_uid",
    "phone_number": "+919876543210",
    "email": "user@example.com",
    "display_name": "John Doe",
    "fcm_token": "...",
    "created_at": "2026-01-26T10:30:00+05:30"
  }
}
```

#### 2. Update FCM Token
```http
PUT /auth/fcm-token
Authorization: Bearer eyJhbGciOiJSUzI1...
Content-Type: application/json

{
  "fcm_token": "new_fcm_token_here"
}
```

#### 3. Send Push Notification (Admin/Testing)
```http
POST /auth/send-notification
Authorization: Bearer eyJhbGciOiJSUzI1...
Content-Type: application/json

{
  "user_uid": "target_user_uid",
  "title": "Market Alert",
  "body": "NIFTY crossed 22,000!",
  "data": {
    "type": "market_alert",
    "symbol": "NIFTY"
  }
}
```

---

## 🔒 Protecting Existing Endpoints

### Example: Protect an existing endpoint

**Before**:
```python
@router.get("/nse/gainers-losers")
async def get_gainers_losers():
    # Anyone can access
    ...
```

**After** (requires authentication):
```python
from Utils.auth_middleware import get_current_user

@router.get("/nse/gainers-losers")
async def get_gainers_losers(current_user: dict = Depends(get_current_user)):
    # Only authenticated users can access
    # current_user contains: {"uid": "...", "phone_number": "...", ...}
    ...
```

**Optional Auth** (public but user-aware):
```python
from Utils.auth_middleware import get_current_user_optional

@router.get("/nse/gainers-losers")
async def get_gainers_losers(current_user: Optional[dict] = Depends(get_current_user_optional)):
    # Anyone can access
    # If authenticated: current_user = {"uid": "...", ...}
    # If not authenticated: current_user = None
    ...
```

---

## 📲 Push Notification Usage

### From Python Code

```python
from Services.push_notification import PushNotificationService

notification_service = PushNotificationService()

# Send to single user
await notification_service.send_to_user(
    user_uid="firebase_uid",
    title="Market Alert",
    body="NIFTY is up 2%!",
    data={"type": "market_alert", "symbol": "NIFTY"}
)

# Send to multiple users
await notification_service.send_to_multiple_users(
    user_uids=["uid1", "uid2", "uid3"],
    title="Daily Market Summary",
    body="Check today's top gainers"
)

# Data-only message (silent push)
await notification_service.send_data_message(
    fcm_token="device_token",
    data={"type": "data_sync", "timestamp": "..."}
)
```

---

## 🧪 Testing Commands

### 1. Test without Firebase (local development)
```bash
# Set ENABLED=False in config.ini [FIREBASE] section
# Auth middleware will skip verification in disabled mode
```

### 2. Test with Firebase
```bash
# Get Firebase token from your Flutter app
# Use it in Authorization header

curl -X POST http://localhost:1020/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_token": "YOUR_FIREBASE_TOKEN",
    "phone_number": "+919876543210",
    "fcm_token": "YOUR_FCM_TOKEN"
  }'
```

### 3. Test protected endpoint
```bash
curl -X GET http://localhost:1020/auth/me \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

### 4. Test push notification
```bash
curl -X POST http://localhost:1020/auth/send-notification \
  -H "Authorization: Bearer YOUR_ADMIN_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_uid": "target_user_uid",
    "title": "Test",
    "body": "Test notification"
  }'
```

---

## 🔧 Environment Setup

### Docker (Lite/Prod)

Add to `docker-compose.lite.yml` volumes:
```yaml
volumes:
  - ./firebase-admin-sdk.json:/app/firebase-admin-sdk.json:ro
```

### Requirements Installed
```bash
pip install firebase-admin
```

---

## 🚀 Deployment Steps

1. **Upload Firebase Admin SDK JSON**
   ```bash
   scp firebase-admin-sdk.json ubuntu@VM_IP:~/NSE-Scraper/
   ```

2. **Update config.ini**
   ```ini
   [FIREBASE]
   ADMIN_SDK_PATH = firebase-admin-sdk.json
   ENABLED = True
   FCM_ENABLED = True
   ```

3. **Rebuild & Restart**
   ```bash
   docker compose -f docker-compose.lite.yml up -d --build
   ```

4. **Verify**
   ```bash
   curl -X POST https://api.jaychauhan.tech/auth/verify-token \
     -H "Content-Type: application/json" \
     -d '{"firebase_token": "TEST_TOKEN"}'
   ```

---

## 📝 Frontend Integration Guide

### Flutter/React Native

```dart
// 1. Get Firebase Auth token
final user = FirebaseAuth.instance.currentUser;
final token = await user?.getIdToken();

// 2. Register/Login on backend
final response = await http.post(
  Uri.parse('https://api.jaychauhan.tech/auth/login'),
  headers: {'Content-Type': 'application/json'},
  body: json.encode({
    'firebase_token': token,
    'fcm_token': await FirebaseMessaging.instance.getToken(),
  }),
);

// 3. Store user data
final userData = json.decode(response.body)['data'];

// 4. Use token for API calls
final apiResponse = await http.get(
  Uri.parse('https://api.jaychauhan.tech/auth/me'),
  headers: {
    'Authorization': 'Bearer $token',
  },
);
```

---

## ⚠️ Security Notes

1. **Never commit `firebase-admin-sdk.json`** to git
   - Add to `.gitignore`
   - Use environment variables or secret management in production

2. **Token Expiry**
   - Firebase tokens expire after 1 hour
   - Frontend should refresh tokens automatically
   - Backend will return 401 for expired tokens

3. **Rate Limiting** (TODO)
   - Consider adding rate limiting to auth endpoints
   - Prevent brute force attacks

4. **CORS Configuration**
   - Update allowed origins in production
   - Currently set to `["*"]` for development

---

## 🐛 Common Issues & Solutions

### 1. "Firebase Admin SDK not initialized"
**Solution**: Check that `firebase-admin-sdk.json` exists and path is correct in `config.ini`

### 2. "Token verification failed"
**Solution**: 
- Ensure token is fresh (< 1 hour old)
- Check that Firebase project matches admin SDK
- Verify `Authorization: Bearer <token>` format

### 3. "User not found"
**Solution**: Call `/auth/register` or `/auth/login` first to create user in MongoDB

### 4. "Push notification failed"
**Solution**:
- Check FCM is enabled in Firebase Console
- Verify FCM token is valid and not expired
- Check user has `fcm_token` stored in MongoDB

---

## 📊 Monitoring & Logs

All authentication events are logged:
```bash
# View auth logs
docker compose -f docker-compose.lite.yml logs -f | grep -i "auth\|firebase"

# View from file
tail -f Logs/Services.firebase_auth.log
tail -f Logs/API.Controller.user_controller.log
```

---

## 🔄 Next Steps / TODO

- [ ] **Provide Firebase Admin SDK JSON file** to complete setup
- [ ] Add role-based access control (admin, user, etc.)
- [ ] Add user profile update endpoints
- [ ] Add email/password authentication support
- [ ] Implement refresh token mechanism
- [ ] Add rate limiting to auth endpoints
- [ ] Add audit logging for auth events
- [ ] Add user activity tracking
- [ ] Implement user blocking/suspension
- [ ] Add bulk notification sending for campaigns
- [ ] Add notification templates
- [ ] Add notification scheduling
- [ ] Add user preferences for notifications

---

## 📁 Files Created/Modified

### Created Files (12)
1. `Utils/firebase_config.py` - Firebase initialization
2. `Services/firebase_auth.py` - Auth service
3. `Services/push_notification.py` - Push notification service
4. `Utils/user_db.py` - User database operations
5. `API/Controller/user_controller.py` - User controller
6. `Utils/auth_middleware.py` - Auth middleware
7. `API/Router/auth_router.py` - Auth endpoints
8. `docs/TEMP_AUTH_IMPLEMENTATION.md` - This document

### Modified Files (3)
1. `config.ini` - Added Firebase section
2. `requirements.txt` - Added firebase-admin
3. `requirements.lite.txt` - Added firebase-admin
4. `Loader/server.py` - Registered auth router

---

**Last Updated**: 2026-01-26
**Implementation Status**: ✅ Complete (pending Firebase Admin SDK JSON file)
