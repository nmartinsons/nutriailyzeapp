import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:intl/intl.dart';
import 'package:flutter_nutriailyze_app/generate_plan_output_screen.dart';

class MealPlanHistoryScreen extends StatefulWidget {
  const MealPlanHistoryScreen({super.key});

  @override
  State<MealPlanHistoryScreen> createState() => _MealPlanHistoryScreenState();
}

class _MealPlanHistoryScreenState extends State<MealPlanHistoryScreen> {
  bool _isLoading = true; // Loading state while fetching from database
  List<Map<String, dynamic>> _history =
      []; // List of meal plan history items from the database

  @override
  void initState() {
    super.initState();
    _fetchHistory(); // Fetch meal plan history when the screen initializes
  }

  // DB fetching function to get meal plan history for the current user
  Future<void> _fetchHistory() async {
    try {
      // 1. Get current user ID from Supabase Auth
      final userId = Supabase.instance.client.auth.currentUser!.id;

      // 2. Query 'meal_plans' table for entries matching the user ID, ordered by creation date (newest first)
      final response = await Supabase.instance.client
          .from('meal_plans')
          .select()
          .eq('user_id', userId)
          .order('created_at', ascending: false); // Newest first

      // If the widget is still mounted, update the state with the fetched history data
      if (mounted) {
        // The response is expected to be a list of maps, where each map represents a meal plan entry from the database.
        setState(() {
          // List<...> because Supabase returns many rows from meal_plans, not just one.
          // Map<String, dynamic> because each row is like a JSON object: key/value pairs such as "created_at", "plan_data", etc.
          // String in Map<String, ...> because column names (keys) are strings.
          // dynamic in Map<..., dynamic> because values can be different types (String, int, bool, nested map/list, null).
          _history = List<Map<String, dynamic>>.from(response);
          _isLoading = false; // Stop loading indicator after data is fetched
        });
      }
    } catch (e) {
      // Error handling: If there's an issue fetching data from the database, we catch the exception and show an error message.
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Error loading history: $e"),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  // UI BUILD FUNCTION
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
          "History",
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
      // BODY: Show loading indicator, empty state, or list of history items
      body: SafeArea(
        child: _isLoading
            ? const Center(
                child: CircularProgressIndicator(color: Color(0xFFE3DAC9)),
              )
            : _history.isEmpty
            ? _buildEmptyState()
            : ListView.builder(
                padding: const EdgeInsets.all(24),
                itemCount: _history.length,
                itemBuilder: (context, index) {
                  final item = _history[index];
                  return _buildHistoryCard(item);
                },
              ),
      ),
    );
  }

  // WIDGET: HISTORY CARD
  Widget _buildHistoryCard(Map<String, dynamic> dbRow) {
    // 1. Parse Database Row
    final DateTime createdAt = DateTime.parse(dbRow['created_at']);
    final Map<String, dynamic> planData = dbRow['plan_data'];

    // 2. Extract Display Data
    final String day = DateFormat('dd').format(createdAt);
    final String month = DateFormat('MMM').format(createdAt).toUpperCase();

    final targets = planData['daily_targets'] ?? {};
    final String calories = (targets['calories'] ?? 0).toString();

    final List meals = planData['meals'] ?? [];
    final int mealCount = meals.length;

    // 3. Extract Goal Tag
    // Try to find it in biometrics, otherwise guess based on targets, or fallback
    String tag = (planData['goal'] ?? "").toString();
    if (tag.isEmpty || tag == "null") {
      if (planData.containsKey('user_biometrics_summary')) {
        tag = planData['user_biometrics_summary']['goal']?.toString() ?? "PLAN";
      } else {
        tag = "CUSTOM";
      }
    }
    // Uppercase the tag for consistent display
    tag = tag.toUpperCase();

    // 4. Build the card UI with the extracted data
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF272727),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF3E3E3E)),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => PlanResultScreen(
                  planData: planData,
                  originalRequest:
                      const {}, // Empty map because we can't regenerate old history
                  fromHistory: true,
                ),
              ),
            );
          },
          splashColor: const Color(0xFFE3DAC9).withValues(alpha: 0.1),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                // 1. DATE BOX
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: const Color(0xFF333333),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF444444)),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        day,
                        style: GoogleFonts.ptMono(
                          color: const Color(0xFFF6F6F6),
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        month,
                        style: GoogleFonts.ptMono(
                          color: const Color(0xFF8E8E8E),
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(width: 16),

                // 2. INFO COLUMN
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Tag / Goal
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFE3DAC9).withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          tag,
                          style: GoogleFonts.ptMono(
                            color: const Color(0xFFE3DAC9),
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      // Stats
                      Text(
                        "$calories kcal • $mealCount Meals",
                        style: GoogleFonts.ptMono(
                          color: const Color(0xFFF6F6F6),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),

                // 3. ARROW
                const Icon(
                  Icons.arrow_forward_ios,
                  color: Color(0xFF8E8E8E),
                  size: 14,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // WIDGET: EMPTY STATE
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.history, size: 80, color: Color(0xFF444444)),
          const SizedBox(height: 20),
          Text(
            "No plans yet",
            style: GoogleFonts.ptMono(
              color: const Color(0xFFF6F6F6),
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "Generate your first meal plan to see it here.",
            style: GoogleFonts.ptMono(
              color: const Color(0xFF8E8E8E),
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}
