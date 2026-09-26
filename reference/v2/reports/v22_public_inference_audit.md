# V2.2 — AUDIT DU CHEMIN D'INFÉRENCE PUBLIC A2 (C0, audit §2.1/§8.2)

**Question (audit A) : l'exécuteur neuronal S (92 802 params) intervient-il
dans l'inférence A2 ?**

**RÉPONSE : NON.** Trace du chemin public A2
(scripts/run_v22_a2_eval.py, identique au harnais de référence) :

```
texte public (state+question+options)
  → LoRA backbone (peft, mean(L14,L21))            [forward seul]
  → MemoryExtractor.extract()                       [mentions normalisées + départ déterministe]
  → mention_reps + fact_reps + fact_logits          [têtes fact-level]
  → transition_matrix_from_facts()                  [A [N+1,N+1]]
  → start_distribution(m.start) → propagate(p0, A, 20)   [p@A, torch CPU/GPU]
  → argmax sur candidats (eps 1e-3, clé stable)
```

L'exécuteur S (`runs/e4b_train/model.pt`, RelationExecutor) n'est chargé
NI invoqué dans ce chemin — il n'apparaît que dans la cellule (a)
diagnostique de V2.1 (run_v21_eval.py). **Les scores A2 s'attribuent à :
lecteur adapté (LoRA + têtes fact) + propagation matricielle explicite.**
L'exécuteur S reste la référence mécanisme structuré (E1–E4b) et l'ancre
diagnostique — pas un composant d'A2.

**Anti-fuite (audit §8.2, test exigé)** : l'inférence ne lit que
`input.{state,question,options}` + `private.graph.options` (mapping
nœud→option des CANDIDATS publics). Test C1 : randomiser les champs privés
(labels/traces/edges) SANS changer le texte public → les prédictions doivent
être inchangées (à exécuter avec l'ablation).
