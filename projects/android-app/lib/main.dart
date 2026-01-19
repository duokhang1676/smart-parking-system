import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_parking/pages/login.dart';
import 'package:smart_parking/pages/main_page.dart';
import 'package:smart_parking/pages/signin.dart';
import 'package:smart_parking/services/user_session.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (context) => UserSession(),
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: ThemeData(fontFamily: 'Poppins'),
        home: LoginPage(),
        routes: {
          '/login': (context) => LoginPage(),
          '/signin': (context) => SignInPage(),
          '/main': (context) => const MainPage(),
        },
      ),
    );
  }
}

