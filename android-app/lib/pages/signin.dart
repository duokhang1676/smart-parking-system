import 'package:flutter/material.dart';
import 'package:smart_parking/pages/color.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';

class SignInPage extends StatefulWidget {
  const SignInPage({super.key});

  @override
  State<SignInPage> createState() => _SignInPageState();
}

class _SignInPageState extends State<SignInPage> {
  // Controllers for form inputs
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmPasswordController = TextEditingController();
  
  // Loading state
  bool _isLoading = false;

  // Validate full name
  // Valid: At least 2 characters
  String? _validateFullName(String name) {
    if (name.isEmpty) {
      return 'Full name is required';
    }

    name = name.trim();

    if (name.length < 2) {
      return 'Full name must have at least 2 characters';
    }

    return null;
  }

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

  // Validate confirm password
  String? _validateConfirmPassword(String confirmPassword, String password) {
    if (confirmPassword.isEmpty) {
      return 'Confirm password is required';
    }

    if (confirmPassword.length < 6) {
      return 'Password must have at least 6 characters';
    }

    if (confirmPassword.length > 20) {
      return 'Password must have less than 20 characters';
    }

    if (confirmPassword != password) {
      return 'Confirm password does not match';
    }

    return null;
  }

  // Handle registration API call
  Future<void> _handleRegistration() async {
    // Validate full name
    String? nameError = _validateFullName(_nameController.text);
    if (nameError != null) {
      _showErrorMessage(nameError);
      return;
    }

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

    // Validate confirm password
    String? confirmPasswordError = _validateConfirmPassword(
      _confirmPasswordController.text,
      _passwordController.text,
    );
    if (confirmPasswordError != null) {
      _showErrorMessage(confirmPasswordError);
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Call your Flask registration API
      final response = await AuthService.register(
        _phoneController.text.trim(),
        _nameController.text.trim(), 
        _passwordController.text.trim()
      );

      if (AuthService.isRegistrationSuccessful(response)) {
        // Registration successful
        _showSuccessMessage('Account created successfully! You can now login.');
        
        // Navigate back to login page
        Navigator.pop(context);
        
      } else {
        // Registration failed - show error from server
        final errorMessage = AuthService.getRegistrationErrorMessage(response);
        _showErrorMessage(errorMessage);
      }
      
    } catch (e) {
      // Handle different types of errors with specific messages
      print('Registration error: $e');
      
      String errorMessage;
      
      if (e is NetworkException) {
        errorMessage = 'Unable to connect to server. Please check your internet connection and try again.';
      } else if (e is ConflictException) {
        errorMessage = 'Phone number already registered. Please use a different phone number or login instead.';
      } else if (e is BadRequestException) {
        errorMessage = 'Please fill in all required fields correctly.';
      } else if (e is ServerException) {
        errorMessage = 'Server is temporarily unavailable. Please try again later.';
      } else if (e.toString().contains('SocketException') || e.toString().contains('Connection refused')) {
        errorMessage = 'Unable to connect to server. Please check your internet connection.';
      } else if (e.toString().contains('TimeoutException')) {
        errorMessage = 'Connection timeout. Please check your internet connection and try again.';
      } else {
        errorMessage = 'Registration failed. Please try again.';
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
    _nameController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
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
                  Text("Sign Up", style: TextStyle(color: Colors.white, fontSize: 40),),
                  SizedBox(height: 10,),
                  Text("Create Account", style: TextStyle(color: Colors.white, fontSize: 18),),
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
                                controller: _nameController,
                                decoration: InputDecoration(
                                  hintText: "Full Name",
                                  hintStyle: TextStyle(color: Colors.grey),
                                  border: InputBorder.none
                                ),
                              ),
                            ),
                            Container(
                              padding: EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                border: Border(bottom: BorderSide(color: Colors.grey.shade200))
                              ),
                              child: TextField(
                                controller: _phoneController,
                                keyboardType: TextInputType.phone,
                                decoration: InputDecoration(
                                  hintText: "Phone Number",
                                  hintStyle: TextStyle(color: Colors.grey),
                                  border: InputBorder.none
                                ),
                              ),
                            ),
                            Container(
                              padding: EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                border: Border(bottom: BorderSide(color: Colors.grey.shade200))
                              ),
                              child: TextField(
                                controller: _passwordController,
                                obscureText: true,
                                decoration: InputDecoration(
                                  hintText: "Password",
                                  hintStyle: TextStyle(color: Colors.grey),
                                  border: InputBorder.none
                                ),
                              ),
                            ),
                            Container(
                              padding: EdgeInsets.all(10),
                              child: TextField(
                                controller: _confirmPasswordController,
                                obscureText: true,
                                decoration: InputDecoration(
                                  hintText: "Confirm Password",
                                  hintStyle: TextStyle(color: Colors.grey),
                                  border: InputBorder.none
                                ),
                              ),
                            )
                          ],
                        ),
                      ),
                      SizedBox(height: 40,),
                      GestureDetector(
                        onTap: _isLoading ? null : _handleRegistration,
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
                              : Text("Sign Up", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),),
                          ),
                        ),
                      ),
                      SizedBox(height: 40,),
                      Text("Already have an account? Login", style: TextStyle(color: Colors.grey),),
                      SizedBox(height: 20,),
                      GestureDetector(
                        onTap: () {
                          Navigator.pop(context);
                        },
                        child: Container(
                          height: 50,
                          margin: EdgeInsets.symmetric(horizontal: 50),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(50),
                            border: Border.all(color: primaryColor),
                            color: Colors.white
                          ),
                          child: Center(
                            child: Text("Back to Login", style: TextStyle(color: primaryColor, fontWeight: FontWeight.bold),),
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