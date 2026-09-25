# V2.1-Q1 — résultats des bancs (checkpoints V2 figés, descriptif 1 seed)

*Registre V2.1-Q1 done. QA @ag-4 : bénédiction mode gévé (recalcul indépendant
8/8 identique) + addendum B / REG-71-72. Rapport QA : `reports/v21_q1_qa_review.md`.*

## ⚠️ Portée des valeurs (R7 — réponse aux exigences QA)

- **Chiffres ENVIRONNEMENT-BOUND** : GPU RTX 3070 Laptop / bf16 / batch 8 /
  chunking d'ordre (mode gévé avant les runs, prouvé par la régression exacte
  vs gelés E5v3-A : a=1.0 b=0.7616 c=0.7616 cn=0.82 d=1.0 abst=0.0827).
  **Aucun mélange d'environnement.**
- **Variance inter-environnements mesurée (QA)** : CPU↔GPU ~6 pts sur dev
  (b=0.82 CPU vs 0.7616 GPU) — quasi-égalités de successeurs du lecteur,
  stables par configuration de batch, pas par composition/platforme ; même
  en fp32 CPU, 11/32 mémoires diffèrent → **pas qu'un arrondi bf16**.
- **GPU batch=1 vs batch=8 (B1, artefact `runs/v21_eval/batch1/`)** :
  b/c 0.805 vs 0.800 · cn 0.8575 vs 0.8525 · d 0.935 vs 0.9375 ·
  Δ −0.130 vs −0.1375 — écarts ≤ 0.5 pt, sans effet sur les conclusions.
- Selftest auto-prouvé désormais : device + valeurs de non-régression dans
  le log (`runs/v21_eval/SELFTEST_Q0.log`).
- **Correctif runs futurs (V2.2)** : tie-break stable à `eps` déclaré ou
  inférence par exemple (audit §4.4).

## Résultats 8/8 (n=400 chacun, mode GPU/batch8)

| banc | (a) ancre | (b) solveur | (c) abst | (cn) naked | (d) direct | Δ(c−d) [IC95] |
|---|---|---|---|---|---|---|
| **B1 (prof 1–4)** | 1.000 | 0.800 (abst .087) | 0.800 | 0.853 | 0.9375 | −13.75 [−18.2,−9.2] |
| B5-surface | 1.000 | 0.810 (.075) | 0.810 | 0.868 | 0.9400 | −13.00 [−17.2,−8.7] |
| B6-distract | 1.000 | 0.772 (.110) | 0.772 | 0.848 | 0.9375 | −16.50 [−21.2,−12.0] |
| B7-options (K=6) | 1.000 | 0.800 (.087) | 0.800 | 0.853 | 0.9400 | −14.00 [−18.5,−9.8] |
| B8-depart | 1.000 | 0.765 (.087) | 0.765 | 0.820 | 0.8400 | −7.50 [−12.8,−2.0] |
| **B2-prof6** | 1.000 | 0.667 (.095) | 0.667 | 0.693 | 0.5250 | **+14.25 [+7.5,+21.0]** |
| **B3-prof8** | 1.000 | 0.598 (.125) | 0.598 | 0.618 | 0.2800 | **+31.75 [+25.0,+38.5]** |
| **B4-prof10** | 1.000 | 0.560 (.165) | 0.560 | 0.593 | 0.3075 | **+25.25 [+18.3,+32.0]** |

**Courbe par profondeur (QA, correction de portée — « B1 » = prof 1–4
mélangées)** : direct 1.00/0.97/0.91/0.87 (prof 1/2/3/4) puis 0.53/0.28/0.31
(prof 6/8/10) vs pipeline (c) 0.92/0.81/0.76/0.71 puis 0.67/0.60/0.56 —
**croisement entre profondeur 4 et 6**.

## Mécanisme (diagnostics QA sur archives, tables oraculaires séparées)

- (a)=1.000 PARTOUT, y compris prof 10 → l'exécuteur compose ; le déficit
  du pipeline est ENTIEREMENT dans la lecture.
- **Déficit = arêtes du chemin utile** : correctif oraculaire `chemin_seul`
  → 0.950/0.965/0.9825/0.9825 (B1..B4) vs baseline 0.800/0.667/0.598/0.560 ;
  `depart_seul`/`hors_chemin` ≈ baseline. `graphe_exact` = 1.000.
- successeur actif ~0.89 stable ; FIN 98.7–99 %.
- **NLL direct** : 0.59 → 5.43 → 8.85 → 7.45 nats (B1→B4) — le direct « sait »
  qu'il est incertain en profondeur (ECE B1 = 0.061).
- **Filtre d'abstention** : cn > c de +5.25 à +6.0 pts all-in (c == b
  exactement — exécuteur ≡ solveur sur graphes valides) → publié en ablation
  couverture/risque.
- **Complémentarité** (pipeline juste, direct faux) : prof 6 : 123/400 ·
  prof 8 : 172/400 · prof 10 : 163/400 → ligne Q4 routeur PERTINENTE ;
  **borne oracle à mesurer avant toute construction**.

## Décision Q4 (matrice préenregistrée) — LIGNE 2

« Direct baisse en profondeur, S fonctionne, lecture se dégrade » →
**travailler l'interface** (audit §6 : transitions incertaines / propagation,
préenregistrement séparé @ag-3). La ligne routeur est documentée comme suite
possible APRÈS mesure de la borne.

## Écarts

1. (p) parser déterministe : **LIVRÉ puis VALIDÉ QA** (commit 5f993a36,
   REG-73) — couverture 1.0000 et accord 1.0000 sur 8/8 bancs (3200/3200,
   zéro INCONNU ; reproduction QA identique, addendum C), public-only,
   règles INCONNU explicites. Étiquette diagnostic hors benchmark §0.3.
   Lecture : l'extraction déterministe depuis le texte public est POSSIBLE
   (existence) → le déficit pipeline est dans l'extraction apprise et
   l'interface ; (p) borné aux templates, ne quantifie pas la difficulté
   d'apprentissage (nuance QA).
2. B1 batch=1 : première exécution a écrasé les fichiers batch=8 (nommage
   non paramétré) — régénéré à l'identique (détails ci-dessus), sortie
   désormais séparée par mode. Aucun chiffre publié affecté.
3. Diagnostics oraculaires = tables séparées, jamais comptés dans les
   benchmarks (protocole §0.3).
