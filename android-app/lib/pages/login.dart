import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_parking/pages/color.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/user_session.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  // Controllers for form inputs
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  
  // Loading state
  bool _isLoading = false;

  // Validate phone number format
  // Valid: 10 digits, starting with 03/05/07/09
  String? _validatePhone(String phone) {
    if (phone.isEmpty) {
      return 'Phone number is required';
    }

    phone = phone.trim();

    // Check if phone has exactly 10 digits
    if (phone.length < 10) {
      return 'Phone number must have 10 digits';
    }

    if (phone.length > 10) {
      return 'Phone number can have maximum 10 digits';
    }

    // Check if phone contains only digits
    final RegExp phoneRegex = RegExp(r'^[0-9]{10}$');
    if (!phoneRegex.hasMatch(phone)) {
      return 'Invalid phone number format';
    }

    // Check if phone starts with valid prefix (03/05/07/09)
    if (!phone.startsWith('03') && !phone.startsWith('05') && 
        !phone.startsWith('07') && !phone.startsWith('09')) {
      return 'Invalid phone number format';
    }

    return null;
  }

  // Validate password
  // Valid: 6-20 characters
  String? _validatePassword(String password) {
    if (password.isEmpty) {
      return 'Password is required';
    }

    if (password.length < 6) {
      return 'Password must have at least 6 characters';
    }

    if (password.length > 20) {
      return 'Password must have less than 20 characters';
    }

    return null;
  }

  // Handle login API call
  Future<void> _handleLogin() async {
    // Validate phone
    String? phoneError = _validatePhone(_phoneController.text);
    if (phoneError != null) {
      _showErrorMessage(phoneError);
      return;
    }

    // Validate password
    String? passwordError = _validatePassword(_passwordController.text);
    if (passwordError != null) {
      _showErrorMessage(passwordError);
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Call your Flask login API
      final response = await AuthService.login(
        _phoneController.text.trim(), 
        _passwordController.text.trim()
      );

      if (AuthService.isLoginSuccessful(response)) {
        // Login successful - extract user_id from message field
        final userId = AuthService.getUserIdFromResponse(response);
        
        if (userId != null && userId.isNotEmpty) {
          print('Login response: $response');
          print('Extracted user data: {userId: $userId, userPhone: $userId}');
          
          // Initialize UserSession with user data
          final userSession = Provider.of<UserSession>(context, listen: false);
          await userSession.initializeSession(
            userId: userId,
            userPhone: userId,
          );
          
          // Show success message
          _showSuccessMessage('Login successful! Welcome back.');
          
          // Navigate to home page (no need to pass userData anymore)
          Navigator.pushReplacementNamed(context, '/main');
        } else {
          _showErrorMessage('Invalid user ID received from server');
        }
        
      } else {
        // Login failed - show error from server
        final errorMessage = AuthService.getErrorMessage(response);
        _showErrorMessage(errorMessage);
      }
      
    } catch (e) {
      // Handle different types of errors with specific messages
      print('Login error: $e');
      
      String errorMessage;
      
      if (e is NetworkException) {
        errorMessage = 'Unable to connect to server. Please check your internet connection and try again.';
      } else if (e is UnauthorizedException) {
        errorMessage = 'Invalid phone number or password. Please check your credentials and try again.';
      } else if (e is BadRequestException) {
        errorMessage = 'Please enter valid phone number and password.';
      } else if (e is NotFoundException) {
        errorMessage = 'Account not found. Please check your phone number or create a new account.';
      } else if (e is ServerException) {
        errorMessage = 'Server is temporarily unavailable. Please try again later.';
      } else if (e.toString().contains('SocketException') || e.toString().contains('Connection refused')) {
        errorMessage = 'Unable to connect to server. Please check your internet connection.';
      } else if (e.toString().contains('TimeoutException')) {
        errorMessage = 'Connection timeout. Please check your internet connection and try again.';
      } else {
        errorMessage = 'Login failed. Please try again.';
      }
      
      _showErrorMessage(errorMessage);
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  // Show error message
  void _showErrorMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red.shade600,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        duration: Duration(seconds: 3),
      ),
    );
  }

  // Show success message
  void _showSuccessMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green.shade600,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: false,
      body: Container(
        decoration: BoxDecoration(
          gradient: backgroundGradient,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            SizedBox(height: 80,),
            Padding(
              padding: EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text("Login", style: TextStyle(color: Colors.white, fontSize: 40),),
                  SizedBox(height: 10,),
                  Text("Welcome Back", style: TextStyle(color: Colors.white, fontSize: 18),),
                ],
              ),
            ),
            SizedBox(height: 20,),
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.only(topLeft: Radius.circular(60), topRight: Radius.circular(60))
                ),
                child: Padding(
                  padding: EdgeInsets.all(30),
                  child: SingleChildScrollView(
                    child: Column(
                      children: <Widget>[
                      SizedBox(height: 60,),
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(10),
                          boxShadow: [BoxShadow(
                            color: Color.fromRGBO(225, 95, 27, .3),
                            blurRadius: 20,
                            offset: Offset(0, 10)
                          )]
                        ),
                        child: Column(
                          children: <Widget>[
                            Container(
                              padding: EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                border: Border(bottom: BorderSide(color: Colors.grey.shade200))
                              ),
                              child: TextField(
                                controller: _phoneController,
                                decoration: InputDecoration(
                                  hintText: "Phone number",
                                  hintStyle: TextStyle(color: Colors.grey),
                                  border: InputBorder.none
                                ),
                              ),
                            ),
                            Container(
                              padding: EdgeInsets.all(10),
                              child: TextField(
                                controller: _passwordController,
                                obscureText: true,
                                decoration: InputDecoration(
                                  hintText: "Password",
                                  hintStyle: TextStyle(color: Colors.grey),
                                  border: InputBorder.none
                                ),
                              ),
                            )
                          ],
                        ),
                      ),
                      SizedBox(height: 40,),
                      Text("Forgot Password?", style: TextStyle(color: secondaryColor),),
                      SizedBox(height: 40,),
                      GestureDetector(
                        onTap: _isLoading ? null : _handleLogin,
                        child: Container(
                          height: 50,
                          margin: EdgeInsets.symmetric(horizontal: 50),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(50),
                            color: _isLoading ? Colors.grey : primaryColor
                          ),
                          child: Center(
                            child: _isLoading 
                              ? CircularProgressIndicator(color: Colors.white)
                              : Text("Login", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ),
                      SizedBox(height: 40,),
                      Text("If you don't have an account, Sign up", style: TextStyle(color: Colors.grey),),
                      SizedBox(height: 20,),
                      GestureDetector(
                        onTap: () {
                          Navigator.pushNamed(context, '/signin');
                        },
                        child: Container(
                          height: 50,
                          margin: EdgeInsets.symmetric(horizontal: 50),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(50),
                            color: primaryColor
                          ),
                          child: Center(
                            child: Text("Sign up", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),),
                          ),
                        ),
                      )
                    ],
                    ),
                  ),
                ),
              ),
            )
          ],
        ),
      ),
    );
  }
}