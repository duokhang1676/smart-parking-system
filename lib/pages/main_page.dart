import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_parking/pages/color.dart';
import 'package:smart_parking/pages/home.dart';
import 'package:smart_parking/pages/register.dart';
import 'package:smart_parking/pages/setting.dart';
import 'package:smart_parking/services/user_session.dart';

class MainPage extends StatefulWidget {
  const MainPage({super.key});

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  int _selectedIndex = 0;

  List<Widget> get _pages => [
    HomePage(),
    RegisterPage(),
    SettingsPage(),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<UserSession>(
      builder: (context, userSession, child) {
        // Check if user is logged in
        if (!userSession.isLoggedIn) {
          // Redirect to login if not logged in
          WidgetsBinding.instance.addPostFrameCallback((_) {
            Navigator.pushReplacementNamed(context, '/login');
          });
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        return Scaffold(
          body: _pages[_selectedIndex],
          bottomNavigationBar: BottomNavigationBar(
            currentIndex: _selectedIndex,
            selectedItemColor: primaryColor,
            type: BottomNavigationBarType.fixed,
            onTap: _onItemTapped,
            items: const [
              BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
              BottomNavigationBarItem(icon: Icon(Icons.app_registration), label: 'Register'),
              BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Settings'),
            ],
          ),
        );
      },
    );
  }
}
