# RAPPORT FINAL V2 — decision-coprocessor-v2

*Clôture du projet V2 (mandat utilisateur « finir le tout », @ag-ask 06:30 /
06:32). Question fondatrice (DECISION-V2 §1) : **démontrer — ou réfuter —
qu'une transition est apprise, composée, et causalement utile, avant de
reconnecter le langage.** Réponse ci-dessous.*

> **Portée des conclusions (audit externe V2-validation, 2026-09-25,
> sha256 f11704d8…).** Ce rapport distingue désormais trois niveaux :
> **ARRÊT D'EXPÉRIENCE** (on cesse d'investir cette configuration — toujours
> légitime sur résultat nettement défavorable) ; **CONCLUSION SCIENTIFIQUE
> LOCALE** (valable pour le domaine et le protocole mesurés) ; **VALIDATION
> PRODUIT** (jamais revendiquée ici). Le verdict T ci-dessous est un arrêt
> d'expérience sur résultat exploratoire nettement défavorable — la
> contre-performance sur un test indépendant n'a PAS été mesurée (le dev a
> servi aux choix de checkpoints → biais de sélection possible). Suite :
> programme V2.1 (`V21_PROTOCOL.md`).

## 1. Réponse à la question fondatrice

**OUI pour le mécanisme structuré (étage S), NON pour l'utilité de la
décomposition sur texte (étage T)** — et cette seconde moitié est une
réponse PROPRE, préenregistrée, causalement établie :

1. **Transition apprise, composée, causale en structuré : ÉTABLI (E1–E4,
   1.000 partout).** L'exécuteur apprend la transition, compose jusqu'à la
   profondeur 10+ jamais vue, suit causalement les interventions (sweep k :
   0.188@k0 → 1.0@k4), résiste au stress pad20 (E4b 399/399).
2. **Texte→graphe : meilleur lecteur dans CE budget (E5v3-A), courbe encore
   montante au dernier eval (edge 0.331→0.928 jusqu'à 1200 steps,
   best=last — plafond NON démontré).** Le lecteur LoRA atteint edge F1
   0.928, validité 0.917, solve 0.762 — 4/4 seuils, première fois. Le
   goulot historique (rappel d'arêtes) est levé PAR l'adaptation du
   backbone, exactement comme préenregistré — pour cette recette et ce
   budget.
3. **Mais la décomposition n'est PAS utile : résultat exploratoire nettement
défavorable (grille v1.6, issue (iii) deux fois).** En représentations
adaptées ÉQUITABLES (F1), le direct texte→réponse atteint **1.000 dev** et
suit les interventions textuelles testées (décisive 0.996, distracteur
0.996, permutation 0.988 — **robustesse fonctionnelle forte**, sans
identification de l'algorithme interne ni exclusion de tout raccourci) —
Δ(c−d) = **−23.8 pts IC[−28.3, −19.6]** (IC conditionnels aux runs
mesurés). Le bénéfice apparent de la décomposition en régime gelé
(+5.1 pts, non concluant) était vraisemblablement un artefact du bridage
du backbone : l'extraction devient le goulot DU pipeline dès que le direct
peut apprendre.

**Formulation autorisée :** sur ce protocole (banc E5v2 français synthétique,
famille B simplifiée, n=411 dev utilisé pour la sélection, Qwen3-0.6B
backbone, 1 seed/voie), la voie décomposée texte→graphe→exécuteur est
nettement inférieure au direct adapté sur le dev à chaînes courtes :
**arrêt d'expérience** ; la GÉNÉRALISATION DES DEUX VOIES (profondeur
6/8/10, surfaces nouvelles, OOD) **reste à comparer** — programme V2.1.

## 2. Trajectoire expérimentale (registre complet, 8+9 commits)

| Étape | Résultat | Verdict |
|---|---|---|
| E0–E2 | contrat données B + exécuteur vS anti-raccourci + registre | PASS |
| E1 | transition autonome 1.000 | PASS |
| E2 | 919/919 zero-shot, profondeur jamais vue | PASS |
| E3 | trajectoire 1.000, sweep k causal 0.188→1.0, exec 1.0 vs direct 0.204 | PASS |
| E4/E4b | 6/8/10 zero-shot + stress pad20 399/399 | PASS |
| E5 v1 | banc défaillant (raccourci de surface, branche B QA v1.3) | ARCHIVÉ |
| E5v2 it1–it3 (gelé) | ent/edge/start ✓, solve MISS 3× (0.166→0.204→0.248) ; it3 : Δ +5.1 non concluant, P+ échoue | (iii) |
| E5v3-A (LoRA, GO user) | lecteur 4/4 ✓✓ ; direct 1.000 ; Δ −23.8 ; causal direct 0.996 | **(iii) DÉFINITIF** |

E5v2_eval : **scellé, jamais ouvert** — aucune conclusion n'en dépend.

## 3. Leçons méthodo (la moitié de la valeur du projet)

1. **Équité de représentation AVANT de comparer** (v1.7 F1) : le verdict
   s'INVERSE sous équité (gelé : +5.1 pipeline ; adapté : −23.8). Toute
   comparaison pipeline/direct doit offrir chaque avantage aux deux voies.
2. **Précédence mécanisme > bénéfice** (v1.8) : un Δ sans profil causal ne
   peut pas valider une décomposition ; un profil causal fort sans Δ ne la
   justifie pas non plus.
3. **Zone grise ≠ succès ni échec** : publier tel quel (it3 : Δ≥5, IC≤0).
4. **Banc avant modèle** : E5 v1 mesurait un banc défaillant (raccourci
   distributionnel du direct 0.78 → 0.33 sur banc sain). Le probe lexical
   near-chance ne suffit PAS à valider un banc — les interventions causales
   le font.
5. **Préenregistrement** : seuils/couches/abstention en config hashée avant
   start (v1.7bis a rattrapé un choix de couches fait sur dev).
6. **Ids dupliqués → appariement positionnel** (leçon it1, reconduite it3 ;
   par construction en E5v3-A).
7. **Incidents reproductibles** : OOM par mode train() après forward (GC
   inactif + dropout silencieusement absent) ; fenêtres d'eval
   chevauchantes (pas≠tranche). Les deux détectés par des INVARIANTS
   (n=814≠411, VRAM 7.6 vs 2.1 Gio) — toujours assert-er les dénominateurs.

## 4. Coûts cumulés

- **4.96 h** de compute enregistrées (29 lignes costs.jsonl) — dont étage S
  ~1 h, E5/E5v2 (gelé, cache) ~2 h, E5v3-A (LoRA, ré-encodage en boucle)
  ~2.5 h (lecteur 74 min + direct 74 min + évals ~25 min).
- VRAM max ~2.1 Gio (LoRA + gradient checkpointing). Backbones gelés via
  caches de hidden states (F2 : caches invalidés sous adaptation, par
  conception).

## 5. Limites

1. n=411 dev, **1 seed** par voie (les 3 seeds n'étaient exigées que pour
   l'eval confirmatoire — jamais ouvert) ; les IC sont **conditionnels aux
   checkpoints mesurés** (bootstrap sur exemples/groupes) — la variabilité
   inter-entraînements n'est PAS mesurée ; l'écart Δ est grand mais ce
   n'est pas une mesure de la variabilité non observée.
2. Banc français synthétique, famille B simplifiée (chaînes 1–4 arêtes,
   terminaux absorbants) ; **généralisation non testée** : profondeur 6/8/10
   textuelle, nouvelles surfaces linguistiques, OOD — le 1.000 du direct ne
   prédit pas son score aux profondeurs longues (et S@10 ne prouve pas
   texte→S@10). C'est l'objet de V2.1 (Q2).
3. B4-4 det structurellement absent du pool (nœuds intermédiaires jamais
   candidats) — exigence propagée pour tout pool futur (QA v1.8 Q3).
4. La cellule (e) hybride (validateur+solveur+abstention) n'a pas été
   re-mesurée sous LoRA : piste (abstention sélective, risque contrôlé) —
   hors périmètre de conclusion (T).
5. L'exécuteur S reste à 20 nœuds (pad20) ; les graphes E5v2 (≤16) ne
   l'ont jamais contraint. E4b : index ≤20 EXPOSÉS par réentraînement
   (réindexation aléatoire) — pas une démonstration d'index jamais vus
   (nuance audit §2.1) ; profondeur testée séparément.
6. Le dev a servi à la sélection de checkpoints et à plusieurs itérations :
   campagne **adaptative** — résultat exploratoire, pas confirmatoire
   (biais de sélection sur validation, S01).

## 6. Pivot et suite (Branche 2 → V2.1)

- **Voie directe adaptée** = **meilleure référence, candidat prioritaire à
  validation indépendante** — PAS un produit validé (1 seul run, dev
  adaptatif, robustesse fonctionnelle sur les interventions testées).
- **Hybride symbolique (e)** : documenté comme piste — un validateur sur
  sortie direct (abstention sélective) pourrait offrir un compromis
  couverture/risque sans décomposition complète.
- **V3 éventuelle** : (i) banc avec det évaluable + distribution plus dure
  (profondeur 6+, graphes partiellement observés) ; (ii) test de
  généralisation OOD où l'explicitation POURRAIT reprendre un avantage
  (transfert de structure, transformations nouvelles à information équitable
  pour les deux voies) ; (iii)
  3 seeds dès le dev si conclusion positive est visée.

## 7. Artefacts et reproductibilité

- Registre append-only : `registry/experiment_registry.jsonl` (90+ lignes),
  coûts `registry/costs.jsonl` ; registre de recherche
  `research_register.md`.
- Portes figées : `E0_E2_GATE_CRITERIA.md`, `E5_GATE_CRITERIA.md` (v1.0 →
  v1.8, toutes datées/signées QA).
- Bundle final : `artifacts/bundle_final_v2/` (exécuteur S, lecteur LoRA,
  direct LoRA, configs hashées, manifeste sha256, vérification reload).
- Tout run rejouable : scripts committés avant usage (règle absolue depuis
  v1.8), caches reproductibles (SER_ID + révisions épinglées).

— @ag-1, clôture V2. QA : @ag-4 (v1.8 + validation finale E5v3-A).
Coordination : @ag-ask. Infra/registre : @ag-5. Recettes : @ag-3. Données : @ag-2.

## 8. Validation QA finale (10:34, addendum v1.9)

@ag-4 a **VALIDÉ la clôture** par recalcul indépendant
(`reports/e5v3a_qa_review.md`) : edge 0.92784 exact (définition FIN
reproduite), Δ(c−d) = −23.844 pts point IDENTIQUE au harnais (IC ±0,2 pt
= graine bootstrap), interventions reproduites (0.780/0.588/0.932 · cn
0.840/0.632/1.000 · d 0.996/0.996/0.988, `opt_map` + positionnel k-à-k
vérifiés), configs préenregistrées inchangées, équité F1 exacte, E5v2_eval
scellé vérifié (0 artefact), bundle 14/14 hashs conformes. **Issue (iii)
définitive + clôture (T) confirmées** ; registre `qa_validated` ×3.

Réserves QA maintenues (publiées telles quelles, n'invalident pas) :
1. négatif mesuré sur **dev seul**, n=411, 1 seed — aucune valeur
   confirmatoire de test n'existe (non requise pour (iii)) ;
2. le direct 1.000 est un seul run — sa supériorité repose surtout sur le
   **profil causal 0.996/0.996/0.988** ;
3. B4-4 det non évaluable sur ces pools (exigence reconduite pour tout
   pool futur).
