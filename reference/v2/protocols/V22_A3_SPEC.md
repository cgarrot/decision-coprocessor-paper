# V22 — SPEC A3 (direct à tête auxiliaire ÉGALE) — PRÉENREGISTRÉE avant tout run

*Arbitrage QA @ag-4 17:04 (REG-76) : la publication revendique une supériorité
→ §10/amendement exigent la tête auxiliaire égale, sinon le gain mélange
architecture de propagation et supervision supplémentaire (attaque d'audit
triviale). Rédaction @ag-1, câblage @ag-3.*

## Définition (une seule variable vs le direct V2.1 : la supervision auxiliaire)

Direct LoRA (recette E5v3-A reconduite : r16/α32 qkvo, deux-lr head 3e-4 /
lora 1e-4, wd 0.01, warmup 5 %, clip 1.0, micro 8, accum 4, 1200 steps,
seed 17, init `direct_lora_best.pt` du bundle) **+ têtes auxiliaires
recevant les MÊMES cibles que A2** :

- tête relations : prédire les distributions (sujet, objet) des faits depuis
  le prompt complet (mêmes cibles fact-level que le lecteur A2) ;
- tête états : la trajectoire d'états p_t (mêmes cibles gold_path que A2,
  β = même schedule 0→[200,600)→1) ;
- pertes : CE réponse (γ=1.0) + α·CE relations (1.0) + β·CE états — les
  mêmes poids qu'A2, la même augmentation INCONNU (25 %/1 fait+rappels/
  seed 17, CE réponse+états masquées sur ces items).

## Sélection (critère primaire DE LA VOIE)

Banc 2213 SANS augmentation, primaire = **accuracy réponse du direct**,
tie-break NLL réponse puis step croissant, eval_every 100. Refus strict si
banc absent. Bancs V2.1 : évaluation pure, jamais sélection.

## Évaluation (harnais de référence @ag-1)

8 bancs scellés, mêmes métriques appariées. **Comparaison PRIMAIRE :
A2 vs A3 apparié** (Δ par base_group_id, bootstrap groupé 2000, IC 95).

## Règle de conclusion FIGÉE (préenregistrée)

| observation | conclusion autorisée |
|---|---|
| Δ(A2 − A3) > 0, IC bas > 0, ≥ 1 banc | **supériorité ARCHITECTURALE de la propagation** (revendication complète) |
| Δ(A2 − A3) ≤ 0 ou IC contient 0 | publication **descriptive** : la supervision auxiliaire, pas l'architecture, porte le gain |
| A2 et A3 saturent ~1.0 partout | **inconcluant** — déclaré tel quel (les bancs ne séparent plus les voies ; des bancs plus durs seraient requis, hors V2.2) |

Interdits V21/V22 reconduits intégralement. Coût ~1 h GPU. Après A3 :
borne oracle routeur, coûts end-to-end, rapport final V2.2.
