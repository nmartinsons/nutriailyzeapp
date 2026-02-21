import 'package:flutter/material.dart';
import 'package:flutter_nutriailyze_app/generate_plan_input_screen.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_nutriailyze_app/profile_screen.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';

// The screen is a StatefulWidget, meaning it changes based on data.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

//
class _HomeScreenState extends State<HomeScreen> {
  // These variables hold the user's display name, avatar URL, selected date for meal plans, loading state, daily meals, and nutritional goals. They are initialized with default values and will be updated when the app fetches data from Supabase.
  String _displayName = "Loading...";
  String? _avatarUrl;

  DateTime _selectedDate = DateTime.now();
  bool _isLoading = true;

  List<Map<String, dynamic>> dailyMeals = [];

  int _goalCalories = 0;
  int _goalProtein = 0;
  int _goalCarbs = 0;
  int _goalFat = 0;

  // When the screen opens, two things happen immediately:
  // 1. _loadUserProfile(): It asks Supabase for the current user's email and avatar (profile picture) to display in the top bar.
  // 2. _fetchDailyPlan(): It tries to find a meal plan for the current date.
  @override
  void initState() {
    super.initState();
    _loadUserProfile();
    _fetchDailyPlan();
  }

  // This method retrieves the current user's profile information from Supabase. It checks if the user is logged in and then extracts the display name and avatar URL from the user's metadata.
  //If the display name is not available, it uses the email prefix as a fallback. Finally, it updates the state to reflect the retrieved profile information on the UI.
  void _loadUserProfile() {
    final user = Supabase.instance.client.auth.currentUser;
    if (user != null) {
      final metaName = user.userMetadata?['display_name'];
      final emailName = (user.email ?? "").split('@')[0];
      final metaAvatar = user.userMetadata?['avatar_url'];

      if (mounted) {
        setState(() {
          // If user has a display name in their profile metadata, use it. Otherwise, fall back to using the email prefix (the part before '@') as the display name.
          _displayName = (metaName != null && metaName.toString().isNotEmpty)
              ? metaName.toString()
              : emailName;
          _avatarUrl = metaAvatar;
        });
      }
    }
  }

  // This method fetches the meal plan for the selected date from Supabase. It constructs a query to get the meal plans for the current user that were created on the selected date. If a meal plan is found, it extracts the daily targets (calories, protein, carbs, fat) and the list of meals.
  Future<void> _fetchDailyPlan() async {
    if (!mounted) return;
    setState(() => _isLoading = true);

    try {
      // Get the current user's ID from Supabase. This is necessary to query the meal plans that belong to this specific user. The '!' operator is used to assert that the currentUser is not null, which means this code assumes that the user is logged in when this method is called.
      final userId = Supabase.instance.client.auth.currentUser!.id;

      // To fetch the meal plan for the selected date, we need to define the start and end timestamps for that day. This is done by creating two DateTime objects: one for the start of the day (00:00:00) and one for the end of the day (23:59:59). These timestamps are then converted to ISO8601 string format, which is compatible with Supabase queries.
      final startOfDay = DateTime(
        _selectedDate.year,
        _selectedDate.month,
        _selectedDate.day,
      ).toIso8601String();
      final endOfDay = DateTime(
        _selectedDate.year,
        _selectedDate.month,
        _selectedDate.day,
        23,
        59,
        59,
      ).toIso8601String();

      // This block of code queries the 'meal_plans' table in Supabase to find a meal plan that matches the current user's ID and was created within the selected date.
      final response = await Supabase.instance.client
          .from('meal_plans')
          .select()
          .eq('user_id', userId)
          .gte('created_at', startOfDay)
          .lte('created_at', endOfDay)
          .order('created_at', ascending: false)
          .limit(1)
          .maybeSingle();

      // If a meal plan is found (response is not null), it extracts the daily targets for calories, protein, carbs, and fat from the response. It also processes the list of meals to extract relevant information such as title, type, calories, protein, carbs, and fat for each meal.
      //This information is then stored in the state to be displayed in the UI. If no meal plan is found for that date, it resets the daily meals and goals to empty/default values.
      if (response != null) {
        final planData = response['plan_data'];
        final targets = planData['daily_targets'] ?? {};
        final mealsList = planData['meals'] as List<dynamic>? ?? [];

        // If the widget is still mounted (i.e., the user hasn't navigated away), we update the state with the new meal plan data. We set the daily meals and nutritional goals based on the fetched meal plan. After updating the meals list, we also load the checkbox states to reflect which meals have been marked as eaten by the user.
        if (mounted) {
          setState(() {
            // It extracts the daily goals from the database JSON.
            _goalCalories = ((targets['calories'] ?? 0) as num).round();
            _goalProtein = ((targets['protein'] ?? 0) as num).round();
            _goalCarbs = ((targets['carbs'] ?? 0) as num).round();
            _goalFat = ((targets['fat'] ?? 0) as num).round();

            // The meals list from the plan data is processed to create a structured list of meals with their nutritional information.
            //Each meal is transformed into a map that includes the meal's title, type, calories, protein, carbs, fat, and an 'isEaten' flag that indicates whether the user has marked the meal as eaten or not.
            dailyMeals = mealsList.asMap().entries.map((entry) {
              final meal = entry.value;
              final idx = entry.key;

              int k = 0, p = 0, c = 0, f = 0;
              String title = "Meal ${idx + 1}";
              String type = "Meal";

              // Format A: Raw Python Output
              if (meal.containsKey('food_data')) {
                final m = meal['food_data']['total_macros'];
                p = (m['protein'] as num).round();
                c = (m['carbs'] as num).round();
                f = (m['fat'] as num).round();
                k = ((p * 4) + (c * 4) + (f * 9)).round();
                title = meal['food_data']['main_dish']['name'];
                type = meal['slot_name'] ?? "Meal";
              }
              // Format B: Enriched / Gemini Output
              else if (meal.containsKey('macros')) {
                final m = meal['macros'];
                p = ((m['protein'] ?? 0) as num).round();
                c = ((m['carbs'] ?? 0) as num).round();
                f = ((m['fat'] ?? 0) as num).round();
                k = ((meal['total_calories'] ?? 0) as num).round();
                title = meal['display_name'] ?? "Meal";
                type = meal['title'] ?? "Meal";
              }

              // Returning a structured map for each meal that includes its index, title, type, calories, protein, carbs, fat, and an 'isEaten' flag initialized to false. This structured data will be used to display the meals in the UI and track which meals have been eaten by the user.
              return {
                "id": idx,
                "title": title,
                "type": type,
                "kcal": k,
                "protein": p,
                "carbs": c,
                "fat": f,
                "isEaten": false,
              };
            }).toList();
          });
          // Load checkbox states AFTER setting the list
          await _loadCheckboxStates();
        }
      }
      // This block runs if the database query completed successfully but found zero meal plans for the selected date.
      else {
        if (mounted) {
          setState(() {
            dailyMeals = []; // 1. Clear the list
            _goalCalories = 0; // 2. Reset the goal
          });
        }
      }
    } finally {
      // This sets the loading state to false after the fetch operation is complete, regardless of whether it succeeded or failed.
      //This ensures that the UI stops showing the loading indicator and can display either the meal plan or an empty state message.
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // This function generates a specific, unique ID string for every single meal slot in history.
  String _getMealKey(int mealIndex) {
    // 1. Unique Key Format: "YYYY-MM-DD_meal_X"
    final dateKey = DateFormat('yyyy-MM-dd').format(_selectedDate);
    // 2. Combine with index: e.g., "2023-10-25_meal_0". Index indicates meal slot (0 for breakfast, 1 for lunch, etc.) and dateKey ensures it's unique per day.
    return "${dateKey}_meal_$mealIndex";
  }

  // This function loads the saved states of the meal checkboxes from SharedPreferences. It retrieves the boolean value for each meal using the unique key generated by _getMealKey.
  //If a value is found, it updates the 'isEaten' status of each meal in the dailyMeals list accordingly.
  Future<void> _loadCheckboxStates() async {
    // SharedPreferences is a way to store simple key-value pairs persistently on the device. Here, we use it to remember which meals the user has marked as eaten, even after they close and reopen the app.
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return; // Safety check
    setState(() {
      // For loop for each meal in the dailyMeals list, it generates the unique key for that meal using the _getMealKey function and retrieves the saved boolean value from SharedPreferences. If a value is found (true or false), it updates the 'isEaten' status of that meal in the dailyMeals list. If no value is found (null), it defaults to false, meaning the meal is not marked as eaten.
      for (int i = 0; i < dailyMeals.length; i++) {
        final key = _getMealKey(i);
        dailyMeals[i]['isEaten'] = prefs.getBool(key) ?? false;
      }
    });
  }

  // This function is called when the user taps the left or right arrows to change the selected date.
  void _changeDate(int days) {
    setState(() {
      _selectedDate = _selectedDate.add(Duration(days: days));
    });
    _fetchDailyPlan();
  }

  // This function toggles the 'isEaten' status of a meal when the user taps on it.
  // It updates the state to reflect the change in the UI and then saves the new status to SharedPreferences using the unique key for that meal.
  void _toggleMeal(int index) async {
    setState(() {
      dailyMeals[index]['isEaten'] = !dailyMeals[index]['isEaten'];
    });

    // Saving to SharedPreferences
    final prefs = await SharedPreferences.getInstance();
    final key = _getMealKey(index);
    await prefs.setBool(key, dailyMeals[index]['isEaten']);
  }

  // Function formatting the selected date for display.
  String _getFormattedDate() {
    // If today is selected, show "Today, 25 Oct". Otherwise, show "Wed, 25 Oct".
    if (_isSelectedDateToday()) {
      return "Today, ${DateFormat('d MMM').format(_selectedDate)}";
    }
    return DateFormat('EEE, d MMM').format(_selectedDate);
  }

  // Bool function to check if the selected date is today.
  bool _isSelectedDateToday() {
    final now = DateTime.now();
    return _selectedDate.year == now.year &&
        _selectedDate.month == now.month &&
        _selectedDate.day == now.day;
  }

  // The build method is responsible for describing how to display the widget in terms of other, lower-level widgets. In this case, it constructs the entire home screen UI, including the app bar with the user's profile information, a date selector, a dashboard showing the consumed calories and macros, a list of meals for the day, and a shared footer for navigation.
  //It also handles different states such as loading, empty meal plans, and displaying the meal plan with interactive checkboxes to mark meals as eaten.
  @override
  Widget build(BuildContext context) {
    // Variables to accumulate the total calories, protein, carbs, and fat consumed based on the meals that have been marked as eaten by the user.
    int currentKcal = 0;
    int currentProtein = 0;
    int currentCarbs = 0;
    int currentFat = 0;

    // For loop to iterate through the dailyMeals list and check if each meal has been marked as eaten (isEaten == true). If a meal is marked as eaten, its calories, protein, carbs, and fat values are added to the respective current totals.
    for (var meal in dailyMeals) {
      if (meal['isEaten'] == true) {
        currentKcal += (meal['kcal'] as int);
        currentProtein += (meal['protein'] as int);
        currentCarbs += (meal['carbs'] as int);
        currentFat += (meal['fat'] as int);
      }
    }

    // This calculates the ratio of consumed calories to the goal calories. If the goal calories is greater than 0, it divides the current calories by the goal calories to get a ratio. If the goal calories is 0 (to avoid division by zero), it defaults the ratio to 0.0.
    double calRatio = _goalCalories > 0 ? (currentKcal / _goalCalories) : 0.0;

    // If ratio > 1.0 (over limit), use Red. Otherwise Green.
    Color circleColor = calRatio > 1.0
        ? Colors.redAccent
        : const Color(0xFF67BD6E);

    // The Scaffold widget provides the basic structure for the home screen, including the app bar and body. The app bar displays the user's avatar and welcome message, while the body contains the main content of the screen, which changes based on the loading state and whether a meal plan exists for the selected date.
    return Scaffold(
      backgroundColor: const Color(0xFF333333),
      appBar: AppBar(
        automaticallyImplyLeading:
            false, // Removes default back button or hamburger menu
        backgroundColor: const Color(0xFF333333),
        elevation: 0, // Removes shadow for a flatter look
        centerTitle: false,
        toolbarHeight: 80,
        title: Padding(
          padding: const EdgeInsets.only(left: 10.0, top: 20.0),
          child: Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: const Color(0xFFEEEEEE),
                backgroundImage: _avatarUrl != null
                    ? ResizeImage(
                        NetworkImage(_avatarUrl!),
                        width: 120,
                        height: 120,
                      )
                    : null,
                child: _avatarUrl == null
                    ? const Icon(
                        Icons.person,
                        size: 32,
                        color: Color(0xFF8E8D8D),
                      )
                    : null,
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Welcome,",
                    style: GoogleFonts.ptMono(
                      color: const Color(0xFFFDFBF7),
                      fontSize: 12,
                    ),
                  ),
                  Text(
                    _displayName,
                    style: GoogleFonts.ptMono(
                      color: const Color(0xFFE3DAC9),
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        // This adds a thin divider line at the bottom of the app bar to visually separate it from the body content. The PreferredSize widget is used to specify the height of the divider, and the Divider widget is styled with a specific color and thickness to match the app's design.
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1.0),
          child: const Divider(
            color: Color(0xFF444444),
            thickness: 0.5,
            height: 0.5,
          ),
        ),
      ),

      // The body of the Scaffold is where the main content of the home screen is displayed.
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              // Scrollable area for the main content, allowing it to expand and contract based on the amount of content and screen size.
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 30.0),
                  child: Column(
                    children: [
                      const SizedBox(height: 15),
                      // Logo
                      SizedBox(
                        height: 35,
                        child: SvgPicture.asset(
                          'assets/logos/LogoFullName.svg',
                          fit: BoxFit.contain,
                          alignment: Alignment.center,
                        ),
                      ),
                      const SizedBox(height: 15),
                      // Date selector
                      Container(
                        decoration: BoxDecoration(
                          color: const Color(0xFFE3DAC9),
                          borderRadius: BorderRadius.circular(30),
                          border: Border.all(color: const Color(0xFF444444)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize
                              .min, // Wraps content tightly, takes only the needed space
                          children: [
                            // Makes the left arrow tappable to go to the previous date. When tapped, it calls the _changeDate function with -1 to subtract one day from the selected date.
                            GestureDetector(
                              onTap: () => _changeDate(-1),
                              child: const Padding(
                                padding: EdgeInsets.all(8.0),
                                child: Icon(
                                  Icons.chevron_left,
                                  color: Color(0xFF272727),
                                  size: 20,
                                ),
                              ),
                            ),
                            const SizedBox(width: 5),
                            Text(
                              _getFormattedDate(),
                              style: GoogleFonts.ptMono(
                                color: const Color(0xFF272727),
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(width: 5),
                            GestureDetector(
                              onTap: () => _changeDate(1),
                              child: const Padding(
                                padding: EdgeInsets.all(8.0),
                                child: Icon(
                                  Icons.chevron_right,
                                  color: Color(0xFF272727),
                                  size: 20,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 30),

                      // Mian content area that changes based on loading state and meal plan availability
                      if (_isLoading) // loading state shows a spinner
                        const Padding(
                          padding: EdgeInsets.only(top: 50),
                          child: CircularProgressIndicator(
                            color: Color(0xFFE3DAC9),
                          ),
                        )
                      // If no meal plan exists for the selected date, it shows an empty state message with an option to generate a new meal plan if the selected date is today.
                      else if (dailyMeals.isEmpty)
                        _buildEmptyState()
                      else
                        Column(
                          children: [
                            // Macro dashboard showing consumed calories and macros with a circular progress indicator. The dashboard displays the total calories consumed, the goal calories, and a circular progress bar that visually represents how close the user is to reaching their calorie goal.
                            // It also includes linear progress bars for protein, carbs, and fat, showing the current intake versus the goals for each macronutrient.
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: const Color(0xFF272727),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Column(
                                children: [
                                  Row(
                                    mainAxisAlignment:
                                        MainAxisAlignment.spaceBetween,
                                    children: [
                                      Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            "Consumed",
                                            style: GoogleFonts.ptMono(
                                              color: const Color(0xFF8E8E8E),
                                              fontSize: 12,
                                            ),
                                          ),
                                          Text(
                                            "$currentKcal kcal",
                                            style: GoogleFonts.ptMono(
                                              color: const Color(0xFFE3DAC9),
                                              fontSize: 24,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                          Text(
                                            "Goal: $_goalCalories",
                                            style: GoogleFonts.ptMono(
                                              color: const Color(0xFF8E8E8E),
                                              fontSize: 12,
                                            ),
                                          ),
                                        ],
                                      ),
                                      SizedBox(
                                        height: 60,
                                        width: 60,
                                        child: CircularProgressIndicator(
                                          value: calRatio.clamp(0.0, 1.0),
                                          backgroundColor: const Color(
                                            0xFF333333,
                                          ),
                                          color: circleColor, // Dynamic Color
                                          strokeWidth: 6,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 20),
                                  _buildProgressBar(
                                    "Protein",
                                    currentProtein,
                                    _goalProtein,
                                  ),
                                  const SizedBox(height: 10),
                                  _buildProgressBar(
                                    "Carbs",
                                    currentCarbs,
                                    _goalCarbs,
                                  ),
                                  const SizedBox(height: 10),
                                  _buildProgressBar(
                                    "Fats",
                                    currentFat,
                                    _goalFat,
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 30),
                            Align(
                              alignment: Alignment.centerLeft,
                              child: Text(
                                "Today's Meals",
                                style: GoogleFonts.ptMono(
                                  color: const Color(0xFFF6F6F6),
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            const SizedBox(height: 10),

                            ...dailyMeals.asMap().entries.map((entry) {
                              return _buildMealCheckboxCard(
                                entry.value,
                                entry.key,
                              );
                            }),
                          ],
                        ),

                      const SizedBox(height: 20),
                    ],
                  ),
                ),
              ),
            ),
            // Footer
            _buildSharedFooter(context, 2),
          ],
        ),
      ),
    );
  }

  // Empty state widget
  Widget _buildEmptyState() {
    bool isToday = _isSelectedDateToday();

    return Padding(
      padding: const EdgeInsets.only(top: 20),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(30),
            decoration: BoxDecoration(
              color: const Color(0xFF272727),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF444444)),
            ),
            child: Column(
              children: [
                Icon(
                  Icons.calendar_today,
                  size: 60,
                  color: const Color(0xFF8E8E8E).withValues(alpha: 0.5),
                ),
                const SizedBox(height: 20),
                Text(
                  "No Meal Plan Found",
                  style: GoogleFonts.ptMono(
                    color: const Color(0xFFF6F6F6),
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  isToday
                      ? "You haven't generated a meal plan for today yet."
                      : "No meal plan recorded for this date.",
                  textAlign: TextAlign.center,
                  style: GoogleFonts.ptMono(
                    color: const Color(0xFF8E8E8E),
                    fontSize: 12,
                  ),
                ),

                if (isToday) ...[
                  const SizedBox(height: 30),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const GeneratePlanScreen(),
                          ),
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFE3DAC9),
                        foregroundColor: const Color(0xFF333333),
                        padding: const EdgeInsets.symmetric(
                          vertical: 16,
                          horizontal: 24,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            "Generate Plan",
                            style: GoogleFonts.ptMono(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          const Icon(Icons.arrow_forward, size: 20),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  // Widget for building the progress bars for protein, carbs, and fats. It takes a label (e.g., "Protein"), the current amount consumed, and the goal amount as parameters. If the goal is 0, it returns an empty widget. Otherwise, it calculates the raw progress as a ratio of current to goal and clamps it for display purposes.
  Widget _buildProgressBar(String label, int current, int goal) {
    // If the goal is 0, we can't calculate progress, so we return an empty widget to avoid showing a misleading progress bar.
    if (goal == 0) return const SizedBox.shrink();

    // Calculating raw percentage
    double rawProgress = current / goal;
    // Clamping the progress to a maximum of 1.0 for display purposes. This means that if the user exceeds their goal, the progress bar will show as full (100%) but we will use color to indicate that they are over the limit.
    double displayProgress = rawProgress.clamp(0.0, 1.0);

    // If over 100%, turn Red/Orange. Otherwise Green.
    Color barColor = rawProgress > 1.0
        ? Colors.redAccent
        : const Color(0xFF67BD6E);

    // The widget consists of a label on the left and the current/goal values on the right, followed by a linear progress bar that visually represents the progress towards the goal.
    //The color of the progress bar changes dynamically based on whether the user has exceeded their goal or not.
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: GoogleFonts.ptMono(
                color: const Color(0xFFF6F6F6),
                fontSize: 12,
              ),
            ),
            Text(
              "$current / ${goal}g",
              style: GoogleFonts.ptMono(
                // Turns text red if over
                color: rawProgress > 1.0
                    ? Colors.redAccent
                    : const Color(0xFF8E8E8E),
                fontSize: 11,
              ),
            ),
          ],
        ),
        const SizedBox(height: 5),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: displayProgress,
            minHeight: 6,
            backgroundColor: const Color(0xFF333333),
            color: barColor, // Use dynamic color
          ),
        ),
      ],
    );
  }

  // This widget builds a card for each meal in the daily meals list. It displays the meal's title, type, calories, and a circular checkbox that indicates whether the meal has been marked as eaten or not. When the user taps on the card, it toggles the 'isEaten' status of that meal and updates the UI accordingly.
  Widget _buildMealCheckboxCard(Map<String, dynamic> meal, int index) {
    bool isEaten = meal['isEaten'];
    return GestureDetector(
      onTap: () => _toggleMeal(index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF272727),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isEaten ? const Color(0xFF67BD6E) : Colors.transparent,
          ),
        ),
        child: Row(
          children: [
            Container(
              height: 24,
              width: 24,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isEaten
                    ? const Color(0xFF67BD6E)
                    : const Color(0xFF333333),
                border: Border.all(color: const Color(0xFFF6F6F6), width: 1),
              ),
              child: isEaten
                  ? const Icon(Icons.check, size: 16, color: Color(0xFF333333))
                  : null,
            ),
            const SizedBox(width: 15),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    meal['title'],
                    style: GoogleFonts.ptMono(
                      color: isEaten
                          ? const Color(0xFF8E8E8E)
                          : const Color(0xFFF6F6F6),
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      decoration: isEaten ? TextDecoration.lineThrough : null,
                      decorationColor: const Color(0xFFE3DAC9),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  // Displays the meal type and calories in a smaller font below the title. The text color is also dimmed if the meal is marked as eaten.s
                  Text(
                    "${meal['type'].toString().toUpperCase()} • ${meal['kcal']} kcal",
                    style: GoogleFonts.ptMono(
                      color: const Color(0xFF8E8E8E),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Footer widget that is shared across multiple screens for navigation.
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
              onTap: () => Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => const GeneratePlanScreen()),
              ),
            ),
            const SizedBox(width: 40),
            ClickableFooterIcon(
              assetPath: 'assets/icons/home.svg',
              isActive: activeIndex == 2,
              onTap: () {},
            ),
          ],
        ),
      ),
    ],
  );
}

// This class defines a custom widget for the footer icons that are used for navigation in the app. Each icon can be in an active or inactive state, which changes its color.
//The widget also handles tap interactions, allowing users to navigate to different screens when they tap on the icons. The color of the icon changes dynamically based on whether it is active and whether it is being pressed, providing visual feedback to the user.
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
        setState(
          () => _isPressed = false,
        ); // 1. Reset pressed state immediately on tap release for instant visual feedback
        widget.onTap(); // 2. Perform action after tap is released
      },
      // This ensures that if the user taps down but then drags their finger away or cancels the tap, the pressed state will still reset, preventing the icon from getting stuck in a pressed state.
      onTapCancel: () => setState(() => _isPressed = false),
      behavior: HitTestBehavior
          .opaque, // This allows the GestureDetector to detect taps even on transparent areas, ensuring that the entire area of the icon is tappable.
      child: SvgPicture.asset(
        widget.assetPath,
        height: 52,
        width: 52,
        colorFilter: ColorFilter.mode(currentColor, BlendMode.srcIn),
      ),
    );
  }
}
