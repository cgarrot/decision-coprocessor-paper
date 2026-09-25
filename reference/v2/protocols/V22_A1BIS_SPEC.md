# V2.2 — SPEC A1-bis (document de traçabilité, réponse à la réserve QA n°4)

*Le hash de préenregistrement `V2.2-A1bis` (registre, commit f6460e29)
pointait `V22_A2_ADDENDUM.md` (2334c67b…) qui ne mentionne pas A1-bis. La
présente note, datée et hashée au registre, EST la spec préenregistrée
d'A1-bis (rédigée AVANT le run, extraite verbatim de l'entrée de registre).*

## A1-bis (préenregistré commit f6460e29, exécuté 14:35–14:40)

- **Motif** : trouvaille @ag-3 (14:22) — en mode fact, le head bilinéaire
  `successor_logits` (source de A dans A1) n'est jamais supervisé (top-1
  0.054 ≈ hasard) ; A1 a propagé du bruit. A1-bis teste la MÊME hypothèse
  avec la source correcte.
- **A** = `transition_matrix_from_facts()` (src/v2model/propagation.py,
  @ag-3, commit d5eba973, tests 132 passés) : A[u,v] = Σ_f P(subj_f=u)·
  P(obj_f=v) ; terminal → self-loop identitaire ; INCONNU = sink absorbant
  max(0, 1−Σ_f P(subj_f=u)) ; pas de renormalisation.
- **Lecteur figé** (bundle_final_v2, sha vérifié), ZERO entraînement,
  départ déterministe reconduit (m.start via extract()).
- **Critères (IDENTIQUES à A1)** : Δ(c_prop − c_discret) ≥ +5.0 pts sur
  B3, IC bas > 0, bootstrap groupé 2000 ; non-régression B1 ≥ −2.0 pts.
- **Évaluation** : bancs V2.1 scellés (évaluation pure, aucune sélection).
- **Résultat** : PASS — voir `runs/v22_a1bis/a1bis_metrics.json` (finish
  registre 2c47b06c).

## Provenance des artefacts A1 (après incident d'écrasement 14:37)

- `runs/v22_a1/` a été RÉGÉNÉRÉ intégralement en mode GPU gévé (14:55)
  après l'écrasement de B1 par import CPU (déclaré par QA @ag-4, REG-74) :
  **agrégats identiques aux publiés au bit près** (vérifié contre la
  référence pré-incident), B1 restauré à 0.3225 (la valeur CPU 0.3450
  accidentelle n'existe plus nulle part).
- Garde `if __name__ == "__main__"` ajoutée à TOUS les runners V2.2
  (aucune écriture `runs/` à l'import — cause racine de l'incident).
