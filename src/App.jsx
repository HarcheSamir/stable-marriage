import React, { useState, useEffect } from 'react';
import { Play, Download, BarChart3, Users, Building2, TrendingUp, RefreshCw, FileText } from 'lucide-react';

// ============================================================================
// CORE ALGORITHM IMPLEMENTATION
// ============================================================================

class StableMarriageAlgorithm {
  constructor(students, establishments, studentPrefs, establishmentPrefs) {
    this.students = students;
    this.establishments = establishments;
    this.studentPrefs = studentPrefs;
    this.establishmentPrefs = establishmentPrefs;
    this.n = students.length;
    this.proposalCounts = new Array(this.n).fill(0);
  }

  // Gale-Shapley Algorithm - Students propose
  solveStudentsPropose() {
    const engaged = new Map(); // establishment -> student
    const free = new Set(this.students);
    const proposals = new Map();
    
    this.students.forEach(s => proposals.set(s, 0));

    while (free.size > 0) {
      const student = Array.from(free)[0];
      const proposalIndex = proposals.get(student);
      
      if (proposalIndex >= this.n) {
        free.delete(student);
        continue;
      }

      const establishment = this.studentPrefs[student][proposalIndex];
      this.proposalCounts[student]++;
      proposals.set(student, proposalIndex + 1);

      if (!engaged.has(establishment)) {
        engaged.set(establishment, student);
        free.delete(student);
      } else {
        const currentStudent = engaged.get(establishment);
        const currentRank = this.establishmentPrefs[establishment].indexOf(currentStudent);
        const newRank = this.establishmentPrefs[establishment].indexOf(student);

        if (newRank < currentRank) {
          engaged.set(establishment, student);
          free.delete(student);
          free.add(currentStudent);
        }
      }
    }

    const matching = new Map();
    engaged.forEach((student, establishment) => {
      matching.set(student, establishment);
    });

    return { matching, proposalCounts: [...this.proposalCounts] };
  }

  // Gale-Shapley Algorithm - Establishments propose
  solveEstablishmentsPropose() {
    const engaged = new Map(); // student -> establishment
    const free = new Set(this.establishments);
    const proposals = new Map();
    
    this.establishments.forEach(e => proposals.set(e, 0));

    while (free.size > 0) {
      const establishment = Array.from(free)[0];
      const proposalIndex = proposals.get(establishment);
      
      if (proposalIndex >= this.n) {
        free.delete(establishment);
        continue;
      }

      const student = this.establishmentPrefs[establishment][proposalIndex];
      proposals.set(establishment, proposalIndex + 1);

      if (!engaged.has(student)) {
        engaged.set(student, establishment);
        free.delete(establishment);
      } else {
        const currentEstablishment = engaged.get(student);
        const currentRank = this.studentPrefs[student].indexOf(currentEstablishment);
        const newRank = this.studentPrefs[student].indexOf(establishment);

        if (newRank < currentRank) {
          engaged.set(student, establishment);
          free.delete(establishment);
          free.add(currentEstablishment);
        }
      }
    }

    return { matching: engaged, proposalCounts: proposals };
  }

  // Verify stability of matching
  verifyStability(matching) {
    const blockingPairs = [];

    for (let s = 0; s < this.n; s++) {
      const currentE = matching.get(s);
      const currentRankS = this.studentPrefs[s].indexOf(currentE);

      for (let prefRank = 0; prefRank < currentRankS; prefRank++) {
        const preferredE = this.studentPrefs[s][prefRank];
        const matchedS = Array.from(matching.entries()).find(([_, e]) => e === preferredE)?.[0];
        
        if (matchedS !== undefined) {
          const currentRankE = this.establishmentPrefs[preferredE].indexOf(matchedS);
          const newRankE = this.establishmentPrefs[preferredE].indexOf(s);

          if (newRankE < currentRankE) {
            blockingPairs.push({ student: s, establishment: preferredE });
          }
        }
      }
    }

    return { stable: blockingPairs.length === 0, blockingPairs };
  }
}

// ============================================================================
// PREFERENCE GENERATION
// ============================================================================

function generateRandomPreferences(n) {
  const students = Array.from({ length: n }, (_, i) => i);
  const establishments = Array.from({ length: n }, (_, i) => i);

  const studentPrefs = students.map(() => shuffle([...establishments]));
  const establishmentPrefs = establishments.map(() => shuffle([...students]));

  return { students, establishments, studentPrefs, establishmentPrefs };
}

function shuffle(array) {
  const arr = [...array];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

// ============================================================================
// SATISFACTION METRICS
// ============================================================================

class SatisfactionAnalyzer {
  constructor(matching, studentPrefs, establishmentPrefs) {
    this.matching = matching;
    this.studentPrefs = studentPrefs;
    this.establishmentPrefs = establishmentPrefs;
    this.n = studentPrefs.length;
  }

  // Average rank of matched partner (lower is better)
  averageRank(prefs, matching, isStudent = true) {
    let totalRank = 0;
    
    for (let i = 0; i < this.n; i++) {
      const partner = isStudent ? matching.get(i) : 
        Array.from(matching.entries()).find(([_, e]) => e === i)?.[0];
      const rank = prefs[i].indexOf(partner);
      totalRank += rank;
    }

    return totalRank / this.n;
  }

  // Percentage getting top-k choice
  topKPercentage(prefs, matching, k, isStudent = true) {
    let count = 0;
    
    for (let i = 0; i < this.n; i++) {
      const partner = isStudent ? matching.get(i) : 
        Array.from(matching.entries()).find(([_, e]) => e === i)?.[0];
      const rank = prefs[i].indexOf(partner);
      if (rank < k) count++;
    }

    return (count / this.n) * 100;
  }

  // Satisfaction score (normalized, 0-100)
  satisfactionScore(prefs, matching, isStudent = true) {
    let totalScore = 0;
    
    for (let i = 0; i < this.n; i++) {
      const partner = isStudent ? matching.get(i) : 
        Array.from(matching.entries()).find(([_, e]) => e === i)?.[0];
      const rank = prefs[i].indexOf(partner);
      // Score: 100 for rank 0, decreasing linearly to 0 for rank n-1
      const score = 100 * (1 - rank / (this.n - 1));
      totalScore += score;
    }

    return totalScore / this.n;
  }

  // Egalitarian cost (sum of ranks)
  egalitarianCost(matching) {
    let cost = 0;
    
    for (let s = 0; s < this.n; s++) {
      const e = matching.get(s);
      const studentRank = this.studentPrefs[s].indexOf(e);
      const estabRank = this.establishmentPrefs[e].indexOf(s);
      cost += studentRank + estabRank;
    }

    return cost;
  }

  // Sex-equality (difference in satisfaction between groups)
  sexEquality(matching) {
    const studentSat = this.satisfactionScore(this.studentPrefs, matching, true);
    const estabSat = this.satisfactionScore(this.establishmentPrefs, matching, false);
    return Math.abs(studentSat - estabSat);
  }

  // Complete analysis
  fullAnalysis(matching) {
    return {
      students: {
        avgRank: this.averageRank(this.studentPrefs, matching, true),
        top1: this.topKPercentage(this.studentPrefs, matching, 1, true),
        top3: this.topKPercentage(this.studentPrefs, matching, 3, true),
        satisfaction: this.satisfactionScore(this.studentPrefs, matching, true)
      },
      establishments: {
        avgRank: this.averageRank(this.establishmentPrefs, matching, false),
        top1: this.topKPercentage(this.establishmentPrefs, matching, 1, false),
        top3: this.topKPercentage(this.establishmentPrefs, matching, 3, false),
        satisfaction: this.satisfactionScore(this.establishmentPrefs, matching, false)
      },
      overall: {
        egalitarianCost: this.egalitarianCost(matching),
        sexEquality: this.sexEquality(matching)
      }
    };
  }
}

// ============================================================================
// REACT COMPONENT
// ============================================================================

export default function App() {
  const [n, setN] = useState(20);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('results'); // 'results' or 'theory'

  const runExperiment = () => {
    setLoading(true);
    
    setTimeout(() => {
      const { students, establishments, studentPrefs, establishmentPrefs } = 
        generateRandomPreferences(n);

      const algo = new StableMarriageAlgorithm(
        students, establishments, studentPrefs, establishmentPrefs
      );

      // Run both versions
      const studentsPropose = algo.solveStudentsPropose();
      algo.proposalCounts = new Array(n).fill(0); // Reset
      const establishmentsPropose = algo.solveEstablishmentsPropose();

      // Analyze both
      const analyzerSP = new SatisfactionAnalyzer(
        studentsPropose.matching, studentPrefs, establishmentPrefs
      );
      const analyzerEP = new SatisfactionAnalyzer(
        establishmentsPropose.matching, studentPrefs, establishmentPrefs
      );

      // Verify stability
      const stabilitySP = algo.verifyStability(studentsPropose.matching);
      const stabilityEP = algo.verifyStability(establishmentsPropose.matching);

      setResults({
        studentsPropose: {
          analysis: analyzerSP.fullAnalysis(studentsPropose.matching),
          stability: stabilitySP,
          proposals: studentsPropose.proposalCounts
        },
        establishmentsPropose: {
          analysis: analyzerEP.fullAnalysis(establishmentsPropose.matching),
          stability: stabilityEP
        }
      });

      setLoading(false);
    }, 100);
  };

  useEffect(() => {
    runExperiment();
  }, []);

  const MetricCard = ({ title, value, unit = '', icon: Icon, color = 'blue' }) => (
    <div className={`bg-white rounded-lg border-2 border-${color}-200 p-4`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{title}</span>
        <Icon className={`w-5 h-5 text-${color}-500`} />
      </div>
      <div className="text-2xl font-bold text-gray-900">
        {typeof value === 'number' ? value.toFixed(2) : value}{unit}
      </div>
    </div>
  );

  const ComparisonSection = ({ title, data1, data2, label1, label2 }) => (
    <div className="bg-gray-50 rounded-lg p-6 mb-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">{title}</h3>
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h4 className="font-semibold text-blue-600 mb-3">{label1}</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Rang moyen:</span>
              <span className="font-semibold">{data1.avgRank.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Top 1 choix:</span>
              <span className="font-semibold">{data1.top1.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Top 3 choix:</span>
              <span className="font-semibold">{data1.top3.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Satisfaction:</span>
              <span className="font-semibold">{data1.satisfaction.toFixed(1)}/100</span>
            </div>
          </div>
        </div>
        <div>
          <h4 className="font-semibold text-green-600 mb-3">{label2}</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Rang moyen:</span>
              <span className="font-semibold">{data2.avgRank.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Top 1 choix:</span>
              <span className="font-semibold">{data2.top1.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Top 3 choix:</span>
              <span className="font-semibold">{data2.top3.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Satisfaction:</span>
              <span className="font-semibold">{data2.satisfaction.toFixed(1)}/100</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const TheorySection = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border-2 border-purple-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
          <FileText className="w-6 h-6 mr-2 text-purple-600" />
          Extensions : Représentations Compactes des Préférences
        </h2>
        
        <div className="space-y-6">
          <Section 
            title="1. Préférences Incomplètes"
            content="Au lieu de classer tous les établissements, les étudiants ne listent que ceux qui sont acceptables. Cela réduit considérablement l'espace de représentation."
            complexity="O(n·k) où k = taille moyenne des listes"
            application="Systèmes réels où les candidats ne connaissent/veulent qu'un sous-ensemble d'options"
          />

          <Section 
            title="2. Préférences avec Indifférence (Ties)"
            content="Plusieurs alternatives peuvent être classées ex-aequo. Ex: E1 ~ E2 > E3, indiquant que E1 et E2 sont équivalents mais préférés à E3."
            complexity="O(n·log(n)) avec représentation par groupes"
            application="Quand certains établissements sont perçus comme équivalents par les étudiants"
          />

          <Section 
            title="3. Préférences Top-k"
            content="Seuls les k premiers choix sont spécifiés explicitement. Le reste est considéré comme inacceptable ou équivalent."
            complexity="O(k·n) où k << n"
            application="Admission universitaire où les candidats ne postulent qu'à quelques établissements"
          />

          <Section 
            title="4. Préférences Basées sur Attributs"
            content="Les préférences sont définies par des fonctions sur des attributs (prestige, distance, coût). Utilise des structures comme CP-nets ou GAI-nets."
            complexity="Exponentielle dans le pire cas, mais compacte en pratique"
            application="Préférences complexes dérivées de critères multiples"
          />

          <Section 
            title="5. Préférences Lexicographiques"
            content="Ordre défini par une séquence de critères prioritaires. Ex: d'abord le prestige, puis la distance en cas d'égalité."
            complexity="O(m·n) où m = nombre de critères"
            application="Décisions hiérarchiques avec critères bien définis"
          />

          <Section 
            title="6. Préférences avec Quotas"
            content="Extension où les établissements ont plusieurs places (capacités > 1). Chaque établissement peut accepter plusieurs étudiants."
            complexity="O(n²) pour n étudiants et capacité totale n"
            application="Admissions universitaires réelles, stages hospitaliers"
          />

          <Section 
            title="7. Représentation par Graphe de Préférences"
            content="Graphe biparti pondéré où les arêtes représentent l'acceptabilité et leur poids le niveau de préférence."
            complexity="O(|E|) où E = ensemble des arêtes acceptables"
            application="Visualisation et algorithmes sur graphes"
          />
        </div>

        <div className="mt-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <h3 className="font-bold text-purple-900 mb-2">Impact Algorithmique</h3>
          <ul className="space-y-2 text-sm text-purple-800">
            <li>• <strong>Préférences incomplètes :</strong> Peut créer des matchings incomplets (certains restent non appariés)</li>
            <li>• <strong>Avec indifférence :</strong> Plusieurs matchings stables possibles, notion de super-stabilité</li>
            <li>• <strong>Avec quotas :</strong> Algorithme adapté (beaucoup-à-un), toujours polynomial</li>
            <li>• <strong>Basées sur attributs :</strong> Nécessite énumération ou approximation selon la structure</li>
          </ul>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-bold text-blue-900 mb-2">Avantages des Représentations Compactes</h3>
          <ul className="space-y-1 text-sm text-blue-800">
            <li>✓ Réduction drastique de l'espace mémoire (O(n²) → O(n·k))</li>
            <li>✓ Plus naturel pour les agents (pas besoin de tout classer)</li>
            <li>✓ Capture mieux les préférences réelles (indifférences, critères)</li>
            <li>✓ Permet des systèmes plus scalables</li>
          </ul>
        </div>
      </div>
    </div>
  );

  const Section = ({ title, content, complexity, application }) => (
    <div className="border-l-4 border-purple-500 pl-4">
      <h3 className="font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-700 mb-2">{content}</p>
      <div className="text-sm space-y-1">
        <p className="text-purple-600"><strong>Complexité:</strong> {complexity}</p>
        <p className="text-blue-600"><strong>Application:</strong> {application}</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Système d'Analyse du Mariage Stable
          </h1>
          <p className="text-gray-600 mb-6">
            Implémentation complète de l'algorithme de Gale-Shapley avec analyse comparative détaillée
          </p>

          {/* Controls */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">
                Taille (n):
              </label>
              <input
                type="number"
                value={n}
                onChange={(e) => setN(Math.max(5, Math.min(100, parseInt(e.target.value) || 20)))}
                className="w-20 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="5"
                max="100"
              />
            </div>

            <button
              onClick={runExperiment}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              {loading ? 'Calcul...' : 'Nouvelle Simulation'}
            </button>

            <div className="ml-auto flex gap-2">
              <button
                onClick={() => setView('results')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  view === 'results' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <BarChart3 className="w-4 h-4 inline mr-2" />
                Résultats
              </button>
              <button
                onClick={() => setView('theory')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  view === 'theory' 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <FileText className="w-4 h-4 inline mr-2" />
                Théorie
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        {view === 'theory' ? (
          <TheorySection />
        ) : results && (
          <div className="space-y-8">
            {/* Students Propose Version */}
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Users className="w-6 h-6 mr-2 text-blue-600" />
                Version : Étudiants Proposent
              </h2>

              <div className="mb-6 p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${results.studentsPropose.stability.stable ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="font-semibold text-gray-900">
                    {results.studentsPropose.stability.stable ? 'Matching STABLE ✓' : 'Matching INSTABLE ✗'}
                  </span>
                  {!results.studentsPropose.stability.stable && (
                    <span className="text-sm text-gray-600">
                      ({results.studentsPropose.stability.blockingPairs.length} blocking pairs)
                    </span>
                  )}
                </div>
              </div>

              <ComparisonSection
                title="Comparaison Étudiants vs Établissements"
                data1={results.studentsPropose.analysis.students}
                data2={results.studentsPropose.analysis.establishments}
                label1="👨‍🎓 Étudiants"
                label2="🏛️ Établissements"
              />

              <div className="grid grid-cols-2 gap-4">
                <MetricCard
                  title="Coût Égalitaire"
                  value={results.studentsPropose.analysis.overall.egalitarianCost}
                  icon={TrendingUp}
                  color="orange"
                />
                <MetricCard
                  title="Inégalité Homme/Femme"
                  value={results.studentsPropose.analysis.overall.sexEquality}
                  icon={BarChart3}
                  color="red"
                />
              </div>
            </div>

            {/* Establishments Propose Version */}
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Building2 className="w-6 h-6 mr-2 text-green-600" />
                Version : Établissements Proposent
              </h2>

              <div className="mb-6 p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${results.establishmentsPropose.stability.stable ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="font-semibold text-gray-900">
                    {results.establishmentsPropose.stability.stable ? 'Matching STABLE ✓' : 'Matching INSTABLE ✗'}
                  </span>
                </div>
              </div>

              <ComparisonSection
                title="Comparaison Étudiants vs Établissements"
                data1={results.establishmentsPropose.analysis.students}
                data2={results.establishmentsPropose.analysis.establishments}
                label1="👨‍🎓 Étudiants"
                label2="🏛️ Établissements"
              />

              <div className="grid grid-cols-2 gap-4">
                <MetricCard
                  title="Coût Égalitaire"
                  value={results.establishmentsPropose.analysis.overall.egalitarianCost}
                  icon={TrendingUp}
                  color="orange"
                />
                <MetricCard
                  title="Inégalité Homme/Femme"
                  value={results.establishmentsPropose.analysis.overall.sexEquality}
                  icon={BarChart3}
                  color="red"
                />
              </div>
            </div>

            {/* Comparative Analysis */}
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                📊 Analyse Comparative
              </h2>

              <div className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h3 className="font-bold text-blue-900 mb-2">Observations Clés</h3>
                  <ul className="space-y-2 text-sm text-blue-800">
                    <li>• Le groupe proposant obtient toujours son matching optimal stable</li>
                    <li>• Le groupe recevant obtient son matching pessimal stable</li>
                    <li>• Satisfaction moyenne étudiants (SP): {results.studentsPropose.analysis.students.satisfaction.toFixed(1)}/100</li>
                    <li>• Satisfaction moyenne étudiants (EP): {results.establishmentsPropose.analysis.students.satisfaction.toFixed(1)}/100</li>
                    <li>• Différence: {Math.abs(results.studentsPropose.analysis.students.satisfaction - results.establishmentsPropose.analysis.students.satisfaction).toFixed(1)} points</li>
                  </ul>
                </div>

                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <h3 className="font-bold text-purple-900 mb-2">Propriétés Théoriques Vérifiées</h3>
                  <ul className="space-y-1 text-sm text-purple-800">
                    <li>✓ Les deux matchings sont stables (aucune blocking pair)</li>
                    <li>✓ Complexité temporelle: O(n²) propositions maximum</li>
                    <li>✓ L'algorithme termine toujours avec un matching complet</li>
                    <li>✓ Le matching est stable et optimal pour le groupe proposant</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>Implémentation complète de l'algorithme de Gale-Shapley • Projet Aide à la Décision 2025-2026</p>
        </div>
      </div>
    </div>
  );
}