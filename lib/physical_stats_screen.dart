import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter/cupertino.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:dropdown_search/dropdown_search.dart';

class PhysicalStatsScreen extends StatefulWidget {
  const PhysicalStatsScreen({super.key});

  @override
  State<PhysicalStatsScreen> createState() => _PhysicalStatsScreenState();
}

class _PhysicalStatsScreenState extends State<PhysicalStatsScreen> {
  bool _isLoading = true; // Show loading spinner while fetching data
  final TextEditingController _ageController =
      TextEditingController(); // Input field for Age
  final TextEditingController _heightController =
      TextEditingController(); // Input field for Height
  final TextEditingController _weightController =
      TextEditingController(); // Input field for Weight
  // Allergy options based on common allergens (can be expanded or modified as needed) - comes from EFSA list: https://www.efsa.europa.eu/en/safe2eat/food-allergens
  final List<String> _allergyOptions = [
    "Gluten",
    "Crustaceans",
    "Eggs",
    "Fish",
    "Peanuts",
    "Soy",
    "Milk",
    "Nuts",
    "Celery",
    "Mustard",
    "Sesame",
    "Sulphites",
    "Lupin",
    "Molluscs",
  ];

  // String? so no option is pre-selected (null means no selection, vs empty string which would be a valid selection but we don't have that)
  String? _selectedGender;
  String? _selectedGoal;
  String? _selectedActivity;

  // We store allergies as a list of strings (e.g. ["Gluten", "Peanuts"])
  List<String> _allergies = [];
  // Temporary variables for the dropdowns
  String? _tempHours;
  String? _tempIntensity;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    try {
      // Get current user ID from Supabase Auth
      final userId = Supabase.instance.client.auth.currentUser!.id;

      // Fetch data from 'profiles' table
      final data = await Supabase.instance.client
          .from('profiles')
          .select()
          .eq('id', userId)
          .maybeSingle(); // Returns null if no row exists yet

      // If data exists, populate the fields. We also check if the widget is still mounted before calling setState to avoid memory leaks or errors if the user navigated away.
      if (data != null && mounted) {
        setState(() {
          // Filling text fields (Converts numbers to strings)
          _ageController.text = data['age']?.toString() ?? '';
          _heightController.text = data['height']?.toString() ?? '';
          _weightController.text = data['weight']?.toString() ?? '';

          // Fill Dropdowns/Selections
          _selectedGender = data['gender'];
          _selectedGoal = data['goal'];
          _selectedActivity = data['activity_level'];

          // Fill Allergies List
          if (data['allergies'] != null) {
            _allergies = List<String>.from(data['allergies']);
          }

          // Fill Extra Activities (JSON handling)
          if (data['extra_activities'] != null) {
            final List<dynamic> jsonList = data['extra_activities'];
            _extraActivities
                .clear(); // Clear any existing data before adding new items. This ensures that if the user saves multiple times, we don't duplicate activities in the list.
            for (var item in jsonList) {
              _extraActivities.add({
                'hours': item['hours'].toString(),
                'intensity': item['intensity'].toString(),
              });
            }
          }
        });
      }
    } finally {
      // Stop loading spinner regardless of success/fail
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // The list of added activities
  final List<Map<String, String>> _extraActivities = [];

  // Activity Intensity Definitions
  final List<Map<String, String>> _intensityData = [
    {
      "level": "Low",
      "desc": "Light sweating (e.g. Yoga, Pilates, Walking). Can talk easily.",
    },
    {
      "level": "Moderate",
      "desc":
          "Hard breathing (e.g. Jogging, light lifting). Can speak in short sentences.",
    },
    {
      "level": "High",
      "desc":
          "Heavy sweating (e.g. Running, HIIT, Heavy Lifting). Difficult to speak.",
    },
    {
      "level": "Very High",
      "desc":
          "Maximum effort (e.g. Sprinting, Competitive Sports). Gasping for air.",
    },
  ];

  // Goal Options
  final List<String> _goals = ["Lose Weight", "Maintain", "Gain Muscle"];

  // Activity Data
  final List<Map<String, String>> _activityLevels = [
    {
      "value": "Sedentary",
      "desc": "Desk job or mostly seated day with minimal movement",
    },
    {
      "value": "Lightly Active",
      "desc": "Light daily movement such as standing, short walks, or errands",
    },
    {
      "value": "Moderately Active",
      "desc":
          "On your feet much of the day; frequent walking or light physical work",
    },
    {
      "value": "Very Active",
      "desc": "Manual or labor-intensive work with significant daily movement",
    },
    {
      "value": "Extra Active",
      "desc":
          "Heavy manual labor or constant physical activity throughout the day",
    },
  ];

  // Logic to show the hour picker
  void _showHourPicker() {
    // Generate list: 0.5, 1, 1.5 ... 30
    final List<String> hours = List.generate(60, (index) {
      double val = (index + 1) * 0.5;
      return val % 1 == 0 ? "${val.toInt()}" : "$val";
    });
    // showModalBottomSheet is a built-in Flutter function that shows a panel from the bottom. We customize it to show our hour options in a wheel format using CupertinoPicker.
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF272727),
      builder: (BuildContext context) {
        return SizedBox(
          height: 250,
          child: Column(
            children: [
              // Done Button
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text(
                    "Done",
                    style: GoogleFonts.ptMono(
                      color: const Color(0xFFE3DAC9),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
              // The Wheel
              Expanded(
                child: CupertinoPicker(
                  itemExtent: 32, // Each item height
                  onSelectedItemChanged: (int index) {
                    setState(() => _tempHours = hours[index]);
                  },
                  children: hours
                      .map(
                        (e) => Text(
                          "$e h/week",
                          style: GoogleFonts.ptMono(
                            color: const Color(0xFFF6F6F6),
                          ),
                        ),
                      )
                      .toList(),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  // Logic to add an extra activity
  void _addExtraActivity() {
    if (_tempHours != null && _tempIntensity != null) {
      setState(() {
        _extraActivities.add({
          "hours": _tempHours!,
          "intensity": _tempIntensity!,
        });
        // Reset dropdowns
        _tempHours = null;
        _tempIntensity = null;
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please select both Hours and Intensity")),
      );
    }
  }

  // Logic to remove an extra activity
  void _removeExtraActivity(int index) {
    setState(() {
      _extraActivities.removeAt(index);
    });
  }

  // Logic to show the intensity picker
  void _showIntensityPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF272727), // Card Color
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 15),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Done Button
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text(
                    "Done",
                    style: GoogleFonts.ptMono(
                      color: const Color(0xFFE3DAC9),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
              Text(
                "Select Intensity",
                style: GoogleFonts.ptMono(
                  color: const Color(0xFFF6F6F6),
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 15),
              // Generate list of options
              // ... is the spread operator, it takes each item from the list and adds it to the children of the column
              ..._intensityData.map((item) {
                bool isSelected = _tempIntensity == item['level'];
                return InkWell(
                  onTap: () {
                    setState(() => _tempIntensity = item['level']);
                    Navigator.pop(context); // Close sheet
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    decoration: const BoxDecoration(
                      border: Border(
                        bottom: BorderSide(
                          color: Color(0xFF444444),
                          width: 0.5,
                        ),
                      ),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                item['level']!,
                                style: GoogleFonts.ptMono(
                                  color: isSelected
                                      ? const Color(0xFFE3DAC9)
                                      : const Color(0xFFF6F6F6),
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                item['desc']!,
                                style: GoogleFonts.ptMono(
                                  color: const Color(0xFF8E8E8E),
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        ),
                        if (isSelected)
                          const Icon(
                            Icons.check,
                            color: Color(0xFFE3DAC9),
                            size: 20,
                          ),
                      ],
                    ),
                  ),
                );
              }),
            ],
          ),
        );
      },
    );
  }

  // The main build function that renders the UI. It uses Scaffold for basic layout, AppBar for the top bar, and conditionally shows a loading spinner or the form based on _isLoading.
  //The form includes text fields, dropdowns, and custom widgets for selecting activity hours and intensity.
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF333333),
      appBar: AppBar(
        backgroundColor: const Color(0xFF333333),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Color(0xFFF6F6F6)),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          "Physical Stats",
          style: GoogleFonts.ptMono(
            color: const Color(0xFFF6F6F6),
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          TextButton(
            style: TextButton.styleFrom(
              // Removes the Ripple Effect
              splashFactory: NoSplash.splashFactory,
              // Removes the Highlight effect (when holding down)
              overlayColor: Colors.transparent,
            ),
            // Function as async because we need to await the database operation. We also added validation to ensure that the user inputs valid data before saving.
            onPressed: () async {
              final int age = int.tryParse(_ageController.text) ?? 0;
              final int height = int.tryParse(_heightController.text) ?? 0;
              final int weight = int.tryParse(_weightController.text) ?? 0;
              if (age <= 0 || height <= 0 || weight <= 0) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      "Please enter valid numbers (greater than 0) for Age, Height, and Weight.",
                    ),
                    backgroundColor: Colors.redAccent,
                  ),
                );
              } else if (_selectedGender == null ||
                  _selectedGoal == null ||
                  _selectedActivity == null) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      "Please select gender, goal and activity level.",
                    ),

                    backgroundColor: Colors.redAccent,
                  ),
                );
                return; // Stop execution
              }
              try {
                // Perform the Save
                final userId = Supabase.instance.client.auth.currentUser!.id;
                // Updating the 'profiles' table with the new data. We use upsert to insert a new row if it doesn't exist or update the existing row if it does.
                //The 'id' field is used as the unique identifier for the upsert operation.
                await Supabase.instance.client.from('profiles').upsert({
                  'id': userId,
                  'age': age,
                  'height': height,
                  'weight': weight,
                  'gender': _selectedGender,
                  'goal': _selectedGoal,
                  // Handle nullable activity
                  'activity_level': _selectedActivity,
                  'allergies': _allergies,
                  'extra_activities': _extraActivities, // The list of maps
                  'updated_at': DateTime.now().toIso8601String(),
                });

                // Check if the screen is still open before touching UI
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text("Stats saved!"),
                      backgroundColor: Colors.green,
                    ),
                  );
                  Navigator.pop(context);
                }
              } catch (e) {
                // Handle Errors
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text("Error saving: $e"),
                      backgroundColor: Colors.redAccent,
                    ),
                  );
                }
              }
            },
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
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFFE3DAC9)),
            )
          : SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Biometrics
                    _buildSectionHeader("Biometrics"),
                    const SizedBox(height: 15),
                    // Gender
                    Row(
                      children: [
                        _buildGenderButton("Male"),
                        const SizedBox(width: 10),
                        _buildGenderButton("Female"),
                      ],
                    ),
                    const SizedBox(height: 15),
                    // Numbers
                    Row(
                      children: [
                        Expanded(
                          child: _buildNumberInput(
                            "Age",
                            _ageController,
                            "yrs",
                          ),
                        ),
                        const SizedBox(width: 15),
                        Expanded(
                          child: _buildNumberInput(
                            "Height",
                            _heightController,
                            "cm",
                          ),
                        ),
                        const SizedBox(width: 15),
                        Expanded(
                          child: _buildNumberInput(
                            "Weight",
                            _weightController,
                            "kg",
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 30),
                    // Goal
                    _buildSectionHeader("Goal"),
                    const SizedBox(height: 10),
                    _buildDropdown(
                      _selectedGoal,
                      _goals,
                      (val) => setState(
                        () => _selectedGoal = val!,
                      ), // Cannot be null when user picks an option, but can be null if they haven't picked anything yet, which is fine because we validate on Save.
                    ),
                    const SizedBox(height: 30),
                    // Aactivity Level
                    _buildSectionHeader("Activity Level"),
                    const SizedBox(height: 10),
                    ..._activityLevels.map(
                      (l) => _buildActivityCard(l['value']!, l['desc']!),
                    ),
                    const SizedBox(height: 30),
                    _buildSectionHeader("Exercise Habits (Optional)"),
                    const SizedBox(height: 5),
                    Text(
                      "Add specific sports or extra activities.",
                      style: GoogleFonts.ptMono(
                        color: const Color(0xFF8E8E8E),
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 15),
                    Row(
                      children: [
                        Expanded(
                          flex: 3,
                          child: GestureDetector(
                            onTap: _showHourPicker, // Opens the wheel
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 14,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFF272727),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    _tempHours != null
                                        ? "$_tempHours h/week"
                                        : "Hours/week",
                                    style: GoogleFonts.ptMono(
                                      color: _tempHours != null
                                          ? const Color(0xFFF6F6F6)
                                          : const Color(0xFF8E8E8E),
                                      fontSize: 13,
                                    ),
                                  ),
                                  const Icon(
                                    Icons.unfold_more,
                                    color: Color(0xFFE3DAC9),
                                    size: 18,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          flex: 4, // Give it more space for the text
                          child: GestureDetector(
                            onTap: _showIntensityPicker, //  Opens the sheet
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 14,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFF272727),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  // If null, show "Intensity". If selected, show value.
                                  Text(
                                    _tempIntensity ?? "Intensity",
                                    style: GoogleFonts.ptMono(
                                      color: _tempIntensity != null
                                          ? const Color(0xFFF6F6F6)
                                          : const Color(0xFF8E8E8E),
                                      fontSize: 13,
                                    ),
                                  ),
                                  const Icon(
                                    Icons.keyboard_arrow_down,
                                    color: Color(0xFFE3DAC9),
                                    size: 20,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    // The add button
                    InkWell(
                      onTap: _addExtraActivity,
                      borderRadius: BorderRadius.circular(8),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          vertical: 12,
                          horizontal: 10,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFF272727).withValues(alpha: 0.5),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: const Color(0xFF444444),
                            style: BorderStyle.solid,
                          ),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(
                              Icons.add,
                              color: Color(0xFFE3DAC9),
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              "Add activity",
                              style: GoogleFonts.ptMono(
                                color: const Color(0xFFE3DAC9),
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    // The lis of added activities. We only show this if there are activities in the list. We use asMap().entries to get both the index and the item, which allows us to implement the remove function.
                    // ...[] spreads all children directly into the parent Column
                    if (_extraActivities.isNotEmpty) ...[
                      const SizedBox(height: 15),
                      ..._extraActivities.asMap().entries.map((entry) {
                        int idx =
                            entry.key; // index (needed for delete function)
                        Map<String, String> item =
                            entry.value; // the activity map
                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFF272727),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: const Color(
                                0xFFE3DAC9,
                              ).withValues(alpha: 0.3),
                            ),
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.fitness_center,
                                color: Color(0xFF8E8E8E),
                                size: 16,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  "${item['hours']} • ${item['intensity']}",
                                  style: GoogleFonts.ptMono(
                                    color: const Color(0xFFF6F6F6),
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                              InkWell(
                                onTap: () => _removeExtraActivity(idx),
                                child: const Icon(
                                  Icons.close,
                                  color: Colors.redAccent,
                                  size: 18,
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                    ],
                    const SizedBox(height: 30),
                    // Allergies
                    _buildSectionHeader("Allergies (Optional)"),
                    const SizedBox(height: 10),
                    // Theme widget is used to override the default theme for the dropdown and its children.
                    //This allows us to customize the colors and styles of the dropdown without affecting the rest of the app.
                    //We specifically style the dropdown.
                    Theme(
                      data: Theme.of(context).copyWith(
                        // Removes Water Ripples
                        splashColor: Colors.transparent,
                        highlightColor: Colors.transparent,

                        primaryColor: const Color(0xFFE3DAC9), // Beige
                        colorScheme: const ColorScheme.dark(
                          primary: Color(0xFFE3DAC9), // Beige (Active elements)
                          onPrimary: Color(
                            0xFF333333,
                          ), // Black (Text on active elements)
                          surface: Color(0xFF272727), // Dark (Backgrounds)
                          onSurface: Color(
                            0xFFF6F6F6,
                          ), // White (Text on backgrounds)
                        ),

                        // Forces "DONE" button style (Beige background, Black text)
                        textButtonTheme: TextButtonThemeData(
                          style: TextButton.styleFrom(
                            backgroundColor: const Color(
                              0xFFE3DAC9,
                            ), // Beige Background
                            foregroundColor: const Color(
                              0xFF333333,
                            ), // Black Text
                            padding: const EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 12,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                            textStyle: GoogleFonts.ptMono(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ),
                        elevatedButtonTheme: ElevatedButtonThemeData(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFE3DAC9),
                            foregroundColor: const Color(0xFF333333),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 12,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                            textStyle: GoogleFonts.ptMono(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ),

                        // Checkbox theme to style the checkboxes in the dropdown menu. We remove the border and set custom colors for checked and unchecked states.
                        checkboxTheme: CheckboxThemeData(
                          side: const BorderSide(
                            color: Colors.transparent,
                            width: 0,
                          ),
                          fillColor: WidgetStateProperty.resolveWith((states) {
                            if (states.contains(WidgetState.selected)) {
                              return const Color(0xFFE3DAC9); // Beige Checked
                            }
                            return const Color(
                              0xFF444444,
                            ); // Dark Grey Unchecked
                          }),
                          checkColor: WidgetStateProperty.all(
                            const Color(0xFF333333),
                          ),
                        ),

                        // Input decoration theme to style the search box in the dropdown menu. We set the background color, hint text style, border styles, and padding.
                        textSelectionTheme: const TextSelectionThemeData(
                          cursorColor: Color(0xFFE3DAC9),
                          selectionColor: Color(0xFF444444),
                        ),
                      ),
                      // This is the actual dropdown widget that allows multiple selection.
                      //We use the DropdownSearch package for this, which provides a lot of customization options and built-in search functionality.
                      child: DropdownSearch<String>.multiSelection(
                        items: (filter, loadProps) => _allergyOptions,
                        // The list of currently selected allergies. This tells the widget which items are selected so it can display them correctly in the UI.
                        selectedItems: _allergies,
                        onChanged: (List<String> items) {
                          setState(() {
                            // When the user selects or deselects an allergy, this callback is triggered with the updated list of selected items.
                            //We update our _allergies state variable with this new list, which will automatically update the UI to reflect the changes.
                            _allergies = items;
                          });
                        },
                        // This section defines how the dropdown field looks when it's not expanded.
                        decoratorProps: DropDownDecoratorProps(
                          decoration: InputDecoration(
                            filled: true,
                            fillColor: const Color(0xFF272727),
                            hintText: "Select or search allergies...",
                            hintStyle: GoogleFonts.ptMono(
                              color: const Color(0xFF666666),
                              fontSize: 14,
                            ),

                            suffixIconColor: const Color(0xFF666666),

                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                              borderSide: BorderSide.none,
                            ),
                            contentPadding: const EdgeInsets.symmetric(
                              horizontal: 15,
                              vertical: 15,
                            ),
                          ),
                        ),
                        // This section defines the appearance and behavior of the dropdown menu that appears when the user taps on the field.
                        popupProps: PopupPropsMultiSelection.menu(
                          showSearchBox: true,
                          menuProps: MenuProps(
                            backgroundColor: const Color(0xFF272727),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          searchFieldProps: TextFieldProps(
                            style: GoogleFonts.ptMono(
                              color: const Color(0xFFF6F6F6),
                            ),
                            cursorColor: const Color(0xFFE3DAC9),
                            cursorWidth: 1,
                            decoration: InputDecoration(
                              hintText: "Search...",
                              hintStyle: GoogleFonts.ptMono(
                                color: const Color(0xFF666666),
                              ),
                              prefixIcon: const Icon(
                                Icons.search,
                                color: Color(0xFF8E8E8E),
                              ),
                              border: const UnderlineInputBorder(
                                borderSide: BorderSide(
                                  color: Color(0xFF444444),
                                ),
                              ),
                              enabledBorder: const UnderlineInputBorder(
                                borderSide: BorderSide(
                                  color: Color(0xFF444444),
                                ),
                              ),
                              focusedBorder: const UnderlineInputBorder(
                                borderSide: BorderSide(
                                  color: Color(0xFFE3DAC9),
                                ),
                              ),
                            ),
                          ),
                          // This defines how each item in the dropdown menu is built.
                          itemBuilder: (context, item, isSelected, isHovered) {
                            return Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 15,
                                vertical: 12,
                              ),
                              color: isSelected
                                  ? const Color(0xFF444444)
                                  : Colors.transparent,
                              child: Row(
                                children: [
                                  Text(
                                    item,
                                    style: GoogleFonts.ptMono(
                                      color: isSelected
                                          ? const Color(0xFFE3DAC9)
                                          : const Color(0xFFF6F6F6),
                                      fontWeight: isSelected
                                          ? FontWeight.bold
                                          : FontWeight.normal,
                                    ),
                                  ),
                                  const Spacer(),
                                  if (isSelected)
                                    const Icon(
                                      Icons.check,
                                      color: Color(0xFFE3DAC9),
                                      size: 18,
                                    ),
                                ],
                              ),
                            );
                          },
                        ),
                        // This defines how the selected items are displayed in the field when the dropdown is not expanded.
                        //We display them as Chips with a delete icon to remove them.
                        dropdownBuilder: (context, selectedItems) {
                          if (selectedItems.isEmpty) {
                            return const SizedBox.shrink();
                          }
                          return Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: selectedItems.map((item) {
                              return Chip(
                                label: Text(
                                  item,
                                  style: GoogleFonts.ptMono(
                                    color: const Color(0xFFE3DAC9),
                                    fontSize: 12,
                                  ),
                                ),
                                backgroundColor: const Color(0xFF333333),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(20),
                                  side: const BorderSide(
                                    color: Color(0xFF444444),
                                  ),
                                ),
                                deleteIcon: const Icon(
                                  Icons.close,
                                  size: 16,
                                  color: Color(0xFF8E8E8E),
                                ),
                                onDeleted: () {
                                  setState(() {
                                    _allergies = List.from(_allergies)
                                      ..remove(item);
                                  });
                                },
                              );
                            }).toList(),
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
    );
  }

  // Helper widget to build section headers with consistent styling. We use uppercase text and a specific font and color to differentiate it from other text in the form.
  Widget _buildSectionHeader(String title) {
    return Text(
      title.toUpperCase(),
      style: GoogleFonts.ptMono(
        color: const Color(0xFF8E8E8E),
        fontSize: 12,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  // Helper widget to build the gender selection buttons.
  // We use GestureDetector to make the entire container tappable, and we change the background color and text color based on whether it's selected or not.
  Widget _buildGenderButton(String gender) {
    bool isSelected =
        _selectedGender ==
        gender; // This line works as follows: If the currently selected gender (_selectedGender) is equal to the gender represented by this button (the gender parameter), then isSelected will be true. Otherwise, it will be false. This boolean variable is then used to determine the styling of the button, such as its background color and text color, to visually indicate whether it is selected or not.
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _selectedGender = gender),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected
                ? const Color(0xFFE3DAC9)
                : const Color(0xFF272727),
            borderRadius: BorderRadius.circular(8),
            border: isSelected
                ? null
                : Border.all(color: const Color(0xFF444444)),
          ),
          child: Center(
            child: Text(
              gender,
              style: GoogleFonts.ptMono(
                color: isSelected
                    ? const Color(0xFF333333)
                    : const Color(0xFF8E8E8E),
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
      ),
    );
  }

  // Helper widget to build number input fields for age, height, and weight.
  // We use TextField with specific input formatters to ensure only valid numbers are entered, and we style it to match the app's theme.
  Widget _buildNumberInput(
    String label,
    TextEditingController ctrl,
    String suffix,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.ptMono(
            color: const Color(0xFFF6F6F6),
            fontSize: 12,
          ),
        ),
        const SizedBox(height: 5), // spacing between label and field
        TextField(
          controller: ctrl,
          keyboardType: TextInputType.number,
          inputFormatters: [
            FilteringTextInputFormatter.digitsOnly,
            LengthLimitingTextInputFormatter(3),
          ],
          style: GoogleFonts.ptMono(color: const Color(0xFFF6F6F6)),
          cursorColor: const Color(0xFFE3DAC9),
          decoration: InputDecoration(
            hintText: "0",
            hintStyle: GoogleFonts.ptMono(color: const Color(0xFF666666)),
            filled: true,
            fillColor: const Color(0xFF272727),
            suffixText: suffix, // yrs, cm, kg
            suffixStyle: GoogleFonts.ptMono(
              color: const Color(0xFF8E8E8E),
              fontSize: 12,
            ),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 10,
              vertical: 12,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none,
            ),
          ),
        ),
      ],
    );
  }

  // Helper widget to build dropdown menus for goal selection.
  Widget _buildDropdown(
    String? current, // Currently selected value (e.g., "Lose Weight")
    List<String>
    items, // Menu options (e.g., ["Lose Weight", "Maintain", "Gain Muscle"])
    ValueChanged<String?>
    change, // Callback function triggered when user selects an item
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 15),
      decoration: BoxDecoration(
        color: const Color(0xFF272727),
        borderRadius: BorderRadius.circular(8),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: current,
          hint: Text(
            "Select...", // Shows this when current is null
            style: GoogleFonts.ptMono(color: const Color(0xFF666666)),
          ),
          isExpanded: true, // Fills available width
          dropdownColor: const Color(0xFF272727),
          icon: const Icon(Icons.keyboard_arrow_down, color: Color(0xFFE3DAC9)),
          style: GoogleFonts.ptMono(color: const Color(0xFFF6F6F6)),
          // Converts list items into clickable DropdownMenuItems
          items: items
              .map((e) => DropdownMenuItem(value: e, child: Text(e)))
              .toList(),
          onChanged: change, // Calls the callback when user picks an option
        ),
      ),
    );
  }

  // Helper widget to build activity level selection cards. Each card represents an activity level option, and when tapped, it updates the selected activity state. The card's appearance changes based on whether it's selected or not, providing visual feedback to the user.
  Widget _buildActivityCard(String title, String subtitle) {
    bool isSelected =
        _selectedActivity ==
        title; // Checks if this card's title matches the currently selected activity level. If it does, isSelected will be true, which we use to change the card's styling to indicate it's selected.
    // When the user taps on the card, we update the _selectedActivity state to this card's title, which will trigger a UI update and mark this card as selected.
    return GestureDetector(
      onTap: () => setState(() => _selectedActivity = title),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF272727),
          borderRadius: BorderRadius.circular(12),
          border: isSelected
              ? Border.all(color: const Color(0xFFE3DAC9))
              : Border.all(color: const Color(0xFF444444)),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: GoogleFonts.ptMono(
                      color: isSelected
                          ? const Color(0xFFE3DAC9)
                          : const Color(0xFFF6F6F6),
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: GoogleFonts.ptMono(
                      color: const Color(0xFF8E8E8E),
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ),
            if (isSelected)
              const Icon(
                Icons.check_circle,
                color: Color(0xFFE3DAC9),
                size: 20,
              ),
          ],
        ),
      ),
    );
  }
}
