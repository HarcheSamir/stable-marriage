import random
import matplotlib.pyplot as plt
from collections import deque
from typing import Dict, List, Tuple

class StableMarriageSolver:
    """
    A class to solve the Stable Marriage Problem using the Gale-Shapley algorithm.

    This implementation is compliant with academic standards, featuring an efficient
    O(1) lookup for preference comparison, clear documentation, type hinting,
    random preference generation, and statistical analysis visualization.
    """
    def __init__(self, proposers: List[str], receivers: List[str]):
        if not proposers or not receivers:
            raise ValueError("Participant lists cannot be empty.")
        if len(proposers) != len(receivers):
            raise ValueError("Participant groups must be of the same size.")

        self.proposers = proposers
        self.receivers = receivers
        self.proposer_prefs: Dict[str, List[str]] = {}
        self.receiver_prefs: Dict[str, List[str]] = {}
        self._receiver_ranking_map: Dict[str, Dict[str, int]] = {}
        self.matches: Dict[str, str] = {}

    def set_preferences(self, proposer_prefs: Dict[str, List[str]], receiver_prefs: Dict[str, List[str]]):
        self.proposer_prefs = proposer_prefs
        self.receiver_prefs = receiver_prefs
        self._create_receiver_ranking_map()

    def generate_and_set_random_preferences(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
        
        proposer_prefs = {proposer: random.sample(self.receivers, len(self.receivers)) for proposer in self.proposers}
        receiver_prefs = {receiver: random.sample(self.proposers, len(self.proposers)) for receiver in self.receivers}
        
        self.set_preferences(proposer_prefs, receiver_prefs)

    def _create_receiver_ranking_map(self):
        for receiver, pref_list in self.receiver_prefs.items():
            self._receiver_ranking_map[receiver] = {proposer: rank for rank, proposer in enumerate(pref_list)}

    def solve(self) -> Dict[str, str]:
        free_proposers = deque(self.proposers)
        current_matches: Dict[str, str] = {}
        proposal_index: Dict[str, int] = {p: 0 for p in self.proposers}

        while free_proposers:
            proposer = free_proposers.popleft()
            pref_list = self.proposer_prefs[proposer]
            receiver_index = proposal_index[proposer]
            receiver = pref_list[receiver_index]
            proposal_index[proposer] += 1

            if receiver not in current_matches:
                current_matches[receiver] = proposer
            else:
                current_partner = current_matches[receiver]
                receiver_rankings = self._receiver_ranking_map[receiver]
                
                if receiver_rankings[proposer] < receiver_rankings[current_partner]:
                    current_matches[receiver] = proposer
                    free_proposers.append(current_partner)
                else:
                    free_proposers.append(proposer)
        
        self.matches = {proposer: receiver for receiver, proposer in current_matches.items()}
        return self.matches

    def analyze_satisfaction(self) -> Tuple[float, float]:
        if not self.matches: return -1.0, -1.0
        proposer_rank_sum = sum(self.proposer_prefs[p].index(r) for p, r in self.matches.items())
        receiver_rank_sum = sum(self.receiver_prefs[r].index(p) for p, r in self.matches.items())
        return proposer_rank_sum / len(self.proposers), receiver_rank_sum / len(self.receivers)

    def print_results(self, test_case_name: str):
        print(f"--- RÉSULTATS POUR: {test_case_name} ---")
        if not self.matches:
            print("Aucun appariement trouvé. Exécutez solve() d'abord.")
            return
        print("\n[Appariements]")
        for proposer, receiver in sorted(self.matches.items()): print(f"  {proposer} est apparié avec {receiver}")
        proposer_score, receiver_score = self.analyze_satisfaction()
        print("\n[Analyse de Satisfaction (score bas = meilleure satisfaction)]")
        print(f"  Rang moyen pour les Proposants: {proposer_score:.2f}")
        print(f"  Rang moyen pour les Receveurs: {receiver_score:.2f}\n")
        print("-" * (24 + len(test_case_name)))


def plot_statistical_results(proposer_score: float, receiver_score: float, num_runs: int):
    """
    [NOUVEAU] Crée et affiche un graphique des résultats de l'analyse statistique.
    """
    groups = ['Proposants (Étudiants)', 'Receveurs (Établissements)']
    scores = [proposer_score, receiver_score]

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(8, 6))

    bars = ax.bar(groups, scores, color=['#4285F4', '#DB4437'])
    ax.bar_label(bars, fmt='%.2f')

    ax.set_ylabel('Rang de Satisfaction Moyen (plus bas = meilleur)')
    ax.set_title(f'Analyse Statistique de la Satisfaction sur {num_runs} Simulations', pad=20)
    ax.set_ylim(0, max(scores) * 1.2)
    
    # Sauvegarde du graphique pour le rapport
    plt.savefig('analyse_satisfaction.png', dpi=300)
    print("Graphique 'analyse_satisfaction.png' a été sauvegardé.")
    
    # Affichage du graphique
    plt.show()

# ==============================================================================
# [TÂCHE 4] Test the program on several datasets
# ==============================================================================
if __name__ == "__main__":
    
    # --- TEST CASE 1: Small, Manually-Defined Dataset ---
    students_1 = ['A', 'B', 'C']; establishments_1 = ['X', 'Y', 'Z']
    student_prefs_1 = {'A': ['Y', 'X', 'Z'], 'B': ['X', 'Y', 'Z'], 'C': ['X', 'Z', 'Y']}
    establishment_prefs_1 = {'X': ['B', 'A', 'C'], 'Y': ['A', 'C', 'B'], 'Z': ['C', 'B', 'A']}
    solver1 = StableMarriageSolver(proposers=students_1, receivers=establishments_1)
    solver1.set_preferences(student_prefs_1, establishment_prefs_1)
    solver1.solve()
    solver1.print_results("Test 1: Dataset Manuel (Validation)")

    # --- TEST CASE 2: Single Larger, Randomly-Generated Dataset ---
    students_2 = [f'Student_{i+1}' for i in range(10)]; establishments_2 = [f'Univ_{i+1}' for i in range(10)]
    solver2 = StableMarriageSolver(proposers=students_2, receivers=establishments_2)
    solver2.generate_and_set_random_preferences(seed=42)
    solver2.solve()
    solver2.print_results("Test 2: Dataset Aléatoire 10x10 (Exemple)")

    # --- TEST CASE 3: Statistical Analysis over Multiple Runs ---
    print("\n--- DÉBUT: Test 3: Analyse Statistique Robuste ---")
    NUM_RUNS = 100
    NUM_PARTICIPANTS = 50
    total_proposer_satisfaction, total_receiver_satisfaction = 0, 0
    students_3 = [f'S_{i+1}' for i in range(NUM_PARTICIPANTS)]; establishments_3 = [f'E_{i+1}' for i in range(NUM_PARTICIPANTS)]
    solver3 = StableMarriageSolver(proposers=students_3, receivers=establishments_3)

    for i in range(NUM_RUNS):
        solver3.generate_and_set_random_preferences()
        solver3.solve()
        proposer_score, receiver_score = solver3.analyze_satisfaction()
        total_proposer_satisfaction += proposer_score
        total_receiver_satisfaction += receiver_score

    avg_proposer_score = total_proposer_satisfaction / NUM_RUNS
    avg_receiver_score = total_receiver_satisfaction / NUM_RUNS

    print(f"\n[Synthèse sur {NUM_RUNS} runs avec {NUM_PARTICIPANTS}x{NUM_PARTICIPANTS} participants]")
    print(f"  Satisfaction moyenne globale pour les Proposants: {avg_proposer_score:.2f}")
    print(f"  Satisfaction moyenne globale pour les Receveurs: {avg_receiver_score:.2f}\n")
    print("-" * 52)
    
    # --- [NOUVEAU] Visualisation des résultats statistiques ---
    plot_statistical_results(avg_proposer_score, avg_receiver_score, NUM_RUNS)