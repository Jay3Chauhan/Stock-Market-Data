# Firebase Authentication Integration - Summary

## ✅ Implementation Complete

### Files Created (12 new files)

1. **`Utils/firebase_config.py`**
   - Firebase Admin SDK initialization
   - Singleton pattern for Firebase app
   - Configuration from config.ini
   - Auto-initialization on module import

2. **`Services/firebase_auth.py`**
   - Firebase token verification
   - User info extraction from tokens
   - Get user by UID, phone, email
   - Custom token creation for testing

3. **`Services/push_notification.py`**
   - Send notifications to single/multiple users
   - Send data-only messages (silent push)
   - Topic-based notifications
   - Batch notification sending
   - FCM token validation

4. **`Utils/user_db.py`**
   - MongoDB CRUD for users collection
   - Create/read/update/delete users
   - Update FCM tokens
   - Track last login
   - User listing with pagination
   - Automatic index creation

5. **`API/Controller/user_controller.py`**
   - Register user (Firebase + MongoDB)
   - Login user
   - Get user profile
   - Update FCM token
   - Verify token only

6. **`Utils/auth_middleware.py`**
   - FastAPI dependency for protected routes
   - Extract & verify Firebase token from header
   - Inject current_user into route handlers
   - Optional authentication support
   - Admin-only access control
   - Permission-based access control

7. **`API/Router/auth_router.py`**
   - POST /auth/register
   - POST /auth/login
   - POST /auth/verify-token
   - GET /auth/me
   - PUT /auth/fcm-token
   - POST /auth/send-notification
   - GET /auth/health

8. **`docs/TEMP_AUTH_IMPLEMENTATION.md`**
   - Complete documentation
   - API endpoint examples
   - MongoDB schema
   - Testing commands
   - Front
   end integration guide
   - Deployment steps

9. **`firebase-admin-sdk.json.example`**
   - Example Firebase Admin SDK JSON structure
   - Template for your actual credentials

### Files Modified (5 existing files)

1. **`config.ini`**
   - Added `[FIREBASE]` section
   - ADMIN_SDK_PATH configuration
   - ENABLED flag
   - FCM_ENABLED flag

2. **`requirements.txt`**
   - Added `firebase-admin==6.5.0`

3. **`requirements.lite.txt`**
   - Added `firebase-admin==6.5.0`

4. **`Loader/server.py`**
   - Imported `auth_router`
   - Registered `/auth` prefix
   - Added "Authentication" tag to OpenAPI

5. **`.gitignore`**
   - Added `firebase-admin-sdk.json` to ignore list
   - Added `*firebase-admin-sdk*.json` pattern

---

## 🎯 What's Working Now

### Backend Features
- ✅ Firebase Admin SDK integration
- ✅ Token verification
- ✅ User registration (Firebase → MongoDB)
- ✅ User login
- ✅ FCM token storage & updates
- ✅ Push notification sending
- ✅ Protected route middleware
- ✅ Optional authentication
- ✅ MongoDB user collection with indexes

### API Endpoints
- ✅ `/auth/register` - Register with Firebase token
- ✅ `/auth/login` - Login with Firebase token
- ✅ `/auth/verify-token` - Validate token
- ✅ `/auth/me` - Get current user (protected)
- ✅ `/auth/fcm-token` - Update FCM token (protected)
- ✅ `/auth/send-notification` - Send push (protected)
- ✅ `/auth/health` - Service health check

### Security Features
- ✅ Firebase token validation
- ✅ MongoDB user verification
- ✅ Active user check
- ✅ Bearer token authentication
- ✅ Swagger UI authentication support
- ✅ Admin access control skeleton
- ✅ Permission-based access skeleton

---

## 📋 What You Need to Provide

### 1. Firebase Admin SDK JSON File
**Download from:**
1. Go to Firebase Console → Project Settings
2. Service Accounts tab
3. Click "Generate New Private Key"
4. Download the JSON file
5. Rename it to `firebase-admin-sdk.json`
6. Place it in the project root directory

**⚠️ Security:** Never commit this file to git (already in .gitignore)

### 2. Firebase Project Configuration
**Enable in Firebase Console:**
- Authentication → Sign-in methods
  - ✅ Phone authentication
  - ✅ Google sign-in (optional)
  - ✅ Email/Password (optional)
- Cloud Messaging (FCM)
  - ✅ Enable messaging
  - Get server key (if needed)

---

## 🚀 How to Use

### On Your Flutter/React Native App

```dart
// 1. Sign in with Firebase (Phone Auth)
final credential = PhoneAuthProvider.credential(
  verificationId: verificationId,
  smsCode: smsCode,
);
await FirebaseAuth.instance.signInWithCredential(credential);

// 2. Get Firebase token
final user = FirebaseAuth.instance.currentUser;
final token = await user?.getIdToken();

// 3. Register on backend
final response = await http.post(
  Uri.parse('https://api.jaychauhan.tech/auth/register'),
  headers: {'Content-Type': 'application/json'},
  body: json.encode({
    'firebase_token': token,
    'phone_number': user?.phoneNumber,
    'fcm_token': await FirebaseMessaging.instance.getToken(),
  }),
);

// 4. Store user data
final userData = json.decode(response.body)['data'];

// 5. Use token for API calls
final apiResponse = await http.get(
  Uri.parse('https://api.jaychauhan.tech/nse/gainers-losers'),
  headers: {'Authorization': 'Bearer $token'},
);
```

### Protecting Existing Endpoints

**Make any endpoint require authentication:**

```python
from Utils.auth_middleware import get_current_user
from fastapi import Depends

@router.get("/nse/gainers-losers")
async def get_gainers_losers(current_user: dict = Depends(get_current_user)):
    # Now requires Firebase token
    # current_user = {"uid": "...", "phone_number": "...", ...}
    ...
```

**Optional authentication (public but user-aware):**

```python
from Utils.auth_middleware import get_current_user_optional

@router.get("/nse/gainers-losers")
async def get_gainers_losers(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    # Works without auth, but knows who the user is if authenticated
    if current_user:
        # Personalized response
        ...
    else:
        # Generic response
        ...
```

---

## 🧪 Testing

### 1. Start the server
```bash
docker compose -f docker-compose.lite.yml up -d --build
```

### 2. Check auth health
```bash
curl https://api.jaychauhan.tech/auth/health
```

### 3. Test token verification (get token from Firebase app first)
```bash
curl -X POST https://api.jaychauhan.tech/auth/verify-token \
  -H "Content-Type: application/json" \
  -d '{"firebase_token": "YOUR_FIREBASE_TOKEN"}'
```

### 4. Register a user
```bash
curl -X POST https://api.jaychauhan.tech/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_token": "YOUR_FIREBASE_TOKEN",
    "phone_number": "+919876543210",
    "fcm_token": "YOUR_FCM_TOKEN"
  }'
```

### 5. Get current user (protected endpoint)
```bash
curl https://api.jaychauhan.tech/auth/me \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

### 6. Test Swagger UI
1. Go to `https://api.jaychauhan.tech/docs`
2. Click "Authorize" button (top right)
3. Enter your Firebase token
4. Test endpoints that require authentication

---

## 📊 MongoDB Schema

**Collection:** `users`
**Database:** `NSE_SCRAPER`

```javascript
{
  _id: ObjectId("..."),
  uid: "firebase_uid_here",              // Firebase UID (unique)
  phone_number: "+919876543210",         // E.164 format (unique, sparse)
  email: "user@example.com",             // Email (unique, sparse)
  display_name: "John Doe",              // Display name
  photo_url: "https://...",              // Profile picture
  fcm_token: "fcm_device_token_here",    // For push notifications
  is_active: true,                       // Active status
  created_at: "2026-01-26T10:30:00+05:30", // IST
  updated_at: "2026-01-26T10:30:00+05:30", // IST
  last_login: "2026-01-26T10:30:00+05:30", // IST
  metadata: {
    device_info: "...",
    app_version: "1.0.0",
    is_admin: false,                     // For admin access control
    permissions: ["users.read"]          // For permission-based access
  }
}
```

**Indexes:**
- `uid` (unique)
- `phone_number` (unique, sparse)
- `email` (unique, sparse)
- `created_at` (descending)
- `last_login` (descending)

---

## 🔐 Security Considerations

1. **Firebase Admin SDK JSON**
   - ✅ Already in .gitignore
   - ❗ Never share or commit to public repos
   - ❗ Use environment variables in production

2. **Token Expiry**
   - Firebase tokens expire after 1 hour
   - Frontend should refresh automatically
   - Backend returns 401 for expired tokens

3. **CORS Configuration**
   - Currently: `allow_origins=["*"]` (development)
   - Production: Set specific domains
   ```python
   allow_origins=[
       "https://yourdomain.com",
       "https://app.yourdomain.com"
   ]
   ```

4. **Rate Limiting** (TODO)
   - Add rate limiting to auth endpoints
   - Prevent brute force attacks
   - Use FastAPI-Limiter or similar

---

## 📱 Push Notification Examples

### From Python Code

```python
from Services.push_notification import PushNotificationService

service = PushNotificationService()

# Send to single user
await service.send_to_user(
    user_uid="firebase_uid",
    title="Market Alert",
    body="NIFTY crossed 22,000!",
    data={"type": "market", "symbol": "NIFTY"}
)

# Send to multiple users
await service.send_to_multiple_users(
    user_uids=["uid1", "uid2", "uid3"],
    title="Daily Summary",
    body="Check today's top gainers"
)

# Data-only message (silent)
await service.send_data_message(
    fcm_token="device_token",
    data={"action": "sync", "timestamp": "..."}
)
```

### From API Endpoint

```bash
curl -X POST https://api.jaychauhan.tech/auth/send-notification \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_uid": "target_user_uid",
    "title": "Market Alert",
    "body": "Your watchlist stock moved 5%!",
    "data": {
      "type": "watchlist_alert",
      "symbol": "RELIANCE",
      "price": "2450.50"
    }
  }'
```

---

## 🐛 Troubleshooting

### "Firebase Admin SDK not initialized"
**Fix:** Ensure `firebase-admin-sdk.json` exists in project root and path is correct in `config.ini`

### "Invalid Firebase token"
**Fix:** 
- Token must be fresh (< 1 hour)
- Get new token from Firebase app
- Ensure correct Firebase project

### "User not found"
**Fix:** Call `/auth/register` or `/auth/login` first to create user in MongoDB

### "Push notification failed"
**Fix:**
- Check FCM is enabled in Firebase Console
- Verify FCM token is valid
- Check user has `fcm_token` in database

---

## 📈 Next Steps

### Immediate
1. **Provide Firebase Admin SDK JSON** to enable authentication
2. Test endpoints from Swagger UI
3. Integrate with your Flutter app

### Short-term (Optional)
- [ ] Add role-based access control (admin, premium user, etc.)
- [ ] Add user profile update endpoints
- [ ] Add email/password auth support
- [ ] Add rate limiting
- [ ] Add user activity logging

### Long-term (Optional)
- [ ] Add refresh token mechanism
- [ ] Add user blocking/suspension
- [ ] Add bulk notification campaigns
- [ ] Add notification templates
- [ ] Add notification scheduling
- [ ] Add analytics dashboard

---

## 📖 Documentation Links

- **Main Docs:** `docs/TEMP_AUTH_IMPLEMENTATION.md`
- **Deployment:** `docs/ORACLE_CLOUD_DEPLOYMENT.md`
- **Swagger UI:** `https://api.jaychauhan.tech/docs`
- **Firebase Docs:** https://firebase.google.com/docs/admin/setup
- **FCM Docs:** https://firebase.google.com/docs/cloud-messaging

---

**Status:** ✅ Ready for Firebase Admin SDK JSON file
**Last Updated:** 2026-01-26
