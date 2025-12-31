import 'package:flutter/material.dart';
import 'package:flutter_nutriailyze_app/edit_profile_screen.dart';
import 'package:flutter_nutriailyze_app/physical_stats_screen.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  // Logging out functionality
  Future<void> _handleLogout(BuildContext context) async {
    try {
      await Supabase.instance.client.auth.signOut();
      // Is this widget still in the widget tree
      if (context.mounted) {
        // Navigate back to Login and clear history
        // Puhses route '/' and removes all previous routes
        Navigator.of(context).pushNamedAndRemoveUntil('/', (route) => false);
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text("Error logging out")));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF333333),
      appBar: AppBar(
        backgroundColor: const Color(0xFF333333),
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Color(0xFFF6F6F6)),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          "Settings",
          style: GoogleFonts.ptMono(
            color: const Color(0xFFF6F6F6),
            fontWeight: FontWeight.bold,
          ),
        ),
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
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 20),

            // SECTION 1: ACCOUNT
            _buildSectionHeader("Account"),
            _buildSettingsItem(
              context,
              title: "Edit Profile",
              icon: Icons.person_outline,
              onTap: () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const EditProfileScreen()),
                );
              },
            ),
            _buildDivider(),
            _buildSettingsItem(
              context,
              title: "Physical Stats",
              icon: Icons.query_stats_outlined,
              onTap: () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => PhysicalStatsScreen()),
                );
              },
            ),

            const SizedBox(height: 30),

            // SECTION 2: APP
            _buildSectionHeader("App"),
            _buildSettingsItem(
              context,
              title: "Notifications",
              icon: Icons.notifications_none,
              onTap: () {
                // FOR NOW DO NOT NAVIGATE ANYWHERE, THIS WILL BE IMPLEMENTED LATER
              },
            ),
            _buildDivider(),
            _buildSettingsItem(
              context,
              title: "Privacy Policy",
              icon: Icons.lock_outline,
              onTap: () {
                // FOR NOW DO NOT NAVIGATE ANYWHERE, THIS WILL BE IMPLEMENTED LATER
              },
            ),

            const SizedBox(height: 40),

            // LOG OUT BUTTON
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: () => _handleLogout(context),
                  style: TextButton.styleFrom(
                    backgroundColor: Colors.redAccent.withValues(alpha: 0.2),
                    padding: const EdgeInsets.symmetric(vertical: 15),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text(
                    "Log Out",
                    style: GoogleFonts.ptMono(
                      color: Colors.redAccent,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 20),
            Column(
              children: [
                Text(
                  "Version 1.0.0", // App version for visual look
                  style: GoogleFonts.ptMono(
                    color: const Color(0xFF8E8E8E),
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 120),
                // COPYRIGHT
                Text(
                  "©${DateTime.now().year} Nutriailyze. All Rights Reserved.",
                  style: GoogleFonts.ptMono(
                    color: const Color(0xFFFDFBF7),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20), // Bottom padding
          ],
        ),
      ),
    );
  }

  // HELPER WIDGETS
  Widget _buildSectionHeader(String title) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      child: Text(
        title.toUpperCase(),
        style: GoogleFonts.ptMono(
          color: const Color(0xFF8E8E8E), // Grey
          fontSize: 12,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  Widget _buildSettingsItem(
    BuildContext context, {
    required String title,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    // Creates automatically - leading, title, and trailing
    // ListTile is perfect for settings screens - uses an internal Row
    return ListTile(
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 5),
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: const Color(0xFF272727),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, color: const Color(0xFFF6F6F6), size: 22),
      ),
      title: Text(
        title,
        style: GoogleFonts.ptMono(color: const Color(0xFFF6F6F6), fontSize: 16),
      ),
      trailing: const Icon(
        Icons.arrow_forward_ios,
        color: Color(0xFF8E8E8E),
        size: 16,
      ),
    );
  }

  Widget _buildDivider() {
    return const Divider(
      color: Color(0xFF444444),
      height: 1,
      indent: 70,
      endIndent: 20,
    );
  }
}
