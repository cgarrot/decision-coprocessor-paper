# V2.2 — ERRATUM DE PORTÉE (C0, audit d47186ec §4)

Corrections de formulation SANS toucher aux chiffres (audit V22-confirmation) :

1. **« Le direct sait qu'il échoue » RETIRÉ** → « qualité probabiliste
   dégradée ; capacité à détecter ses erreurs RESTE À MESURER » (une NLL
   élevée = bonne réponse peu probable, PAS connaissance des erreurs ;
   contre-exemple confiant-faux ; outils : confiance inférence,
   risque-couverture — mesure C1/C2).
2. **« A2 calibré » NUANCÉ** → bonne qualité probabiliste observée sur un
   domaine quasi résolu ; calibration complète à établir (fiabilité par
   bin, par profondeur). Le score publié est renommé
   `gold_class_squared_error` (ex-« Brier gold-class ») ; **Brier
   multiclasse complet à calculer séparément** (C1).
3. **« Plafond parser 0.95 » RÉCONCILIÉ** : le parser mesure 1.000/1.000
   (couverture/accord). Le 0.95 était une approximation erronée du framing
   GO (proche des diagnostics chemin_seul 0.95–0.98, pas une mesure du
   parser). A2 rejoint, ne dépasse pas, la solution déterministe bornée.
   Parser+solveur ajouté à la table produit (D02 §4 + audit §4.1).
4. **Statut des bancs requalifié** : B1–B8 = hors gradients, hors sélection
   de checkpoints, mais observés pendant la campagne adaptative de
   développement → évaluation développement, pas confirmation indépendante.
   Le banc 2213 (sélection) contient 50 % prof 6/8 → la performance
   profondeur d'A2 n'est PAS une extrapolation aveugle.
5. **Coûts** : « propagation gratuite » → « faible dans ce profil
   (1.3–1.5 % du p50, batch 8) » ; unités précisées (lots/s batch 8, temps
   amorti/exemple ≠ latence requête isolée) ; mesure batch 1 = C1 ;
   ×1.273 vs plafond 1.25 : PAS une validation automatique (règle
   d'agrégation préfixée requise).
6. **IC canoniques** : l'artefact canonique = runs/v22_a3_eval/
   a3_eval_verdict.json (script run_v22_a3_eval.py, seed bootstrap 17,
   groupé par base_group_id) ; les bornes QA différant de ≤0.5 pt viennent
   de la graine bootstrap — citer le canonique.
7. **« Le direct reste dominant en court »** : vrai en V2.1 uniquement ;
   en V2.2 A2 > direct V2.1 sur les 8/8 (distinction versions/comparateurs
   à conserver partout).

## 8. Sémantique du tie-break eps (R-E, QA REG-82)

- **Égalité réelle** ET **quasi-égalité (écart ≤ eps=1e-3)** : le choix se
  fait par **clé alphabétique des labels** — y compris lorsque la masse du
  label alphabétiquement premier est légèrement INFÉRIEURE (l'eps absorbe
  le bruit numérique, pas l'inverse : on préfère la stabilité à la dernière
  goutte de masse).
- **Renommage = équivariance, PAS invariance** (QA tiebreak 8/8) : permuter
  les identifiants change la clé alpha → peut changer le choix À ÉGALITÉ
  PARFAITE ; les prédictions à masse dominante sont invariantes.
- Ordre des faits/candidats : invariance vérifiée (8/8).

## 9. Localisation CPU/GPU (R-D exécuté, QA REG-83)

Premier étage divergent : **h14 (backbone), 16/16 items** — max|Δ| médian
2.0 (h21 : 3.0) sur |h| médian ≈ 428 → **erreur relative ~0.49 % (max
2.29 %) = dérive bf16 inter-plateformes au fil des couches, PAS un bug de
code** (token_ids/mask/spans/p0 exacts, loaders 100 % des deux côtés).
Aval : logits fact Δ 0.3–1.2, A ≤ 0.01, pT médian 1.2e-4 ; **décisions
stables 0/16 flips (successeurs ET réponses)** ; un seul flip d'argmax
objet sur quasi-égalité (marge 0.044 vs 0.005), sans effet décisionnel.
**Cohérent avec R7** : les ~6 pts CPU↔GPU de V2.1 concernaient le lecteur
E5v3-A (marges faibles) ; A2 a des marges plus larges. Le bruit remonte du
backbone et ne mord que les quasi-égalités. Artefact :
reports/qa_stage_diff.json. (Option non bloquante : dump élargi +
distribution des marges top-2 comme prédicteur — utile pour l'interprétation
C2, à la discrétion QA.)

## 10. Compléments C1 (R-B, sweep, decodeurs v2, toolchain — @ag-3 55ccd342)

- **R-B anti-fuite PASS** (64 items × R0/R1) : batch sans AUCUN champ privé →
  mémoires identiques 64/64 ; privé randomisé (vérité change 28–30/64) →
  prédictions inchangées 64/64 ×2. L'inférence est strictement publique.
- **Sweep budget 0/1/2/4/8/16/20** : R0 converge à ≈ profondeur+1 puis
  DÉCROÎT (fuite du lecteur figé au-delà de l'horizon utile : B5 0.915@4 →
  0.850@20) ; R1 converge plus tôt et PLATEAU STABLE (0.998–1.0). Budget 0
  ≈ hasard ; creux à budget 4 en profondeur = « pas encore de masse ».
- **Decodeurs v2** (5 findings corrigés : TERMINAL≠auto-successeur, tie-break
  stable, horizon 20, symétrie, résidu scindé) : **soft v2 ≡ v1 (0 divergence
  → chiffres publiés VALIDES)** ; hard R1 +0.75 à +2.25 pts en v2 (R0 −0.75
  à +0.5) — la colonne hard du 2×2 est corrigée en diagnostic (JSON
  versionnés séparément), la conclusion d'attribution (deux facteurs,
  soft>hard) est inchangée.
- **§8.3 raffiné** : torch 2.6.0+cu124 reproduit les publiés EXACTEMENT
  (0/3200) ; torch 2.14.0+cu130 diverge sur 18/3200 (≤0.75 pt), divergence
  née au FORWARD BACKBONE. **Règle** : toute assertion « == publié » se
  rejoue dans le toolchain de publication (stamp toolchain/cuda sur les
  nouveaux JSON) ; sinon tolérance 1.5 pt + diff par item publié.

## 11. R-A clos (Brier complet, @ag-3 f0bca89c)

Archives PAR ITEM (16 fichiers, budget 20 : truth, cand, p_cand, p_inconnu,
p_hors_candidats, residu_total, answer, ok). Convention déclarée :
classes = candidats ∪ {AUTRE}, P(AUTRE) = p_inconnu + p_hors ; gold hors
candidats → AUTRE. **Brier complet recalculable des seules archives**
(`brier_scores()`, testé) : R1 B3 : 0.0079 (candidats-seuls) → **0.0118
complet** (p_INCONNU 0.0075, p_hors 0.0020) ; R0 B3 : 0.3073 → **0.4632**
(p_INCONNU **0.2017** = la fuite du lecteur figé en profondeur, cohérente
avec le sweep §10). Anti-fuite fusionnée en 3 couches rejouables
(structurelle 3200/3200, publique 64/64, comportementale 64/64 ×2).
Second passage toolchain de publication : **0 flip / 3200** (exactitude
reproduite deux fois).
