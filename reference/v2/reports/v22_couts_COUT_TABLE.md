# V2.2-couts — end-to-end A2 (pipeline) vs A3 (direct) — 2026-09-25

Machine : RTX 3070 Laptop 8 Go, bf16, Qwen3-0.6B rev c1899de2, sdpa, use_cache=False.
Protocole §8 / audit §7. Latences V1 INTERDITES (aucune reutilisee — tout est mesure ici).
Chemins : A2 = tok + forward + extract + mention/fact + transition + start + propagate T=20 + answer
(+ ext.tokenisation via collate) ; A3 = collate_direct_text + forward + tete reponse.
Batchs EGAUX, memes lots/ordre, warmup 2 batchs non comptes, sync CUDA autour de chaque batch.
Assert LoRA 100 % : A2 224/224 step=1200, A3 224/224 step=800. Source : runs/v22_couts/couts_metrics.json.

## B1-court (n=400)

| voie | batch | item p50 (ms) | item p95 (ms) | debit (items/s) | alloc pic (MiB) | reserved pic (MiB) | RSS pic (MiB) |
|---|---|---|---|---|---|---|---|
| A2 pipeline | 8 | 40.32 | 46.20 | 22.65 | 1472 | 1736 | 1906 |
| A3 direct | 8 | 32.65 | 38.12 | 28.98 | 1478 | 1564 | 2577 |
| A2 pipeline | 1 | 43.21 | 50.44 | 22.42 | 1219 | 1768 | 1906 |
| A3 direct | 1 | 30.78 | 39.99 | 30.27 | 1203 | 1596 | 2577 |

Ratio A2/A3 (batch8, p50) : x1.23 (+7.7 ms/item). Batch vs unitaire : A3 gagne +6 % en batch8
vs batch1 ; A2 quasi identique (extraction domine, pas le batching).

## B3-prof8 (n=400)

| voie | batch | item p50 (ms) | item p95 (ms) | debit (items/s) | alloc pic (MiB) | reserved pic (MiB) | RSS pic (MiB) |
|---|---|---|---|---|---|---|---|
| A2 pipeline | 8 | 51.59 | 55.42 | 18.66 | 1493 | 1818 | 2585 |
| A3 direct | 8 | 40.52 | 43.51 | 23.55 | 1512 | 1686 | 2618 |
| A2 pipeline | 1 | 52.22 | 59.69 | 19.19 | 1222 | 1850 | 2585 |
| A3 direct | 1 | 41.76 | 46.27 | 23.76 | 1208 | 1718 | 2618 |

Ratio A2/A3 (batch8, p50) : x1.27 (+11.1 ms/item). Profondeur : B3/B1 = x1.28 (A2), x1.24 (A3).

## Propagation p@A (N≤20, T=20) — isolee, comme exige

| mesure | ms/item |
|---|---|
| A2 B1 prop mean / p95 (dans le timed, GPU) | 0.59 / 0.72 |
| A2 B3 prop mean / p95 (dans le timed, GPU) | 0.66 / 0.80 |
| Microbench CPU B=4,N=20(+1),T=20, 200 reps | 0.187 |

Part de la propagation dans A2 : ~1.3-1.4 % — NEGLIGEABLE mais MESUREE.
Le surcout A2 (~8-11 ms) vient de l'extraction (mention/fact reps + logits + collate),
pas de la propagation.

## Memoire

Batch8 : alloc A2≈A3 a ~20 MiB pres (1472 vs 1478 B1 ; 1493 vs 1512 B3) — parite.
Reserved : A2 +~130-170 MiB vs A3 (fragmentation des allocs extracteur).
Batch1 : alloc ~1202-1222 (les deux voies), soit ~270 MiB de moins que batch8.
RSS : ~1.9 Go (phase A2 seule chargee) a ~2.6 Go (phase A3). Un seul modele charge a la fois.

## Multi-questions / amortissement memoire

NON MESURE (note comme mesure future) : le harnais encode chaque exemple independamment,
sans cache inter-questions ; un chiffre d'amortissement exigerait un encodage partage
explicite offert aux DEUX voies a egalite — non trivial, hors scope du run demande.

## Lecture

A2 paie +23-27 % de latence (~+8 ms B1, +11 ms B3) pour +3.25 pts B1 et +50-75 pts
en profondeur (verdict A3-eval 8/8) : le cout est petit devant l'ecart de qualite,
et la propagation elle-meme est gratuite (~0.6 ms). Le direct reste le plus rapide
partout — aucun argument latence ne renverse la conclusion architecturale.
