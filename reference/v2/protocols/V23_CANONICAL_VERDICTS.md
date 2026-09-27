# VERDICT CANONIQUE CONSOLIDÉ — Decision Coprocessor (V1→V2.3)

*Document unique faisant foi. Remplace les formulations historiques des
rapports successifs. Tous les chiffres sont **recalculés indépendamment par
la QA** (REG-74→94). Tout écart ultérieur = addendum daté. Chiffres
ENVIRONNEMENT-BOUND (GPU/bf16, R7) ; campagne adaptative — aucun banc n'est
une confirmation totalement indépendante (sauf mention explicite).*

## Règle de lecture
Verdict **multi-critères** par expérience : chaque critère est rendu
séparément (PASS/PARTIEL/FAIL), la hiérarchie est explicite, et **aucune
revendication ne se globalise au-delà des cellules mesurées**.

---

## V1 — Coprocesseur latent (clôturé)
- Verdict : **N1** (échec local documenté). H1–H4 **non soutenues** ;
  Δ(R4−B2) = **−0.59 pt [−1.25 ; +0.07]**.
- Réserves : poids non archivés (`weight_hashes` null, couvert par
  bundle_manifest), fragmentation ×1.8 (pas de déduplication).

## V2 — Étage S (mécanisme) et étage T (connexion texte)
- **S : DÉMONTRÉ** (E1–E4b : 1.000 sur le pool décrit ; E4b pad20 399/399,
  index ≤20 exposés par réentraînement — nuance publiée).
- **T : échec local (iii) sur le protocole V2, deux fois** (dont E5v3-A sous
  équité F1). Direct adapté **1.000 dev** vs pipeline **0.762** ;
  Δ(c−d) = **−23.844 pts** IC [−28.19 ; −19.76] ; profil causal direct
  0.996/0.996/0.988. E5v2_eval **scellé à jamais, jamais ouvert**.
- Réserves : dev seul n=411, 1 seed ; eval jamais ouvert (non requis pour une
  issue (iii)) ; B4-4 det structurellement non évaluable sur ces pools.

## V2.1 — Renversement en profondeur (checkpoints figés)
- **Renversement CONFIRMÉ** sur les 8 bancs scellés : courts Δ(c−d)
  −7.5→−16.5 pts ; profondeurs **+14.25 (+6) / +31.75 (+8) / +25.25 (+10)**,
  IC bas > 0 ; (a) = 1.000 partout.
- Mécanisme : **déficit = arêtes du chemin utile** (`chemin_seul` recalculé
  0.95–0.98 vs baseline 0.56–0.80 ; hors-chemin/départ ≈ baseline) ;
  succ_actif ≈ 0.89 stable ; NLL direct explose (0.59→8.85) ; ECE B1 0.061.
- Réserves : « prof 4 » = B1 entier (1–4), croisement entre 4 et 6 ;
  chiffres liés à l'environnement (R7, dérive bf16 ~0.49 % au backbone,
  décisions stables 0/16) ; le parser mesurait 1.000/1.000 (le « plafond
  0.95 » était un framing erroné).

## V2.2 — Interface apprise + propagation
- **A1 : FAIL documenté** — propagation sur tête bilinéaire **non entraînée**
  en mode fact (top-1 0.054 ≈ hasard) : mécanisme « fuite 0.75^k » **RETIRÉ**
  (rétracté). **A1-bis : PASS** — A fact-level, c_prop **0.83–0.86 invariant**,
  Δ vs discret IC>0 8/8, +57.25 pts vs direct à prof 8 (zéro entraînement).
- **A2 : PASS** — c_prop **0.995–1.000**, Δ vs direct positif 8/8 IC>0
  (+5.75 B1 → +71.75 B3) ; au-dessus du plafond parser ; B5/B6 **saturés à
  1.000** (déclaré) ; NLL 0.0044–0.0294, Brier complet publié (canonical
  table) ; qualités probabilistes par item archivées.
- **A3 : contrôle équitable PASS** — Δ(A2−A3) **positif 8/8, IC bas > 0**
  (B1 +3.25 → B3 +75.0) → **supériorité ARCHITECTURALE de la propagation
  établie par banc**, sans saturation (A3 effondré 0.25–0.49 en profondeur).
  Nuance : l'auxiliaire seul apporte +2.5 pts en court (B1 significatif ;
  autres courts IC∋0) et ~0 en profondeur.
- **Routeur : INUTILE** sur ces bancs — oracle A2∪A3 0.9975–1.000, soit
  +0.00–0.50 pt sur A2 ; A3-seul 0–2 items/banc. Aucune construction.
- Réserves : 1 seed par voie (A2/A3), dev adaptatif ; coûts batch8
  A2 ×1.23–1.27 latence, propagation 0.59–0.66 ms ≈ 1.3–1.5 % (pas
  « gratuite ») ; head `relations` inutilisée en inférence ; assertions de
  chargement passées à 100 %.

## C2 — Confirmation (3 seeds) et extrapolation aveugle
- **C2-a : PASS** — Δ(A2−A3) profond poolé **+65.30 / +64.05 / +68.14 pts**
  (IC bas > 0 ×3 ; moyenne +65.83) ; dispersion A2 0.33 pt ; non-régression
  court 0.9992.
- **C2-b : LARGEMENT RÉUSSIE** — A2-blind **0.9867** ≥ 0.90 (sélection
  court-seule) ; A3-blind 0.271.
- Réserves : sélection 2213 inclut 6/8 → « blind » = sélection court-seule
  uniquement pour C2-b ; bancs = campagne adaptative ; marges top-2 :
  agrégées 0.991–0.996, deep-seul plus fragile (s20 1.50 % ≤1e-2).

## V2.3 — Langage non gabaritée
- **L1-a : PASS** — A2 variante **1.0000 ×3** (canonique 0.9983) ; Q2
  +0.25 pt (sans dégradation) ; parser 1.000/1.000 (reste dans sa grammaire).
- **L2-inv : A2 CASSE (échec local)** — A2 variante **0.5450 ×3**, Q2
  **−45.0/−45.5 pts** IC<0, **A3 > A2** (0.700–0.735) : renversement du
  régime gabarit ; P_eval couverture variante **0.00** (attendu, inchangé).
- **E2 (réentraînement) : PASS** — A2-E2 L2-inv var **0.9375/0.94** (porte
  0.9375 ≥ 0.70) ; Δ(A2−A3) positif 16/16 ; non-régression à ~1–2 pts près
  (L3-lbl −1.2/−2.2 pts, publié).
- **L3-lbl : tenable** — A2 ~0.95–0.97 après régénération (mapping unique,
  400/400 paires) ; **coût lexical 0/−1.5/0 pt** ; parser 0.9875/0.9875.
- **L3-adv (adversarial séparé) : tenable** — A2 0.995–1.000 ; usage
  `adversarial_separate`, hors score primaire.
- **E3 (diversité×profondeur) : VALIDÉ** — A2-E2 inv **0.927→0.823→0.753→
  0.680** (monotone) ; A3 ≤0.37 ; can/l1 au plafond (0.997–1.000) ;
  triples appariés 1200/1200. **Réserve : E2-era = 1 seed/voie**
  (collisions de tags) ; anomalie 20:00 documentée non rejouable QA.
- **P2 (diagnostic) : VALIDÉ avec réserves** — p_edge **0.819–0.854**
  (constant inter-profondeurs, < plage prédite 0.93–0.96) ; |t1−t3| ≤ 1.9 pt
  → **H-B non soutenue** (V4 non exécuté — écart déclaré) ; top-1 0.82–0.85
  < 0.99 → **H-C rejetée** ; masses : terminal ↓ 0.51→0.27, INCONNU ↑
  0.38→0.57 → **fuite composée établie**. **H-A PARTIELLE** (fit
  |acc−p^prof|≤3 violé ; O1 défaillant 0.007–0.017 → non interprété ;
  recommandation E2-bis présentée comme mixte/O1-indisponible).
- **E2-bis : PASS COUVERTURE** — A2 inv×prof s26 **0.980/0.973/0.953/0.930**,
  s28 **0.977/0.940/0.937/0.900** (porte ≥0.85, 2 seeds) ; non-régression
  totale (L1a 0.9925–1.0, can 0.993–1.0, L2-inv 0.978–0.985, L3-lbl
  0.930–0.9525, L3-adv 0.988–0.9975) ; A3 profond 0.24–0.42. **Requalifié
  EXTRAPOLATION AVEUGLE** (mixture+sélection profondeurs 1–4 uniquement,
  preuve par données) ; **nuance mécaniste : INCONNU profond 0.38–0.41 > 0.25**
  (terminal 0.46–0.69, p_edge ~0.86) — publié comme nuance, pas échec.

---

## M1 — Définitions canoniques des masses (P2 / E2-bis)
- **Population** : p_T ∈ [0,1]^{N+1} — N nœuds = mentions normalisées de la
  mémoire prédite, +1 = **sink INCONNU** (colonne terminale auto-bouclée,
  jamais renormalisée) ; A stochastique par ligne (masse totale =1, sink
  inclus).
- **Normalisation** : aucune opération supplémentaire ; `p_T` = p0@A^{20}.
- **Masses publiées** : `mass_term` = p_T[terminal correct] ; `mass_inconnu`
  = p_T[sink] ; `mass_hors` = masse sur nœuds hors candidats ; `parasites` =
  masse sur terminaux ≠ correct.
- **Périmètre argmax** : candidats = **nœuds uniquement** (sink jamais
  candidat) ; tie-break eps=1e-3 clé alphabétique des labels.
- **Populations mesurées** : P2 initial 300 items/cellule (s22/s24) ;
  e2bis_masses 100 items/cellule (E2-bis).

## M3 — Chronologie P2
1) Audit final → protocole P2 rédigé (22:0x) ; **validé QA sous 5 conditions**
(R1 seuils, R2 dominance, R3 terciles, R4 assistance oracle, R5 post-hoc). 2)
Figage/hash → diagnostic (~40 min) : p_edge constant, masses, O1/O2/O3. 3)
**O1 défaillant** (alignement) publié avec avertissement ; V4 et parser-étendu
**non exécutés** (écarts déclarés). 4) Réserves QA : H-A partielle, H-B rejet
faible → appliquées (20a29e54). 5) Recommandation E2-bis (mixte/O1-indisponible)
→ arbitrage utilisateur → **E2-bis exécutée et validée** (2 seeds).

## Réserves transverses (toujours valables)
- **R7** : chiffres liés à l'environnement (GPU/bf16/batch) ; variance CPU↔GPU
  mesurée (~0.2–1.3 % des items flippables, ≲1 pt) ; tie-break eps=1e-3 clé
  stable (sémantique documentée : quasi-égalité → clé alpha, même si masse
  légèrement inférieure ; renommage = équivariance ≠ invariance).
- **Campagne adaptative** : les bancs V2.1/B1–B8 ont servi au diagnostic et à
  des décisions d'architecture avant d'être réutilisés en V2.2/V2.3 —
  « hors entraînement et hors sélection des checkpoints, mais pendant une
  campagne adaptative ». Seule C2-b (sélection court-seule) et E2-bis
  (profondeurs 1–4 en mixture+sélection) méritent le label **extrapolation
  aveugle** ; les autres profondeurs ont été observées avant décision.
- **Seeds** : 1 seed/voie pour V2.2 et E2-era-E3 ; 3 seeds pour C2-a et V2.3
  L1-a/L2-inv ; 2 seeds pour E2-bis. Ne jamais présenter une expérience
  mono-seed comme répliquée.
- **Scellés** : E5v2_eval jamais ouvert ; les autres bancs ne sont pas des
  confirmations totalement indépendantes.

*Verdict canonique produit par @ag-4 (QA), sur la base des recalculs
indépendants REG-74→94. Il fait foi ; toute reformulation future doit le
citer et ne pas réintroduire les formulations historiques retirées.*
