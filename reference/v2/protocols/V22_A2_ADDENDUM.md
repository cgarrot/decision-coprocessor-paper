# V22_PROTOCOL — ADDENDUM A2 (supervision distributionnelle + INCONNU)

*Complète `V22_PROTOCOL.md` (sha 6fc9d7d4, commit c40a168a) — **ne le modifie
pas**. Rédaction @ag-3, co-signature @ag-1 (registre). Préenregistré AVANT
toute implémentation de A2. Les interdits V21_PROTOCOL §0 et V22 §0 sont
reconduits intégralement.*

## Motif (pourquoi A2, et pourquoi INCONNU)

- **A1 a échoué proprement** (commit dcdcf7f9) : c_prop 0.19–0.32 vs discret
  0.56–0.81. Mécanisme identifié : la fuite non calibrée (top-1 ≈ 0.75/arête
  ⇒ masse du chemin en 0.75^k) s'accumule sur les mauvais terminaux
  absorbants. Les distributions argmax-fiables ne sont pas des distributions
  de propagation. L'audit §6.2 l'avait prévu.
- **Découverte sémantique bloquante** : `successors_from_facts`
  (`src/v2model/extractor.py`) applique « entité sans fait ⇒ terminale (-1) ».
  C'est exactement l'interdit « absence d'information ≠ terminal » (audit §5).
  A2 définit INCONNU pour corriger ce défaut : sans fait sujet ET sans fait
  terminal ⇒ `-2` (INCONNU). C'est la motivation de la classe INCONNU,
  distincte des terminaux — pas une classe « poubelle ».

## Définition A2 (une hypothèse)

Lecteur LoRA réentraîné avec supervision **distributionnelle** (transitions)
+ **propagation dans la boucle** (la chaîne p_{t+1} = p_t @ A backpropague le
CE de la réponse jusqu'aux distributions d'arêtes) + états intermédiaires
supervisés + INCONNU à sémantique définie. Un seul changement d'hypothèse vs
A1 : les distributions ne servent plus en lecture seule, elles sont
entraînées pour la propagation.

## Valeurs FIGÉES (co-signées)

1. **Espace de transition** : N successeurs + TERMINAL (index N) + INCONNU
   (index N+1). `A[i, i] += P(TERMINAL)` (self-loop : l'identité du terminal
   atteint est conservée) ; INCONNU = **sink absorbant global** (dernière
   ligne de A = one-hot sur le sink), distinct des terminaux. T = 20 pas.
2. **Pas de renormalisation silencieuse** (audit §6.2) : le CE de réponse
   porte sur l'état complet (N+1 : nœuds + sink), cible = terminal gold.
   L'inférence répond par **argmax sur les nœuds CANDIDATS** de p_T, règle A1
   inchangée, tie-break eps = 1e-3 par clé stable (labels, mandat n°4).
3. **Fact mode** : règle « conflit de faits = argmax P(sujet)·P(objet) »
   reconduite ; mention sans fait sujet ET sans fait terminal ⇒ `-2`.
4. **Augmentation INCONNU (entraînement SEULEMENT)** : 25 % des items de
   E5v2_train, 1 fait retiré + ses rappels, seed 17 fixe, déterministe. Sur
   ces items : **CE_answer et CE_states MASQUÉES** (le texte public ne
   détermine plus la réponse) ; seules les CE locales (transitions, dont
   INCONNU) s'appliquent. **Le banc 2213 est évalué SANS augmentation**
   (performance propre, pas robustesse). Aucune autre utilisation de
   l'augmentation (ni sélection, ni scellés).
5. **Pertes** : pertes lecteur reconduites à l'identique (tag 1.0, fact 1.0,
   successor/α 1.0, start 1.0) + γ·CE_answer + β·moyenne_t CE_states.
   γ = 1.0 constant ; **β = 0 si step < 200, linéaire 0→1 sur [200, 600),
   1.0 après** ; α = 1.0 ; poids INCONNU = 1.0 (aucune constante magique).
6. **Recette reconduite à l'identique** (E5v3-A) : LoRA r16/α32 q/k/v/o,
   `head_lr = 3e-4`, `lora_lr = 1e-4`, wd 0.01, warmup 5 %, clip 1.0,
   micro 8, accum 4, max_steps 1200, seed 17 ; H = mean(L14, L21) fp32
   recalculé LoRA actif ; données = E5v2_train (+augmentation §4) ;
   **init = `artifacts/bundle_final_v2/reader_lora_best.pt`** (seule la tête
   INCONNU est neuve ; le reste continue).
7. **Sélection** : banc **seed 2213** (@ag-2), primaire **c_prop** (cellule
   propagation), tie-break b (discret) puis step le plus petit,
   `eval_every = 100`. **Dépendance stricte : si le banc 2213 n'est pas posé
   avant la fin du câblage, A2 ATTEND — aucune sélection de repli sur les
   scellés, aucune exception.**
8. **Évaluation** : bancs V2.1 scellés B1–B8 avec le harnais A1 étendu
   (sink INCONNU + tie-break), évaluation pure. Grille A1 reconduite pour le
   verdict : Δ(c_prop − c_discret) ≥ **+5.0 pts** sur B3 (prof 8), apparié par
   `base_group_id`, bootstrap groupé 2000, **IC bas > 0** ; non-régression
   court B1 : c_prop ≥ c_discret − 2.0 pts. Publication systématique : Δ vs
   direct (descriptif), écart au plafond (p) = 0.95, couverture.
9. **INCONNU non évalué en A2** : mécanisme interne ; les bancs restent des
   graphes complets (l'évaluation INCONNU/chaîne cassée est un jalon
   ultérieur, sémantique déjà fixée ici).
10. **Équité** : toute revendication de bénéfice ⇒ A3 direct avec tête
    auxiliaire **ÉGALE** (mêmes annotations, mêmes cibles) ; sinon publication
    descriptive A2 vs A1/discret/solveur.
11. **Coûts/registre** : job GPU unique sous verrou ; hash de config, commit
    du code et hash du checkpoint enregistrés AVANT le run ; aucune retouche
    de seuil après coup ; diagnostics oraculaires en tables séparées.

## Preuve d'implémentation exigée (tests CPU avant tout run GPU)

- A stochastique (lignes = 1), self-loop terminal, sink absorbant ;
- **gradient de la réponse (CE) jusqu'aux logits d'arêtes à travers la
  propagation** (= ce qui distingue A2 d'A1) ;
- pas de renormalisation ; tie-break stable ;
- extractor OFF par défaut byte-identique (non-régression V2/V2.1) ;
- augmentation : retrait fait+rappels ⇒ cible -2, CE answer/states masquées,
  déterminisme seed 17.
