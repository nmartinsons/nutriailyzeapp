import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_nutriailyze_app/home_screen.dart';
import 'package:flutter_nutriailyze_app/profile_screen.dart';
import 'package:flutter_nutriailyze_app/generate_plan_input_screen.dart';
import 'package:flutter_nutriailyze_app/generate_plan_loading_screen.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class PlanResultScreen extends StatefulWidget {
  final Map<String, dynamic> planData; // The actual meal plan JSON from Python
  final Map<String, dynamic>
  originalRequest; // What the user asked for, the user's original inputs (age, weight, goal, etc.) Used to enable the "Regenerate" button
  final bool fromHistory; // Bool is this a saved plan

  const PlanResultScreen({
    super.key,
    required this.planData,
    required this.originalRequest,
    this.fromHistory =
        false, // optional parameter to indicate if this screen is being shown from a history item
  });

  // createState() is the factory method that creates the actual mutable state object where all UI logic lives (_PlanResultScreenState).
  @override
  State<PlanResultScreen> createState() => _PlanResultScreenState();
}

class _PlanResultScreenState extends State<PlanResultScreen> {
  bool _isSaved =
      false; // Tracks whether the current plan has been saved to history. This is used to update the bookmark icon and prevent multiple saves.
  bool _isSaving = false; // To show a loading state while saving

  Future<void> _handleSave() async {
    // Preventing double saving
    if (_isSaved) return;

    // Set loading state to true to disable the save button and show a spinne
    setState(() => _isSaving = true);

    // 1. Prepare data for Supabase
    try {
      // Get the current user's ID from Supabase Auth
      final userId = Supabase.instance.client.auth.currentUser!.id;
      // widget.originalRequest['goal'] = get the goal from original request (e.g., "Maintain")
      // ?.toString() = safely convert to string using optional chaining
      // If it's null, returns null (doesn't crash)
      // If it exists, converts it to a string
      // ?? 'custom' = fallback to 'custom' if the left side was null
      // .toLowerCase() = normalize to lowercase (e.g., "Maintain" → "maintain")
      final String goal =
          (widget.originalRequest['goal']?.toString() ?? 'custom')
              .toLowerCase();
      // This is needed so that when users retrieve the plan from history, goal can displayed
      // Map<String, dynamic>.from(widget.planData) = creates a shallow copy of the plan data
      // Not modifying the original widget.planData
      // Creating a new map with the same contents
      // ..['goal'] = goal = cascade operator (..) adds/overrides the goal field
      // Sets planDataToSave['goal'] = goal
      // The cascade returns the modified map
      // We get a new map with all the original plan data PLUS the goal field set to the normalized goal.
      final Map<String, dynamic>
      planDataToSave = Map<String, dynamic>.from(widget.planData)
        ..['goal'] =
            goal; // same as planDataToSave['goal'] = goal, but allows us to do it inline while creating the map, makes code cleaner

      // Extract a short summary for the DB column
      // This comes from the original AI response
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

      // 2. Update UI state to reflect that the plan is now saved, and show a success message.
      if (mounted) {
        setState(() {
          _isSaved = true;
          _isSaving = false;
        });
        // sUCCESS SNACKBAR
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Plan saved to History!"),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      // ERROR HANDLING
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

  // The build method is called every time the UI needs to be rendered. It constructs the entire screen based on the current state and the plan data passed from the previous screen.
  @override
  Widget build(BuildContext context) {
    // 1. Extracting target macros from the plan data.
    final targets = widget.planData['daily_targets'] ?? {};
    final int targetCal = (targets['calories'] ?? 0);
    final int targetProt = (targets['protein'] ?? 0);
    final int targetCarb = (targets['carbs'] ?? 0);
    final int targetFat = (targets['fat'] ?? 0);
    // mealsList is the list of meals in the plan. Each meal contains its own macros which we will sum up to get the actual intake for the day.
    final mealsList = widget.planData['meals'] as List<dynamic>? ?? [];
    // canRegenerate is true if this screen was not accessed from history (since history items are already saved and we don't want to allow regenerating from them) AND if we have an originalRequest with data (since without it we wouldn't know what parameters to use for regeneration).
    final bool canRegenerate =
        !widget.fromHistory && widget.originalRequest.isNotEmpty;

    // Variables to hold the actual calculated macros from the meals. We will loop through each meal, extract its macros, and sum them up to get the total actual intake for the day. This will allow us to display "X / Y" in the summary (e.g., "1500 kcal / 2000 kcal").
    int actualCal = 0;
    int actualProt = 0;
    int actualCarb = 0;
    int actualFat = 0;

    // Loop through each meal in the mealsList and extract macros.
    for (var meal in mealsList) {
      // KNN Format: macros are under meal['food_data']['total_macros']
      if (meal.containsKey('food_data')) {
        final m = meal['food_data']['total_macros'];
        actualProt += (m['protein'] as num).round();
        actualCarb += (m['carbs'] as num).round();
        actualFat += (m['fat'] as num).round();
      }
      // AI Format: macros are under meal['macros']
      else if (meal.containsKey('macros')) {
        final m = meal['macros'];
        actualProt += (m['protein'] as num).round();
        actualCarb += (m['carbs'] as num).round();
        actualFat += (m['fat'] as num).round();
      }
    }
    // Macronutrient calorie formula for calculating actual calories based on the summed macros from the meals:
    actualCal = (actualProt * 4) + (actualCarb * 4) + (actualFat * 9);

    // Now we have both the target macros (from the plan's daily_targets) and the actual macros (calculated from summing up the meals).
    // This can be used to create strings to display in the summary box at the top of the screen.
    final String cals = "$actualCal / $targetCal";
    final String prot = "${actualProt}g / ${targetProt}g";
    final String carb = "${actualCarb}g / ${targetCarb}g";
    final String fat = "${actualFat}g / ${targetFat}g";

    // Scaffold is the main structure of the screen, providing the app bar, body, and other UI elements.
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
          if (!widget.fromHistory) ...[
            // Save button only shown if not from history (since it's already saved)
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

            // 2. Scrollable list (AI Summary + Rgenerate butto + Meals)
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 10,
                ),
                children: [
                  // AI SUMMARY
                  // The spread operator (...) When combined with [, means "unpack this list into the parent list.". This reduces nesting and allows us to conditionally add multiple widgets (the summary container and the spacing) in one clean block without needing to wrap them in an extra container or use multiple if statements.
                  // This allows us to show an AI-generated summary at the top of the meal list, providing users with a quick overview of their plan.
                  if (widget.planData.containsKey('daily_summary')) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE3DAC9).withValues(alpha: 0.05),
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
                  // Regenerate Button
                  // Only show if we have an original request (to avoid showing it in history) and if we are not already in a regeneration loop
                  if (canRegenerate)
                    Padding(
                      padding: const EdgeInsets.only(top: 5, bottom: 10),
                      child: TextButton.icon(
                        onPressed: () {
                          // If we don't have the original request data, we can't regenerate since we won't know what parameters to use for the new generation.
                          //Also, if we're already in a regeneration loop (e.g., user keeps hitting regenerate), we want to prevent stacking multiple loading screens on top of each other.
                          //This check ensures that the button only works when it's valid to do so.
                          if (!canRegenerate) return;
                          // Increment the generation index in the original request to signal the backend to create a new plan based on the same parameters but with a different random seed or generation logic.
                          //This allows users to get a completely new plan without changing their inputs.
                          int currentIndex =
                              widget.originalRequest['generation_index'] ?? 0;
                          // This makes a copy of the original request map and updates the generation_index field. This way we keep all the original parameters intact but just signal to the backend that we want a new generation.
                          Map<String, dynamic> newRequest = Map.from(
                            widget.originalRequest,
                          );
                          newRequest['generation_index'] = currentIndex + 1;
                          // Navigate to the loading screen with the new request data. The loading screen will use this data to call the API and fetch a new plan, and then navigate back to this result screen with the new plan data once it's ready.
                          Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(
                              builder: (context) =>
                                  LoadingPlanScreen(requestData: newRequest),
                            ),
                          );
                        },
                        icon: const Icon(
                          Icons.refresh,
                          color: Color(0xFFE3DAC9),
                        ),
                        label: Text(
                          "Not feeling it? Regenerate",
                          style: GoogleFonts.ptMono(
                            color: const Color(0xFFE3DAC9),
                          ),
                        ),
                      ),
                    ),
                  // Meal Cards
                  // ... means we are unpacking the list of widgets generated by mapping each meal in mealsList to a Column that contains the meal card and some spacing.
                  // This allows us to dynamically create a list of meal cards based on the data we have, and insert them directly into the ListView without needing an extra wrapper.
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

            // 3. Fixed Footer with navigation (Profile, Generate Plan, Home)
            _buildSharedFooter(context, 1),
          ],
        ),
      ),
    );
  }

  // Widegt to build each meal card dynamically based on the structure of the meal data.
  // This function checks whether the meal is in AI format or Raw KNN format, extracts the relevant information accordingly, and builds a styled card that displays the meal details, ingredients, macros, and any health tips if available.
  Widget _buildDynamicMealCard(Map<String, dynamic> meal) {
    // Determining the format of the meal data. AI-generated meals have a 'display_name' field, while raw KNN meals do not. This check allows us to handle both formats in one function and display them correctly.
    final bool isAiFormat = meal.containsKey('display_name');
    // Variables to hold the extracted information that will be displayed on the card. We initialize them with default values and then populate them based on the meal format.
    String title = "";
    String calories = "";
    String protein = "0";
    String carbs = "0";
    String fat = "0";

    // List of widgets that will represent the ingredient rows in the meal card. We will populate this list based on the meal format, and then insert it into the card's column.
    List<Widget> ingredientRows = [];

    // Helper to map string types (Main, Side) to Emojis
    String getEmoji(String type) {
      type = type.toLowerCase();
      if (type.contains('main')) return "🍖";
      if (type.contains('side')) return "🍚";
      if (type.contains('veg') || type.contains('vegetable')) return "🥦";
      if (type.contains('soup')) return "🥣";
      if (type.contains('drink') || type.contains('smoothie')) return "🥤";
      if (type.contains('booster') || type.contains('plus')) return "✨";
      return "🍽️";
    }

    // Helper to clean raw names
    String cleanName(String raw) => raw.split(',')[0].trim();

    if (isAiFormat) {
      // SCENARIO 1: AI format
      title = meal['title'] ?? "Meal";
      calories = "${meal['total_calories']} kcal";

      final m = meal['macros'] ?? {};
      protein = "${m['protein'] ?? 0}";
      carbs = "${m['carbs'] ?? 0}";
      fat = "${m['fat'] ?? 0}";

      // 1. Culinary Name
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
      // This builds a list of ingredient rows based on the AI response. Each ingredient has a type (e.g., Main, Side) which we use to determine the emoji and label, a name, and an amount.
      // We loop through the ingredients and create a styled row for each one using the _buildIngredientRow helper function.
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

      // 3. Health Tip (From AI)
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
      // SCENARIO 2: Raw KNN format
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

      // Building rows
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

          // Spread operator to insert the list of ingredient rows directly into the column. This allows us to dynamically generate as many ingredient rows as needed based on the meal data, without needing to manually code for a specific number of ingredients or wrap them in an extra container.
          // Each row was created based on the meal data format and contains the relevant information about the ingredient, styled with emojis and labels for clarity.
          ...ingredientRows,

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

  // This widget builds each individual summary item in the summary box at the top of the screen.
  // It takes a label (e.g., "Calories") and a value (e.g., "1500 kcal / 2000 kcal") and styles them in a consistent way.
  Widget _buildSummaryItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: GoogleFonts.ptMono(
            color: const Color(0xFFE3DAC9),
            fontWeight: FontWeight.bold,
            fontSize: 14,
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

// Helper widget to build each ingredient row in the meal card. It takes an emoji (based on the ingredient type), a label (e.g., "Main", "Side"), the name of the ingredient, and the quantity, and styles them in a consistent way for display in the meal card.
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
        // Expanded makes its child take up the remaining space in a Row or Column. Here it lets the text fill the rest of the row after the emoji and spacing.
        Expanded(
          // RichText allows multiple styles within one block of text.
          child: RichText(
            // TextSpan is a styled chunk of text used inside RichText
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
// Footer widget that is shared across multiple screens for consistent navigation.

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

// A reusable widget for the footer icons that can be clicked to navigate between screens.
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
