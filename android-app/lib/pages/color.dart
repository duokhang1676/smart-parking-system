import 'package:flutter/material.dart';

final Color primaryColor = Color(0xFF0D47A1); // Dark Blue
final Color secondaryColor = Color(0xFF1976D2); // Medium Blue
final Color accentColor = Color(0xFF42A5F5); // Amber

final LinearGradient backgroundGradient = LinearGradient(
  begin: Alignment.topCenter,
  // end: Alignment.bottomCenter,
  colors: [
    primaryColor,
    secondaryColor,
    accentColor,
  ],
);