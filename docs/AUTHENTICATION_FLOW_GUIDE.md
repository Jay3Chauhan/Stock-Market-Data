# Authentication Flow Guide for Flutter Integration

## Overview
This document provides a complete authentication flow for integrating the NSE Scraper backend with your Flutter application. **No code is provided** - only the logical flow, API endpoints to call, and expected request/response formats.

**Supported Authentication Methods:**
- ✅ Email/Password Authentication
- ✅ Google Sign-In (OAuth)
- ❌ Phone Number Authentication (Removed - requires paid Firebase plan)

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [User Registration Flow](#user-registration-flow)
3. [User Login Flow](#user-login-flow)
4. [Google Sign-In Flow](#google-sign-in-flow)
5. [Get User Profile Flow](#get-user-profile-flow)
6. [Update FCM Token Flow](#update-fcm-token-flow)
7. [Logout Flow](#logout-flow)
8. [Delete Account Flow](#delete-account-flow)
9. [Token Verification Flow](#token-verification-flow)
10. [Error Handling](#error-handling)
11. [Security Best Practices](#security-best-practices)

---

## Prerequisites

### 1. Firebase Project Setup
- Create Firebase project at https://console.firebase.google.com
- Enable **Email/Password** authentication
- Enable **Google** sign-in provider
- Add your Flutter app (Android/iOS/Web) to Firebase project
- Download and add configuration files:
  - `google-services.json` (Android)
  - `GoogleService-Info.plist` (iOS)
  - Firebase config for Web

### 2. Backend API Configuration
- **Base URL**: `https://api.jaychauhan.tech` (Production) or `http://localhost:1020` (Development)
- **Authentication Header**: `Authorization: Bearer <firebase_id_token>`

---

## User Registration Flow

### Purpose
Register a new user in the system after Firebase authentication.

### Step-by-Step Flow

1. **User Action**
   - User opens registration screen
   - User enters email and password
   - User clicks "Register" button

2. **Firebase Authentication (Client-Side)**
   - Call Firebase SDK method: `createUserWithEmailAndPassword(email, password)`
   - Firebase returns:
     - Success: Firebase User object with UID
     - Error: Handle Firebase error (weak password, email already exists, etc.)

3. **Get Firebase ID Token**
   - Call Firebase method: `user.getIdToken()`
   - Store this token temporarily (valid for 1 hour)

4. **Backend Registration**
   - **Endpoint**: `POST /auth/register`
   - **Headers**:
     ```
     Content-Type: application/json
     ```
   - **Request Body**:
     ```json
     {
       "firebase_token": "<firebase_id_token>",
       "fcm_token": "<fcm_device_token>"  // Optional for push notifications
     }
     ```

5. **Backend Response**
   - **Success (200)**:
     ```json
     {
       "success": true,
       "message": "User registered successfully",
       "data": {
         "user": {
           "uid": "firebase_user_uid",
           "email": "user@example.com",
           "display_name": "User Name",
           "photo_url": null,
           "is_active": true,
           "created_at": "2026-01-26T10:30:00.000000+05:30",
           "last_login": "2026-01-26T10:30:00.000000+05:30"
         },
         "is_new_user": true
       }
     }
     ```
   - **Error (400/500)**:
     ```json
     {
       "success": false,
       "message": "Registration failed",
       "error": "TOKEN_INVALID"
     }
     ```

6. **Store User Data Locally**
   - Save user profile data in local storage (SharedPreferences/Hive/etc.)
   - Save Firebase token for authenticated API calls
   - Navigate to home screen

### Important Notes
- Firebase token must be fresh (obtained after successful Firebase auth)
- FCM token is optional but recommended for push notifications
- Backend automatically creates user in MongoDB
- If user already exists, backend returns existing user data with `is_new_user: false`

---

## User Login Flow

### Purpose
Login existing user and sync data with backend.

### Step-by-Step Flow

1. **User Action**
   - User opens login screen
   - User enters email and password
   - User clicks "Login" button

2. **Firebase Authentication (Client-Side)**
   - Call Firebase SDK method: `signInWithEmailAndPassword(email, password)`
   - Firebase returns:
     - Success: Firebase User object with UID
     - Error: Handle Firebase error (wrong password, user not found, etc.)

3. **Get Firebase ID Token**
   - Call Firebase method: `user.getIdToken()`
   - Token is valid for 1 hour

4. **Backend Login**
   - **Endpoint**: `POST /auth/login`
   - **Headers**:
     ```
     Content-Type: application/json
     ```
   - **Request Body**:
     ```json
     {
       "firebase_token": "<firebase_id_token>",
       "fcm_token": "<fcm_device_token>"  // Optional
     }
     ```

5. **Backend Response**
   - **Success (200)**:
     ```json
     {
       "success": true,
       "message": "Login successful",
       "data": {
         "user": {
           "uid": "firebase_user_uid",
           "email": "user@example.com",
           "display_name": "User Name",
           "photo_url": null,
           "fcm_token": "updated_fcm_token",
           "is_active": true,
           "created_at": "2026-01-20T10:30:00.000000+05:30",
           "last_login": "2026-01-26T10:35:00.000000+05:30"
         },
         "is_new_user": false
       }
     }
     ```
   - **Error (401/500)**:
     ```json
     {
       "success": false,
       "message": "Login failed",
       "error": "TOKEN_INVALID"
     }
     ```

6. **Update Local Data**
   - Update user profile in local storage
   - Update last login timestamp
   - Navigate to home screen

### Important Notes
- If user doesn't exist in MongoDB, backend automatically registers them
- Backend updates `last_login` timestamp
- Backend updates FCM token if provided
- Token must be refreshed every hour (Firebase handles this automatically)

---

## Google Sign-In Flow

### Purpose
Authenticate users using their Google account.

### Step-by-Step Flow

1. **User Action**
   - User clicks "Sign in with Google" button
   - Google sign-in popup/bottom sheet appears

2. **Google Authentication (Client-Side)**
   - Call Firebase SDK method: `signInWithGoogle()`
   - User selects Google account
   - Firebase returns:
     - Success: Firebase User object with email, name, photo
     - Error: Handle cancellation or Google auth error

3. **Get Firebase ID Token**
   - Call Firebase method: `user.getIdToken()`
   - Token contains Google user info

4. **Backend Registration/Login**
   - **Endpoint**: `POST /auth/register` (same endpoint works for both)
   - **Headers**:
     ```
     Content-Type: application/json
     ```
   - **Request Body**:
     ```json
     {
       "firebase_token": "<firebase_id_token>",
       "fcm_token": "<fcm_device_token>"  // Optional
     }
     ```

5. **Backend Response**
   - **Success (200)** - New User:
     ```json
     {
       "success": true,
       "message": "User registered successfully",
       "data": {
         "user": {
           "uid": "google_user_uid",
           "email": "user@gmail.com",
           "display_name": "Google User Name",
           "photo_url": "https://lh3.googleusercontent.com/...",
           "is_active": true,
           "created_at": "2026-01-26T10:30:00.000000+05:30"
         },
         "is_new_user": true
       }
     }
     ```
   - **Success (200)** - Existing User:
     ```json
     {
       "success": true,
       "message": "Login successful",
       "data": {
         "user": { /* same structure */ },
         "is_new_user": false
       }
     }
     ```

6. **Store User Data**
   - Save Google profile data (including photo URL)
   - Save Firebase token
   - Navigate to home screen

### Important Notes
- Backend automatically detects if user is new or existing
- Google profile photo URL is automatically stored
- Display name from Google is used by default
- Same endpoint handles both registration and login for Google users

---

## Get User Profile Flow

### Purpose
Fetch current user's profile data from backend.

### Step-by-Step Flow

1. **Prerequisites**
   - User must be logged in
   - Firebase token must be valid (not expired)

2. **Refresh Token if Needed**
   - Check token expiry (tokens expire after 1 hour)
   - If expired, call: `user.getIdToken(forceRefresh: true)`

3. **Fetch Profile**
   - **Endpoint**: `GET /auth/me`
   - **Headers**:
     ```
     Authorization: Bearer <firebase_id_token>
     Content-Type: application/json
     ```
   - **Request Body**: None (GET request)

4. **Backend Response**
   - **Success (200)**:
     ```json
     {
       "success": true,
       "message": "User profile retrieved successfully",
       "data": {
         "user": {
           "uid": "user_uid",
           "email": "user@example.com",
           "display_name": "User Name",
           "photo_url": "https://...",
           "fcm_token": "current_fcm_token",
           "is_active": true,
           "created_at": "2026-01-20T10:30:00.000000+05:30",
           "last_login": "2026-01-26T10:35:00.000000+05:30",
           "metadata": {}
         }
       }
     }
     ```
   - **Error (401)**:
     ```json
     {
       "detail": "Invalid or expired token"
     }
     ```

5. **Update Local Cache**
   - Update user data in local storage
   - Refresh UI with latest profile data

### When to Use This
- On app startup (to sync latest data)
- After network reconnection
- When user navigates to profile screen
- After updating profile in Firebase

---

## Update FCM Token Flow

### Purpose
Update user's FCM device token for push notifications.

### Step-by-Step Flow

1. **When to Update**
   - On app startup (if token changed)
   - When Firebase generates new FCM token
   - After user logs in on new device

2. **Get Current FCM Token**
   - Call Firebase Messaging: `getToken()`
   - Store token locally

3. **Update Token in Backend**
   - **Endpoint**: `PUT /auth/fcm-token`
   - **Headers**:
     ```
     Authorization: Bearer <firebase_id_token>
     Content-Type: application/json
     ```
   - **Request Body**:
     ```json
     {
       "fcm_token": "<new_fcm_device_token>"
     }
     ```

4. **Backend Response**
   - **Success (200)**:
     ```json
     {
       "success": true,
       "message": "FCM token updated successfully",
       "data": {
         "uid": "user_uid",
         "fcm_token": "updated_token"
       }
     }
     ```
   - **Error (401/500)**:
     ```json
     {
       "detail": "Failed to update FCM token"
     }
     ```

5. **Store Updated Token**
   - Update local token reference
   - Log success for debugging

### Important Notes
- Always update FCM token after login
- Listen for token refresh events from Firebase Messaging
- Backend uses this token to send push notifications
- Token can become invalid if app is uninstalled/reinstalled

---

## Logout Flow

### Purpose
Sign out user and clean up local data.

### Step-by-Step Flow

1. **User Action**
   - User clicks "Logout" button
   - Show confirmation dialog (optional)

2. **Clear Local Data**
   - Remove user profile from local storage
   - Clear cached API responses
   - Clear any sensitive data

3. **Firebase Sign Out**
   - Call Firebase SDK method: `signOut()`
   - This invalidates the current session

4. **Optional: Clear FCM Token on Backend**
   - **Endpoint**: `PUT /auth/fcm-token`
   - **Headers**:
     ```
     Authorization: Bearer <firebase_id_token>
     ```
   - **Request Body**:
     ```json
     {
       "fcm_token": null
     }
     ```
   - This prevents notifications after logout

5. **Navigation**
   - Navigate to login/welcome screen
   - Reset navigation stack (remove history)

### Important Notes
- No backend API call required (Firebase handles session)
- Optional: Clear FCM token to stop notifications
- Always clear sensitive local data
- Firebase token becomes invalid after signOut()

---

## Delete Account Flow

### Purpose
Permanently delete user account and all associated data.

### Step-by-Step Flow

1. **User Action**
   - User navigates to account settings
   - User clicks "Delete Account" button
   - **IMPORTANT**: Show strong warning dialog with:
     - "This action cannot be undone"
     - "All your data will be permanently deleted"
     - Require user confirmation (type "DELETE" or similar)

2. **Re-authenticate User (Required)**
   - For security, Firebase requires recent authentication
   - If user logged in recently (< 5 minutes): Skip this
   - If not recent: Re-authenticate using:
     - Email/Password: Call `signInWithEmailAndPassword()`
     - Google: Call `signInWithGoogle()`

3. **Delete from Backend First**
   - **Endpoint**: `DELETE /auth/me`
   - **Headers**:
     ```
     Authorization: Bearer <firebase_id_token>
     Content-Type: application/json
     ```
   - **Request Body**: None

4. **Backend Response**
   - **Success (200)**:
     ```json
     {
       "success": true,
       "message": "User account deleted successfully",
       "data": {
         "uid": "user_uid",
         "deleted_at": "2026-01-26T10:40:00.000000+05:30"
       }
     }
     ```
   - **Error (401/500)**:
     ```json
     {
       "detail": "Failed to delete user account"
     }
     ```

5. **Delete from Firebase**
   - Call Firebase SDK method: `user.delete()`
   - This permanently removes user from Firebase Authentication
   - **Error Handling**:
     - If "requires-recent-login" error: Go back to step 2
     - If other error: Show error message to user

6. **Clear Local Data**
   - Remove all user data from local storage
   - Clear app cache
   - Clear any databases (Hive, SQLite, etc.)

7. **Navigation**
   - Navigate to welcome/login screen
   - Show success message: "Account deleted successfully"
   - Reset navigation stack completely

### Important Notes
- **Order matters**: Delete from backend FIRST, then Firebase
- If Firebase deletion fails but backend succeeds: User can't login anymore
- If backend deletion fails: Stop and show error (don't delete from Firebase)
- Re-authentication is mandatory for security
- All user data in MongoDB is permanently deleted
- Firebase Auth user is permanently deleted
- FCM token is automatically removed

---

## Token Verification Flow

### Purpose
Verify Firebase ID token validity without database operations (useful for debugging).

### Step-by-Step Flow

1. **When to Use**
   - Debugging authentication issues
   - Checking token expiry before API calls
   - Validating token after refresh

2. **Verify Token**
   - **Endpoint**: `POST /auth/verify-token`
   - **Headers**:
     ```
     Content-Type: application/json
     ```
   - **Request Body**:
     ```json
     {
       "firebase_token": "<firebase_id_token>"
     }
     ```

3. **Backend Response**
   - **Success (200)**:
     ```json
     {
       "success": true,
       "message": "Token is valid",
       "data": {
         "uid": "user_uid",
         "email": "user@example.com",
         "name": "User Name",
         "picture": "https://...",
         "email_verified": true
       }
     }
     ```
   - **Error (401)**:
     ```json
     {
       "success": false,
       "message": "Token verification failed",
       "error": "TOKEN_EXPIRED / TOKEN_INVALID"
     }
     ```

4. **Handle Response**
   - If valid: Continue with API calls
   - If invalid: Refresh token or force re-login

### Important Notes
- This endpoint does NOT create or update user in database
- Use this for token validation only
- Token expiry is 1 hour by default
- Backend verifies signature, expiry, and Firebase project

---

## Error Handling

### Common Error Scenarios

#### 1. Invalid or Expired Token (401)
**Cause**: Firebase token expired (> 1 hour old) or invalid

**Solution**:
```
1. Call user.getIdToken(forceRefresh: true)
2. Retry API call with new token
3. If still fails: Force user to re-login
```

#### 2. User Not Found (404)
**Cause**: User exists in Firebase but not in MongoDB

**Solution**:
```
1. Call /auth/register endpoint
2. Backend will create user in MongoDB
3. Continue normal flow
```

#### 3. Network Error
**Cause**: No internet connection or server down

**Solution**:
```
1. Show user-friendly error message
2. Implement retry logic with exponential backoff
3. Cache data locally if possible
```

#### 4. Firebase Authentication Error
**Cause**: Wrong password, email not found, weak password, etc.

**Solution**:
```
1. Catch Firebase exception
2. Parse error code (wrong-password, user-not-found, etc.)
3. Show appropriate error message to user
4. Do NOT call backend if Firebase auth fails
```

#### 5. Account Disabled (403)
**Cause**: User account is disabled in Firebase or backend

**Solution**:
```
1. Show error message: "Account disabled. Contact support."
2. Provide support email/contact
3. Force logout
```

### Error Response Format
All backend errors follow this structure:
```json
{
  "detail": "Error message here"
}
```

Or for custom errors:
```json
{
  "success": false,
  "message": "Human-readable error message",
  "error": "ERROR_CODE"
}
```

---

## Security Best Practices

### 1. Token Management
- ✅ **Never store Firebase ID token permanently** (it expires in 1 hour)
- ✅ **Refresh token before API calls** if it's about to expire
- ✅ **Use secure storage** for sensitive data (Flutter Secure Storage)
- ❌ **Never log tokens** in production builds

### 2. API Calls
- ✅ **Always use HTTPS** in production (`https://api.jaychauhan.tech`)
- ✅ **Implement request timeout** (e.g., 30 seconds)
- ✅ **Retry failed requests** with exponential backoff
- ✅ **Validate response data** before using it

### 3. User Data
- ✅ **Encrypt sensitive data** in local storage
- ✅ **Clear data on logout** completely
- ✅ **Validate user input** before sending to backend
- ❌ **Never store passwords** locally

### 4. Firebase Configuration
- ✅ **Enable email verification** (optional but recommended)
- ✅ **Set password policy** (minimum 6 characters)
- ✅ **Enable multi-factor authentication** (optional for high security)
- ✅ **Monitor Firebase Console** for suspicious activity

### 5. Error Messages
- ✅ **Show user-friendly messages** to users
- ✅ **Log detailed errors** for debugging (dev mode only)
- ❌ **Never expose internal errors** to users in production

---

## Complete Flow Summary

### Registration Flow
```
User Input → Firebase createUser() → Get ID Token → 
POST /auth/register → Store Data Locally → Navigate to Home
```

### Login Flow
```
User Input → Firebase signIn() → Get ID Token → 
POST /auth/login → Update Local Data → Navigate to Home
```

### Google Sign-In Flow
```
Click Google Button → Firebase signInWithGoogle() → Get ID Token → 
POST /auth/register → Store Data → Navigate to Home
```

### Authenticated API Call Flow
```
Check Token Expiry → Refresh if Needed → Add Authorization Header → 
Make API Call → Handle Response → Update UI
```

### Logout Flow
```
Clear Local Data → Firebase signOut() → Optional: Clear FCM Token → 
Navigate to Login Screen
```

### Delete Account Flow
```
Show Warning → Re-authenticate → DELETE /auth/me → 
Firebase user.delete() → Clear Local Data → Navigate to Login
```

---

## API Endpoints Summary

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/auth/register` | POST | No | Register new user |
| `/auth/login` | POST | No | Login existing user |
| `/auth/verify-token` | POST | No | Verify token validity |
| `/auth/me` | GET | Yes | Get user profile |
| `/auth/fcm-token` | PUT | Yes | Update FCM token |
| `/auth/me` | DELETE | Yes | Delete account |
| `/health` | GET | No | Check backend status |
| `/auth/health` | GET | No | Check Firebase connectivity |

---

## Testing Checklist

### Registration Testing
- [ ] Register with valid email and password
- [ ] Try registering with existing email (should show error)
- [ ] Try registering with weak password (Firebase error)
- [ ] Verify user created in MongoDB (check via `/auth/me`)
- [ ] Verify FCM token stored correctly

### Login Testing
- [ ] Login with correct credentials
- [ ] Try login with wrong password (Firebase error)
- [ ] Try login with non-existent email (Firebase error)
- [ ] Verify last_login timestamp updates
- [ ] Verify FCM token updates on login

### Google Sign-In Testing
- [ ] Sign in with Google for first time (registration)
- [ ] Sign in with Google again (login)
- [ ] Verify display_name and photo_url stored correctly
- [ ] Verify email from Google stored

### Token Management Testing
- [ ] Make API call with valid token
- [ ] Make API call with expired token (should auto-refresh)
- [ ] Make API call with invalid token (should fail with 401)
- [ ] Verify token refresh works correctly

### Profile Testing
- [ ] Fetch profile after login
- [ ] Verify all fields returned correctly
- [ ] Update profile in Firebase, fetch again (should sync)

### Logout Testing
- [ ] Logout and verify local data cleared
- [ ] Verify can't make authenticated API calls after logout
- [ ] Verify navigation to login screen

### Delete Account Testing
- [ ] Delete account with recent authentication
- [ ] Try delete without re-authentication (should require it)
- [ ] Verify user deleted from backend
- [ ] Verify user deleted from Firebase
- [ ] Verify can't login with deleted credentials

---

## Troubleshooting

### Issue: "Invalid Firebase token" error
**Solution**: Token might be expired. Call `user.getIdToken(forceRefresh: true)`

### Issue: User exists in Firebase but not in backend
**Solution**: Call `/auth/register` endpoint to sync user to MongoDB

### Issue: FCM notifications not working
**Solution**: Verify FCM token is updated after login using `/auth/fcm-token`

### Issue: Token refresh not working
**Solution**: Check Firebase SDK version, ensure `getIdToken(forceRefresh: true)` is called

### Issue: Google Sign-In not working
**Solution**: Verify SHA-1 fingerprint added in Firebase Console (Android)

### Issue: Account deletion fails with "requires-recent-login"
**Solution**: Re-authenticate user before deleting (within last 5 minutes)

---

## Support

For backend API issues or questions:
- API Documentation: `https://api.jaychauhan.tech/docs`
- Backend Logs: Check Oracle VM Docker logs
- Firebase Console: Monitor authentication events

For Flutter integration issues:
- Firebase Documentation: https://firebase.google.com/docs/flutter
- FlutterFire GitHub: https://github.com/firebase/flutterfire

---

**Last Updated**: January 26, 2026
**API Version**: 1.0
**Backend URL**: https://api.jaychauhan.tech
