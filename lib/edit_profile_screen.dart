import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter/services.dart';

class EditProfileScreen extends StatefulWidget {
  const EditProfileScreen({
    super.key,
  }); // This is the widget’s constructor, which accepts a key and passes it to StatefulWidget. Allows Flutter to optimize rebuilds

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final TextEditingController _nameController = TextEditingController();
  String _email =
      "Loading..."; // Placeholder when email/username has not been loaded yet
  String? _avatarUrl; // To store the current image URL
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadUserIdentity();
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  // FETCHES USER EMAIL AND NAME
  Future<void> _loadUserIdentity() async {
    final user = Supabase
        .instance
        .client
        .auth
        .currentUser; // Reads the current authenticated user

    if (user != null) {
      // Trying to fetch from TABLE first
      final data = await Supabase.instance.client
          .from('profiles')
          .select()
          .eq('id', user.id) // match the logged-in user
          .maybeSingle(); // Prevents errors if the profile row does not exist yet

      if (mounted) {
        setState(() {
          _email =
              user.email ??
              ""; // Uses email from Supabase Auth. Otherwise, fallback to empty string if null

          // Prefer Table Data -> Fallback to Metadata -> Fallback to Empty
          _nameController.text =
              data?['display_name'] ?? user.userMetadata?['display_name'] ?? "";
          _avatarUrl = data?['avatar_url'] ?? user.userMetadata?['avatar_url'];
        });
      }
    }
  }

  // PHOTO UPLOAD LOGIC
  Future<void> _uploadPhoto() async {
    final ImagePicker picker = ImagePicker();
    // Picks Image first
    // Allows selecting images from Allows selecting images from gallery and camera
    final XFile? image = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 600, // Compress it slightly
    );

    if (image == null) return;

    // Disables buttons and shows spinner in UI
    setState(() => _isLoading = true);

    try {
      // Only authenticated users upload avatars
      final user = Supabase.instance.client.auth.currentUser;
      if (user == null) return;

      // Converts image file into raw binary
      final bytes = await image.readAsBytes();
      // Extracts original file type
      final fileExt = image.path.split('.').last;
      // Creates a unique, user-scoped filename
      final fileName =
          '${user.id}/avatar.${DateTime.now().millisecondsSinceEpoch}.$fileExt';

      // 2. Upload to Supabase Storage
      await Supabase.instance.client.storage
          .from('avatars')
          .uploadBinary(
            fileName,
            bytes,
            fileOptions: const FileOptions(
              upsert: true,
              contentType: 'image/jpeg',
            ),
          );
      // Get Public URL
      final String publicUrl = Supabase.instance.client.storage
          .from('avatars')
          .getPublicUrl(fileName);

      // Update Auth Metadata (Keeps session in sync)
      await Supabase.instance.client.auth.updateUser(
        UserAttributes(data: {'avatar_url': publicUrl}),
      );

      // Update the 'profiles' TABLE
      await Supabase.instance.client.from('profiles').upsert({
        'id': user.id,
        'avatar_url': publicUrl,
        'updated_at': DateTime.now().toIso8601String(),
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Photo updated!"),
            backgroundColor: Colors.green,
          ),
        );
      }
      setState(() {
        _avatarUrl = publicUrl;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Upload failed: $e"),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // SAVE DISPLAY NAME CHANGES
  Future<void> _updateIdentity() async {
    // SANITIZE AND VALIDATE
    final cleanName = _nameController.text.trim();

    if (cleanName.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Display Name cannot be empty."),
          backgroundColor: Colors.redAccent, // Red for error
        ),
      );
      return; // STOP execution here. Do not send to Supabase.
    }

    // PROCEED WITH SAVE
    setState(() => _isLoading = true);

    try {
      final userId = Supabase.instance.client.auth.currentUser!.id;
      // Update Supabase User Metadata
      await Supabase.instance.client.auth.updateUser(
        UserAttributes(
          data: {
            'display_name': cleanName, // Uses the trimmed version
          },
        ),
      );

      await Supabase.instance.client.from('profiles').upsert({
        'id': userId,
        'display_name': cleanName,
        'updated_at': DateTime.now().toIso8601String(),
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Profile updated successfully!"),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Error updating profile: $e"),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
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
          "Edit Profile",
          style: GoogleFonts.ptMono(
            color: const Color(0xFFF6F6F6),
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          // Save Button (Shows spinner if loading)
          TextButton(
            onPressed: _updateIdentity,
            style: ButtonStyle(
              overlayColor: WidgetStateProperty.all(
                Colors.transparent,
              ), // no ripple effect for all states (pressed, hovered, focused)
            ),

            child: Text(
              "Save",
              style: GoogleFonts.ptMono(
                color: const Color(0xFFE3DAC9),
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(30.0),
        child: Column(
          children: [
            // PHOTO CHANGE
            Center(
              child: GestureDetector(
                onTap: _uploadPhoto,
                child: Stack(
                  children: [
                    CircleAvatar(
                      radius: 55,
                      backgroundColor: Color(0xFFEEEEEE),
                      // If URL exists, show image. Else show Person Icon
                      backgroundImage: _avatarUrl != null
                          ? NetworkImage(_avatarUrl!)
                          : null,
                      child: _avatarUrl == null
                          ? const Icon(
                              Icons.person,
                              size: 88,
                              color: Color(0xFF8E8D8D),
                            )
                          : null,
                    ),
                    // Loading Spinner Overlay
                    if (_isLoading)
                      const Positioned.fill(
                        child: CircularProgressIndicator(
                          color: Color(0xFFE3DAC9),
                        ),
                      ),
                    Positioned(
                      bottom: 0,
                      right: 0,
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: const BoxDecoration(
                          color: Color(0xFFE3DAC9),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.camera_alt,
                          size: 16,
                          color: Color(0xFF333333),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 40),

            // DISPLAY NAME FIELD
            _buildLabel("Display Name"),
            const SizedBox(height: 8),
            TextField(
              controller: _nameController,
              style: GoogleFonts.ptMono(color: const Color(0xFFF6F6F6)),
              cursorColor: const Color(0xFFF6F6F6),
              cursorWidth: 1,

              inputFormatters: [
                // Allow: a-z, A-Z, 0-9
                FilteringTextInputFormatter.allow(RegExp(r'[a-zA-Z0-9]')),

                // Limit length
                LengthLimitingTextInputFormatter(30),
              ],
              decoration: InputDecoration(
                filled: true,
                fillColor: const Color(0xFF272727),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: BorderSide.none,
                ),
                // Hint if empty
                hintText: "Enter your name",
                hintStyle: GoogleFonts.ptMono(color: const Color(0xFF666666)),
              ),
            ),

            const SizedBox(height: 20),

            // EMAIL FIELD (READ ONLY)
            _buildLabel("Email"),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                // Slightly darker/transparent to indicate "Read Only"
                color: const Color(0xFF272727).withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF444444)),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.lock_outline,
                    size: 16,
                    color: const Color(0xFF8E8E8E),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _email, // Displays the loaded email
                      style: GoogleFonts.ptMono(color: const Color(0xFF8E8E8E)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "Email cannot be changed.",
                style: GoogleFonts.ptMono(
                  color: const Color(0xFF8E8E8E),
                  fontSize: 10,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // HELPER WIDGET
  Widget _buildLabel(String text) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        text,
        style: GoogleFonts.ptMono(color: const Color(0xFF8E8E8E), fontSize: 12),
      ),
    );
  }
}
