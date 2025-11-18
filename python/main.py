import random
import matplotlib.pyplot as plt
import seaborn as sns
from collections import deque
from typing import List, Dict, Tuple, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ============================================================================
# CLASSES 1, 2, 4 (No changes here, logic is sound)
# ============================================================================
class StableMarriageAlgorithm:
    def __init__(self, students: List[str], establishments: List[str],
                 student_prefs: Dict[str, List[str]], establishment_prefs: Dict[str, List[str]]):
        self.students, self.establishments = students, establishments
        self.student_prefs, self.establishment_prefs = student_prefs, establishment_prefs
        self.n = len(students)
        self._student_rankings = {s: {e: i for i, e in enumerate(prefs)} for s, prefs in self.student_prefs.items()}
        self._establishment_rankings = {e: {s: i for i, s in enumerate(prefs)} for e, prefs in self.establishment_prefs.items()}
    def solve_students_propose(self) -> Dict[str, str]:
        free_students: deque[str] = deque(self.students)
        engagements: Dict[str, str] = {}
        proposals_made: Dict[str, int] = {s: 0 for s in self.students}
        while free_students:
            student = free_students.popleft()
            establishment = self.student_prefs[student][proposals_made[student]]
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
        return {student: est for est, student in engagements.items()}
    def solve_establishments_propose(self) -> Dict[str, str]:
        free_establishments: deque[str] = deque(self.establishments)
        engagements: Dict[str, str] = {}
        proposals_made: Dict[str, int] = {e: 0 for e in self.establishments}
        while free_establishments:
            establishment = free_establishments.popleft()
            student = self.establishment_prefs[establishment][proposals_made[establishment]]
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
        blocking_pairs = []
        for student, establishment in matching.items():
            student_rank_of_partner = self._student_rankings[student][establishment]
            for i in range(student_rank_of_partner):
                preferred_establishment = self.student_prefs[student][i]
                partner_of_preferred_est = [s for s, e in matching.items() if e == preferred_establishment][0]
                if self._establishment_rankings[preferred_establishment][student] < self._establishment_rankings[preferred_establishment][partner_of_preferred_est]:
                    blocking_pairs.append((student, preferred_establishment))
        return len(blocking_pairs) == 0, blocking_pairs

class SatisfactionAnalyzer:
    def __init__(self, matching: Dict[str, str], student_prefs: Dict[str, List[str]], establishment_prefs: Dict[str, List[str]]):
        self.matching, self.student_prefs, self.establishment_prefs = matching, student_prefs, establishment_prefs
        self.n = len(student_prefs)
    def _get_ranks(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        student_ranks = {s: self.student_prefs[s].index(e) for s, e in self.matching.items()}
        rev_matching = {e: s for s, e in self.matching.items()}
        establishment_ranks = {e: self.establishment_prefs[e].index(s) for e, s in rev_matching.items()}
        return student_ranks, establishment_ranks
    def full_analysis(self) -> Dict[str, Any]:
        s_ranks, e_ranks = self._get_ranks()
        s_avg_rank = sum(s_ranks.values()) / self.n if self.n > 0 else 0
        e_avg_rank = sum(e_ranks.values()) / self.n if self.n > 0 else 0
        s_sat_score = 100 * (1 - s_avg_rank / (self.n - 1)) if self.n > 1 else 100
        e_sat_score = 100 * (1 - e_avg_rank / (self.n - 1)) if self.n > 1 else 100
        return {
            "students": {"avg_rank": s_avg_rank, "top_1_pct": sum(1 for r in s_ranks.values() if r == 0) / self.n * 100 if self.n > 0 else 0, "top_3_pct": sum(1 for r in s_ranks.values() if r < 3) / self.n * 100 if self.n > 0 else 0, "satisfaction_score": s_sat_score},
            "establishments": {"avg_rank": e_avg_rank, "top_1_pct": sum(1 for r in e_ranks.values() if r == 0) / self.n * 100 if self.n > 0 else 0, "top_3_pct": sum(1 for r in e_ranks.values() if r < 3) / self.n * 100 if self.n > 0 else 0, "satisfaction_score": e_sat_score},
            "overall": {"egalitarian_cost": sum(s_ranks.values()) + sum(e_ranks.values()), "sex_equality_score": abs(s_sat_score - e_sat_score)}
        }

class ExperimentRunner:
    def __init__(self, n: int):
        self.n = n
        self.students = [f'S_{i+1}' for i in range(n)]
        self.establishments = [f'E_{i+1}' for i in range(n)]
        self.console = Console()
        self.visualizer = Visualizer()
        self.student_prefs, self.establishment_prefs = self._generate_preferences()
    def _generate_preferences(self) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        student_prefs = {s: random.sample(self.establishments, self.n) for s in self.students}
        establishment_prefs = {e: random.sample(self.students, self.n) for e in self.establishments}
        return student_prefs, establishment_prefs
    def run_single_experiment(self):
        self.console.print(Panel(f"[bold blue]Lancement d'une simulation unique avec n={self.n}[/bold blue]", title="Expérience Unique", expand=False))
        algo = StableMarriageAlgorithm(self.students, self.establishments, self.student_prefs, self.establishment_prefs)
        matching_sp = algo.solve_students_propose(); is_stable_sp, _ = algo.verify_stability(matching_sp)
        analyzer_sp = SatisfactionAnalyzer(matching_sp, self.student_prefs, self.establishment_prefs)
        analysis_sp = analyzer_sp.full_analysis()
        matching_ep = algo.solve_establishments_propose(); is_stable_ep, _ = algo.verify_stability(matching_ep)
        analyzer_ep = SatisfactionAnalyzer(matching_ep, self.student_prefs, self.establishment_prefs)
        analysis_ep = analyzer_ep.full_analysis()
        self._display_single_results(analysis_sp, is_stable_sp, "Étudiants Proposent")
        self._display_single_results(analysis_ep, is_stable_ep, "Établissements Proposent")
        self.visualizer.plot_satisfaction_comparison(analysis_sp, analysis_ep, self.n)
    def _display_single_results(self, analysis: Dict, is_stable: bool, title: str):
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("Métrique", style="dim", width=25); table.add_column("Étudiants", justify="right"); table.add_column("Établissements", justify="right")
        table.add_row("Score de Satisfaction", f"{analysis['students']['satisfaction_score']:.2f} / 100", f"{analysis['establishments']['satisfaction_score']:.2f} / 100")
        table.add_row("Rang Moyen", f"{analysis['students']['avg_rank']:.2f}", f"{analysis['establishments']['avg_rank']:.2f}")
        table.add_row("Pourcentage Top 1", f"{analysis['students']['top_1_pct']:.1f}%", f"{analysis['establishments']['top_1_pct']:.1f}%")
        table.add_row("Pourcentage Top 3", f"{analysis['students']['top_3_pct']:.1f}%", f"{analysis['establishments']['top_3_pct']:.1f}%")
        self.console.print(table)
        stable_text = "[bold green]✓ Matching STABLE[/bold green]" if is_stable else "[bold red]✗ Matching INSTABLE[/bold red]"
        self.console.print(f"Stabilité: {stable_text}")
        self.console.print(f"Coût Égalitaire: [bold yellow]{analysis['overall']['egalitarian_cost']}[/bold yellow]")
        self.console.print(f"Score d'Inégalité: [bold red]{analysis['overall']['sex_equality_score']:.2f}[/bold red]\n")

# ============================================================================
# 3. VISUALIZATION 
# ============================================================================
class Visualizer:
    """Handles the creation of plots with a focus on informational clarity."""
    def __init__(self, style: str = 'whitegrid'):
        sns.set_theme(style=style, palette='deep')

    def plot_satisfaction_comparison(self, analysis_sp: Dict, analysis_ep: Dict, n: int):
        """
        Generates a high-clarity grouped bar chart.
        This version groups by SCENARIO to make the algorithm's bias obvious.
        """
        # --- RESTRUCTURED DATA ---
        # Instead of grouping by participant, we group by scenario.
        labels = [
            'Scénario: Étudiants Proposent',
            'Scénario: Établissements Proposent'
        ]
        student_scores = [
            analysis_sp['students']['satisfaction_score'],
            analysis_ep['students']['satisfaction_score']
        ]
        establishment_scores = [
            analysis_sp['establishments']['satisfaction_score'],
            analysis_ep['establishments']['satisfaction_score']
        ]

        x = range(len(labels))
        width = 0.35

        fig, ax = plt.subplots(figsize=(14, 8)) # Wider figure
        rects1 = ax.bar([i - width/2 for i in x], student_scores, width, label='Satisfaction des Étudiants', color='#1f77b4')
        rects2 = ax.bar([i + width/2 for i in x], establishment_scores, width, label='Satisfaction des Établissements', color='#ff7f0e')

        # --- ENHANCED LABELS AND TITLE ---
        ax.set_ylabel('Score de Satisfaction (0-100)', fontsize=14, fontweight='bold')
        ax.set_title(
            f"Preuve Visuelle du Biais de l'Algorithme (n={n})",
            fontsize=18, fontweight='bold', pad=20
        )
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=12, fontweight='bold')
        ax.tick_params(axis='y', labelsize=12)
        ax.set_ylim(0, 115)
        
        ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=0.5)
        ax.set_axisbelow(True)

        ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)

        ax.bar_label(rects1, padding=5, fmt='%.1f', fontsize=12, fontweight='bold')
        ax.bar_label(rects2, padding=5, fmt='%.1f', fontsize=12, fontweight='bold')
        
        sns.despine(left=True)
        
        fig.tight_layout(rect=[0, 0.1, 1, 1])
        plt.savefig(f'satisfaction_comparison_restructured_n{n}.png', dpi=300)
        plt.show(block=True)


# ============================================================================
# 5. MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    # --- Execute a single, detailed experiment with the redesigned plot ---
    single_run = ExperimentRunner(n=100)
    single_run.run_single_experiment()