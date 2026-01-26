# Flutter Firebase Authentication Integration Guide

**Backend API:** `https://api.jaychauhan.tech`  
**Firebase Project:** `ipo-lens`  
**Authentication Methods:** Phone Number + Email/Password

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Firebase Setup in Flutter](#firebase-setup-in-flutter)
3. [Package Dependencies](#package-dependencies)
4. [Firebase Configuration](#firebase-configuration)
5. [Authentication Service Implementation](#authentication-service-implementation)
6. [API Service Implementation](#api-service-implementation)
7. [User Model](#user-model)
8. [Authentication Flow](#authentication-flow)
9. [Protected API Calls](#protected-api-calls)
10. [FCM Push Notifications](#fcm-push-notifications)
11. [Error Handling](#error-handling)
12. [Complete Usage Examples](#complete-usage-examples)

---

## Prerequisites

- Flutter SDK installed (3.0.0 or higher)
- Firebase project created: `ipo-lens`
- Firebase Authentication enabled (Phone + Email/Password)
- Firebase Cloud Messaging enabled
- Android: `google-services.json` in `android/app/`
- iOS: `GoogleService-Info.plist` in `ios/Runner/`

---

## Firebase Setup in Flutter

### Step 1: Add Firebase to Your Flutter Project

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Install FlutterFire CLI
dart pub global activate flutterfire_cli

# Configure Firebase for your Flutter app
flutterfire configure --project=ipo-lens
```

This will automatically:
- Create `firebase_options.dart`
- Add platform-specific config files
- Link your app to the `ipo-lens` Firebase project

---

## Package Dependencies

Add these to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # Firebase Core (Required)
  firebase_core: ^3.8.1
  
  # Firebase Authentication
  firebase_auth: ^5.3.3
  
  # Firebase Cloud Messaging (FCM)
  firebase_messaging: ^15.1.5
  
  # HTTP Client for API calls
  http: ^1.2.0
  
  # Secure Storage for tokens
  flutter_secure_storage: ^9.2.2
  
  # State Management (choose one)
  provider: ^6.1.1
  # OR
  # riverpod: ^2.5.1
  # OR
  # bloc: ^8.1.4
  
  # Optional: Phone Number Input
  intl_phone_field: ^3.2.0
  
  # Optional: JWT Decoder
  jwt_decoder: ^2.0.1

dev_dependencies:
  flutter_test:
    sdk: flutter
```

Run:
```bash
flutter pub get
```

---

## Firebase Configuration

### Initialize Firebase in `main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IPO Lens',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const AuthWrapper(),
    );
  }
}
```

---

## Authentication Service Implementation

Create `lib/services/auth_service.dart`:

```dart
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import 'api_service.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  final ApiService _apiService = ApiService();
  
  // Storage keys
  static const String _userKey = 'user_data';
  static const String _tokenKey = 'firebase_token';
  static const String _fcmTokenKey = 'fcm_token';
  
  // Get current Firebase user
  User? get currentUser => _auth.currentUser;
  
  // Stream of auth state changes
  Stream<User?> get authStateChanges => _auth.authStateChanges();
  
  // ============================================================
  // PHONE AUTHENTICATION
  // ============================================================
  
  /// Send OTP to phone number
  Future<void> sendOTP({
    required String phoneNumber,
    required Function(String verificationId) onCodeSent,
    required Function(String error) onError,
    Function(PhoneAuthCredential credential)? onAutoVerify,
  }) async {
    try {
      await _auth.verifyPhoneNumber(
        phoneNumber: phoneNumber, // Format: +91XXXXXXXXXX
        timeout: const Duration(seconds: 60),
        verificationCompleted: (PhoneAuthCredential credential) async {
          // Auto-verification (Android only)
          if (onAutoVerify != null) {
            onAutoVerify(credential);
          } else {
            await signInWithCredential(credential);
          }
        },
        verificationFailed: (FirebaseAuthException e) {
          String errorMessage = 'Verification failed';
          if (e.code == 'invalid-phone-number') {
            errorMessage = 'Invalid phone number format';
          } else if (e.code == 'too-many-requests') {
            errorMessage = 'Too many requests. Try again later';
          }
          onError(errorMessage);
        },
        codeSent: (String verificationId, int? resendToken) {
          onCodeSent(verificationId);
        },
        codeAutoRetrievalTimeout: (String verificationId) {
          // Handle timeout
        },
      );
    } catch (e) {
      onError(e.toString());
    }
  }
  
  /// Verify OTP and sign in
  Future<UserCredential?> verifyOTP({
    required String verificationId,
    required String otp,
  }) async {
    try {
      PhoneAuthCredential credential = PhoneAuthProvider.credential(
        verificationId: verificationId,
        smsCode: otp,
      );
      
      return await signInWithCredential(credential);
    } catch (e) {
      throw Exception('Invalid OTP: ${e.toString()}');
    }
  }
  
  /// Sign in with phone credential
  Future<UserCredential> signInWithCredential(
    PhoneAuthCredential credential,
  ) async {
    try {
      UserCredential userCredential = await _auth.signInWithCredential(
        credential,
      );
      
      // Register/Login with backend
      await _registerWithBackend(userCredential.user!);
      
      return userCredential;
    } catch (e) {
      throw Exception('Sign in failed: ${e.toString()}');
    }
  }
  
  // ============================================================
  // EMAIL/PASSWORD AUTHENTICATION
  // ============================================================
  
  /// Sign up with email and password
  Future<UserCredential?> signUpWithEmail({
    required String email,
    required String password,
    String? displayName,
  }) async {
    try {
      UserCredential userCredential = await _auth
          .createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
      
      // Update display name if provided
      if (displayName != null && displayName.isNotEmpty) {
        await userCredential.user?.updateDisplayName(displayName);
      }
      
      // Register with backend
      await _registerWithBackend(userCredential.user!);
      
      return userCredential;
    } on FirebaseAuthException catch (e) {
      String errorMessage = 'Sign up failed';
      if (e.code == 'weak-password') {
        errorMessage = 'Password is too weak';
      } else if (e.code == 'email-already-in-use') {
        errorMessage = 'Email already registered';
      } else if (e.code == 'invalid-email') {
        errorMessage = 'Invalid email format';
      }
      throw Exception(errorMessage);
    }
  }
  
  /// Sign in with email and password
  Future<UserCredential?> signInWithEmail({
    required String email,
    required String password,
  }) async {
    try {
      UserCredential userCredential = await _auth
          .signInWithEmailAndPassword(
        email: email,
        password: password,
      );
      
      // Login with backend
      await _loginWithBackend(userCredential.user!);
      
      return userCredential;
    } on FirebaseAuthException catch (e) {
      String errorMessage = 'Sign in failed';
      if (e.code == 'user-not-found') {
        errorMessage = 'No user found with this email';
      } else if (e.code == 'wrong-password') {
        errorMessage = 'Incorrect password';
      } else if (e.code == 'invalid-email') {
        errorMessage = 'Invalid email format';
      } else if (e.code == 'user-disabled') {
        errorMessage = 'This account has been disabled';
      }
      throw Exception(errorMessage);
    }
  }
  
  // ============================================================
  // BACKEND INTEGRATION
  // ============================================================
  
  /// Register user with backend after Firebase authentication
  Future<void> _registerWithBackend(User user) async {
    try {
      // Get Firebase ID token
      String? idToken = await user.getIdToken();
      if (idToken == null) throw Exception('Failed to get Firebase token');
      
      // Get FCM token for push notifications
      String? fcmToken = await _messaging.getToken();
      
      // Call backend register endpoint
      final response = await _apiService.register(
        firebaseToken: idToken,
        phoneNumber: user.phoneNumber,
        fcmToken: fcmToken,
      );
      
      // Save user data and tokens
      await _saveUserData(response['data']);
      await _storage.write(key: _tokenKey, value: idToken);
      if (fcmToken != null) {
        await _storage.write(key: _fcmTokenKey, value: fcmToken);
      }
    } catch (e) {
      print('Backend registration failed: $e');
      throw Exception('Backend registration failed');
    }
  }
  
  /// Login user with backend after Firebase authentication
  Future<void> _loginWithBackend(User user) async {
    try {
      // Get Firebase ID token
      String? idToken = await user.getIdToken();
      if (idToken == null) throw Exception('Failed to get Firebase token');
      
      // Get FCM token
      String? fcmToken = await _messaging.getToken();
      
      // Call backend login endpoint
      final response = await _apiService.login(
        firebaseToken: idToken,
        fcmToken: fcmToken,
      );
      
      // Save user data and tokens
      await _saveUserData(response['data']);
      await _storage.write(key: _tokenKey, value: idToken);
      if (fcmToken != null) {
        await _storage.write(key: _fcmTokenKey, value: fcmToken);
      }
    } catch (e) {
      print('Backend login failed: $e');
      throw Exception('Backend login failed');
    }
  }
  
  /// Get fresh Firebase ID token
  Future<String?> getIdToken({bool forceRefresh = false}) async {
    try {
      User? user = _auth.currentUser;
      if (user == null) return null;
      
      String? token = await user.getIdToken(forceRefresh);
      if (token != null) {
        await _storage.write(key: _tokenKey, value: token);
      }
      return token;
    } catch (e) {
      print('Failed to get ID token: $e');
      return null;
    }
  }
  
  /// Get stored Firebase ID token
  Future<String?> getStoredToken() async {
    return await _storage.read(key: _tokenKey);
  }
  
  /// Update FCM token on backend
  Future<void> updateFCMToken(String fcmToken) async {
    try {
      String? idToken = await getIdToken();
      if (idToken == null) return;
      
      await _apiService.updateFCMToken(
        firebaseToken: idToken,
        fcmToken: fcmToken,
      );
      
      await _storage.write(key: _fcmTokenKey, value: fcmToken);
    } catch (e) {
      print('Failed to update FCM token: $e');
    }
  }
  
  // ============================================================
  // USER DATA MANAGEMENT
  // ============================================================
  
  /// Save user data to secure storage
  Future<void> _saveUserData(Map<String, dynamic> userData) async {
    await _storage.write(key: _userKey, value: jsonEncode(userData));
  }
  
  /// Get user data from secure storage
  Future<Map<String, dynamic>?> getUserData() async {
    String? data = await _storage.read(key: _userKey);
    if (data != null) {
      return jsonDecode(data);
    }
    return null;
  }
  
  /// Get user profile from backend
  Future<Map<String, dynamic>?> getUserProfile() async {
    try {
      String? idToken = await getIdToken();
      if (idToken == null) return null;
      
      final response = await _apiService.getUserProfile(idToken);
      await _saveUserData(response['data']);
      return response['data'];
    } catch (e) {
      print('Failed to get user profile: $e');
      return null;
    }
  }
  
  // ============================================================
  // SIGN OUT
  // ============================================================
  
  /// Sign out from Firebase and clear local data
  Future<void> signOut() async {
    try {
      await _auth.signOut();
      
      // Clear stored data
      await _storage.delete(key: _userKey);
      await _storage.delete(key: _tokenKey);
      await _storage.delete(key: _fcmTokenKey);
    } catch (e) {
      print('Sign out failed: $e');
      throw Exception('Sign out failed');
    }
  }
  
  // ============================================================
  // PASSWORD RESET
  // ============================================================
  
  /// Send password reset email
  Future<void> sendPasswordResetEmail(String email) async {
    try {
      await _auth.sendPasswordResetEmail(email: email);
    } catch (e) {
      throw Exception('Failed to send reset email: ${e.toString()}');
    }
  }
  
  // ============================================================
  // TOKEN REFRESH
  // ============================================================
  
  /// Check if token needs refresh (expires in 1 hour)
  Future<bool> needsTokenRefresh() async {
    try {
      User? user = _auth.currentUser;
      if (user == null) return false;
      
      // Get token result with metadata
      IdTokenResult tokenResult = await user.getIdTokenResult();
      
      // Check if token expires in next 5 minutes
      DateTime? expirationTime = tokenResult.expirationTime;
      if (expirationTime != null) {
        Duration timeUntilExpiry = expirationTime.difference(DateTime.now());
        return timeUntilExpiry.inMinutes < 5;
      }
      
      return false;
    } catch (e) {
      return true; // Refresh on error
    }
  }
  
  /// Auto-refresh token if needed
  Future<String?> getValidToken() async {
    if (await needsTokenRefresh()) {
      return await getIdToken(forceRefresh: true);
    }
    return await getStoredToken();
  }
}
```

---

## API Service Implementation

Create `lib/services/api_service.dart`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://api.jaychauhan.tech';
  
  // ============================================================
  // AUTHENTICATION ENDPOINTS
  // ============================================================
  
  /// Register user with backend
  Future<Map<String, dynamic>> register({
    required String firebaseToken,
    String? phoneNumber,
    String? fcmToken,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'firebase_token': firebaseToken,
        'phone_number': phoneNumber,
        'fcm_token': fcmToken,
      }),
    );
    
    return _handleResponse(response);
  }
  
  /// Login user with backend
  Future<Map<String, dynamic>> login({
    required String firebaseToken,
    String? fcmToken,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'firebase_token': firebaseToken,
        'fcm_token': fcmToken,
      }),
    );
    
    return _handleResponse(response);
  }
  
  /// Verify Firebase token
  Future<Map<String, dynamic>> verifyToken(String firebaseToken) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/verify-token'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'firebase_token': firebaseToken,
      }),
    );
    
    return _handleResponse(response);
  }
  
  /// Get user profile (Protected)
  Future<Map<String, dynamic>> getUserProfile(String firebaseToken) async {
    final response = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: {
        'Authorization': 'Bearer $firebaseToken',
        'Content-Type': 'application/json',
      },
    );
    
    return _handleResponse(response);
  }
  
  /// Update FCM token (Protected)
  Future<Map<String, dynamic>> updateFCMToken({
    required String firebaseToken,
    required String fcmToken,
  }) async {
    final response = await http.put(
      Uri.parse('$baseUrl/auth/fcm-token'),
      headers: {
        'Authorization': 'Bearer $firebaseToken',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'fcm_token': fcmToken,
      }),
    );
    
    return _handleResponse(response);
  }
  
  /// Check Firebase health
  Future<Map<String, dynamic>> checkHealth() async {
    final response = await http.get(
      Uri.parse('$baseUrl/auth/health'),
    );
    
    return _handleResponse(response);
  }
  
  // ============================================================
  // NSE MARKET DATA ENDPOINTS (Protected)
  // ============================================================
  
  /// Get top gainers and losers
  Future<Map<String, dynamic>> getTopGainersLosers(
    String firebaseToken,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/nse/top-gainers-losers'),
      headers: {
        'Authorization': 'Bearer $firebaseToken',
        'Content-Type': 'application/json',
      },
    );
    
    return _handleResponse(response);
  }
  
  /// Get 52-week high/low stocks
  Future<Map<String, dynamic>> get52WeekHighLow(
    String firebaseToken,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/nse/52-week-high-low'),
      headers: {
        'Authorization': 'Bearer $firebaseToken',
        'Content-Type': 'application/json',
      },
    );
    
    return _handleResponse(response);
  }
  
  /// Get all NSE indexes
  Future<Map<String, dynamic>> getAllIndexes(String firebaseToken) async {
    final response = await http.get(
      Uri.parse('$baseUrl/nse/all-indexes'),
      headers: {
        'Authorization': 'Bearer $firebaseToken',
        'Content-Type': 'application/json',
      },
    );
    
    return _handleResponse(response);
  }
  
  /// Get most active equities
  Future<Map<String, dynamic>> getMostActiveEquities(
    String firebaseToken,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/nse/most-active-equities'),
      headers: {
        'Authorization': 'Bearer $firebaseToken',
        'Content-Type': 'application/json',
      },
    );
    
    return _handleResponse(response);
  }
  
  // ============================================================
  // IPO DATA ENDPOINTS
  // ============================================================
  
  /// Get IPO data
  Future<Map<String, dynamic>> getIPOData(String firebaseToken) async {
    final response = await http.get(
      Uri.parse('$baseUrl/ipo/data'),
      headers: {
        'Authorization': 'Bearer $firebaseToken',
        'Content-Type': 'application/json',
      },
    );
    
    return _handleResponse(response);
  }
  
  /// Get upcoming IPOs
  Future<Map<String, dynamic>> getUpcomingIPOs(
    String firebaseToken,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/ipo/forthcoming-listings'),
      headers: {
        'Authorization': 'Bearer $firebaseToken',
        'Content-Type': 'application/json',
      },
    );
    
    return _handleResponse(response);
  }
  
  // ============================================================
  // HELPER METHODS
  // ============================================================
  
  /// Handle HTTP response
  Map<String, dynamic> _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body);
    } else {
      throw ApiException(
        statusCode: response.statusCode,
        message: _getErrorMessage(response),
      );
    }
  }
  
  /// Extract error message from response
  String _getErrorMessage(http.Response response) {
    try {
      final body = jsonDecode(response.body);
      return body['message'] ?? 'Request failed';
    } catch (e) {
      return 'Request failed with status ${response.statusCode}';
    }
  }
}

/// Custom API Exception
class ApiException implements Exception {
  final int statusCode;
  final String message;
  
  ApiException({required this.statusCode, required this.message});
  
  @override
  String toString() => 'ApiException($statusCode): $message';
}
```

---

## User Model

Create `lib/models/user_model.dart`:

```dart
class UserModel {
  final String uid;
  final String? phoneNumber;
  final String? email;
  final String? displayName;
  final String? photoUrl;
  final bool isActive;
  final DateTime createdAt;
  final DateTime? lastLogin;
  final Map<String, dynamic>? metadata;
  
  UserModel({
    required this.uid,
    this.phoneNumber,
    this.email,
    this.displayName,
    this.photoUrl,
    required this.isActive,
    required this.createdAt,
    this.lastLogin,
    this.metadata,
  });
  
  /// Create UserModel from JSON
  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      uid: json['uid'],
      phoneNumber: json['phone_number'],
      email: json['email'],
      displayName: json['display_name'],
      photoUrl: json['photo_url'],
      isActive: json['is_active'] ?? true,
      createdAt: DateTime.parse(json['created_at']),
      lastLogin: json['last_login'] != null
          ? DateTime.parse(json['last_login'])
          : null,
      metadata: json['metadata'],
    );
  }
  
  /// Convert UserModel to JSON
  Map<String, dynamic> toJson() {
    return {
      'uid': uid,
      'phone_number': phoneNumber,
      'email': email,
      'display_name': displayName,
      'photo_url': photoUrl,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
      'last_login': lastLogin?.toIso8601String(),
      'metadata': metadata,
    };
  }
  
  /// Check if user is admin
  bool get isAdmin => metadata?['is_admin'] == true;
  
  /// Get user's display name or fallback
  String get name => displayName ?? phoneNumber ?? email ?? 'User';
}
```

---

## Authentication Flow

### Auth Wrapper Widget

Create `lib/screens/auth_wrapper.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../services/auth_service.dart';
import 'login_screen.dart';
import 'home_screen.dart';

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final authService = AuthService();
    
    return StreamBuilder<User?>(
      stream: authService.authStateChanges,
      builder: (context, snapshot) {
        // Show loading while checking auth state
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(
              child: CircularProgressIndicator(),
            ),
          );
        }
        
        // User is signed in
        if (snapshot.hasData && snapshot.data != null) {
          return const HomeScreen();
        }
        
        // User is not signed in
        return const LoginScreen();
      },
    );
  }
}
```

---

## Complete Usage Examples

### Example 1: Phone Authentication Screen

```dart
import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class PhoneAuthScreen extends StatefulWidget {
  const PhoneAuthScreen({Key? key}) : super(key: key);

  @override
  State<PhoneAuthScreen> createState() => _PhoneAuthScreenState();
}

class _PhoneAuthScreenState extends State<PhoneAuthScreen> {
  final AuthService _authService = AuthService();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _otpController = TextEditingController();
  
  String? _verificationId;
  bool _codeSent = false;
  bool _loading = false;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Phone Login')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            if (!_codeSent) ...[
              // Phone number input
              TextField(
                controller: _phoneController,
                decoration: const InputDecoration(
                  labelText: 'Phone Number',
                  hintText: '+919876543210',
                  prefixIcon: Icon(Icons.phone),
                ),
                keyboardType: TextInputType.phone,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loading ? null : _sendOTP,
                child: _loading
                    ? const CircularProgressIndicator()
                    : const Text('Send OTP'),
              ),
            ] else ...[
              // OTP input
              TextField(
                controller: _otpController,
                decoration: const InputDecoration(
                  labelText: 'Enter OTP',
                  prefixIcon: Icon(Icons.lock),
                ),
                keyboardType: TextInputType.number,
                maxLength: 6,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loading ? null : _verifyOTP,
                child: _loading
                    ? const CircularProgressIndicator()
                    : const Text('Verify OTP'),
              ),
            ],
          ],
        ),
      ),
    );
  }
  
  Future<void> _sendOTP() async {
    setState(() => _loading = true);
    
    await _authService.sendOTP(
      phoneNumber: _phoneController.text.trim(),
      onCodeSent: (verificationId) {
        setState(() {
          _verificationId = verificationId;
          _codeSent = true;
          _loading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('OTP sent successfully')),
        );
      },
      onError: (error) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error)),
        );
      },
      onAutoVerify: (credential) async {
        // Auto-verification on Android
        try {
          await _authService.signInWithCredential(credential);
          Navigator.pushReplacementNamed(context, '/home');
        } catch (e) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Auto-verification failed: $e')),
          );
        }
      },
    );
  }
  
  Future<void> _verifyOTP() async {
    if (_verificationId == null) return;
    
    setState(() => _loading = true);
    
    try {
      await _authService.verifyOTP(
        verificationId: _verificationId!,
        otp: _otpController.text.trim(),
      );
      
      Navigator.pushReplacementNamed(context, '/home');
    } catch (e) {
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }
}
```

### Example 2: Email/Password Authentication Screen

```dart
import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class EmailAuthScreen extends StatefulWidget {
  const EmailAuthScreen({Key? key}) : super(key: key);

  @override
  State<EmailAuthScreen> createState() => _EmailAuthScreenState();
}

class _EmailAuthScreenState extends State<EmailAuthScreen> {
  final AuthService _authService = AuthService();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _nameController = TextEditingController();
  
  bool _isSignUp = false;
  bool _loading = false;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isSignUp ? 'Sign Up' : 'Sign In'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            if (_isSignUp) ...[
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Full Name',
                  prefixIcon: Icon(Icons.person),
                ),
              ),
              const SizedBox(height: 16),
            ],
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(
                labelText: 'Email',
                prefixIcon: Icon(Icons.email),
              ),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _passwordController,
              decoration: const InputDecoration(
                labelText: 'Password',
                prefixIcon: Icon(Icons.lock),
              ),
              obscureText: true,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _loading ? null : _handleAuth,
              child: _loading
                  ? const CircularProgressIndicator()
                  : Text(_isSignUp ? 'Sign Up' : 'Sign In'),
            ),
            TextButton(
              onPressed: () {
                setState(() => _isSignUp = !_isSignUp);
              },
              child: Text(
                _isSignUp
                    ? 'Already have an account? Sign In'
                    : 'Don\'t have an account? Sign Up',
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Future<void> _handleAuth() async {
    setState(() => _loading = true);
    
    try {
      if (_isSignUp) {
        await _authService.signUpWithEmail(
          email: _emailController.text.trim(),
          password: _passwordController.text.trim(),
          displayName: _nameController.text.trim(),
        );
      } else {
        await _authService.signInWithEmail(
          email: _emailController.text.trim(),
          password: _passwordController.text.trim(),
        );
      }
      
      Navigator.pushReplacementNamed(context, '/home');
    } catch (e) {
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }
}
```

### Example 3: Making Protected API Calls

```dart
import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';

class MarketDataScreen extends StatefulWidget {
  const MarketDataScreen({Key? key}) : super(key: key);

  @override
  State<MarketDataScreen> createState() => _MarketDataScreenState();
}

class _MarketDataScreenState extends State<MarketDataScreen> {
  final AuthService _authService = AuthService();
  final ApiService _apiService = ApiService();
  
  bool _loading = false;
  List<dynamic> _gainers = [];
  List<dynamic> _losers = [];
  
  @override
  void initState() {
    super.initState();
    _loadMarketData();
  }
  
  Future<void> _loadMarketData() async {
    setState(() => _loading = true);
    
    try {
      // Get valid Firebase token (auto-refreshes if needed)
      String? token = await _authService.getValidToken();
      
      if (token == null) {
        throw Exception('No authentication token');
      }
      
      // Make API call with token
      final response = await _apiService.getTopGainersLosers(token);
      
      setState(() {
        _gainers = response['data']['gainers'] ?? [];
        _losers = response['data']['losers'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      
      // Handle token expiration
      if (e.toString().contains('401')) {
        // Token expired, try to refresh
        try {
          String? newToken = await _authService.getIdToken(forceRefresh: true);
          if (newToken != null) {
            // Retry the request
            _loadMarketData();
            return;
          }
        } catch (refreshError) {
          // Refresh failed, sign out
          await _authService.signOut();
          Navigator.pushReplacementNamed(context, '/login');
        }
      }
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load data: $e')),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    return ListView(
      children: [
        const Padding(
          padding: EdgeInsets.all(16.0),
          child: Text(
            'Top Gainers',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
        ),
        ..._gainers.map((stock) => ListTile(
          title: Text(stock['symbol']),
          subtitle: Text('${stock['lastPrice']}'),
          trailing: Text(
            '+${stock['pChange']}%',
            style: const TextStyle(color: Colors.green),
          ),
        )),
        const Padding(
          padding: EdgeInsets.all(16.0),
          child: Text(
            'Top Losers',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
        ),
        ..._losers.map((stock) => ListTile(
          title: Text(stock['symbol']),
          subtitle: Text('${stock['lastPrice']}'),
          trailing: Text(
            '${stock['pChange']}%',
            style: const TextStyle(color: Colors.red),
          ),
        )),
      ],
    );
  }
}
```

---

## FCM Push Notifications

### Setup FCM in `main.dart`

```dart
import 'package:firebase_messaging/firebase_messaging.dart';

// Background message handler (top-level function)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print('Background message: ${message.notification?.title}');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  // Setup background message handler
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  
  runApp(const MyApp());
}
```

### FCM Service

Create `lib/services/fcm_service.dart`:

```dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'auth_service.dart';

class FCMService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final AuthService _authService = AuthService();
  
  // Local notifications plugin
  final FlutterLocalNotificationsPlugin _localNotifications = 
      FlutterLocalNotificationsPlugin();
  
  /// Initialize FCM
  Future<void> initialize() async {
    // Request permission
    NotificationSettings settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      print('User granted permission');
      
      // Get FCM token
      String? token = await _messaging.getToken();
      if (token != null) {
        print('FCM Token: $token');
        // Update token on backend
        await _authService.updateFCMToken(token);
      }
      
      // Listen for token refresh
      _messaging.onTokenRefresh.listen((newToken) {
        _authService.updateFCMToken(newToken);
      });
      
      // Initialize local notifications
      await _initializeLocalNotifications();
      
      // Handle foreground messages
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
      
      // Handle notification tap
      FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
      
      // Check for initial message (app opened from notification)
      RemoteMessage? initialMessage = await _messaging.getInitialMessage();
      if (initialMessage != null) {
        _handleNotificationTap(initialMessage);
      }
    }
  }
  
  /// Initialize local notifications
  Future<void> _initializeLocalNotifications() async {
    const AndroidInitializationSettings androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    
    const DarwinInitializationSettings iosSettings =
        DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    
    const InitializationSettings settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    
    await _localNotifications.initialize(settings);
  }
  
  /// Handle foreground messages
  void _handleForegroundMessage(RemoteMessage message) {
    print('Foreground message: ${message.notification?.title}');
    
    // Show local notification
    _showLocalNotification(message);
  }
  
  /// Show local notification
  Future<void> _showLocalNotification(RemoteMessage message) async {
    const AndroidNotificationDetails androidDetails =
        AndroidNotificationDetails(
      'ipo_lens_channel',
      'IPO Lens Notifications',
      importance: Importance.high,
      priority: Priority.high,
    );
    
    const NotificationDetails details = NotificationDetails(
      android: androidDetails,
      iOS: DarwinNotificationDetails(),
    );
    
    await _localNotifications.show(
      message.hashCode,
      message.notification?.title,
      message.notification?.body,
      details,
    );
  }
  
  /// Handle notification tap
  void _handleNotificationTap(RemoteMessage message) {
    print('Notification tapped: ${message.data}');
    
    // Navigate based on notification data
    // Example: Navigate to specific screen
    // navigatorKey.currentState?.pushNamed('/details', arguments: message.data);
  }
}
```

### Usage in App

```dart
// In your main app or home screen
final FCMService fcmService = FCMService();

@override
void initState() {
  super.initState();
  fcmService.initialize();
}
```

---

## Error Handling

### Global Error Handler

Create `lib/utils/error_handler.dart`:

```dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ErrorHandler {
  static void handleError(BuildContext context, dynamic error) {
    String message = 'An error occurred';
    
    if (error is ApiException) {
      message = error.message;
      
      // Handle specific status codes
      if (error.statusCode == 401) {
        message = 'Session expired. Please login again';
        // Navigate to login
        Navigator.pushReplacementNamed(context, '/login');
      } else if (error.statusCode == 403) {
        message = 'Access denied';
      } else if (error.statusCode == 404) {
        message = 'Resource not found';
      } else if (error.statusCode >= 500) {
        message = 'Server error. Please try again later';
      }
    } else if (error is Exception) {
      message = error.toString().replaceAll('Exception:', '').trim();
    }
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }
}
```

---

## Testing Checklist

- [ ] Firebase project configured correctly (`flutterfire configure`)
- [ ] `google-services.json` (Android) in `android/app/`
- [ ] `GoogleService-Info.plist` (iOS) in `ios/Runner/`
- [ ] Firebase Authentication enabled (Phone + Email/Password)
- [ ] Firebase Cloud Messaging enabled
- [ ] Backend API health check passes
- [ ] Phone authentication works (OTP send + verify)
- [ ] Email authentication works (sign up + sign in)
- [ ] Protected API calls work with Bearer token
- [ ] Token auto-refresh works
- [ ] FCM notifications received (foreground + background)
- [ ] Sign out clears all data
- [ ] Password reset email works

---

## Common Issues & Solutions

### Issue 1: "PlatformException (null-error, host is not found)"
**Solution:** Ensure Firebase is initialized before using any Firebase services.

### Issue 2: Token expired (401 error)
**Solution:** Use `getValidToken()` instead of `getStoredToken()` for auto-refresh.

### Issue 3: FCM token not updating on backend
**Solution:** Listen to `onTokenRefresh` stream and call `updateFCMToken()`.

### Issue 4: Notifications not showing in foreground
**Solution:** Implement local notifications using `flutter_local_notifications`.

### Issue 5: Phone authentication not working
**Solution:** 
- Check phone number format (+country_code + number)
- Enable Phone authentication in Firebase Console
- Add SHA-256 fingerprint for Android

---

## Additional Resources

- [Firebase Flutter Setup](https://firebase.google.com/docs/flutter/setup)
- [Firebase Auth Documentation](https://firebase.google.com/docs/auth/flutter/start)
- [FCM Flutter Guide](https://firebase.google.com/docs/cloud-messaging/flutter/client)
- [Backend API Documentation](./TEMP_AUTH_IMPLEMENTATION.md)

---

## Support

For backend API issues, refer to:
- `docs/TEMP_AUTH_IMPLEMENTATION.md` - Complete backend documentation
- `docs/AUTH_IMPLEMENTATION_SUMMARY.md` - Quick summary
- `FIREBASE_SETUP_GUIDE.md` - Backend Firebase setup

For Flutter-specific issues, check Firebase Console logs and Flutter debug console.

---

**Last Updated:** January 26, 2026  
**Backend API Version:** 1.0  
**Flutter SDK:** 3.0.0+
