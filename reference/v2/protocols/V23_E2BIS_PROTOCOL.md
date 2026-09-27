# PROTOCOLE E2-bis — inversions aux profondeurs variées (COUVERTURE, pas extrapolation)

*GO utilisateur 22:04. Cadre : périmètre V2.4 partiel, une seule modification.
Revendication EXPLICITE : objectif = COUVERTURE in-domaine de inv×profond —
l'étiquette « aveugle » reste réservée aux expériences où la sélection n'a
jamais vu la profondeur. INCONNU reste hors périmètre.*

## Mixture E2-bis (figée, pas de recherche)

Re-rendus DÉTERMINISTES des graphes E5v2_train (seeds d'allocation 2320) :

| part | rendu | proportion |
|---|---|---|
| canonique | render seed A | 25 % |
| L1 paraphrase | render seed B | 30 % |
| L2-inv | render seed B + table fermée | **45 %** |

**Distribution de profondeurs des inversions** : les profondeurs des graphes
E5v2_train sont 1-4 (128/715/619/587). Les inversions sont appliquées à TOUS
les rendus L2-inv quelle que soit la profondeur du graphe — la mixture couvre
donc inv×prof1-4. La NOUVEAUTÉ vs E2 : la part inv passe de 25 % à 45 %
(la fuite étant le mécanisme, plus d'exemples inversés par epoch).

Configs : `configs/c23/e2bis_v22_a2_s26.yaml`, `e2bis_v22_a3_s27.yaml`
(pilote), `e2bis_v22_a2_s28.yaml`, `e2bis_v22_a3_s29.yaml` (complément).
Recettes inchangées (deux-lr, 1200 steps, augmentation INCONNU 25 %/seed 17
avec masquage, sélection sur banc neuf court-seulement seed 2330 —
JAMAIS sur les bancs d'évaluation E3).

## Seuils de succès PRÉFIXÉS (à figer avec la QA)

| critère | seuil | justification |
|---|---|---|
| **Accuracy inv×p10** (bancs E3 neufs, 2 seeds min) | **≥ 0.85** | couverture : la fuite composée doit être réduite au point que l'argmax récupère en profondeur |
| **Masse INCONNU en profond** (p8-p10, diagnostic P2 reconduit) | **≤ 0.25** (vs 0.57-0.64 en E2) | la réduction mécaniste de la fuite est la cause attendue |
| **Non-régression** | toutes cellules E1+E2 existantes à ±2 pts (L1a, L2-inv court, L3-lbl, L3-adv, canonique toutes profondeurs) | pas de compromis caché |
| Δ(A2−A3) inv×profond | > 0, IC bas > 0 | l'équité de supervision doit continuer à isoler l'architecture |

## Chaîne (autonome, anti-écrasement actif, pattern éprouvé)

1. Pilote : A2-s26 + A3-s27 (~2.5 h GPU) → porte inv×p10 ≥ 0.85 (2 seeds
   mesurés, bancs E3-p8/p10-inv NEUFS si générés, sinon existants — les bancs
   E3 actuels sont de l'évaluation, pas de la sélection, donc réutilisables
   pour la mesure de couverture).
2. Si PASS : seeds complémentaires s28/s29 (total 2/voie + pilote = 3).
3. Éval complète : toutes cellules existantes + inv×prof + masses (INCONNU,
   terminal) + marges top-2 + hard/soft.
4. Rapport + QA.
5. Si FAIL : documenter (la fuite ne se réduit pas par la mixture seule =
   information sur sa nature — peut-être structurelle à l'interface).

## Interdits reconduits

Aucune sélection sur les bancs d'évaluation ; anti-écrasement structurel
actif (tags era-seed-mode-cellule, FORCE_EVAL=1 explicite) ; registre
append-only ; FAIL = résultat ; INCONNU hors périmètre ; une seule
modification (la mixture — pas de changement d'architecture).
