

### **High-Level Architecture**

The code is organized into four main classes and a main execution block:

1.  **`StableMarriageAlgorithm`:** The core engine. Its only job is to take a defined problem (participants and preferences) and solve it using the Gale-Shapley algorithm.
2.  **`SatisfactionAnalyzer`:** The report card. Its only job is to take a completed matching and calculate a rich set of performance and fairness metrics.
3.  **`Visualizer`:** The graphics department. Its only job is to take the final analysis data and generate high-quality, readable plots.
4.  **`ExperimentRunner`:** The conductor. It manages the entire process: it creates the problem, tells the algorithm to solve it, asks the analyzer to score it, and instructs the visualizer to plot it.
5.  **`if __name__ == "__main__":`**: The entry point. This is what runs when you execute the script.

---

### **Class 1: `StableMarriageAlgorithm`**

This is the pure, mathematical core of the program.

*   **`__init__(self, students, establishments, student_prefs, establishment_prefs)`**
    *   **Purpose:** This is the constructor. It sets up the algorithm with a specific problem instance.
    *   **Parameters:** It takes the lists of `students`, `establishments`, and their respective preference dictionaries (`_prefs`).
    *   **Key Feature (The Optimization):** It immediately pre-computes `_student_rankings` and `_establishment_rankings`. Instead of just storing a list like `['E_3', 'E_1', 'E_2']`, it creates a dictionary like `{'E_3': 0, 'E_1': 1, 'E_2': 2}`. This is a critical optimization. When the algorithm needs to compare two partners, it can now look up their rank in O(1) time (instantly) instead of searching through a list, which is much slower (O(n) time).

*   **`solve_students_propose(self)`**
    *   **Purpose:** Implements the Gale-Shapley algorithm where the students are the proposers.
    *   **Logic:**
        1.  `free_students`: A queue of students who are not yet engaged.
        2.  `engagements`: A dictionary mapping each establishment to the student they are currently, tentatively holding onto.
        3.  The `while` loop continues as long as there is at least one free student.
        4.  Inside the loop, a `student` proposes to their next-highest-ranked `establishment`.
        5.  If the `establishment` is free, they become engaged.
        6.  If the `establishment` is already engaged, it uses the pre-computed ranking map to instantly check if the new `student` is better than their `current_partner`. If so, they dump the old partner (who becomes free again) and accept the new one.
    *   **Returns:** A final dictionary of the stable matching, mapping each student to their assigned establishment.

*   **`solve_establishments_propose(self)`**
    *   **Purpose:** The mirror-image of the above, where establishments are the proposers.
    *   **Logic:** Identical to `solve_students_propose`, but all the roles are reversed. The `free_establishments` queue drives the loop, and students receive and evaluate proposals.

*   **`verify_stability(self, matching)`**
    *   **Purpose:** A quality-control function to prove the algorithm's output is correct.
    *   **Logic:** It systematically searches for "blocking pairs." It iterates through every matched couple `(student, establishment)` and checks if there exists another `preferred_establishment` that the `student` likes more. If so, it then checks if that `preferred_establishment` *also* prefers this `student` over its own final partner. If both conditions are true, a blocking pair is found, and the matching is unstable.
    *   **Returns:** A tuple: `(True/False, list_of_blocking_pairs)`.

---

### **Class 2: `SatisfactionAnalyzer`**

This class's only job is to score the results. It is the "analysis" part of the project.

*   **`__init__(self, matching, student_prefs, establishment_prefs)`**
    *   **Purpose:** The constructor. It takes the final `matching` dictionary and the original preferences needed to perform the analysis.

*   **`_get_ranks(self)`**
    *   **Purpose:** A private helper function that does the initial work of finding the final rank for every single participant.
    *   **Returns:** Two dictionaries, mapping each student and each establishment to the rank of the partner they ended up with.

*   **`full_analysis(self)`**
    *   **Purpose:** The main public method of this class. It computes all the required metrics from the project.
    *   **Logic:** It calls `_get_ranks()` once, then uses that information to calculate:
        *   **`avg_rank`**: The simple average rank for each group.
        *   **`top_1_pct` / `top_3_pct`**: What percentage of each group got their 1st or a top-3 choice.
        *   **`satisfaction_score`**: A normalized 0-100 score, which is much better for comparisons than raw rank. A rank of 0 is 100 points, a rank of `n-1` is 0 points.
        *   **`egalitarian_cost`**: The sum of all ranks from both groups. Measures the total "unhappiness" of the system.
        *   **`sex_equality_score`**: The absolute difference between the student and establishment satisfaction scores. It's a direct measure of the bias.
    *   **Returns:** A single, neatly structured dictionary containing all these results.

---

### **Class 3: `Visualizer`**

This class is responsible for creating professional, readable graphs.

*   **`__init__(self, style='whitegrid')`**
    *   **Purpose:** Sets up the plotting environment using the `seaborn` library for better aesthetics.

*   **`plot_satisfaction_comparison(self, analysis_sp, analysis_ep, n)`**
    *   **Purpose:** To generate the single most important graph that visually proves the algorithm's bias.
    *   **Logic (This is the key change):**
        1.  It structures the data by **scenario**, not by participant.
        2.  The first group on the x-axis is "Scénario: Étudiants Proposent." It shows two bars: the high student satisfaction and the low establishment satisfaction *in that scenario*.
        3.  The second group is "Scénario: Établissements Proposent." It shows the inverted result: low student satisfaction and high establishment satisfaction.
        4.  This structure makes the comparison direct and the conclusion unavoidable. It's not about aesthetics; it's about informational clarity.
    *   **Output:** It `saves` the plot to a PNG file and then `shows` it in a pop-up window.

---

### **Class 4: `ExperimentRunner`**

This class acts as the main controller, orchestrating the work of the other classes.

*   **`__init__(self, n)`**
    *   **Purpose:** Sets up an experiment of size `n`. It creates the lists of participants and instantiates the helper classes (`Console` for printing, `Visualizer` for plotting). It also generates one set of random preferences to be used for the single-run experiment.

*   **`run_single_experiment(self)`**
    *   **Purpose:** Executes the complete workflow for a single, detailed analysis.
    *   **Steps:**
        1.  Instantiates the `StableMarriageAlgorithm`.
        2.  Calls **both** `solve_students_propose()` and `solve_establishments_propose()`.
        3.  Instantiates the `SatisfactionAnalyzer` for each of the two results.
        4.  Calls `full_analysis()` to get the complete metrics for both scenarios.
        5.  Calls `_display_single_results()` to print the findings in clean tables to the terminal.
        6.  Calls `visualizer.plot_satisfaction_comparison()` to generate the final, conclusive graph.

*   **`_display_single_results(self, analysis, is_stable, title)`**
    *   **Purpose:** A helper function for presentation. It uses the `rich` library to render the analysis data in beautiful, easy-to-read tables in the terminal.

---

### **The Main Execution Block (`if __name__ == "__main__":`)**

*   **Purpose:** This is the code that runs when you execute `python main.py`.
*   **Logic:**
    1.  It creates an `ExperimentRunner` instance for a problem of size `n=20`.
    2.  It calls the `run_single_experiment()` method, which triggers the entire process described above.
    3.  The code for the statistical analysis is present but "commented out" (disabled) as requested.