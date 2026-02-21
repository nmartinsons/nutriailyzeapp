import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_nutriailyze_app/home_screen.dart';
import 'package:flutter_nutriailyze_app/profile_screen.dart';
import 'package:flutter_nutriailyze_app/generate_plan_input_screen.dart';
import 'package:flutter_nutriailyze_app/generate_plan_loading_screen.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class PlanResultScreen extends StatefulWidget {
  // Accept the JSON data from Python
  final Map<String, dynamic> planData;
  final Map<String, dynamic> originalRequest;

  const PlanResultScreen({
    super.key,
    required this.planData,
    required this.originalRequest, // Require it
  });

  @override
  State<PlanResultScreen> createState() => _PlanResultScreenState();
}

class _PlanResultScreenState extends State<PlanResultScreen> {
  bool _isSaved = false;
  bool _isSaving = false; // To show a loading state while saving

  Future<void> _handleSave() async {
    // Prevent double saving
    if (_isSaved) return;

    setState(() => _isSaving = true);

    try {
      final userId = Supabase.instance.client.auth.currentUser!.id;
      final String goal =
          (widget.originalRequest['goal']?.toString() ?? 'custom')
              .toLowerCase();
      final Map<String, dynamic> planDataToSave = Map<String, dynamic>.from(
        widget.planData,
      )..['goal'] = goal;

      // Extract a short summary for the DB column (optional)
      final String summary =
          widget.planData['daily_summary'] ?? "Custom Meal Plan";

      // Insert into Supabase
      await Supabase.instance.client.from('meal_plans').insert({
        'user_id': userId,
        'plan_data':
            planDataToSave, // Supabase automatically converts Map to JSONB
        'plan_summary': summary,
        'created_at': DateTime.now().toIso8601String(),
      });

      if (mounted) {
        setState(() {
          _isSaved = true;
          _isSaving = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Plan saved to History!"),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Error saving plan: $e"),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // 1. Calculations (Same as before)
    final targets = widget.planData['daily_targets'] ?? {};
    final int targetCal = (targets['calories'] ?? 0);
    final int targetProt = (targets['protein'] ?? 0);
    final int targetCarb = (targets['carbs'] ?? 0);
    final int targetFat = (targets['fat'] ?? 0);

    final mealsList = widget.planData['meals'] as List<dynamic>? ?? [];
    final bool canRegenerate = widget
        .originalRequest
        .isNotEmpty; // Only show regenerate if we have the original request data

    int actualCal = 0;
    int actualProt = 0;
    int actualCarb = 0;
    int actualFat = 0;

    for (var meal in mealsList) {
      if (meal.containsKey('food_data')) {
        final m = meal['food_data']['total_macros'];
        actualProt += (m['protein'] as num).round();
        actualCarb += (m['carbs'] as num).round();
        actualFat += (m['fat'] as num).round();
      } else if (meal.containsKey('macros')) {
        final m = meal['macros'];
        actualProt += (m['protein'] as num).round();
        actualCarb += (m['carbs'] as num).round();
        actualFat += (m['fat'] as num).round();
      }
    }
    actualCal = (actualProt * 4) + (actualCarb * 4) + (actualFat * 9);

    final String cals = "$actualCal / $targetCal";
    final String prot = "${actualProt}g / ${targetProt}g";
    final String carb = "${actualCarb}g / ${targetCarb}g";
    final String fat = "${actualFat}g / ${targetFat}g";

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
          "Your Plan",
          style: GoogleFonts.ptMono(
            color: const Color(0xFFF6F6F6),
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          // --- UPDATED SAVE BUTTON ---
          IconButton(
            onPressed: _isSaving ? null : _handleSave, // Disable while saving
            icon: _isSaving
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      color: Color(0xFFE3DAC9),
                      strokeWidth: 2,
                    ),
                  )
                : Icon(
                    _isSaved ? Icons.bookmark : Icons.bookmark_border,
                    color: _isSaved
                        ? const Color(0xFFE3DAC9)
                        : const Color(0xFF8E8E8E),
                    size: 26,
                  ),
          ),
          const SizedBox(width: 10),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1.0),
          child: const Divider(
            color: Color(0xFF444444),
            thickness: 0.5,
            height: 0.5,
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Container(
              margin: const EdgeInsets.fromLTRB(
                24,
                20,
                24,
                10,
              ), // Margin around the box
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF272727),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF3E3E3E)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.2),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildSummaryItem("Calories", cals),
                      _buildSummaryItem("Protein", prot),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildSummaryItem("Carbs", carb),
                      _buildSummaryItem("Fat", fat),
                    ],
                  ),
                ],
              ),
            ),

            // --- 2. SCROLLABLE CONTENT (AI Summary + Meals) ---
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 10,
                ),
                children: [
                  // AI SUMMARY (Now part of the scrollable list)
                  if (widget.planData.containsKey('daily_summary')) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(
                          0xFFE3DAC9,
                        ).withValues(alpha: 0.05), // Very subtle beige tint
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFF444444)),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(
                            Icons.auto_awesome,
                            color: Color(0xFFE3DAC9),
                            size: 18,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              widget.planData['daily_summary'],
                              style: GoogleFonts.ptMono(
                                color: const Color(0xFFE3DAC9),
                                fontSize: 13,
                                height: 1.4,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 10),
                  ],
                  // REGENERATE BUTTON
                  Padding(
                    padding: const EdgeInsets.only(top: 5, bottom: 10),
                    child: TextButton.icon(
                      onPressed: canRegenerate
                          ? () {
                              int currentIndex =
                                  widget.originalRequest['generation_index'] ??
                                  0;
                              Map<String, dynamic> newRequest = Map.from(
                                widget.originalRequest,
                              );
                              newRequest['generation_index'] = currentIndex + 1;

                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => LoadingPlanScreen(
                                    requestData: newRequest,
                                  ),
                                ),
                              );
                            }
                          : null,
                      icon: const Icon(Icons.refresh, color: Color(0xFFE3DAC9)),
                      label: Text(
                        "Not feeling it? Regenerate",
                        style: GoogleFonts.ptMono(
                          color: const Color(0xFFE3DAC9),
                        ),
                      ),
                    ),
                  ),
                  // MEAL CARDS
                  ...mealsList.map(
                    (meal) => Column(
                      children: [
                        _buildDynamicMealCard(meal),
                        const SizedBox(height: 15),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // --- 3. FIXED FOOTER ---
            _buildSharedFooter(context, 1),
          ],
        ),
      ),
    );
  }

  // --- WIDGET BUILDERS ---

  Widget _buildDynamicMealCard(Map<String, dynamic> meal) {
    final bool isAiFormat = meal.containsKey('display_name');

    String title = "";
    String calories = "";
    String protein = "0";
    String carbs = "0";
    String fat = "0";

    List<Widget> ingredientRows = [];

    // Helper to map string types (Main, Side) to Emojis
    String getEmoji(String type) {
      type = type.toLowerCase();
      if (type.contains('main')) return "🍖";
      if (type.contains('side') || type.contains('veg')) return "🍚";
      if (type.contains('soup')) return "🥣";
      if (type.contains('drink') || type.contains('smoothie')) return "🥤";
      if (type.contains('booster') || type.contains('plus')) return "✨";
      return "🍽️";
    }

    // Helper to clean raw names
    String cleanName(String raw) => raw.split(',')[0].trim();

    if (isAiFormat) {
      // --- SCENARIO 1: AI FORMAT ---
      title = meal['title'] ?? "Meal";
      calories = "${meal['total_calories']} kcal";

      final m = meal['macros'] ?? {};
      protein = "${m['protein'] ?? 0}";
      carbs = "${m['carbs'] ?? 0}";
      fat = "${m['fat'] ?? 0}";

      // 1. Culinary Name (The "Fancy" Title)
      ingredientRows.add(
        Padding(
          padding: const EdgeInsets.only(bottom: 12.0),
          child: Text(
            meal['display_name'] ?? "Meal",
            style: GoogleFonts.ptMono(
              color: const Color(0xFFF6F6F6),
              fontSize: 16,
              fontWeight: FontWeight.bold,
              height: 1.3,
            ),
          ),
        ),
      );

      // 2. Ingredients List (From AI)
      if (meal['ingredients'] != null) {
        for (var item in meal['ingredients']) {
          ingredientRows.add(
            _buildIngredientRow(
              getEmoji(item['type'] ?? ""),
              item['type'] ?? "Item",
              item['name'],
              item['amount'] ?? "",
            ),
          );
        }
      }

      // 3. Health Tip (The AI Bonus)
      if (meal['health_tip'] != null) {
        ingredientRows.add(const SizedBox(height: 8));
        ingredientRows.add(
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: const Color(0xFF333333),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFF444444)),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.lightbulb_outline,
                  color: Color(0xFFE3DAC9),
                  size: 16,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    meal['health_tip'],
                    style: GoogleFonts.ptMono(
                      color: const Color(0xFFB0B0B0),
                      fontSize: 11,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      }
    } else {
      // --- SCENARIO 2: RAW KNN FORMAT ---
      title = meal['slot_name'] ?? "Meal";
      final foodData = meal['food_data'];

      final macros = foodData['total_macros'];
      final int p = (macros['protein'] as num).round();
      final int c = (macros['carbs'] as num).round();
      final int f = (macros['fat'] as num).round();
      final int cals = ((p * 4) + (c * 4) + (f * 9)).round();

      calories = "$cals kcal";
      protein = "$p";
      carbs = "$c";
      fat = "$f";

      // Build rows (converting num grams to String)
      if (foodData['main_dish'] != null) {
        ingredientRows.add(
          _buildIngredientRow(
            "🍖",
            "Main",
            cleanName(foodData['main_dish']['name']),
            "${foodData['main_dish']['grams']}g",
          ),
        );
      }
      if (foodData['side_dish'] != null) {
        ingredientRows.add(
          _buildIngredientRow(
            "🍚",
            "Side",
            cleanName(foodData['side_dish']['name']),
            "${foodData['side_dish']['grams']}g",
          ),
        );
      }
      if (foodData['soup'] != null) {
        ingredientRows.add(
          _buildIngredientRow(
            "🥣",
            "Soup",
            cleanName(foodData['soup']['name']),
            "${foodData['soup']['grams']}g",
          ),
        );
      }
      if (foodData['drink'] != null) {
        ingredientRows.add(
          _buildIngredientRow(
            "🥤",
            "Drink",
            cleanName(foodData['drink']['name']),
            "${foodData['drink']['grams']}g",
          ),
        );
      }
      if (foodData['boosters'] != null) {
        for (var booster in foodData['boosters']) {
          ingredientRows.add(
            _buildIngredientRow(
              "✨",
              "Plus",
              cleanName(booster['name']),
              "${booster['grams']}g",
            ),
          );
        }
      }
    }

    return Container(
      // ... (Rest of the container styling and Footer Row remains the same) ...
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF272727),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF3E3E3E)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title.toUpperCase(),
                style: GoogleFonts.ptMono(
                  color: const Color(0xFFE3DAC9),
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Icon(Icons.restaurant, color: Color(0xFF8E8E8E), size: 16),
            ],
          ),
          const Divider(color: Color(0xFF444444), height: 20, thickness: 0.5),

          ...ingredientRows, // <--- This now works for both AI and Raw

          const Divider(color: Color(0xFF444444), height: 20, thickness: 0.5),

          // Footer
          Row(
            children: [
              const Icon(
                Icons.local_fire_department,
                color: Color(0xFF8E8E8E),
                size: 14,
              ),
              const SizedBox(width: 4),
              Text(
                calories,
                style: GoogleFonts.ptMono(
                  color: const Color(0xFF8E8E8E),
                  fontSize: 12,
                ),
              ),
              const Spacer(),
              Text(
                "P:",
                style: GoogleFonts.ptMono(
                  color: const Color(0xFF8E8E8E),
                  fontSize: 12,
                ),
              ),
              Text(
                protein,
                style: GoogleFonts.ptMono(
                  color: const Color(0xFFE3DAC9),
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                "C:",
                style: GoogleFonts.ptMono(
                  color: const Color(0xFF8E8E8E),
                  fontSize: 12,
                ),
              ),
              Text(
                carbs,
                style: GoogleFonts.ptMono(
                  color: const Color(0xFFE3DAC9),
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                "F:",
                style: GoogleFonts.ptMono(
                  color: const Color(0xFF8E8E8E),
                  fontSize: 12,
                ),
              ),
              Text(
                fat,
                style: GoogleFonts.ptMono(
                  color: const Color(0xFFE3DAC9),
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: GoogleFonts.ptMono(
            color: const Color(0xFFE3DAC9),
            fontWeight: FontWeight.bold,
            fontSize: 14, // Slightly larger since we have more space now
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label.toUpperCase(),
          style: GoogleFonts.ptMono(
            color: const Color(0xFF8E8E8E),
            fontSize: 10,
            letterSpacing: 1.1,
          ),
        ),
      ],
    );
  }
}

Widget _buildIngredientRow(
  String emoji,
  String label,
  String name,
  String quantity,
) {
  return Padding(
    padding: const EdgeInsets.only(bottom: 6.0),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(emoji, style: const TextStyle(fontSize: 14)),
        const SizedBox(width: 8),
        Expanded(
          child: RichText(
            text: TextSpan(
              style: GoogleFonts.ptMono(
                color: const Color(0xFFF6F6F6),
                fontSize: 13,
              ),
              children: [
                TextSpan(
                  text: "$label: ",
                  style: const TextStyle(color: Color(0xFF8E8E8E)),
                ),
                TextSpan(
                  text: "$name ",
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                TextSpan(
                  // [FIX] Just display the string passed in
                  text: "($quantity)",
                  style: const TextStyle(color: Color(0xFFE3DAC9)),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
  );
}
// --- SHARED FOOTER WIDGET DEFINITIONS ---

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

    Color currentColor;
    if (widget.isActive) {
      currentColor = _isPressed ? activePressed : activeColor;
    } else {
      currentColor = _isPressed ? inactivePressed : inactiveColor;
    }

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
