import 'package:flutter/material.dart';
import 'package:flutter_nutriailyze_app/physical_stats_screen.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_nutriailyze_app/home_screen.dart';
import 'package:flutter_nutriailyze_app/profile_screen.dart';
import 'package:flutter_nutriailyze_app/generate_plan_loading_screen.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter/services.dart';

// SCREEN 1: INPUT
class GeneratePlanScreen extends StatefulWidget {
  const GeneratePlanScreen({super.key});

  @override
  State<GeneratePlanScreen> createState() => _GeneratePlanScreenState();
}

// Stateful widget to manage user input, profile loading, and form validation for meal plan generation.
class _GeneratePlanScreenState extends State<GeneratePlanScreen> {
  bool _isLoading = true;
  String? _weight;
  String? _height;
  String? _goal;
  String? _age;
  String? _gender;
  String? _activityLevel;
  int _selectedMeals = 3; // Default to 3 meals/day

  // State for Restriction Checkbox
  bool _hasRestrictions = false;

  final TextEditingController _preferencesController =
      TextEditingController(); // For the "Today's Vibe" text input
  final ScrollController _scrollController =
      ScrollController(); // For horizontal meal frequency selector

  bool _showErrorState =
      false; // To trigger red borders and error messages when profile is incomplete

  // Clean up controllers to prevent memory leaks
  @override
  void dispose() {
    _scrollController.dispose();
    _preferencesController.dispose();
    super.dispose();
  }

  // On init, load user profile stats and allergies from Supabase to pre-fill the form and provide recommendations.
  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  List<String> _allergies = [];
  List<Map<String, dynamic>> _activities = [];

  // Map frontend intensity values to backend API enum
  String _mapIntensityToBackend(String frontendIntensity) {
    final intensityMap = {
      'low': 'low',
      'moderate': 'moderate',
      'high': 'high',
      'very high': 'very_high',
    };
    return intensityMap[frontendIntensity.toLowerCase()] ?? 'moderate';
  }

  Future<void> _loadStats() async {
    try {
      final userId = Supabase.instance.client.auth.currentUser!.id;
      final client = Supabase.instance.client;

      // 1. Fetch Profile Data (including 'activities' column)
      final profileResponse = await client
          .from('profiles')
          .select()
          .eq('id', userId)
          .maybeSingle();

      // 2. Fetch Allergies (Existing logic)
      final allergyResponse = await client
          .from('profiles')
          .select('allergies')
          .eq('id', userId);
      //
      if (mounted) {
        setState(() {
          // Update Profile Stats
          if (profileResponse != null) {
            _weight = profileResponse['weight']?.toString();
            _height = profileResponse['height']?.toString();
            _goal = profileResponse['goal']?.toString();
            _age = profileResponse['age']?.toString();
            _gender = profileResponse['gender']?.toString();
            _activityLevel = profileResponse['activity_level']?.toString();

            // Load & Map Activities
            // Checking if 'activities' exists and is a list
            if (profileResponse['extra_activities'] != null) {
              final List<dynamic> rawActs = profileResponse['extra_activities'];

              _activities = rawActs.map((act) {
                return {
                  // Backend key: "hours" (Float)
                  // We handle potential int/string types safely
                  "hours":
                      num.tryParse(act['hours'].toString())?.toDouble() ?? 0.0,

                  // Backend key: "intensity" (String, enum: low/moderate/high/very_high)
                  "intensity": _mapIntensityToBackend(
                    act['intensity']?.toString() ?? "moderate",
                  ),
                };
              }).toList();
            }
          }

          // Update Allergies
          if (allergyResponse.isNotEmpty) {
            _allergies = allergyResponse
                .map((row) => row['allergen'] as String?)
                .where((item) => item != null)
                .map((item) => item!)
                .toList();

            if (_allergies.isNotEmpty) {
              _hasRestrictions = true;
            }
          }
        });
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // Helper method to check if all required profile stats are valid before allowing meal plan generation.
  //This ensures that the app has the necessary information to provide accurate recommendations and prevents errors during API calls.
  bool _isProfileValid() {
    bool isValid(String? value) =>
        value != null && value.isNotEmpty && value != "0";

    return isValid(_weight) &&
        isValid(_height) &&
        isValid(_goal) &&
        isValid(_age) &&
        isValid(_gender) &&
        isValid(_activityLevel);
  }

  // The build method constructs the UI of the Generate Plan screen, including profile summary, meal frequency selection, dietary restriction toggle, context input, and the generate button.
  //It also handles loading states and error states for incomplete profiles.
  @override
  Widget build(BuildContext context) {
    String displayHeight = _height != null
        ? "$_height cm"
        : "--"; // Display height with units or placeholder
    String displayWeight = _weight != null
        ? "$_weight kg"
        : "--"; // Display weight with units or placeholder
    String displayGoal = _goal ?? "--"; // Display goal or placeholder

    // Main Scaffold for the screen with a dark theme, custom app bar, and conditional body content based on loading state.
    return Scaffold(
      backgroundColor: const Color(0xFF333333),
      appBar: AppBar(
        automaticallyImplyLeading: false,
        backgroundColor: const Color(0xFF333333),
        elevation: 0,
        centerTitle: true,
        title: Text(
          "Generate Plan",
          style: GoogleFonts.ptMono(
            color: const Color(0xFFF6F6F6),
            fontWeight: FontWeight.bold,
          ),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1.0),
          child: const Divider(
            color: Color(0xFF444444),
            thickness: 0.5,
            height: 0.5,
          ),
        ),
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFFE3DAC9)),
            )
          : SafeArea(
              child: Column(
                children: [
                  Expanded(
                    child: SingleChildScrollView(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 30),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 20),

                            // 1. Profile summary
                            Material(
                              color: const Color(0xFF272727),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                                side: BorderSide(
                                  color: _showErrorState
                                      ? Colors.redAccent
                                      : const Color(0xFF444444),
                                  width: _showErrorState ? 1.5 : 1.0,
                                ),
                              ),
                              clipBehavior: Clip
                                  .hardEdge, // Ensures ripple effect is contained within the border
                              child: InkWell(
                                onTap: () {
                                  setState(() => _showErrorState = false);
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) =>
                                          const PhysicalStatsScreen(),
                                    ),
                                  ).then(
                                    (_) => _loadStats(),
                                  ); // Refresh stats when returning from physical stats screen
                                },
                                hoverColor: const Color(
                                  0xFFE3DAC9,
                                ).withValues(alpha: 0.1),
                                splashColor: const Color(
                                  0xFFE3DAC9,
                                ).withValues(alpha: 0.1),
                                child: Container(
                                  padding: const EdgeInsets.all(16),
                                  child: Row(
                                    children: [
                                      Icon(
                                        Icons.info_outline,
                                        color: _showErrorState
                                            ? Colors.redAccent
                                            : const Color(0xFF8E8E8E),
                                        size: 20,
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              "Using Profile Stats",
                                              style: GoogleFonts.ptMono(
                                                color: const Color(0xFF8E8E8E),
                                                fontSize: 10,
                                              ),
                                            ),
                                            Text(
                                              "$displayHeight • $displayWeight • $displayGoal",
                                              style: GoogleFonts.ptMono(
                                                color: const Color(0xFFF6F6F6),
                                                fontSize: 12,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      Icon(
                                        Icons.edit_outlined,
                                        color: _showErrorState
                                            ? Colors.redAccent
                                            : const Color(0xFFE3DAC9),
                                        size: 18,
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),

                            if (_showErrorState)
                              Padding(
                                padding: const EdgeInsets.only(
                                  top: 8.0,
                                  left: 4.0,
                                ),
                                child: Text(
                                  "Missing: ${_getMissingFieldsText()}",
                                  style: GoogleFonts.ptMono(
                                    color: Colors.redAccent,
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),

                            const SizedBox(height: 30),

                            // 2. Meal frequency selection
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  "Meals per day",
                                  style: GoogleFonts.ptMono(
                                    color: const Color(0xFFF6F6F6),
                                    fontSize: 16,
                                  ),
                                ),
                              ],
                            ),

                            const SizedBox(height: 8),

                            // Suggestion Text
                            Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: const Color(0xFFE3DAC9).withAlpha(25),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: const Color(0xFF444444),
                                ),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Icon(
                                    Icons.lightbulb_outline,
                                    color: Color(0xFFE3DAC9),
                                    size: 16,
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      _getMealRecommendationText(),
                                      style: GoogleFonts.ptMono(
                                        color: const Color(0xFFC7C5C1),
                                        fontSize: 11,
                                        height: 1.3,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),

                            const SizedBox(height: 12),

                            RawScrollbar(
                              controller: _scrollController,
                              thumbColor: const Color(0xFFE3DAC9),
                              trackColor: const Color(0xFF272727),
                              trackVisibility: true,
                              thumbVisibility: true,
                              thickness: 4,
                              radius: const Radius.circular(20),
                              padding: const EdgeInsets.only(top: 50),
                              child: SingleChildScrollView(
                                controller: _scrollController,
                                scrollDirection: Axis.horizontal,
                                padding: const EdgeInsets.only(bottom: 15),
                                child: Row(
                                  children: [2, 3, 4, 5, 6].map((meals) {
                                    final isSelected = _selectedMeals == meals;
                                    return Padding(
                                      padding: const EdgeInsets.only(right: 12),
                                      child: ChoiceChip(
                                        label: Text("$meals Meals"),
                                        selected: isSelected,
                                        selectedColor: const Color(0xFFE3DAC9),
                                        backgroundColor: const Color(
                                          0xFF272727,
                                        ),
                                        side: BorderSide.none,
                                        labelStyle: GoogleFonts.ptMono(
                                          color: isSelected
                                              ? const Color(0xFF333333)
                                              : const Color(0xFFF6F6F6),
                                          fontWeight: FontWeight.bold,
                                        ),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            8,
                                          ),
                                        ),
                                        onSelected: (val) => setState(
                                          () => _selectedMeals = meals,
                                        ),
                                      ),
                                    );
                                  }).toList(),
                                ),
                              ),
                            ),

                            const SizedBox(height: 30),

                            // Restriction Checkbox with dynamic helper text and styled input field that changes based on the checkbox state.
                            // This allows users to easily indicate if they have dietary restrictions and provides contextual guidance for their input.
                            GestureDetector(
                              onTap: () {
                                setState(() {
                                  _hasRestrictions = !_hasRestrictions;
                                });
                              },
                              child: Container(
                                color: Colors.transparent, // Increases tap area
                                child: Row(
                                  children: [
                                    Transform.scale(
                                      scale: 1.1,
                                      child: SizedBox(
                                        height: 22,
                                        width: 22,
                                        child: Checkbox(
                                          value: _hasRestrictions,
                                          activeColor: const Color(0xFFE3DAC9),
                                          checkColor: const Color(0xFF333333),
                                          side: const BorderSide(
                                            color: Color(0xFF8E8E8E),
                                            width: 1.5,
                                          ),
                                          shape: RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(
                                              4,
                                            ),
                                          ),
                                          onChanged: (val) {
                                            setState(
                                              () => _hasRestrictions = val!,
                                            );
                                          },
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        "I have dietary restrictions",
                                        style: GoogleFonts.ptMono(
                                          color: _hasRestrictions
                                              ? const Color(
                                                  0xFFE3DAC9,
                                                ) // Highlight when checked
                                              : const Color(0xFFF6F6F6),
                                          fontSize: 13,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),

                            const SizedBox(height: 15),

                            // 3. Context input section with dynamic text and styling based on whether the user has indicated dietary restrictions.
                            Text(
                              "Today's Vibe",
                              style: GoogleFonts.ptMono(
                                color: const Color(0xFFF6F6F6),
                                fontSize: 16,
                              ),
                            ),
                            const SizedBox(height: 5),

                            // Dynamic Helper Text
                            Text(
                              _hasRestrictions
                                  ? "Please specify your restrictions below:" // Prompt if checked
                                  : "Any other preferences? (Optional)", // Subtle if not
                              style: GoogleFonts.ptMono(
                                color: _hasRestrictions
                                    ? const Color(0xFFE3DAC9) // Highlight
                                    : const Color(0xFF8E8E8E),
                                fontSize: 12,
                                fontWeight: _hasRestrictions
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                              ),
                            ),

                            const SizedBox(height: 12),

                            TextField(
                              controller: _preferencesController,
                              maxLines: 4,
                              cursorColor: const Color(0xFFF6F6F6),
                              cursorWidth: 1,
                              style: GoogleFonts.ptMono(
                                color: const Color(0xFFF6F6F6),
                                fontSize: 14,
                              ),
                              maxLength: 200,
                              buildCounter:
                                  (
                                    context, {
                                    required currentLength,
                                    required isFocused,
                                    maxLength,
                                  }) => null,
                              decoration: InputDecoration(
                                // Dynamic Hint
                                hintText: _hasRestrictions
                                    ? "e.g. Gluten-free, No Dairy, Diabetic-friendly..."
                                    : "e.g. I want to have broccoli in my meal...",
                                hintStyle: GoogleFonts.ptMono(
                                  color: const Color(0xFF666666),
                                  fontSize: 13,
                                ),
                                filled: true,
                                fillColor: const Color(0xFF272727),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  // Dynamic Border Color
                                  borderSide: _hasRestrictions
                                      ? const BorderSide(
                                          color: Color(0xFFE3DAC9),
                                          width: 1.0,
                                        )
                                      : BorderSide.none,
                                ),
                                enabledBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  borderSide: _hasRestrictions
                                      ? const BorderSide(
                                          color: Color(0xFFE3DAC9),
                                          width: 1.0,
                                        )
                                      : BorderSide.none,
                                ),
                                focusedBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  borderSide: const BorderSide(
                                    color: Color(0xFFE3DAC9),
                                    width: 1.5,
                                  ),
                                ),
                                contentPadding: const EdgeInsets.all(16),
                              ),
                              inputFormatters: [
                                // This allows letters, numbers, spaces, and basic punctuation (.,!?)
                                FilteringTextInputFormatter.allow(
                                  RegExp(r'[a-zA-Z0-9 .,!?\n-]'),
                                ),
                              ],
                            ),

                            const SizedBox(height: 40),

                            // 4. Generate Button with validation logic that checks if the user's profile is complete before allowing them to proceed.
                            // If the profile is incomplete, it triggers an error state that highlights missing fields and prevents navigation.
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                onPressed: () {
                                  if (!_isProfileValid()) {
                                    setState(() => _showErrorState = true);
                                    return;
                                  }
                                  setState(() => _showErrorState = false);

                                  String rawPreference = _preferencesController
                                      .text
                                      .trim();
                                  // Data to send to the loading screen (and eventually the API) when generating the meal plan.
                                  // This includes all profile stats, user preferences, and any additional activities or allergies.
                                  // The backend will use this data to create a personalized meal plan.
                                  Map<String, dynamic> requestData = {
                                    "age": int.tryParse(_age ?? "30") ?? 30,
                                    "weight":
                                        double.tryParse(_weight ?? "75") ??
                                        75.0,
                                    "height":
                                        double.tryParse(_height ?? "180") ??
                                        180.0,
                                    "gender": _gender?.toLowerCase() ?? "male",
                                    "daily_activity":
                                        _activityLevel?.toLowerCase() ??
                                        "moderate",
                                    "goal": _goal?.toLowerCase() ?? "maintain",
                                    "activities": _activities,
                                    "meal_amount": _selectedMeals,
                                    "allergies": _allergies,
                                    "text_input": rawPreference,
                                  };
                                  // Navigate to the loading screen and pass the request data for meal plan generation.
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) => LoadingPlanScreen(
                                        requestData: requestData,
                                      ),
                                    ),
                                  );
                                },
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFFE3DAC9),
                                  foregroundColor: const Color(0xFF333333),
                                  padding: const EdgeInsets.symmetric(
                                    vertical: 16,
                                  ),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                ),
                                child: Text(
                                  "Generate Meal Plan",
                                  style: GoogleFonts.ptMono(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  // FOOTER
                  _buildSharedFooter(context, 1),
                ],
              ),
            ),
    );
  }

  // helper method for error state text generation (called in build method when profile is invalid)
  String _getMissingFieldsText() {
    List<String> missing = [];
    if (_age == null || _age!.isEmpty || _age == "0") missing.add("Age");
    if (_gender == null || _gender!.isEmpty) missing.add("Gender");
    if (_height == null || _height!.isEmpty || _height == "0") {
      missing.add("Height");
    }
    if (_weight == null || _weight!.isEmpty || _weight == "0") {
      missing.add("Weight");
    }
    if (_goal == null || _goal!.isEmpty) missing.add("Goal");
    if (_activityLevel == null || _activityLevel!.isEmpty) {
      missing.add("Activity");
    }
    if (missing.isEmpty) return "Complete profile stats";
    return missing.join(", ");
  }

  // Helper method to provide meal frequency recommendations based on user's profile stats. This adds a personalized touch to the UI and helps guide users in making informed choices about their meal plan structure.
  String _getMealRecommendationText() {
    if (_goal == null || _activityLevel == null) {
      return "Choose what fits your schedule best.";
    }
    final String goal = _goal!.toLowerCase();
    final String activity = _activityLevel!.toLowerCase();

    if (goal.contains('gain') ||
        goal.contains('muscle') ||
        activity.contains('extra') ||
        activity.contains('very')) {
      return "Tip: Higher frequencies (4-6) make it easier to hit high calorie/protein goals.";
    }
    if (goal.contains('lose') || goal.contains('weight')) {
      return "Tip: Fewer meals (3) allow for larger, more satisfying portions while dieting.";
    }
    return "Tip: 3 Main meals + 1 Snack is a balanced approach for maintenance.";
  }
}

// Shared Footer Builder (Used in multiple screens for consistency)
Widget _buildSharedFooter(BuildContext context, int activeIndex) {
  return Column(
    children: [
      const Divider(color: Color(0xFF444444), thickness: 0.5),
      Padding(
        padding: const EdgeInsets.only(bottom: 5.0, top: 5.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ClickableFooterIcon(
              assetPath: 'assets/icons/profile.svg',
              isActive: activeIndex == 0,
              onTap: () => Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => const ProfileScreen()),
              ),
            ),
            const SizedBox(width: 40),
            ClickableFooterIcon(
              assetPath: 'assets/icons/generate_plan.svg',
              isActive: activeIndex == 1,
              onTap: () {
                if (activeIndex != 1) {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const GeneratePlanScreen(),
                    ),
                  );
                }
              },
            ),
            const SizedBox(width: 40),
            ClickableFooterIcon(
              assetPath: 'assets/icons/home.svg',
              isActive: activeIndex == 2,
              onTap: () => Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => const HomeScreen()),
              ),
            ),
          ],
        ),
      ),
    ],
  );
}

// Custom Widget for Footer Icons with Press Feedback
class ClickableFooterIcon extends StatefulWidget {
  final String assetPath;
  final bool isActive;
  final VoidCallback onTap;

  const ClickableFooterIcon({
    super.key,
    required this.assetPath,
    required this.isActive,
    required this.onTap,
  });

  @override
  State<ClickableFooterIcon> createState() => _ClickableFooterIconState();
}

class _ClickableFooterIconState extends State<ClickableFooterIcon> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    const activeColor = Color(0xFFFDFBF7);
    const inactiveColor = Color(0xFF898987);
    const activePressed = Color(0xFFC7C5C1);
    const inactivePressed = Color(0xFF5E5E5C);

    Color currentColor = widget.isActive
        ? (_isPressed ? activePressed : activeColor)
        : (_isPressed ? inactivePressed : inactiveColor);

    return GestureDetector(
      onTapDown: (_) => setState(() => _isPressed = true),
      onTapUp: (_) {
        setState(() => _isPressed = false);
        widget.onTap();
      },
      onTapCancel: () => setState(() => _isPressed = false),
      behavior: HitTestBehavior.opaque,
      child: SvgPicture.asset(
        widget.assetPath,
        height: 52,
        width: 52,
        colorFilter: ColorFilter.mode(currentColor, BlendMode.srcIn),
      ),
    );
  }
}
