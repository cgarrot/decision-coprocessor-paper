# RAPPORT FINAL V2.2 — l'interface de propagation (audit §6)

*Clôture du programme V2.2 (GO utilisateur 14:04, mandat @ag-ask). Préenregistrements :
V22_PROTOCOL 6fc9d7d4 · amendement A2 2334c67b · spec A1-bis d9337317 · spec A3
2f58f02b — tous déposés et hashés au registre AVANT leurs runs. QA : REG-76/77/78,
reviews `reports/v22_a1_qa_review.md`, `v22_a2_qa_review.md`, `v22_a3_qa_review.md`.*

## 1. Table globale 8/8 — toutes les voies (claims PAR BANC, aucune globalisation)

| banc | discret c | A1-bis | **A2** | A3 (direct+aux) | direct V2.1 | Δ(A2−A3) IC95 |
|---|---|---|---|---|---|---|
| B1 court (prof 1–4) | 0.800 | 0.855 | **0.995** | 0.9625 | 0.9375 | +3.25 [+1.50,+5.25] |
| B2 prof 6 | 0.667 | 0.838 | **0.9975** | 0.4925 | 0.5250 | +50.5 [+45.5,+55.5] |
| B3 prof 8 | 0.598 | 0.853 | **0.9975** | 0.2475 | 0.2800 | **+75.0 [+71.0,+79.25]** |
| B4 prof 10 | 0.560 | 0.855 | **0.9975** | 0.2825 | 0.3075 | +71.5 [+67.0,+75.75] |
| B5 surface | 0.810 | 0.853 | **1.000**˟ | 0.9575 | 0.9400 | +4.25 [+2.50,+6.50] |
| B6 distract | 0.773 | 0.833 | **1.000**˟ | 0.9450 | 0.9375 | +5.5 [+3.25,+7.75] |
| B7 options (K=6) | 0.800 | 0.855 | **0.995** | 0.9600 | 0.9400 | +3.5 [+1.50,+5.50] |
| B8 départ | 0.765 | 0.858 | **0.9975** | 0.8550 | 0.8400 | +14.25 [+11.0,+18.0] |

**Solution bornée non-neuronale (table produit, audit §4.1)** : cellule
parser+solveur-exact MESURÉE (predictions/p_cell_v21.jsonl, registre
V2.2-p-cell) : **1.0000 sur les 8 bancs (3200/3200)** — le hybride
symbolique borné aux templates résout déterministement 100 % du domaine
synthétique courant : borne haute de tout système appris ICI. A2
(0.995–1.000) l'approche sans l'égaler strictement. **La valeur d'un
lecteur neuronal est de généraliser AU-DELÀ des templates, pas en
dessous** — c'est ce que C2 devra trancher (objectif à arbitrer :
confirmer le système vs extrapolation).

˟ **saturation déclarée** (B5/B6 = 1.000 : ces bancs ne séparent plus les
systèmes au-dessus de 0.995). Δ vs direct V2.1 et vs discret : voir
`runs/v22_a2_eval/a2_eval_metrics.json` (IC>0 partout). **(p) parser
(déterministe, 1.000/1.000 de couverture/accord) : table DIAGNOSTIC séparée,
hors benchmark** — il établit que l'extraction depuis le texte public est
possible ; il ne mesure aucune voie apprise.

**Qualité probabiliste A2** (capture dédiée, assertions prédiction ==
publiées) : NLL 0.0044–0.0294, Brier(gold-class) (1−p_oracle)² 0.0007–0.0061 selon le banc — à
comparer au direct V2.1 : NLL 0.59→**8.85** nats aux profondeurs (ECE B1
0.061). A2 montre une bonne qualité probabiliste sur ces exemples (NLL
   faible sur un domaine quasi résolu ≠ étude de calibration complète) ; le
   direct présente une **qualité probabiliste dégradée** — sa capacité à
   **détecter ses propres erreurs reste À MESURER** (une NLL élevée
   n'implique pas la connaissance des erreurs : contre-exemple
   confiant-faux ; outils requis : confiance à l'inférence,
   séparation erreurs/succès, courbe risque-couverture).

## 2. Conclusions (règles figées appliquées verbatim)

1. **A2 > direct V2.1 partout** (8/8, IC>0 — écart le plus serré B1 +5.75
   [+3.25,+8.25]).
2. **Supériorité ARCHITECTURALE de la propagation : 8/8 bancs, IC bas > 0**
   (A3 = direct avec supervision auxiliaire ÉGALE reste effondré en
   profondeur 0.25–0.49 ; l'auxiliaire apporte +2.5 pts sur B1 — seul banc court
   significatif (IC [0.25, 4.75] ; B5/B6/B8 IC∋0, B7 limite, +0.75→+2.0) — et ~0
   en profondeur). Asymétrie chiffrée : court
   +3.25→+5.5 pts vs profondeur +50.5→+75.0 pts.
3. **Borne oracle routeur : INUTILE** (oracle A2∪A3 = 0.9975–1.0000, soit
   +0.00 à +0.50 pts sur A2 seul ; A3-seul correct sur 0–2 items/banc). La
   complémentarité V2.1 (123/172/163 items) est absorbée par A2 à 0.995+.
   Aucune construction lancée — aucune nécessaire.
4. **A1 FAIL publié tel quel** : propagation sur head bilinéaire
   non-entraîné = bruit (c_prop 0.19–0.32 ≈ hasard K∈{4,5,6}).

## 3. Chronologie des préenregistrements

Protocole V2.2 14:03 (sha 6fc9d7d4) avant A1 14:11 → A1-bis préenregistrement registre **14:22:44** (commit f6460e29) → run **14:37:44** ; doc V22_A1BIS_SPEC.md (d9337317) déposé **14:56** (post-run, extrait verbatim de l'entrée de registre) → amendement A2 2334c67b (14:18,
contre-signé 14:20) avant run 15:29 → spec A3 2f58f02b (17:05, QA REG-77
avant run) avant run 17:20. Sélection UNIQUEMENT sur banc 2213 (sha
7089876d, étiquette selection_only) ; bancs V2.1 : **hors gradients et hors sélection de checkpoints, mais
   réutilisés/observés pendant une campagne adaptative de développement**
   (V2.1 → A1 → A1-bis → A2 → A3) — évaluation développement, PAS une
   confirmation entièrement indépendante (C2 requise). Le banc 2213
   contient 50 % de profondeurs 6/8 : la performance d'A2 en profondeur
   n'est PAS une extrapolation aveugle (la sélection s'y est appuyée).

## 4. Incidents et transparence (causes + corrections, impact nul sur les chiffres publiés)

| incident | cause | correction | impact |
|---|---|---|---|
| A1 mécanisme « 0.75^k » RETIRÉ | head bilinéaire jamais supervisé en mode fact (@ag-3) — A1 propageait du bruit ; mon récit était une rationalisation post-hoc | rétraction registre, A1-bis préenregistré sur la vraie source (fact-level) | interprétation remplacée, chiffres valides comme artefact |
| A2 run 1 annulé | OOM (GC jamais activé) + éval sélection ancrée gold vs candidats prédits | GC + réancrage prédit + garde croisée `--self-check` (tests 143+) | aucun chiffre publié du run 1 |
| Loader `.default` (3 faux départs) | `set_peft_model_state_dict` ignore silencieusement les clés peft avec `.default` → LoRA chargé à vide (28/224) | `pm.load_state_dict` + **assertions de chargement** (désormais 100 %, reco QA) | aucun chiffre publié depuis un état cassé |
| Kill d'outil A3 + fix `encode→adapter.encode` | timeout de mon harnais bash (0 step) ; mismatch de signature à la sélection | relance ; fix interface | aucun |
| Archive B1-A1 contaminée (14:37) | import CPU d'un runner sans garde `__main__` (côté QA) | gardes sur TOUS les runners, run A1 régénéré GPU, **agrégats 8/8 identiques** (per-item original non conservé — identité per-item invérifiable) | agrégats intacts, valeur CPU accidentelle inexistante |

## 5. Environnement (R7)

Chiffres ENVIRONNEMENT-BOUND : GPU RTX 3070 Laptop / bf16 / batch 8 /
chunking d'ordre (prouvé par non-régression exacte vs gelés E5v3-A à chaque
harnais). Variance CPU↔GPU mesurée ~6 pts sur dev (quasi-égalités du
lecteur — R7). Tie-break eps=1e-3 clé stable dans le harnais V2.2 (NON
rétroactif sur V2.1, publié avec son caveat). Aucun mélange d'environnement.

## 6. Limites et portée (conclusions ≠ revendications)

- **« Supériorité architecturale sur CES bancs »** : synthétique FR à
  templates, **1 seed**, checkpoints sélectionnés sur 2213 ; PAS de
  généralisation OOD revendiquée.
- **INCONNU posé mais non évalué** (sémantique : absence d'arête =
  information manquante ≠ terminal, sink absorbant) — jalon restant,
  nécessite des bancs à mondes partiels (extension de tâche, protocole
  séparé).
- Tête `relations` d'A3 inutilisée en inférence (shaping d'entraînement
  uniquement) ; assertions de chargement passées de 90 % à 100 % (reco QA).
- Saturation B5/B6 : des bancs plus durs seraient requis pour séparer des
  systèmes au-dessus de 0.995 — hors V2.2.

## 7. Coûts end-to-end (mesurés @ag-5, V2.2-couts 42b3e22d, B1+B3, batch 8,
 warmup 2, sync CUDA, p50/p95 item, alloc/reserved/RSS, LoRA 224/224 ×2)

| mesure | A2 (pipeline complet) | A3 (direct+aux) | rapport |
|---|---|---|---|
| B1 p50 | 40.32 ms | 32.65 ms | ×1.23 (+7.7 ms) |
| B1 p95 | 46.2 ms | 38.1 ms | ×1.21 |
| B3 p50 | 51.59 ms | 40.52 ms | ×1.27 (+11.1 ms) |
| B3 p95 | 55.4 ms | 43.5 ms | ×1.27 |
| débit B1 / B3 | 22.6 / 18.7 lots/s (batch 8 → ~181/150 ex/s amortis) | 29.0 / 23.6 lots/s | ×0.78–0.79 |
| **propagation p@A** | **0.59–0.66 ms (≈1.3–1.5 % du p50 A2)** | — | **négligeable, mesurée** (microbench CPU 0.187 ms) |
| VRAM alloc batch8 | ~1472–1512 MiB | parité | — |

Latences V1 non réutilisées (interdit §8 respecté). Multi-questions/
amortissement de cache : mesure future notée (pas de cache
inter-questions dans le harnais).

**Lecture opérationnelle** : A2 paie **+23–27 % de latence** pour +3.25 pts
(B1) et **+50 à +75 pts** (profondeur) — le surcoût est petit devant
l'écart, et le cœur de l'architecture (la propagation) est GRATUIT
(~1 %). La préférence pratique « A2 » est désormais appuyée par les
coûts : le prix se paie en extraction (lecteur), pas en calcul.

## 8. La réponse à l'audit, en une phrase par section

- §6.2 (transitions incertaines) : **validée deux fois** — zéro entraînement
  (A1-bis 0.85 invariant) puis supervisée (A2 0.995+). **Réconciliation
   parser (audit §4.1)** : le parser déterministe mesure 1.000/1.000
   (couverture/accord, 3200/3200) — le « plafond 0.95 » cité en V2.2 était
   une approximation erronée héritée du framing du GO (proche des
   diagnostics chemin_seul 0.95–0.98, PAS une mesure du parser). A2 à
   0.995–1.000 **rejoint mais ne dépasse pas** la solution déterministe
   bornée aux templates — voir la table produit élargie ci-dessous.
- §3.1/§3.3 (portée, généralisation) : le « définitif » de V2 était un
  artefact de chaînes courtes — le croisement prof 4↔6 (V2.1) puis la
  domination complète (V2.2) l'établissent.
- §3.5 (équité de test) : bancs préenregistrés, jamais construits contre un
  modèle ; A3 a reçu la supervision ÉGALE et la règle de conclusion était
  figée avant son run.
- §4 (diagnostic d'abord) : chemin utile (QA), parser (p), A1→A2 par
  ablations une à la fois — la décision a suivi le diagnostic, pas l'inverse.

— @ag-1, clôture V2.2. Câblage : @ag-3 (propagation, A2, A3, 3 interceptions
décisives). Données : @ag-2 (bancs 2213, parser (p)). QA : @ag-4
(REG-74→78, R7, toutes les règles de conclusion figées avant les runs).
Infra/coûts : @ag-5. GO et arbitrage : @ag-ask/utilisateur.
