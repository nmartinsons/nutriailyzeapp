import 'package:flutter/material.dart';
import 'package:flutter_nutriailyze_app/login_screen.dart';
import 'package:flutter_nutriailyze_app/signup_screen.dart';
import 'package:flutter_nutriailyze_app/home_screen.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:google_fonts/google_fonts.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // For web deployments, use compile-time values or safe public defaults.
  // These are public Supabase client credentials (URL + publishable key).
  const url = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://zsqswroaevuxqdamdykl.supabase.co',
  );
  const key = String.fromEnvironment(
    'SUPABASE_KEY',
    defaultValue:
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpzcXN3cm9hZXZ1eHFkYW1keWtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkwNzYyMjUsImV4cCI6MjA3NDY1MjIyNX0.yMOUsRZhffVqBDPJmi_yX9hJ1UjWQDdL6jNowYKPVqI',
  );

  if (url.isEmpty || key.isEmpty) {
    throw StateError(
      'Missing SUPABASE_URL or SUPABASE_KEY. Provide them via --dart-define for build/release.',
    );
  }

  final parsedUrl = Uri.tryParse(url);
  if (parsedUrl == null || !parsedUrl.hasScheme || parsedUrl.host.isEmpty) {
    throw FormatException(
      'SUPABASE_URL is invalid. Expected a full URL like https://your-project.supabase.co',
      url,
    );
  }

  // Initialize Supabase with the URL and anon key from environment variables
  await Supabase.initialize(url: url, anonKey: key);

  // Now that Supabase is initialized, we can run the app
  runApp(const MyApp());
}

// Create a global Supabase client instance for easy access throughout the app
final supabase = Supabase.instance.client;

// The main app widget that sets up the MaterialApp and routes
class MyApp extends StatelessWidget {
  // const MyApp({super.key}) is a constructor for the MyApp class.
  //The 'const' keyword indicates that this constructor can be used to create compile-time constant instances of MyApp.
  //The 'super.key' part is passing the key parameter to the superclass (StatelessWidget) constructor, which is a common practice in Flutter to allow for widget identification and optimization.
  const MyApp({super.key});

  // The build method is responsible for describing how to display the widget in terms of other, lower-level widgets. In this case, it returns a MaterialApp widget that sets up the overall theme and routing for the app.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false, // Removes the red "DEBUG" banner
      title:
          'Nutriailyze', // Sets the title of the app, which can be used by the operating system to identify the app
      theme: ThemeData(
        textTheme:
            GoogleFonts.ptMonoTextTheme(), // Sets the font for the whole app
        scaffoldBackgroundColor: const Color(
          0xFF333333,
        ), // Sets the background to Dark Grey
        useMaterial3: true, // Uses the latest Android design style
      ),
      home:
          const AuthGate(), // The first screen isn't Home, it's the "Gatekeeper" that checks if the user is logged in or not.
      routes: {'/login': (context) => const LoginOrSignupScreen()},
    );
  }
}

// Class for the authentication gate that checks if the user is logged in or not and routes them accordingly
class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    // StreamBuilder listens to the authentication state changes from Supabase. Whenever the auth state changes (like logging in or out), it rebuilds the UI accordingly.
    return StreamBuilder<AuthState>(
      stream: supabase.auth.onAuthStateChange, // Listens to auth state changes
      // The builder function is called whenever the stream emits a new value (like when the user logs in or out). It receives the current BuildContext and an AsyncSnapshot of the AuthState.
      builder: (context, snapshot) {
        // if statement checks if the connection state of the snapshot is still waiting, which means it's still checking the authentication status. If it is waiting, it shows a loading indicator (a circular progress bar) to indicate that the app is processing.
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            backgroundColor: Color(0xFF333333),
            body: Center(
              child: CircularProgressIndicator(color: Color(0xFFE3DAC9)),
            ),
          );
        }
        // This line extracts the current session from the snapshot data. The session contains information about the user's authentication status, such as whether they are logged in or not. If the session is not null, it means the user is logged in; otherwise, they are not.
        final session = snapshot.data?.session;

        // Handimg the case when the user is logged in or not. If the session is not null, it means the user is logged in, and we return the HomeScreen widget. If the session is null, it means the user is not logged in, and we return the LoginOrSignupScreen widget, which prompts the user to either log in or sign up.
        if (session != null) {
          // User is logged in
          return const HomeScreen();
        } else {
          // User is not logged in
          return const LoginOrSignupScreen();
        }
      },
    );
  }
}

// This is the screen that shows when the user is not logged in, prompting them to either log in or sign up.
class LoginOrSignupScreen extends StatelessWidget {
  const LoginOrSignupScreen({super.key});

  Future<void> _handleGoogleSignIn(BuildContext context) async {
    try {
      await supabase.auth.signInWithOAuth(OAuthProvider.google);
    } on AuthException catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.redAccent),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Google sign-in failed.'),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF333333),
      body: Column(
        children: [
          // Expanded helps to divide the screen into flexible parts. The first Expanded takes up more space (flex: 6) and contains the welcome text, while the second Expanded (flex: 5) contains the login and signup buttons.
          Expanded(
            flex: 6, // Takes up more space than the bottom container
            child: SafeArea(
              // Only apply SafeArea to the top (status bar)
              bottom: false,
              child: Center(
                child: Text(
                  "Let’s Nutriailyze...",
                  textAlign: TextAlign.center,
                  style: GoogleFonts.ptMono(
                    textStyle: const TextStyle(
                      color: Color(0xFFF6F6F6),
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                    ),
                  ),
                ),
              ),
            ),
          ),
          Expanded(
            flex: 5, // Takes up remaining space
            child: Container(
              width: double
                  .infinity, // Makes the container take the full width of the screen
              padding: const EdgeInsets.only(
                top: 30,
                bottom: 20,
              ), // Adds vertical padding to the container
              decoration: const BoxDecoration(
                color: Color(
                  0xFF272727,
                ), // Sets the background color of the container to a darker grey
                borderRadius: BorderRadius.vertical(
                  top: Radius.circular(100),
                ), // Creates a rounded top border with a radius of 100, giving it a pill-shaped appearance at the top
              ),
              child: Column(
                // This centers the buttons inside the dark grey box
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildButton(
                    context,
                    "Log in",
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const LoginScreen(),
                        ),
                      );
                    },
                  ),
                  const SizedBox(
                    height: 17,
                  ), // Adds vertical spacing between the two buttons
                  _buildButton(
                    context,
                    "Sign up",
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const SignupScreen(),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 17),
                  _buildGoogleButton(
                    context,
                    onPressed: () => _handleGoogleSignIn(context),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // This is a helper method to build the login and signup buttons with consistent styling.
  Widget _buildButton(
    BuildContext context,
    String text, {
    required VoidCallback onPressed,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFE3DAC9),
            foregroundColor: const Color(0xFF333333),
            padding: const EdgeInsets.symmetric(vertical: 15),
            textStyle: GoogleFonts.ptMono(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          onPressed: onPressed,
          child: Text(text),
        ),
      ),
    );
  }

  Widget _buildGoogleButton(
    BuildContext context, {
    required VoidCallback onPressed,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFF6F6F6),
            foregroundColor: const Color(0xFF333333),
            padding: const EdgeInsets.symmetric(vertical: 15),
            textStyle: GoogleFonts.ptMono(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          onPressed: onPressed,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SvgPicture.asset(
                'assets/icons/google.svg',
                width: 18,
                height: 18,
              ),
              const SizedBox(width: 10),
              const Text('Continue with Google'),
            ],
          ),
        ),
      ),
    );
  }
}
