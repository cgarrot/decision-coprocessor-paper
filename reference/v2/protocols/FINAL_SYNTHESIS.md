# SYNTHÈSE FINALE EXPLICITE — Decision Coprocessor V1→V2.4-E2bis

*Document faisant foi qui remplace les formulations historiques trop fortes
sans réécrire l'histoire. Sources canoniques : V23_CANONICAL_VERDICTS.md
(96cf3b77, QA REG-95), v23_release_manifest.json (@ag-5), v23_adapter_flow.md
(@ag-3), audits 096bc009/ea21d509. Phrase-honnête de l'auditeur final :*

> « Le résultat recherché n'est pas de faire perdre le parser. Il est de
> savoir quel langage public le système traite réellement, à quel coût, et
> ce que le calcul de propagation apporte dans ce domaine. »

## Ce qui est démontré (et sous quelles conditions)

| affirmation | conditions exactes |
|---|---|
| « Transition apprise et causale » | étage S, domaines E1-E4, exécuteur 92 802 params, 1.000 partout, zéro-shot aux profondeurs jamais vues |
| « Supériorité architecturale de la propagation » | 8 bancs synthétiques français V2.1 (préenregistrés), contrôle A3 à supervision égale, 3 seeds, Δ profond poolé +65.8 pts IC bas > 0 |
| « Extrapolation aveugle en profondeur » | C2-b (s20-blind, 1 seed/voie) et E2-bis (s26/s28, 2 seeds) — seuls à mériter ce label ; ni gradients ni sélection n'ont vu prof > 4 |
| « Robustesse aux paraphrases » | L1-a (decks sans remise, gabarit), 3 seeds, 1.000, zéro dégradation appariée |
| « Récupération des inversions par la donnée » | E2 (×1.8 inv, 2 seeds, 0.94 court) et E2-bis (+20 pts inv, 2 seeds, 0.90-0.93 p10) — extrapolation aveugle authentique |
| « Fuite de masse composée vers INCONNU » | P2 (H-A partielle, O1 défaillant, V4 non exécuté) : p(arête) ~0.85 constant, INCONNU 0.38→0.57 (E2) / 0.24→0.41 (E2-bis) |

## Ce qui est corrigé des formulations historiques

| formulation historique | correct |
|---|---|
| « T réfuté définitivement » | réfuté **sur ce protocole et ces bancs** — le renversement V2.1 l'a établi 6 h plus tard |
| « A2 domine partout » | sur les 8 bancs V2.1 et les cellules V2.3 évaluées, vs les modèles comparés (A3, direct V2.1) — pas une preuve universelle |
| « Non-régression totale » | non-régression **±2 pts** sur les cellules mesurées (L3-lbl a reculé de 1-2 pts, publié) |
| « Sans aucune dégradation » (E1 L1-a) | sans dégradation **significative** (Q2 −0.25 pt IC contient 0) |
| « Composition réelle » (direct) | **robustesse fonctionnelle sur les interventions testées** — n'identifie pas l'algorithme interne |
| « Calibré » | NLL faible sur domaine quasi résolu — calibration complète non établie (recommandations QA S02) |
| « Invariance parfaite en profondeur » | **très forte robustesse dans les conditions évaluées** — seuls C2-b et E2-bis qualifient d'aveugle |
| « Couverture » (E2-bis initial) | **extrapolation aveugle** (B1, preuve par données) — plus fort, pas moins |
| « Doubler la part d'inversions » | **×1.8 / +20 pts** (C1) |

## Ce qui reste ouvert (enregistré, jamais exécuté sans arbitrage)

- **Plafond de fuite INCONNU** (0.38-0.41 en profond, objectif ≤0.25 échoué) :
  modification d'interface (contrainte de cohérence inter-formulations)
  suggérée par P2/audit P3 ;
- **INCONNU / mondes partiels** : sémantique posée (V2.2), jamais évaluée ;
- **Multi-relations, cycles, négation, cœférence** : hors périmètre V2.3 ;
- **3 seeds blind** : E2-bis en a 2 ; un 3ᵉ affinerait la dispersion ;
- **Coûts batch 1 texte brut** : mesurés par @ag-5 (profil C0), à consulter
  dans le manifeste pour toute décision produit.

## Coût total du projet (approximatif, GPU)

V1 (inclus) + V2 (E0-E5) + C0-C2 + V2.3 (E1+E2+E3) + P2 + E2-bis
≈ **35-40 h GPU** étalées sur 3 jours, RTX 3070 8 Go, un job à la fois.
Coût de **campagne**, pas latence de décision (une question ≈ 40-50 ms).

## Ancre de publication (formulation bornée, relecture finale §13)

> Une interface relationnelle apprise (lecteur LoRA + têtes fact-level) et
> une propagation explicite (p_{t+1} = p_t @ A) produisent une généralisation
> en profondeur très supérieure aux comparateurs directs étudiés, confirmée
> sur de nouvelles données et plusieurs seeds pour le système principal, et
> une extrapolation aveugle authentique (E2-bis 0.90-0.93 en profondeur 10
> sans jamais avoir vu de profondeur > 4). La robustesse linguistique est
> asymétrique : paraphrases parfaites, inversions récupérables par la donnée,
> fuite de masse résiduelle documentée (INCONNU 0.40 en profond). Les résultats
> sont conditionnels aux bancs synthétiques, seeds et protocoles décrits ;
> les seuils, incidents et réserves sont publiés intégralement.
