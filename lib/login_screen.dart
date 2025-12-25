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
  final _formKey = GlobalKey<FormState>();
  bool _isPasswordVisible = false;
  bool _isLoading = false; // To show spinner

  Future<void> _handleLogin() async {
    // A. Validate Form
    if (!_formKey.currentState!.validate()) return;

    // B. Start Loading
    setState(() => _isLoading = true);

    final email = _emailController.text.trim();
    final password = _passwordController.text;

    try {
      // C. CALL SUPABASE
      final AuthResponse res = await Supabase.instance.client.auth
          .signInWithPassword(email: email, password: password);

      // D. Handle Success
      if (mounted) {
        if (res.session != null) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const HomeScreen()),
          );
        }
      }
    } on AuthException catch (e) {
      // E. Handle Supabase Errors (e.g. User already exists)
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
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const SizedBox(height: 165),
                // EMAIL FIELD
                TextFormField(
                  controller: _emailController,
                  style: const TextStyle(color: Color(0xFF272727)),
                  // Form validation
                  validator: (value) {
                    // Validation logic
                    final error = FormBuilderValidators.compose([
                      FormBuilderValidators.required(
                        errorText: 'Email is required.',
                      ),
                      FormBuilderValidators.email(
                        errorText: 'Enter a valid email.',
                      ),
                    ])(value);
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
                    hintText: 'Email',
                    // For visible placeholder
                    hintStyle: TextStyle(color: Color(0xFF272727)),
                    floatingLabelBehavior: FloatingLabelBehavior.never,
                    // Borders
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
                    // ERROR BORDER (Matches Enabled Border -> No Red Line)
                    errorBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Color(0xFFF6F6F6), // Same as enabled color
                        width: 1.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    // FOCUSED ERROR BORDER (Matches Focused Border -> No Red Line)
                    focusedErrorBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Color(0xFFE3DAC9), // Same as focused color
                        width: 2.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                  ),
                ),
                // 24PX SPACE
                const SizedBox(height: 24),
                // PASSWORD FIELD
                TextFormField(
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
                      FormBuilderValidators.minLength(
                        6,
                        errorText: 'Password must be 6+ characters.',
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
                        // Choose icon based on state
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
                    // ERROR BORDER (Matches Enabled Border -> No Red Line)
                    errorBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Color(0xFFF6F6F6), // Same as enabled color
                        width: 1.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    // FOCUSED ERROR BORDER (Matches Focused Border -> No Red Line)
                    focusedErrorBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                        color: Color(0xFFE3DAC9), // Same as focused color
                        width: 2.0,
                      ),
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                // Log in button
                SizedBox(
                  width: double.infinity, // Forces button to fill the width
                  child: ElevatedButton(
                    // CHECK IF FORM IS VALID
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
                      // TODO: Reset password logic
                    },
                    style: ButtonStyle(
                      // Remove the background splash effect
                      overlayColor: WidgetStateProperty.all(Colors.transparent),

                      // Remove default padding/sizing (to keep it compact)
                      padding: WidgetStateProperty.all(EdgeInsets.zero),
                      minimumSize: WidgetStateProperty.all(Size.zero),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,

                      // DEFINE COLOR LOGIC
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
                        decorationColor: Color(0xFFF6F6F6),
                      ),
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
