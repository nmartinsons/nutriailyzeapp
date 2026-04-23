import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:form_builder_validators/form_builder_validators.dart';
import 'package:flutter_nutriailyze_app/home_screen.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

// StatefulWidget (Best practice when using Controllers) to ensure that there are no memory leaks
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  // Initialize Controller
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  // Allows validation of the entire form
  final _formKey = GlobalKey<FormState>();
  // Toggles password visibility
  bool _isPasswordVisible = false;
  bool _isLoading = false; // To show spinner

  Future<void> _handleLogin() async {
    // Validate Form
    if (!_formKey.currentState!.validate()) return;

    // Start Loading
    setState(() => _isLoading = true);

    // Variables for email and password
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    try {
      // CALL SUPABASE
      final AuthResponse res = await Supabase.instance.client.auth
          .signInWithPassword(email: email, password: password);

      // Handle Success
      if (mounted) {
        if (res.session != null) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const HomeScreen()),
          );
        }
      }
    } on AuthException catch (e) {
      // Handle Supabase Errors (e.g. User already exists)
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.redAccent),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("An unexpected error occurred."),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleGoogleSignIn() async {
    setState(() => _isLoading = true);
    try {
      await Supabase.instance.client.auth.signInWithOAuth(OAuthProvider.google);
    } on AuthException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.redAccent),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Google sign-in failed.'),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    // Always dispose controllers to free up memory
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF333333),
      appBar: AppBar(
        toolbarHeight: 100,
        backgroundColor: const Color(0xFF333333),
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Color(0xFFF6F6F6)),
          onPressed: () {
            Navigator.pop(context);
          },
        ),
        title: Padding(
          padding: const EdgeInsets.only(top: 40.0),
          child: SvgPicture.asset(
            'assets/logos/LogoN.svg',
            height: 105,
            fit: BoxFit.contain,
          ),
        ),
      ),

      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32.0),
          child: Form(
            key: _formKey, // enables validation
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const SizedBox(height: 165),
                // EMAIL FIELD
                TextFormField(
                  controller: _emailController,
                  style: const TextStyle(color: Color(0xFF272727)),
                  // Form validation
                  // if null is returned -> valid, otherwise not valid
                  validator: (value) {
                    // Validation logic
                    final error = FormBuilderValidators.compose([
                      FormBuilderValidators.required(
                        errorText: 'Email is required.',
                      ),
                      FormBuilderValidators.email(
                        errorText: 'Enter a valid email.',
                      ),
                    ])(value); // calls validator with value
                    return error;
                  },
                  cursorColor: const Color(0xFF272727),
                  cursorWidth: 1,
                  decoration: const InputDecoration(
                    errorMaxLines: 2,
                    errorStyle: TextStyle(
                      color: Colors.redAccent,
                      fontSize: 13,
                    ),
                    contentPadding: EdgeInsets.symmetric(
                      vertical: 12.0,
                      horizontal: 15.0,
                    ),
                    filled: true,
                    fillColor: Color(0xFFF6F6F6),
                    // placeholder
                    hintText: 'Email',
                    // For visible placeholder
                    hintStyle: TextStyle(color: Color(0xFF272727)),
                    // No label to the top
                    floatingLabelBehavior: FloatingLabelBehavior.never,
                    // Borders
                    enabledBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Color(0xFFF6F6F6),
                        width: 1.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    // border when field is pressed
                    focusedBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Color(0xFFE3DAC9),
                        width: 2.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    // ERROR BORDER
                    errorBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Colors.redAccent,
                        width: 1.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    // FOCUSED ERROR BORDER
                    focusedErrorBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Colors.redAccent,
                        width: 2.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                // PASSWORD FIELD
                TextFormField(
                  // Toggles pasword visibility
                  obscureText: !_isPasswordVisible,
                  controller: _passwordController,
                  style: const TextStyle(color: Color(0xFF272727)),
                  cursorColor: const Color(0xFF272727),
                  cursorWidth: 1,
                  // Password validation
                  validator: (value) {
                    final error = FormBuilderValidators.compose([
                      FormBuilderValidators.required(
                        errorText: 'Password is required.',
                      ),
                      FormBuilderValidators.password(),
                    ])(value);
                    return error;
                  },
                  decoration: InputDecoration(
                    errorMaxLines: 2,
                    contentPadding: EdgeInsets.symmetric(
                      vertical: 12.0,
                      horizontal: 15.0,
                    ),
                    errorStyle: TextStyle(
                      color: Colors.redAccent,
                      fontSize: 13,
                    ),
                    suffixIcon: IconButton(
                      icon: Icon(
                        // Choose icon based on state for enabling/disabling visibility
                        _isPasswordVisible
                            ? Icons.visibility
                            : Icons.visibility_off,
                        color: const Color(0xFF272727),
                      ),
                      onPressed: () {
                        // UPDATE STATE ON PRESS
                        setState(() {
                          _isPasswordVisible = !_isPasswordVisible;
                        });
                      },
                    ),
                    filled: true,
                    fillColor: Color(0xFFF6F6F6),
                    hintText: 'Password',
                    hintStyle: TextStyle(color: Color(0xFF272727)),
                    floatingLabelBehavior: FloatingLabelBehavior.never,
                    enabledBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Color(0xFFF6F6F6),
                        width: 1.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Color(0xFFE3DAC9),
                        width: 2.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    // ERROR BORDER
                    errorBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Colors.redAccent, // Same as enabled color
                        width: 1.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    // FOCUSED ERROR BORDER
                    focusedErrorBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Colors.redAccent, // Same as focused color
                        width: 2.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                // Log in button
                SizedBox(
                  width: double
                      .infinity, // Forces button to fill the full allowed width
                  child: ElevatedButton(
                    // CHECK IF FORM IS VALID
                    // Button is disabled while loading
                    onPressed: _isLoading ? null : _handleLogin,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(
                        0xFFE3DAC9,
                      ), // Button background
                      foregroundColor: const Color(0xFF272727), // Text color
                      elevation:
                          0, // Removes shadow to match the flat input style
                      padding: const EdgeInsets.symmetric(
                        vertical: 12,
                        horizontal: 15,
                      ), // Matches input height
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8), // 8px Radius
                      ),
                    ),
                    // Shows spinner instead of text when button is pressed, otherwise button is showed
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Color(0xFFE3DAC9),
                            ),
                          )
                        : const Text(
                            'Log in',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                  ),
                ),
                const SizedBox(height: 12),
                // Forgot password text button
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () {
                      // TODO: Reset password logic (is not important for now)
                    },
                    style: ButtonStyle(
                      // Removes the background splash effect
                      overlayColor: WidgetStateProperty.all(Colors.transparent),

                      // Removes default padding/sizing (to keep it compact)
                      padding: WidgetStateProperty.all(
                        EdgeInsets.zero,
                      ), // Removes all internal padding inside the button. The text takes up only its natural size
                      minimumSize: WidgetStateProperty.all(
                        Size.zero,
                      ), // same for min width and height
                      tapTargetSize: MaterialTapTargetSize
                          .shrinkWrap, // Shrinks the tap target to the widget’s actual size. Prevents Flutter from adding invisible padding around the button
                      // DEFINES COLOR LOGIC
                      // Chooses a color dynamically based on the button’s current state
                      foregroundColor: WidgetStateProperty.resolveWith<Color>((
                        states,
                      ) {
                        if (states.contains(WidgetState.pressed)) {
                          return const Color(
                            0xFFE3DAC9,
                          ); // COLOR WHEN PRESSED (Beige)
                        }
                        return const Color(0xFFF6F6F6); // DEFAULT COLOR
                      }),
                    ),
                    child: const Text(
                      "Forgot password?",
                      style: TextStyle(
                        fontSize: 14,
                        decoration: TextDecoration.underline,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: const [
                    Expanded(
                      child: Divider(color: Color(0xFFF6F6F6), thickness: 0.6),
                    ),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Text(
                        'OR',
                        style: TextStyle(
                          color: Color(0xFFF6F6F6),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    Expanded(
                      child: Divider(color: Color(0xFFF6F6F6), thickness: 0.6),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _handleGoogleSignIn,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF6F6F6),
                      foregroundColor: const Color(0xFF333333),
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(
                        vertical: 12,
                        horizontal: 15,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        SvgPicture.asset(
                          'assets/icons/google.svg',
                          width: 18,
                          height: 18,
                        ),
                        const SizedBox(width: 10),
                        const Text(
                          'Continue with Google',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
