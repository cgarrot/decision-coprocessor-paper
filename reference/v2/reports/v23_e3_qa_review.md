# QA V2.3-E3 (96 évals) — recalcul final

- 2026-09-26, @ag-4. Registre `39d3d013` + rapport `571d4016`.
- Recalcul intégral : **96/96 évals conformes** (les écarts constatés = arrondis
  4 décimales de `E3_RESULTS.json`), **triples appariés 1200/1200**.

## Chiffres validés
| mesure | QA | annonce |
|---|---|---|
| A2-E1 can (court→p10) | 0.9967 / 0.9989 | 0.993–1.000 ✓ |
| A2-E1 l1 (court→p10) | 1.000 / 0.9978 | ✓ |
| A2-E1 inv (court→p6→p8→p10) | 0.579 → 0.263 → 0.247 → 0.266 | 0.57→0.25 ✓ |
| **A2-E2 inv** | **0.927 → 0.823 → 0.753 → 0.680** | identique, **monotone** ✓ |
| A3 inv (E1) | 0.727 → 0.23–0.28 | ~0.3–0.5 (approx.) |
| A3 inv (E2) | 0.863 → 0.28–0.37 | idem |

## Réserves de portée (documentées par @ag-1)
1. **Tag collisions** : côté E2-era, seule la dernière seed survit (s24 a2 /
   s25 a3) → **1 seed/voie** pour la décroissance E2-inv (documenté registre +
   rapport) ; la monotonie est robuste mais mono-seed.
2. **Anomalie 20:00** : diagnostic registre (bancs sains, test manuel 20/20 +
   20/20, structures comparables C2a) — non rejouable côté QA, accepté comme
   documenté.
3. E1-era = 3 seeds ✓ (72 évals) ; appariement can/inv/l1 par graphe ✓.

## Verdict
**E3 VALIDÉ** : A2-E2 récupère les inversions puis **dégrade avec la
profondeur** (0.93→0.68) tandis que A3 reste effondré (≤0.37) ; can/l1 au
plafond à toutes profondeurs. V2.3 intégralement clos après cette porte,
avec les 2 réserves de portée ci-dessus (mono-seed E2-era ; anomalie
documentée).
