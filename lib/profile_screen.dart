import 'package:flutter/material.dart';
import 'package:flutter_nutriailyze_app/generate_plan_input_screen.dart';
import 'package:flutter_nutriailyze_app/meal_plan_history_screen.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_nutriailyze_app/home_screen.dart';
import 'package:flutter_nutriailyze_app/settings_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  // State object
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  // Variable to hold the name
  String _displayName = "Loading...";
  // Default placeholders until data loads
  String _weight = "--";
  String _height = "--";
  String _goal = "--";

  @override
  // Called after mounting
  void initState() {
    super.initState();
    // LOAD DATA WHEN SCREEN OPENS
    _loadUserProfile();
  }

  // LOADING LOGIC
  Future<void> _loadUserProfile() async {
    final user = Supabase.instance.client.auth.currentUser;

    if (user != null) {
      // GET IDENTITY (From Auth Metadata)
      final metaName = user.userMetadata?['display_name'];
      final emailName = (user.email ?? "").split('@')[0];
      final nameToDisplay = (metaName != null && metaName.toString().isNotEmpty)
          ? metaName.toString()
          : emailName;

      // GET STATS (From Database 'profiles' table)
      // .maybeSingle() is used because a new user might not have a profile row yet.
      // If no row exists, it returns null instead of crashing.
      final profileData = await Supabase.instance.client
          .from('profiles')
          .select()
          .eq('id', user.id)
          .maybeSingle();
      // If state is in the widget tree
      if (mounted) {
        setState(() {
          _displayName = nameToDisplay;

          if (profileData != null) {
            // Add units (kg/cm) only if data exists
            _weight = profileData['weight'] != null
                ? "${profileData['weight']}kg"
                : "--";
            _height = profileData['height'] != null
                ? "${profileData['height']}cm"
                : "--";

            // Format Goal: "Lose Weight" -> "Lose" to fit the small UI space
            String rawGoal = profileData['goal'] ?? "--";
            _goal = rawGoal.split(' ')[0]; // Takes first word only
          }
        });
      }
    }
  }

  @override
  // Rendering widget
  Widget build(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;
    final avatarUrl = user?.userMetadata?['avatar_url'];

    // Page structure
    return Scaffold(
      backgroundColor: const Color(0xFF333333),
      appBar: AppBar(
        automaticallyImplyLeading: false,
        backgroundColor: const Color(0xFF333333),
        elevation: 0,
        centerTitle: true,
        title: Text(
          "Profile",
          style: GoogleFonts.ptMono(
            color: const Color(0xFFF6F6F6),
            fontWeight: FontWeight.bold,
          ),
        ),
        iconTheme: const IconThemeData(color: Color(0xFFF6F6F6)),
        actions: [
          IconButton(
            onPressed: () async {
              // WAITS FOR USER TO RETURN FROM SETTINGS
              // Using 'await' pauses this function until Settings is popped
              await Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const SettingsScreen()),
              );
              // REFRESH DATA WHEN THEY COME BACK
              // This updates the name if user changed it in Edit Profile
              _loadUserProfile();
            },
            icon: const Icon(CupertinoIcons.gear, size: 24),
            style: ButtonStyle(
              overlayColor: WidgetStateProperty.all(Colors.transparent),
              foregroundColor: WidgetStateProperty.resolveWith<Color>((states) {
                if (states.contains(WidgetState.pressed)) {
                  return const Color(0xFFE3DAC9);
                }
                return const Color(0xFFF6F6F6);
              }),
              padding: WidgetStateProperty.all(const EdgeInsets.all(8)),
            ),
          ),
          const SizedBox(width: 15),
        ],
        bottom: PreferredSize(
          // This defines the height of the bottom area (keeps it tight)
          preferredSize: const Size.fromHeight(1.0),
          child: const Divider(
            color: Color(0xFF444444),
            thickness: 0.5,
            height: 0.5, // Removes extra vertical padding
          ),
        ),
      ),

      // ROOT STRUCTURE
      // Using SafeArea, which adds auto padding, so UI does not get hidden by other items
      body: SafeArea(
        child: Column(
          children: [
            // MAIN CONTENT (Expanded + Padded)
            // Tellls to take up all remaining space along the main axis.
            Expanded(
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 30.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(height: 30),

                      // AVATAR & NAME
                      // CircleAvatar widget is used to display the user's profile picture in a circular frame. If the user has an avatar URL, it loads the image from the network; otherwise, it shows a default person icon.
                      CircleAvatar(
                        radius: 50,
                        backgroundColor: const Color(0xFFEEEEEE),
                        backgroundImage: avatarUrl != null
                            ? ResizeImage(
                                NetworkImage(avatarUrl),
                                width: 330,
                                height: 330,
                              )
                            : null,
                        child: avatarUrl == null
                            ? const Icon(
                                Icons.person,
                                size: 80,
                                color: Color(0xFF8E8D8D),
                              )
                            : null,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _displayName, // Displays the real name
                        style: GoogleFonts.ptMono(
                          color: const Color(0xFFF6F6F6),
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      // Membership chip card
                      const SizedBox(height: 5),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFF272727),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: const Color(0xFF444444)),
                        ),
                        child: Text(
                          "Free Member", // For now just for visual look, later there will be tiers and will change dynamically
                          style: GoogleFonts.ptMono(
                            color: const Color(0xFFE3DAC9),
                            fontSize: 10,
                          ),
                        ),
                      ),

                      const SizedBox(height: 25),

                      // STATS DASHBOARD
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 20),
                        decoration: BoxDecoration(
                          color: const Color(0xFF272727),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            _buildStatItem("Height", _height),
                            _buildDivider(),
                            _buildStatItem("Weight", _weight),
                            _buildDivider(),
                            _buildStatItem("Goal", _goal),
                          ],
                        ),
                      ),

                      const SizedBox(height: 30),

                      // MEAL PLAN BUTTON
                      _buildButton(
                        "Meal Plan History",
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) =>
                                  const MealPlanHistoryScreen(),
                            ),
                          );
                        },
                      ),

                      const SizedBox(height: 20),
                    ],
                  ),
                ),
              ),
            ),

            // FOOTER SECTION
            Column(
              children: [
                const Divider(color: Color(0xFF444444), thickness: 0.5),
                Padding(
                  padding: const EdgeInsets.only(bottom: 5.0, top: 5.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      ClickableFooterIcon(
                        assetPath: 'assets/icons/profile.svg',
                        isActive: true,
                        onTap: () {
                          // Stay in the same place
                        },
                      ),
                      const SizedBox(width: 40),
                      ClickableFooterIcon(
                        assetPath: 'assets/icons/generate_plan.svg',
                        isActive: false,
                        onTap: () {
                          Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const GeneratePlanScreen(),
                            ),
                          );
                        },
                      ),
                      const SizedBox(width: 40),
                      ClickableFooterIcon(
                        assetPath: 'assets/icons/home.svg',
                        isActive: false,
                        onTap: () {
                          Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const HomeScreen(),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // HELPER WIDGETS
  // This widget builds a section header with a specific style, used to separate different sections of the profile screen - height, weight, goal.
  Widget _buildStatItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: GoogleFonts.ptMono(
            color: const Color(0xFFE3DAC9),
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: GoogleFonts.ptMono(
            color: const Color(0xFF8E8E8E),
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  // This widget builds a vertical divider used in the stats dashboard to separate Height, Weight, and Goal visually. It is a simple container with a specified width and color.
  Widget _buildDivider() {
    return Container(height: 30, width: 1, color: const Color(0xFF444444));
  }

  Widget _buildButton(String text, {required VoidCallback onPressed}) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFFE3DAC9),
          foregroundColor: const Color(0xFF333333),
          padding: const EdgeInsets.symmetric(vertical: 17, horizontal: 20),
          textStyle: GoogleFonts.ptMono(
            fontSize: 15,
            fontWeight: FontWeight.bold,
          ),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        onPressed: onPressed,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(text),
            const Icon(
              Icons.arrow_forward_ios,
              size: 16,
              color: Color(0xFF333333),
            ),
          ],
        ),
      ),
    );
  }
}

// CUSTOM ICON CLASS FOR PRESS EFFECT
class ClickableFooterIcon extends StatefulWidget {
  // inputs
  final String assetPath;
  final bool isActive;
  final VoidCallback onTap;

  const ClickableFooterIcon({
    // passes widget key up to StatefulWidget
    super.key,
    required this.assetPath,
    required this.isActive,
    required this.onTap,
  });

  @override
  State<ClickableFooterIcon> createState() => _ClickableFooterIconState();
}

class _ClickableFooterIconState extends State<ClickableFooterIcon> {
  // ineraction state
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    const activeColor = Color(0xFFFDFBF7);
    const inactiveColor = Color(0xFF898987);

    // Darker shades for press effect
    const activePressed = Color(0xFFC7C5C1);
    const inactivePressed = Color(0xFF5E5E5C);

    Color currentColor;
    if (widget.isActive) {
      currentColor = _isPressed ? activePressed : activeColor;
    } else {
      currentColor = _isPressed ? inactivePressed : inactiveColor;
    }
    // touch handling
    return GestureDetector(
      // pressed
      onTapDown: (_) => setState(() => _isPressed = true),
      // released
      onTapUp: (_) {
        setState(() => _isPressed = false);
        widget.onTap();
      },
      // Handles cases like finger sliding off icon and prevents stuck “pressed” state
      onTapCancel: () => setState(() => _isPressed = false),
      // Makes entire area tappable 52x52 in this case
      behavior: HitTestBehavior.opaque,
      child: SvgPicture.asset(
        widget.assetPath,
        height: 52,
        width: 52,
        // Recolors the svg image
        colorFilter: ColorFilter.mode(currentColor, BlendMode.srcIn),
      ),
    );
  }
}
