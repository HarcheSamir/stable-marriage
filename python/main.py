import random
import matplotlib.pyplot as plt
import seaborn as sns
from collections import deque
from typing import List, Dict, Tuple, Set, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ============================================================================
# 1. CORE ALGORITHM IMPLEMENTATION
# ============================================================================

class StableMarriageAlgorithm:
    """
    Encapsulates the Gale-Shapley algorithm logic.
    This class is responsible only for solving the matching problem.
    """
    def __init__(self, students: List[str], establishments: List[str], 
                 student_prefs: Dict[str, List[str]], establishment_prefs: Dict[str, List[str]]):
        self.students = students
        self.establishments = establishments
        self.student_prefs = student_prefs
        self.establishment_prefs = establishment_prefs
        self.n = len(students)
        
        # Pre-compute ranking maps for O(1) lookups, a critical optimization.
        self._student_rankings: Dict[str, Dict[str, int]] = {
            s: {e: i for i, e in enumerate(prefs)} for s, prefs in self.student_prefs.items()
        }
        self._establishment_rankings: Dict[str, Dict[str, int]] = {
            e: {s: i for i, s in enumerate(prefs)} for e, prefs in self.establishment_prefs.items()
        }

    def solve_students_propose(self) -> Dict[str, str]:
        """Runs the Gale-Shapley algorithm with students as proposers."""
        free_students: deque[str] = deque(self.students)
        engagements: Dict[str, str] = {}  # establishment -> student
        proposals_made: Dict[str, int] = {s: 0 for s in self.students}

        while free_students:
            student = free_students.popleft()
            proposal_index = proposals_made[student]
            establishment = self.student_prefs[student][proposal_index]
            proposals_made[student] += 1

            if establishment not in engagements:
                engagements[establishment] = student
            else:
                current_partner = engagements[establishment]
                if self._establishment_rankings[establishment][student] < self._establishment_rankings[establishment][current_partner]:
                    engagements[establishment] = student
                    free_students.append(current_partner)
                else:
                    free_students.append(student)

        # Reverse map for a {student: establishment} result
        return {student: est for est, student in engagements.items()}

    def solve_establishments_propose(self) -> Dict[str, str]:
        """Runs the Gale-Shapley algorithm with establishments as proposers."""
        free_establishments: deque[str] = deque(self.establishments)
        engagements: Dict[str, str] = {}  # student -> establishment
        proposals_made: Dict[str, int] = {e: 0 for e in self.establishments}

        while free_establishments:
            establishment = free_establishments.popleft()
            proposal_index = proposals_made[establishment]
            student = self.establishment_prefs[establishment][proposal_index]
            proposals_made[establishment] += 1

            if student not in engagements:
                engagements[student] = establishment
            else:
                current_partner = engagements[student]
                if self._student_rankings[student][establishment] < self._student_rankings[student][current_partner]:
                    engagements[student] = establishment
                    free_establishments.append(current_partner)
                else:
                    free_establishments.append(establishment)
        return engagements

    def verify_stability(self, matching: Dict[str, str]) -> Tuple[bool, List[Tuple[str, str]]]:
        """Verifies stability by searching for blocking pairs."""
        blocking_pairs = []
        for student, establishment in matching.items():
            student_rank_of_partner = self._student_rankings[student][establishment]
            # Check for establishments the student prefers
            for i in range(student_rank_of_partner):
                preferred_establishment = self.student_prefs[student][i]
                
                # Find who this preferred establishment is matched with
                partner_of_preferred_est = [s for s, e in matching.items() if e == preferred_establishment][0]
                
                # Check if the preferred establishment also prefers this student
                if self._establishment_rankings[preferred_establishment][student] < self._establishment_rankings[preferred_establishment][partner_of_preferred_est]:
                    blocking_pairs.append((student, preferred_establishment))
        
        return len(blocking_pairs) == 0, blocking_pairs

# ============================================================================
# 2. SATISFACTION ANALYSIS
# ============================================================================

class SatisfactionAnalyzer:
    """
    Calculates a rich set of metrics for a given matching.
    """
    def __init__(self, matching: Dict[str, str], student_prefs: Dict[str, List[str]], establishment_prefs: Dict[str, List[str]]):
        self.matching = matching
        self.student_prefs = student_prefs
        self.establishment_prefs = establishment_prefs
        self.n = len(student_prefs)

    def _get_ranks(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        student_ranks = {s: self.student_prefs[s].index(e) for s, e in self.matching.items()}
        
        # Reverse matching to iterate through establishments
        rev_matching = {e: s for s, e in self.matching.items()}
        establishment_ranks = {e: self.establishment_prefs[e].index(s) for e, s in rev_matching.items()}
        return student_ranks, establishment_ranks

    def full_analysis(self) -> Dict[str, Any]:
        """Computes all metrics and returns them in a structured dictionary."""
        s_ranks, e_ranks = self._get_ranks()
        
        s_avg_rank = sum(s_ranks.values()) / self.n
        e_avg_rank = sum(e_ranks.values()) / self.n

        s_sat_score = 100 * (1 - s_avg_rank / (self.n - 1)) if self.n > 1 else 100
        e_sat_score = 100 * (1 - e_avg_rank / (self.n - 1)) if self.n > 1 else 100

        analysis = {
            "students": {
                "avg_rank": s_avg_rank,
                "top_1_pct": sum(1 for r in s_ranks.values() if r == 0) / self.n * 100,
                "top_3_pct": sum(1 for r in s_ranks.values() if r < 3) / self.n * 100,
                "satisfaction_score": s_sat_score,
            },
            "establishments": {
                "avg_rank": e_avg_rank,
                "top_1_pct": sum(1 for r in e_ranks.values() if r == 0) / self.n * 100,
                "top_3_pct": sum(1 for r in e_ranks.values() if r < 3) / self.n * 100,
                "satisfaction_score": e_sat_score,
            },
            "overall": {
                "egalitarian_cost": sum(s_ranks.values()) + sum(e_ranks.values()),
                "sex_equality_score": abs(s_sat_score - e_sat_score),
            }
        }
        return analysis

# ============================================================================
# 3. VISUALIZATION
# ============================================================================

class Visualizer:
    """Handles the creation of all plots."""
    def __init__(self, style: str = 'whitegrid'):
        sns.set_theme(style=style)

    def plot_satisfaction_comparison(self, analysis_sp: Dict, analysis_ep: Dict, n: int):
        """Generates a grouped bar chart comparing the two algorithm versions."""
        labels = ['Étudiants', 'Établissements']
        sp_scores = [analysis_sp['students']['satisfaction_score'], analysis_sp['establishments']['satisfaction_score']]
        ep_scores = [analysis_ep['students']['satisfaction_score'], analysis_ep['establishments']['satisfaction_score']]

        x = range(len(labels))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 7))
        rects1 = ax.bar([i - width/2 for i in x], sp_scores, width, label='Étudiants Proposent', color='#4285F4')
        rects2 = ax.bar([i + width/2 for i in x], ep_scores, width, label='Établissements Proposent', color='#DB4437')

        ax.set_ylabel('Score de Satisfaction (0-100)')
        ax.set_title(f'Comparaison de la Satisfaction selon le Groupe Proposant (n={n})', pad=20, fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 105)
        ax.legend()

        ax.bar_label(rects1, padding=3, fmt='%.1f')
        ax.bar_label(rects2, padding=3, fmt='%.1f')

        fig.tight_layout()
        plt.savefig(f'satisfaction_comparison_n{n}.png', dpi=300)
        plt.show()

    def plot_statistical_summary(self, stats: Dict, n: int, num_runs: int):
        """Generates a bar chart for the aggregated statistical results."""
        labels = ['Étudiants (Proposants)', 'Établissements (Receveurs)']
        scores = [stats['avg_student_proposer_score'], stats['avg_establishment_receiver_score']]
        
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.bar(labels, scores, color=['#4285F4', '#DB4437'])
        
        ax.set_ylabel('Score de Satisfaction Moyen (0-100)')
        ax.set_title(f'Analyse Statistique sur {num_runs} Simulations (n={n})', pad=20, fontsize=16)
        ax.set_ylim(0, 105)
        ax.bar_label(bars, fmt='%.2f')

        plt.savefig(f'statistical_summary_n{n}_runs{num_runs}.png', dpi=300)
        plt.show()

# ============================================================================
# 4. EXPERIMENT MANAGEMENT & UI
# ============================================================================

class ExperimentRunner:
    """Manages the execution of experiments and displays results."""
    def __init__(self, n: int):
        self.n = n
        self.students = [f'S_{i+1}' for i in range(n)]
        self.establishments = [f'E_{i+1}' for i in range(n)]
        self.console = Console()
        self.visualizer = Visualizer()
        
        # Generate one set of preferences for the single run experiment
        self.student_prefs, self.establishment_prefs = self._generate_preferences()

    def _generate_preferences(self) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """Generates a single, new set of random preferences."""
        student_prefs = {s: random.sample(self.establishments, self.n) for s in self.students}
        establishment_prefs = {e: random.sample(self.students, self.n) for e in self.establishments}
        return student_prefs, establishment_prefs

    def run_single_experiment(self):
        """Runs and displays a detailed analysis of a single matching instance."""
        self.console.print(Panel(f"[bold blue]Lancement d'une simulation unique avec n={self.n}[/bold blue]", 
                                 title="Expérience Unique", expand=False))

        algo = StableMarriageAlgorithm(self.students, self.establishments, self.student_prefs, self.establishment_prefs)

        # Students Propose
        matching_sp = algo.solve_students_propose()
        is_stable_sp, _ = algo.verify_stability(matching_sp)
        analyzer_sp = SatisfactionAnalyzer(matching_sp, self.student_prefs, self.establishment_prefs)
        analysis_sp = analyzer_sp.full_analysis()

        # Establishments Propose
        matching_ep = algo.solve_establishments_propose()
        is_stable_ep, _ = algo.verify_stability(matching_ep)
        analyzer_ep = SatisfactionAnalyzer(matching_ep, self.student_prefs, self.establishment_prefs)
        analysis_ep = analyzer_ep.full_analysis()

        self._display_single_results(analysis_sp, is_stable_sp, "Étudiants Proposent")
        self._display_single_results(analysis_ep, is_stable_ep, "Établissements Proposent")
        
        self.visualizer.plot_satisfaction_comparison(analysis_sp, analysis_ep, self.n)

    def _display_single_results(self, analysis: Dict, is_stable: bool, title: str):
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("Métrique", style="dim", width=25)
        table.add_column("Étudiants", justify="right")
        table.add_column("Établissements", justify="right")

        table.add_row("Score de Satisfaction", f"{analysis['students']['satisfaction_score']:.2f} / 100", f"{analysis['establishments']['satisfaction_score']:.2f} / 100")
        table.add_row("Rang Moyen", f"{analysis['students']['avg_rank']:.2f}", f"{analysis['establishments']['avg_rank']:.2f}")
        table.add_row("Pourcentage Top 1", f"{analysis['students']['top_1_pct']:.1f}%", f"{analysis['establishments']['top_1_pct']:.1f}%")
        table.add_row("Pourcentage Top 3", f"{analysis['students']['top_3_pct']:.1f}%", f"{analysis['establishments']['top_3_pct']:.1f}%")
        
        self.console.print(table)
        
        stable_text = "[bold green]✓ Matching STABLE[/bold green]" if is_stable else "[bold red]✗ Matching INSTABLE[/bold red]"
        self.console.print(f"Stabilité: {stable_text}")
        self.console.print(f"Coût Égalitaire: [bold yellow]{analysis['overall']['egalitarian_cost']}[/bold yellow]")
        self.console.print(f"Score d'Inégalité: [bold red]{analysis['overall']['sex_equality_score']:.2f}[/bold red]\n")
        
    def run_statistical_analysis(self, num_runs: int):
        """Runs multiple simulations and displays the aggregated results."""
        self.console.print(Panel(f"[bold blue]Lancement de l'analyse statistique ({num_runs} runs, n={self.n})[/bold blue]",
                                 title="Analyse Statistique", expand=False))
        
        total_student_proposer_scores = 0
        total_establishment_receiver_scores = 0
        
        for _ in range(num_runs):
            s_prefs, e_prefs = self._generate_preferences()
            algo = StableMarriageAlgorithm(self.students, self.establishments, s_prefs, e_prefs)
            matching = algo.solve_students_propose() # Standard is students propose
            analyzer = SatisfactionAnalyzer(matching, s_prefs, e_prefs)
            analysis = analyzer.full_analysis()
            total_student_proposer_scores += analysis['students']['satisfaction_score']
            total_establishment_receiver_scores += analysis['establishments']['satisfaction_score']
            
        avg_student_score = total_student_proposer_scores / num_runs
        avg_establishment_score = total_establishment_receiver_scores / num_runs

        stats = {
            "avg_student_proposer_score": avg_student_score,
            "avg_establishment_receiver_score": avg_establishment_score,
        }

        table = Table(title=f"Synthèse Statistique sur {num_runs} runs", show_header=True, header_style="bold cyan")
        table.add_column("Groupe", style="dim")
        table.add_column("Score de Satisfaction Moyen Global", justify="right")
        table.add_row("Étudiants (Proposants)", f"{avg_student_score:.2f} / 100")
        table.add_row("Établissements (Receveurs)", f"{avg_establishment_score:.2f} / 100")
        self.console.print(table)
        
        self.visualizer.plot_statistical_summary(stats, self.n, num_runs)

# ============================================================================
# 5. MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # --- PART 1: Run a single, detailed experiment ---
    # This provides a deep dive into one specific, randomly generated case.
    single_run = ExperimentRunner(n=20)
    single_run.run_single_experiment()

    # --- PART 2: Run a robust statistical analysis ---
    # This smooths out randomness to show the algorithm's true average behavior.
    stats_run = ExperimentRunner(n=50)
    stats_run.run_statistical_analysis(num_runs=100)