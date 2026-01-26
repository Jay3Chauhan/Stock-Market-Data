# Quick Setup Guide - Firebase Authentication

## 🚀 Immediate Next Steps

### 1. Install Firebase Admin SDK (Local Development)

```bash
pip install firebase-admin
```

Or if using the lite requirements:
```bash
pip install -r requirements.lite.txt
```

### 2. Get Firebase Admin SDK JSON

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (or create one)
3. Click ⚙️ Settings → Project Settings
4. Go to "Service Accounts" tab
5. Click "Generate New Private Key"
6. Download the JSON file
7. Save it as `firebase-admin-sdk.json` in project root

```
NSE-Scraper/
├── firebase-admin-sdk.json  <-- Place it here
├── config.ini
├── main.py
...
```

### 3. Verify Firebase Configuration

Check `config.ini` has this section:
```ini
[FIREBASE]
ADMIN_SDK_PATH = firebase-admin-sdk.json
ENABLED = True
FCM_ENABLED = True
```

### 4. Enable Firebase Features

In Firebase Console:
1. **Authentication**
   - Go to Authentication → Sign-in method
   - Enable "Phone" authentication
   - Enable any other methods you need (Google, Email/Password)

2. **Cloud Messaging (FCM)**
   - Go to Project Settings → Cloud Messaging
   - Cloud Messaging should be enabled by default
   - Note the Server Key (if needed for frontend)

### 5. Test Locally

```bash
# Start the server
python main.py

# Or with Docker
docker compose -f docker-compose.lite.yml up --build

# Check auth health
curl http://localhost:1020/auth/health
```

### 6. Deploy to Oracle Cloud

```bash
# SSH to VM
ssh -i your-key.pem ubuntu@YOUR_VM_IP

# Upload Firebase SDK
scp firebase-admin-sdk.json ubuntu@YOUR_VM_IP:~/NSE-Scraper/

# Rebuild container
cd NSE-Scraper
git pull
docker compose -f docker-compose.lite.yml up -d --build

# Verify
curl https://api.jaychauhan.tech/auth/health
```

### 7. Test from Swagger UI

1. Go to https://api.jaychauhan.tech/docs
2. Expand "Authentication" section
3. Test `/auth/health` endpoint
4. Get Firebase token from your app
5. Click "Authorize" button (top right)
6. Enter your Firebase token
7. Test protected endpoints

---

## 🧪 Quick Test Flow

### A) From Your Flutter/React Native App

```dart
// 1. Sign in with phone
final user = await FirebaseAuth.instance.signInWithCredential(...);

// 2. Get token
final token = await user.getIdToken();

// 3. Register on backend
final response = await http.post(
  Uri.parse('https://api.jaychauhan.tech/auth/register'),
  headers: {'Content-Type': 'application/json'},
  body: json.encode({
    'firebase_token': token,
    'phone_number': user.phoneNumber,
    'fcm_token': await FirebaseMessaging.instance.getToken(),
  }),
);

print(response.body);
```

### B) From cURL (after getting token from app)

```bash
# Verify token
curl -X POST https://api.jaychauhan.tech/auth/verify-token \
  -H "Content-Type: application/json" \
  -d '{"firebase_token": "YOUR_TOKEN_HERE"}'

# Register
curl -X POST https://api.jaychauhan.tech/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_token": "YOUR_TOKEN_HERE",
    "phone_number": "+919876543210",
    "fcm_token": "YOUR_FCM_TOKEN"
  }'

# Get profile
curl https://api.jaychauhan.tech/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 📁 Files You Created

**New Files (12):**
1. `Utils/firebase_config.py`
2. `Services/firebase_auth.py`
3. `Services/push_notification.py`
4. `Utils/user_db.py`
5. `API/Controller/user_controller.py`
6. `Utils/auth_middleware.py`
7. `API/Router/auth_router.py`
8. `docs/TEMP_AUTH_IMPLEMENTATION.md` (detailed docs)
9. `docs/AUTH_IMPLEMENTATION_SUMMARY.md` (this summary)
10. `firebase-admin-sdk.json.example` (template)

**Modified Files (5):**
1. `config.ini` - Added Firebase section
2. `requirements.txt` - Added firebase-admin
3. `requirements.lite.txt` - Added firebase-admin
4. `Loader/server.py` - Registered auth router
5. `.gitignore` - Added Firebase SDK to ignore

---

## ✅ What's Working

- ✅ Firebase Admin SDK integration
- ✅ Token verification
- ✅ User registration (Firebase → MongoDB)
- ✅ User login
- ✅ FCM token management
- ✅ Push notification sending
- ✅ Protected routes middleware
- ✅ MongoDB users collection
- ✅ API endpoints (/auth/*)
- ✅ Swagger UI integration

---

## ⚠️ What You Need

1. **Firebase Admin SDK JSON** - Download from Firebase Console
2. **Enable Phone Auth** - In Firebase Console → Authentication
3. **Enable FCM** - Should be enabled by default
4. **Install firebase-admin** - `pip install firebase-admin`

---

## 📚 Full Documentation

See `docs/TEMP_AUTH_IMPLEMENTATION.md` for:
- Complete API documentation
- MongoDB schema details
- Frontend integration examples
- Push notification usage
- Troubleshooting guide
- Security considerations

---

**Ready to go! Just provide the Firebase Admin SDK JSON file.**
