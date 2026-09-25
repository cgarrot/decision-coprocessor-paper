# 08 — Data generation: oracles, contracts, seals

## 1. Principles (identical in V1 and V2)

1. **Programmatic generation with exact oracles.** No LLM-generated labels. The oracle can prove the answer is unique, control difficulty, and produce exact traces.
2. **Two views of every example.** Public view (what the model sees) and private view (oracle, answer, proof/trace, depth, group id, transformation history). Serialisation has no access to private fields; tests fail if a forbidden metadata ever appears in a public input.
3. **Grouping before variation.** `group_id` is assigned before any paraphrase/permutation/counterfactual variant; all variants of a group stay in the same split. This is what makes paired statistics honest and prevents leakage across train/test.
4. **Explicit generalisation axes.** IID (new instances of known distributions) vs **depth** (train on dependencies 1–4, test on 6/8/10) vs **composition** (reserved structures/patterns).
5. **Anti-shortcut controls**, statistically tested: candidate position round-robin, opaque ids uncorrelated with the answer, distractors that are plausible but unreachable, option-order permutation counters.
6. **Independent audit.** The QA agent reimplemented V1 oracles and checked labels, leaks, duplicates and reserved structures.

## 2. V1 corpora (53,500 examples, frozen 2026-09-24 13:20)

| Partition | Size | Use |
|---|---:|---|
| Train | 30,000 | direct head and all experimental modules |
| Dev | 3,000 | checkpoint/hyperparameter selection only |
| Router-train / Router-dev | 3,000 / 1,500 | gate training and policy choice (after models frozen) |
| Calibration | 2,000 | temperature, after policy fixed |
| Test IID | 4,000 | near-distribution instances |
| Test depth | 4,000 | chains/dependencies deeper than train (d = 6/8/10) |
| Test composition | 4,000 | reserved structures/combinations |
| Pilot | 2,000 | excluded from results |

Train composition: ≈ 8,000 A + 8,000 B + 8,000 C + 6,000 D, answers balanced within families.

### Families

- **A — rule deduction.** Facts, Horn-style rules, questions with an explicit three-way semantics: *established / refuted / undetermined*. Absence of proof is not proof of negation; explicit negations are handled by the oracle; contradictions excluded or given a dedicated class. Reported difficulty: minimal proof depth + number of proof nodes (a distinct axis from prompt length).
- **B — relation tracking / pointers.** Opaque entities, chains and branches, deterministic follow-the-pointer oracle; names renewed, presentation order permuted, minimal relevant chain length controlled; no surface cue to the answer.
- **C — bounded programs and successive states.** Small language (assignments, additions, subtractions, comparisons, simple conditions, bounded values); options include plausible errors (for example a forgotten operation); dependency graph generated; relevant path length recorded; independent distractor operations to decouple prompt length from necessary dependencies; useless/cancelled instructions possible.
- **D — simple control.** Routing/classification with explicit rules and deterministic solution; guards against degradation > 1 pt on simple decisions. *Not* called multi-step reasoning.

### Audit and reserves

Independent QA: **0 label error, 0 leak, 0 intra-dataset duplicate, 0 reserved-structure violation**; candidate position round-robin exact (≤ 1 per bucket). Documented reserves: M1 (difficulty, fixed), **M2** (47→49 C variants without distractor, never fixed — data frozen), M3 (pilot↔train overlap, documented).

V1's 512-token limit amputated 23 % of `test_depth` (81 % of family-B depth-10) — a design flaw recorded as the main coverage limit.

## 3. V2 structured data: family B simplified

Purpose: isolate the executor. 16-transition budget; absorbing terminal.

Guaranteed by construction and tested (`tests/test_v2data.py`):

1. unique solution: the oracle walk equals the answer; the answer appears exactly once among candidates;
2. unique successor; no cycles; terminals = nodes without successor;
3. **≥ 3 terminals**; non-answer candidates unreachable from the start; internal candidates ≤ 1 and < 50 %;
4. **no trace leak**: no private key/marker in `input` (or `text`); the answer terminal is not the most mentioned; id order uncorrelated with trace position;
5. controlled pairs: `answer_changed` ⇒ different answer; `answer_same` ⇒ identical; same group ⇒ same pool;
6. traces: length ≤ budget+1, exact absorbing padding, loss weights summing to 1;
7. files: one JSONL line per problem + manifest with counts, isomorphism signatures, sha256.

### Pools

| Pool | Size | Depths | Nodes | Terminals | Pairs | Domain |
|---|---:|---|---:|---:|---:|---|
| E1 (overfit) | 128 | 1–3 | 9 | 3 | 0 | codes |
| E2 (held-out) | 256 | 2–4 | 12–15 | 4 | ~30 % groups | A–Z letters |
| E3_train | 768 bases (+ variants) | 2/3/4 | **13–16 band** | 4–5 | ~10 % | codes |
| E3_eval | 192 bases (+ variants) | 2/3/4 | 13–16 | 4–5 | ~30 % | codes |
| E4 (reserved) | 399 generated at run time | 6/8/10/16 | ~22 (stress 20) | 5 | pairs | codes |

Variety invariant: at most 16 exemplars per isomorphism class per pool (small structures are finite — pigeonhole), strict class disjunction reserved for E4, independent generation seeds.

## 4. V2 text data: E5 → E5v2

The public text view is a deterministic French rendering ("Le point X mène au point Y.", "Le point Z est un terminal.", "Départ : le point S.") with shuffled lines; the answer terminal is not distinguished; mention counts are controlled.

`E5` v1 was **invalidated** (template distribution predicted the answer; lexical probe solved it). It was archived as `bench-deficient`, and `E5_eval` v1 (seed 1007) was sealed forever.

`E5v2` (the sound bench) incorporates recall formulations (p = 0.30), second declarations (p = 0.25), per-option wrappers, varied distractor lengths with a post-pass guaranteeing at least one distractor as long as the answer chain, and shuffled template decks:

| Pool | Total | Bases | Decisive pairs | Paraphrases | Depths | Seed |
|---|---:|---:|---:|---:|---|---:|
| E5v2_train | 2,049 | 1,400 | 360 | 272 | 2/3/4 | 1105 |
| E5v2_dev | 411 | 280 | 80 | 55 | 2/3/4 | 1106 |
| E5v2_eval | **sealed forever** | ~280 | ~25 % | ~20 % | 2/3/4 | 1107 |

Discriminant: a trivial lexical probe (bag of words, bigrams, mention counts/positions, wrapper, index; Bernoulli naïve Bayes, stdlib only) scores 0.2179–0.2429 vs chance 0.2205 → `NEAR_CHANCE`.

Text↔structure oracle: `parse_state` recovers the private edges/terminals exactly; the walk from the start gives the answer on 100 % of lines of both pools.

## 5. V2.1 benches (sealed evaluation)

8 cells × 400 (seeds 2205–2212), described in [doc 06](06-v21-frozen-validation.md). Contract specifics: unique `example_uid`, `base_group_id` for matched variants (B5/B8 ↔ B1 by `pair.anchor`), public hash per example, `path_candidate_option_id` (intermediate path nodes as candidates, ~25 %), token length measured with the frozen Qwen3 tokenizer (≤ 512 by construction). B7 shares its anchor's exact graph by design (only options change). Disjunction guarantees: strict B1–B4 ↔ E5v2 signatures; global uniqueness of exact graphs (outside B7 matching).

## 6. V2.2 selection bench

`S-selection` (seed 2213, n = 400, 50 % depth 6/8, 15–16 nodes documented), strict anti-duplicate signatures (93 forbidden signatures, 0 intersection), per-line `selection_only` label. Used **only** for A2 checkpoint selection; all V2.1 benches remain pure evaluation.

## 7. What "sealed" means in this project

- V1 reserved test: opened **once** after pre-registration v2.1; no post-hoc metric change possible.
- `E5_eval` v1 (seed 1007): sealed forever after the bench was found defective; **0 artefacts**.
- `E5v2_eval` (seed 1107): sealed forever; **0 artefacts**; no conclusion depends on it; verified by QA.
- V2.1 benches: pure evaluation, never used for selection.
- Seed 2213: selection only for A2; never used for evaluation.

This discipline is the reason the project can publish a grey-zone result as a grey zone and an experience stop as an experience stop.
