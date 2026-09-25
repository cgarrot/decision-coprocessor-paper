# PROTOCOLE V2.1 — validation ciblée (préenregistré AVANT toute génération/run)

*Décision @ag-1 le 25/09 ~11:40, mandate par l'audit externe V2-validation
(sha256 f11704d8…) relayé par @ag-ask. **Aucun réentraînement, aucun
changement de checkpoint** : V2.1 évalue les checkpoints V2 EXISTANTS
(bundle_final_v2) sur de nouveaux bancs, puis attribue les erreurs, puis
mesure les coûts. Pas de V3/nouvelle architecture avant le diagnostic.*

## 0. Interdits (audit §3.5, §5, §9 — repris mot pour mot comme contraintes)

1. **E5v2_eval (seed 1107) reste scellé à jamais** — les nouveaux bancs sont
   des pools NEUFS avec seeds/groupes distincts.
2. **Aucun test choisi à partir des erreurs du direct** : les transformations
   sont préenregistrées ci-dessous, difficultés définies indépendamment de
   toute observation d'erreur ; information publique ÉQUITABLE aux deux
   voies.
3. Diagnostics oraculaires (graphe exact fourni, corrigeur de chemin) =
   **outils de localisation, jamais comptés dans un benchmark** ; publiés
   dans des tables séparées étiquetées « diagnostic ».
4. Un seul job GPU à la fois (verrou) ; scripts committés avant usage
   (règle v1.8 n°4) ; seuils/critères figés avant toute prédiction.

## 1. Checkpoints figés (aucune modification)

| artefact | source (sha256 au manifeste bundle) |
|---|---|
| exécuteur S pad20 | artifacts/bundle_final_v2/executor_s_e4b_pad20.pt |
| lecteur LoRA E5v3-A best@1200 | artifacts/bundle_final_v2/reader_lora_best.pt |
| direct LoRA E5v3-A best@1000 | artifacts/bundle_final_v2/direct_lora_best.pt |

## 2. Bancs neufs (génération @ag-2, capability build_E5v2_pool étendue)

Seeds V2.1 : **2205–2212** (jamais utilisés ; manifeste dédié
`manifest_v21data.json` avec anti-doublons de signatures strictes contre
E5v2_train+dev ET interne). `example_uid` unique, `base_group_id` pour les
variantes, hash du contenu public par exemple. n=400 items par cellule
(±5 %), K∈{4,5,6}, budget ≤20 nœuds (pad20), langage français, famille B.

| banc | contenu | contrôle |
|---|---|---|
| **B1-court** | profondeur 1–4, NOUVEAUX groupes/seeds/noms | tailles/formats connus ; comparable à dev |
| **B2-prof6 / B3-prof8 / B4-prof10** | chaînes 6/8/10 arêtes | longueur tokenisée couverte par construction (≤512) ; nb nœuds/longueur contrôlés entre cellules |
| **B5-surface** | paraphrases + noms nouveaux, logique identique à B1 | mêmes graphes-signatures que B1 (appariés) |
| **B6-distract** | faits inutiles supplémentaires (+50 % lignes), chemin/réponse identiques | apparié à B1 |
| **B7-options** | candidats permutés + distracteurs admissibles | question inchangée, par id stable |
| **B8-depart** | même graphe, AUTRE nœud de départ | faits inchangés, apparié par graphe |

Contrainte dét (audit/QA v1.8 Q3) : les pools incluent des cas où un nœud
intermédiaire du chemin EST candidat (pour rendre broken-chain det évaluable
à l'avenir) — générés par construction, pas sélectionnés post-hoc.

## 3. Voies évaluées (mêmes droits, batch/encode identiques)

- **(d)** direct LoRA figé.
- **(c)** pipeline figé : lecteur → validateur → exécuteur (abstention
  préenregistrée V2, inchangée) + variante naked (diagnostic).
- **(b)** lecteur → solveur exact (extraction pure).
- **(a)** mémoire exacte → exécuteur (ancre, diagnostic).
- **(p)** parser déterministe borné aux templates (texte public seul) —
  contrôle d'ingénierie, pas un lecteur général.

## 4. Métriques (figées)

All-in (abstention=erreur) + couverture/risque séparés ; par banc et par
profondeur ; numérateurs/dénominateurs/groupes publiés. Δ apparié par
base_group_id, bootstrap groupé 2000 (IC conditionnels, étiquetés comme
tels). **Descriptif d'abord** (1 seed existante) : AUCUNE revendication
générale — des seeds multiples ne viendraient qu'après décision Q4 et
recette figée.

## 5. Attribution d'erreurs (audit §4/Q3 — sur erreurs B1..B8, diagnostic seul)

Par erreur : entités/départ corrects ; liens du CHEMIN UTILE corrects
(rappel/precision séparés) ; liens hors chemin ; FIN vs INCONNU ; validité +
motif de rejet ; solveur vs exécuteur sur même graphe prédit (archives des
désaccords) ; première divergence de trajectoire ; effet du filtre
d'abstention (c vs cn) ; réponse directe appariée. Correctifs oraculaires :
départ seul / chemin seul / hors-chemin seul / graphe exact — tables
DIAGNOSTIC séparées.

## 6. Critères de décision (Q4, préenregistrés)

| observation | suite |
|---|---|
| direct robuste partout, pas de complémentarité | conserver direct ; stop calcul additionnel pour ce domaine |
| direct chute en profondeur, S@prof tient, lecture dégrade | travailler l'INTERFACE (§7) |
| les deux chutent ensemble | isoler compréhension/taille/composition |
| gain seulement avec graphe exact | publication diagnostic (pas solution textuelle) |
| complémentarité réelle sur partitions | mesurer avant tout routeur (borne oracle d'abord) |

Aucun critère de « victoire » du pipeline n'est posé : V2.1 est un diagnostic,
pas une porte de revanche.

## 7. Piste conditionnelle (SEULEMENT si §5 désigne l'interface)

UNE ablation à la fois, même lecteur : graphe discret+solveur vs graphe
discret+exécuteur vs **transitions incertaines + propagation p_{t+1}=p_t@A**
(self-loop terminaux, INCONNU à sémantique définie, pas de renormalisation
silencieuse) vs direct (avec tête auxiliaire ÉGALE si supervision locale
revendiquée). Préenregistrement séparé requis avant tout run.

## 8. Coûts end-to-end (audit §7)

Texte brut → décision : tokenisation, transferts, lecture, exécution,
validation. p50/p95, batch, longueur, échauffement, mémoire
allouée/réservée/RSS. CPU séparé pour solveurs/stats. **Les latences V1 ne
sont PAS réutilisées.** Le direct bénéficie des mêmes droits de
batch/encodage partagé que le pipeline (multi-questions : les DEUX voies
batchent).

## 9. Rôles

@ag-2 : génération bancs (§2) + manifeste. @ag-3 : revue recettes/éventuel
§7. @ag-4 : validation du présent préenregistrement + QA des résultats.
@ag-5 : registre/runs/ coûts. @ag-1 : harnais d'éval checkpoints figés,
attribution d'erreurs, coordination, décisions Q4.

---

# Addendum A (QA @ag-4 11:26 — GO conditionnel, exigences A1–A5 transcrites)

*Métriques §4/§5 inchangées par ailleurs ; cet addendum les COMPLÈTE avant
toute prédiction V2.1.*

- **A1 — Qualité probabiliste (audit §7).** Ajouté à §4 : **NLL et Brier**
  par banc pour (d) (probs candidates) et (c) (probs exécuteur sur
  terminaux) ; **calibration** (courbe de fiabilité + ECE) calculée sur une
  partition désignée distincte : B1 (n≈400) pour l'ECE, les autres bancs
  publient NLL/Brier seuls. Couverture/risque publiés conjointement (une
  invariance triviale par abstention systématique reste détectable).
- **A2 — Préfixe et successeur actif (audit §4.2).** Ajouté à §5 :
  exactitude du successeur pour le NŒUD ACTIF à chaque pas (par position de
  pas), longueur de préfixe correcte (nombre de transitions correctes
  consécutives depuis le départ), en plus de la première divergence.
- **A3 — Ensembles adversariaux (audit §3.5, préventif).** Ajouté à §0 :
  tout ensemble construit contre un modèle spécifique doit être **étiqueté
  adversarial** et **complété par une évaluation indépendante** ; aucun banc
  V2.1 n'est construit ainsi (vérifié par construction : transformations
  préenregistrées, indépendantes des erreurs observées).
- **A4 — Chaîne cassée : det NON ÉVALUABLE en V2.1** (cohérent v1.8 Q3).
  Sémantique future fixée dès maintenant pour tout usage ultérieur :
  l'absence d'arête = **information manquante ≠ terminal** (monde partiellement
  observé) ; INCONNU = catégorie distincte des terminaux. Les cas
  « nœud intermédiaire candidat » générés (§2) restent de l'infrastructure
  pour une éventuelle V2.2 — JAMAIS comptés dans un scoring V2.1.
- **A5 — Tests minimaux harnais (audit Q0).** Exigés et FAITS avant runs :
  `scripts/run_v21_eval.py --selftest` = tailles 1/7/8/9/16/17/**411**,
  dernier minibatch incomplet, ordre mélangé == trié (identité exacte),
  batch vs unitaire (identité), ids dupliqués (résultats par position),
  chaque exemple exactement une fois. Preuve : `runs/v21_eval/SELFTEST_Q0.log`.
- **B1 — Unité de généralisation (clarification).** B5-surface = **renommage
  + paraphrase**, PAS une nouveauté structurelle (graphes-signatures
  identiques à B1) — étiqueté « surface » dans tous les tableaux ; la
  nouveauté structurelle = B1 (nouveaux groupes/graphes) et B2–B4
  (profondeur).
- **B2 — Périmètre.** Aucune exclusion d'exemples post-test (une exclusion
  révélée après coup = écart documenté avec dénominateurs avant/après) ;
  cycles, successeurs multiples, contradictions, observations incomplètes =
  **extensions de tâche hors périmètre V2.1** (elles changent les
  hypothèses du solveur — protocole séparé requis).
