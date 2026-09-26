# Decision Coprocessor : audit critique et relance expérimentale V2

## Statut et périmètre

Ce document est une revue des douze fichiers de compaction transmis et de la spécification originale `DECISION-COPROCESSOR-SPEC.md`. Il propose un nouveau programme expérimental. Il ne constitue ni une inspection du code exécuté, ni une reproduction des entraînements, ni une certification des prédictions brutes.

Les valeurs V1 ci-dessous sont rapportées par le dossier. Les calculs élémentaires explicitement signalés sont dérivés de ces valeurs. Les diagnostics de cause restent des hypothèses lorsqu'une intervention ne les départage pas. Les architectures V2 et les seuils de passage sont des propositions, pas des résultats.

La V1 répond à une question étroite : dans cette configuration, ce budget d'entraînement, ces représentations et ces données retenues, un correcteur récurrent a-t-il amélioré la décision ? La réponse rapportée est négative. Cela ne démontre pas l'impossibilité générale d'un coprocesseur non génératif.

**Décision recommandée : ne pas reconstruire immédiatement tout le système. Commencer par un exécuteur de transitions vérifiables sur une seule famille, puis reconnecter le langage.**

## 1. Références internes

Les références `[Dxx]` désignent les documents fournis, pas une inspection des artefacts sous-jacents.

| Référence | Document |
|---|---|
| D00 | `00-INDEX(1).md` |
| D01 | `01-CONTEXTE-QUESTION-RECHERCHE.md` |
| D02 | `02-ORGANISATION-ORCHESTRATION-AGENTS.md` |
| D03 | `03-CHRONOLOGIE-COMPLETE-P0-P7.md` |
| D04 | `04-DONNEES-GENERATION-AUDITS.md` |
| D05 | `05-MODELISATION-ENTRAINEMENTS-P2-P3.md` |
| D06 | `06-DIAGNOSTICS-P4-ERRATUM-GATE-P5.md` |
| D07 | `07-PRE-ENREGISTREMENT-P6-TEST-RESERVE.md` |
| D08 | `08-EXPORT-P7-REVIEW-CLOSURE.md` |
| D09 | `09-LIMITES-LECONS-PROCHAINES-ETAPES.md` |
| D10 | `10-INVENTAIRE-ARTEFACTS-REPRODUCTION.md` |
| D11 | `11-NOTE-VERIFICATION-MAJ.md` |
| SPEC | `DECISION-COPROCESSOR-SPEC.md`, spécification originale de 1 643 lignes |

Les références publiques S01 à S07 sont définies en section 14.

## 2. Ce que la V1 établit

### 2.1 Résultats à préserver sans les embellir

Moyennes de trois seeds, macro des familles A/B/C, selon D07 §3 :

| Mesure | B2 direct | R4 | Interprétation |
|---|---:|---:|---|
| Test IID | 48,84 % | 49,08 % | +0,24 point, gain non établi |
| Test profondeur | 34,18 % | 33,59 % | -0,59 point ; IC 95 % [-1,25 ; +0,07] |
| Test composition | 40,81 % | 40,73 % | -0,08 point, gain non établi |
| Tâche simple D, IID | 74,73 % | 74,73 % | Pas de dégradation, mais compétence simple non parfaite |
| Latence moyenne complète L512 | 46,18 ms | 50,04 ms | Surcoût mesuré sans gain de qualité |
| NLL profondeur | 1,3511 | 1,3540 | Pas d'amélioration probabiliste |

R4 ne démontre pas d'avantage sur B3/B4. R4-R1 vaut environ -0,02 point sur le test de profondeur. Les 181 corrections et 238 dégradations sont des comptes cumulés sur trois seeds ; ils ne sont pas 419 problèmes indépendants. [D07 §3]

L'intervalle publié ne soutient pas un gain pratique de +3 points pour cette configuration. Augmenter seulement le nombre de seeds n'est pas la priorité de relance.

### 2.2 Résultats d'ingénierie utiles

Le dossier rapporte des oracles réimplémentés indépendamment, des données figées, des prédictions archivées, des comparaisons appariées et groupées, des contrôles de paramètres/coût et un rechargement déterministe. Ces éléments sont à conserver. [D02 §4 ; D04 §6 ; D07 §1 ; D08 §1]

La correction de l'erratum de permutation était indispensable et a été documentée. Les réserves historiques sur les poids et scripts ont majoritairement été levées après clôture : ne pas les présenter comme encore ouvertes. [D06 §1 ; D08 §2, tableau de statut]

La présence d'un script de reproduction et un `--dry-run` réussi ne constituent pas, à eux seuls, la preuve d'un nouvel entraînement complet depuis un clone propre. Cette distinction limite la certification externe, pas nécessairement les résultats V1. [D08 §1 ; D10 §3]

## 3. Diagnostic prioritaire : le chemin de correction pouvait éviter le raisonnement

### 3.1 Le raccourci architectural existe dans la spécification

SPEC §5.6 prévoyait :

```python
r_i = CandidateAttention(query=c_i, keys=Z_t, values=Z_t)
delta_i = CorrectionHead(concat(q, c_i, r_i))
logit_i = logit_B2_i + delta_i
```

Cette architecture autorise une solution dans laquelle la tête ignore `r_i` et apprend une nouvelle correction directement depuis `q` et `c_i`. De plus, `Z0` est initialisé à partir de `q`. Un gain éventuel ne prouve donc pas que le modèle a appris à utiliser la mémoire ou les étapes supplémentaires. [SPEC §5.5-5.6]

Ce raccourci était permis par la conception initiale, pas nécessairement introduit par les agents. L'absence d'effet des ablations de mémoire et la saturation à k=1 sont compatibles avec cette explication. Elles ne prouvent pas que c'est l'unique cause. [D06 §1]

### 3.2 Interventions minimales pour la tester

Sur un nouveau jeu exploratoire :

- Comparer un correcteur `MLP(q,c)` explicitement sans mémoire à la V1.
- Supprimer les entrées directes `q,c` de la tête de correction, tout en conservant une définition claire de la question et des candidats pour le processeur.
- Comparer l'initialisation par `q` à un état initial contraint par la tâche, par exemple le pointeur de départ.
- Mesurer séparément les gradients de la lecture mémoire, du bloc récurrent, de l'initialisation et de la tête de sortie.
- Comparer les logits centrés, les marges et les distributions, pas uniquement la norme brute des logits.

Une constante ajoutée à tous les logits ne change pas le softmax. Des logits qui changent ne prouvent donc pas une amélioration ni même une modification de la distribution.

Supprimer un raccourci n'oblige pas magiquement le modèle à raisonner : cela ne fait que retirer une solution facile. L'apprentissage des transitions reste à démontrer.

## 4. Interprétations du dossier à corriger

### 4.1 « La branche H est peu utilisée » ne signifie pas « les faits ne sont pas utilisés »

`q` est le dernier état valide de Qwen et les candidats sont encodés après l'état du problème dans un modèle causal. Ces représentations peuvent déjà contenir des informations sur les faits. [SPEC §5.3-5.4 ; D05 §1]

Ablater H dans une branche en conservant les représentations contextualisées `q,c` n'enlève pas toutes les voies d'accès aux faits. La conclusion correcte est locale : la branche mémoire supplémentaire apporte peu de sensibilité dans les conditions diagnostiquées.

Vérifier aussi ce que signifie « mélanger H ». Une permutation conjointe des lignes de clés, valeurs et masque ne détruit pas forcément l'information d'une cross-attention :

```text
Attention(Q, P K, P V) = Attention(Q, K, V)
```

lorsque le masque est permuté de manière cohérente et qu'aucune autre opération ne dépend de l'indice des lignes. Cette identité ne neutralise pas le résultat d'une mise à zéro ; elle interdit seulement d'interpréter une simple permutation de mémoire comme preuve générale de non-utilisation.

Tests plus informatifs :

- Changer un fait décisif dans le texte puis recalculer tout l'encodage.
- Remplacer la mémoire par celle d'un autre problème apparié, avec mêmes question et candidats mais réponse différente.
- Préserver un fait non pertinent et modifier un fait pertinent dans deux interventions distinctes.
- Remplacer un état interne par un autre état valide et vérifier la continuation prédite.

Les ablations de branches et les interventions sur le texte répondent à des questions différentes : publier les deux.

### 4.2 Les probes ne justifient pas l'exclusion de LoRA

Les probes n'utilisent que 25 exemples par famille et certaines cibles sont très partielles. Lire la première étape d'un programme ne prouve pas que toutes les étapes et leurs relations sont accessibles au petit module. [D06 §13.3]

Il faut tester la qualité de l'extraction de plusieurs faits et états à différentes profondeurs, avec des splits groupés. Un échec de probe ne démontre pas l'absence d'information ; une réussite ne démontre pas son usage causal.

Une adaptation légère du backbone reste une ablation possible. Elle n'est ni démontrée nécessaire, ni exclue par les données.

### 4.3 Des nombres de paramètres faibles ne garantissent pas un entraînement suffisant

Le plafond principal était de 1 200 mises à jour et le batch effectif de 32 : environ 38 400 présentations, soit 1,28 passage sur 29 959 exemples retenus. Le plafond « 3 époques » n'a donc pas été atteint. Deux meilleurs checkpoints B2 se situent au dernier point évalué. [D05 §4 ; calcul dérivé]

Cela suggère de vérifier la convergence, sans prouver un sous-entraînement. Les compactions ne fournissent pas les courbes complètes train/dev permettant de trancher.

Avant d'augmenter le budget :

1. Faire surapprendre un petit ensemble fixe.
2. Vérifier une tâche à une étape sur de nouveaux exemples.
3. Tracer loss, accuracy, gradients et résultats par profondeur.
4. Seulement ensuite comparer plusieurs budgets d'entraînement, avec les mêmes possibilités de sélection pour les contrôles.

### 4.4 La perte finale seule n'impose pas une progression des états

La V1 entraîne les budgets 1, 2 et 4 sur la même réponse finale, avec CE seule. [D05 §5 ; SPEC §8.2]

Cette formulation permet une bonne correction dès le premier passage, puis sa répétition. Elle n'exige pas que `Z1`, `Z2` et `Z4` représentent des étapes différentes.

Ce n'est pas une preuve qu'une CE finale ne peut jamais apprendre une récurrence. C'est une raison de tester une supervision de transition dans ce contexte, où des solveurs fournissent déjà les états intermédiaires exacts.

### 4.5 Une baseline commune mal sélectionnée n'annule pas tous les effets du bug

La sélection de B2 utilisait initialement une métrique incorrecte, puis la même B2 a été réutilisée pour son sidecar apparié. [D05 §4]

Le delta reste interprétable conditionnellement à ces checkpoints. Cela ne prouve pas que le delta aurait été identique avec la baseline sélectionnée selon la règle correcte. La réponse du sidecar dépend de son point de départ.

En V2, une seule implémentation testée des métriques doit servir à sélectionner et à évaluer. Une comparaison indépendante sur de petits logits fabriqués à la main doit précéder tout run.

### 4.6 Autres formulations trop fortes

- « B3 égale ou dépasse R sur les trois seeds » ne correspond pas au tableau dev : R est légèrement supérieur sur deux seeds. Cela ne change pas la conclusion finale d'absence d'avantage établi. [D05 §5]
- « Le gate n'est pas en cause puisqu'il apprend sur train » n'est pas une conclusion valide. L'overfit, la rareté des transitions utiles et la qualité des features restent des explications possibles. [D06 §2]
- Un gain moyen négatif de R4 ne rend pas impossible un routage utile sur un sous-ensemble. C'est le ratio de rétention d'un gain non positif qui devient inapproprié.
- À plusieurs seuils du gate, le gain net observé est identique (+4), mais les activations vont de 47,5 % à 9,8 %. Une règle de départage par coût aurait évité de sélectionner inutilement le seuil le plus actif ; la petite taille de ces comptes interdit toutefois une conclusion robuste sur le meilleur seuil. [D06 §2]
- Les étiquettes de taxonomie telles que `chain_interrupted` doivent être distinguées d'une preuve que le modèle a effectivement exécuté puis interrompu une chaîne interne.

## 5. Trois défauts du banc d'essai à traiter avant une V2

### 5.1 La profondeur est confondue avec d'autres changements

Dans A, l'entraînement contient approximativement autant d'établis, de réfutés et d'indéterminés. Le test de profondeur contient 662/662/76 exemples. [D04 §4]

L'évaluation combine donc longueur de dépendance et changement de proportions de réponses. Ce n'est pas une fuite, mais cela limite l'attribution causale de l'échec à la profondeur.

Prévoir :

- un test profondeur pour les exemples possédant une dérivation, avec proportions contrôlées ;
- un test distinct d'indétermination et d'exceptions ;
- un test de changement de proportions explicitement étiqueté ;
- des tableaux par famille et profondeur, avec dénominateurs.

Ne pas inventer une profondeur de preuve pour les cas indéterminés.

### 5.2 Les exclusions retirent une partie essentielle de la difficulté

La règle >512 tokens a exclu 920 des 4 000 exemples de profondeur, dont 376 des 466 exemples B à profondeur 10. [D04 §8 ; D07 §3]

Appliquer les mêmes exclusions à tous les modèles protège la comparaison sur la population retenue. Cela ne rend pas cette population représentative du problème initial.

La V2 doit couvrir son domaine déclaré par construction : textes suffisamment compacts, plafond de contexte mesuré, et distribution des longueurs connue avant entraînement. Aucune troncature qui détruit silencieusement les faits. Toute abstention ou impossibilité de traiter une entrée doit être comptée dans la couverture du produit.

### 5.3 L'ordre des options reste un défaut fonctionnel majeur

Environ 39 % des décisions B2/R4 changent sous permutation des options, même après correction de la métrique. [D06 §11.1]

L'équilibre positionnel du dataset n'assure pas une invariance par instance.

Pour une invariance structurelle des candidats, leurs représentations ne doivent pas dépendre de leur position parmi les autres options. Proposition : encoder le problème sans la liste ordonnée des candidats, encoder chaque candidat séparément avec la même fonction, puis utiliser un score partagé ou un bloc de set équivariant sans encodage positionnel des options.

Ce changement a un coût et peut modifier la qualité de l'encodage ; mesurer les deux. Il ne rend pas automatiquement invariantes les permutations des faits, ni celles des instructions dont l'ordre a un sens.

## 6. Ne pas assimiler la V1 à une réplication des papiers

La V1 utilise un Qwen généraliste gelé, une tête directe apprise et un petit module post-encodage. Eos n'a pas été exécuté. Ce n'est pas encore une mesure sur un Jev entraîné puis augmenté. [D01 §4 ; D05 §6]

Le comparateur B1 utilisait un format brut commun aux variantes. Cette égalité de format facilite le contrôle mais ne constitue pas une mesure de la meilleure utilisation du modèle Qwen. Sa fiche décrit un chemin chat et un mode non-thinking explicites. Tester ce chemin comme baseline séparée, sans changer le format d'une seule variante dans une comparaison contrôlée. [S07]

LRT injecte ses latents dans un Qwen3-8B gelé qui produit ensuite la réponse ; les gradients traversent les activations du décodeur. Son module est appris par famille de tâches. Ce n'est pas le même problème que confier toute la composition à notre petite tête après un unique encodage. [S06]

Les références utiles à la relance sont plutôt des principes complémentaires : états et messages relationnels [S01], contrôle/mémoire séparés [S02], apprentissage algorithmique [S03], annotations d'états intermédiaires [S04], récurrence de petits réseaux [S05]. Aucun de ces papiers ne garantit un gain dans notre protocole.

## 7. Architecture V2 recommandée : un exécuteur de transitions, pas un correcteur libre

### 7.1 Principe

```text
Problème visible
    |
    +--> encodage du problème --> mémoire de faits M
    |
    +--> extraction de la requête --> état initial s0

Mémoire M + état st
    |
    v
Transition partagée F
    |
    v
État s(t+1)
    |
    +--> supervision d'état pendant l'entraînement
    |
    +--> nouvelle transition, si budget disponible
    |
    v
Lecture finale de l'état + candidats indépendants
    |
    v
Probabilités
```

La première version ne contient ni gate, ni plusieurs experts, ni world model, ni génération textuelle.

La séparation recherchée :

- `M` décrit les faits disponibles ;
- `s_t` décrit l'avancement du calcul ;
- `F` apprend une opération réutilisable ;
- la sortie est lue dans l'état calculé.

Éviter dans la branche de recherche une tête finale recevant directement un résumé contextualisé suffisamment riche pour ignorer entièrement le processeur. Conserver le chemin direct séparément pour la comparaison et, plus tard, pour un éventuel routage.

### 7.2 Première famille : suivi de relations

Commencer par une version simplifiée de B : plusieurs chaînes orientées, un successeur au plus par nœud, aucune boucle dans le premier pilote. La question demande le terminal atteint depuis un nœud de départ.

Exemple :

```text
A pointe vers C.
C pointe vers F.
F pointe vers D.
D est un terminal.

B pointe vers E.
E est un autre terminal.

Départ : A.
Candidats : D, E, autres terminaux distracteurs.
```

États-cibles : A, C, F, D, D...

**Précaution anti-raccourci : plusieurs terminaux doivent être présents.** Avec un unique nœud sans sortie, le modèle pourrait donner ce nœud sans suivre le départ. Les candidats doivent inclure des terminaux distracteurs et non seulement des nœuds internes facilement éliminables.

Renommer les entités par problème ; mélanger l'ordre des faits indépendants ; équilibrer les candidats ; varier le départ et modifier une arête décisive dans des paires contrôlées. Garder initialement le nombre de nœuds comparable entre profondeurs.

### 7.3 État et transition

Prototype d'état : un vecteur par entité, plus une distribution désignant le pointeur actif. Un bloc local partagé transmet des messages le long des relations et met à jour les états.

```text
m_i(t) = aggregate_j phi(h_j(t), h_i(t), relation_ji)
h_i(t+1) = update(h_i(t), m_i(t), question)
p_t = softmax(pointer_head(h(t)))
```

La formule définit une proposition de modèle, pas un algorithme dont les gains seraient établis.

Une transition limitée aux arêtes locales et une cible « pointeur après t transitions » donnent un sens testable au déroulement. Dans un module global non contraint, k itérations ne correspondent pas nécessairement à k sauts logiques.

Prévoir un état terminal absorbant : une fois le terminal atteint, le bon état reste ce terminal. Les longues chaînes sont ainsi évaluables avec un plafond commun.

### 7.4 Les cibles intermédiaires sont réservées à l'apprentissage

Départ proposé :

```text
L = CE(reponse_finale, cible_finale)
  + alpha * moyenne_t CE(etat_predit_t, etat_exact_t)
```

Choisir une valeur simple d'alpha sur un pilote et enregistrer toute modification. Ne pas empiler cinq pertes et un contrôleur de calcul dans la même expérience.

Les cibles d'état proviennent de l'oracle, mais ne doivent pas apparaître dans les entrées d'inférence. Pendant l'entraînement, un amorçage sur états exacts est possible, puis il faut apprendre et mesurer des déroulements depuis les états prédits. Rapporter séparément les résultats avec états imposés et les résultats autonomes.

La normalisation de la perte doit éviter de donner un poids disproportionné aux longues traces ou aux répétitions de l'état terminal.

### 7.5 Budget d'inférence

Ne jamais choisir le budget d'un exemple à partir de sa profondeur privée fournie par le solveur.

Avant un arrêt appris : plafond identique pour tous les exemples d'un protocole, par exemple 16 transitions, avec terminal absorbant. Un nombre d'étapes explicitement demandé dans la question est, lui, une information d'entrée légitime pour une tâche de suivi à nombre de sauts fixé.

Le coût adaptatif viendra après la preuve d'utilité, et sera mesuré end-to-end.

## 8. Séparer compréhension du texte et exécution

Trois versions doivent être étiquetées clairement.

### Version S : entrée structurée exacte, contrôle positif

Fournir les nœuds, arêtes et requête tirés des faits visibles du générateur, sans les réponses ni la trajectoire.

Cette représentation est une information privilégiée par rapport au texte brut. Le résultat doit donc être présenté comme **diagnostic d'exécuteur**, pas comme victoire sur un modèle qui doit analyser le texte.

Objectif : savoir si le petit réseau apprend les transitions et les compose sans obstacle linguistique.

### Version T : texte vers mémoire apprise

Le modèle ne reçoit que le problème visible. Qwen gelé ou un encodeur plus petit produit des représentations, puis un module apprend à extraire les relations nécessaires.

La représentation structurée devient une cible d'extraction, pas une entrée oracle. Mesurer l'extraction et l'exécution séparément :

- mémoire exacte + exécuteur appris ;
- mémoire prédite + exécuteur exact ;
- mémoire prédite + exécuteur appris ;
- modèle direct sur le même texte.

Cette factorisation localise les erreurs. Si la mémoire exacte fonctionne mais pas la mémoire prédite, modifier le lecteur plutôt que multiplier les étapes du processeur.

### Version A : adaptation limitée

Seulement si les diagnostics d'extraction le justifient : adapter une partie du backbone ou des projections par LoRA ou dégel limité. Ajouter un contrôle direct bénéficiant exactement de la même adaptation.

Les états cachés dépendant de poids modifiés ne peuvent pas être réutilisés depuis un cache pré-calculé. Profiler les activations et les gradients avant de promettre la compatibilité 8 Go.

## 9. Une alternative pratique à maintenir : le coprocesseur symbolique

Pour ces tâches synthétiques, un processeur exact existe déjà : vos solveurs. Construire aussi :

```text
Texte visible
    -> extraction de faits dans un schéma borné
    -> validateur
    -> solveur déterministe
    -> réponse ou abstention
```

Ce n'est pas une preuve de raisonnement neuronal général. C'est un système hybride dont l'exactitude dépend notamment de l'extraction et du domaine couvert. Il peut cependant être un meilleur produit.

Le solveur n'accède jamais aux champs privés du dataset. Pas de `eval` ni d'exécution libre de code fourni dans les prompts : utiliser un interpréteur explicite d'un langage limité.

Cette variante donne un usage concret au CPU, sans transferts GPU/CPU répétés de grandes mémoires latentes. Elle doit être comparée en qualité, couverture, temps complet et erreurs d'extraction.

## 10. Programme d'expériences avec vrais arrêts

Les seuils suivants sont des propositions d'ingénierie à figer avant les runs concernés, pas des prédictions de performance.

| Étape | Expérience | Critère indicatif | Si échec |
|---|---|---|---|
| E0 | Tests de contrats, masques, métriques, gradients, candidates IDs | Tous les cas manuels cohérents | Corriger, aucun benchmark principal |
| E1 | Surapprendre 128 problèmes structurés courts | >=99 % train, traces cohérentes | Auditer optimisation et expressivité |
| E2 | Transition unique sur nouveaux graphes | >=98 % sur ce domaine volontairement simple | Ne pas lancer l'extrapolation |
| E3 | Déroulement autonome à profondeurs connues 2/3/4 | États et réponses nettement au-dessus des contrôles triviaux | Distinguer accumulation d'erreurs et mauvais état |
| E4 | Profondeurs nouvelles 6/8/10, puis stress 16 | Avantage documenté des itérations utiles | Revoir transition, pas ajouter un gate |
| E5 | Connexion au texte | Extraction et exécution mesurées séparément | Modifier lecteur ou adaptation |
| E6 | Contrôles équitables et plusieurs seeds | Gain, mécanisme et coût établis | Publier résultat négatif local |
| E7 | Nouveau test réservé final | Règles gelées, aucune sélection dessus | Clôture confirmatoire |
| E8 | Gate ou emballage produit | Seulement après un expert utile | Pas une dépendance du projet de recherche |

E1/E2 ne prouvent pas la généralisation. Ils empêchent seulement de lancer une expérience de composition dont les opérations de base ne sont pas apprises.

Commencer avec une seed pendant le débogage. Passer à trois seeds quand le mécanisme fonctionne ; cinq seeds deviennent pertinentes pour une estimation finale, pas pour sauver un modèle qui ignore ses étapes.

### Matrice centrale des contrôles

| Modèle | Cible finale | Cibles intermédiaires |
|---|---|---|
| Direct/non récurrent | Oui | Non |
| Direct/non récurrent + têtes auxiliaires | Oui | Oui |
| Récurrent | Oui | Non |
| Récurrent supervisé par transitions | Oui | Oui |

Les têtes auxiliaires directes peuvent prédire des états intermédiaires pendant l'apprentissage sans être exécutées comme une chaîne à l'inférence. Leur coût d'entraînement est à compter.

Ajouter une pile non partagée de coût comparable et une baseline de continuation d'entraînement de B2. Séparer « davantage de paramètres », « davantage de supervision », « davantage d'optimisation » et « récurrence ».

Pour chaque comparaison, publier à la fois budget de données et coût réel : même nombre de mises à jour n'implique pas même nombre de FLOPs.

## 11. Mesures et tests mécanistes

### Qualité des réponses

Exactitude par famille et profondeur, moyenne macro explicitement définie, exactitude de trajectoire complète, exactitude de la transition conditionnelle à un état d'entrée correct, et exactitude du déroulement autonome.

Publier correction/dégradation par rapport au direct sur les mêmes groupes, pas seulement une accuracy globale.

### Usage causal des faits et états

Sur paires appariées :

- fait décisif modifié : les deux réponses doivent être correctes, pas seulement différentes ;
- fait distracteur modifié : stabilité de la bonne réponse ;
- candidats permutés : comparaison par identifiant stable ;
- état intermédiaire valide remplacé : continuation compatible avec cet état ;
- mémoire d'un autre problème : intervention de branche explicitement décrite.

Un état doit non seulement être décodable par un probe, mais influencer correctement la suite lorsqu'on intervient dessus. L'attention ou les probes seuls ne sont pas une preuve de raisonnement.

### Progrès avec les étapes

Mesurer k=0/1/2/4/8/16 sur les mêmes poids lorsque le protocole s'y prête. Publier les changements de réponse et de distribution, ainsi que l'avancement de l'état.

Une grande norme d'état, un delta de logits ou une attention différente ne sont pas des gains.

### Statistiques

Bootstrap apparié par groupe. L'intervalle sur la moyenne de trois seeds, obtenu en rééchantillonnant les problèmes, reste conditionnel aux seeds entraînées ; ce n'est pas une estimation complète de toutes les initialisations possibles.

Publier la dispersion entre seeds. Fixer une comparaison primaire. Identifier les nombreuses analyses secondaires comme exploratoires ou ajuster les conclusions de multiplicité.

Les tests V1 déjà vus peuvent servir d'exploration V2, à condition de le déclarer. Ils ne redeviennent pas des tests indépendants parce qu'on les renomme. Le nouveau test doit avoir des groupes/graphes distincts, des seeds de génération indépendantes et des contrôles de doublons structurels.

### Numérique et latence

Avant figement : comparaison FP32/bf16 du petit module sur les mêmes représentations, puis distinction éventuelle avec un backbone entièrement FP32. Les deux comparaisons ne mesurent pas la même chose.

Inclure tokenisation, transferts pertinents, lecture, processeur et décision. Distinguer moyenne, médiane, p95, débit et latence de module. Mesurer les variantes complètes, y compris les éventuelles étapes supplémentaires sur CPU. Utiliser rampe thermique, ordre de benchmark contrôlé et synchronisations GPU.

## 12. Exploitation de la machine

Machine rapportée : i7-11800H, 8 cœurs/16 threads, environ 29,3 GiB RAM utilisable, RTX 3070 Laptop 8 Go sous Debian 13. [D01 §9]

La V1 rapporte environ 1,9 à 2,1 GiB de pic pour les entraînements du sidecar et environ 1,2 GiB réservé dans le profil d'inférence. La limite de mémoire n'était donc pas saturée dans ces mesures. Cela ne prouve pas que le GPU était peu occupé. [D05 §5 ; D07 §3]

### Répartition proposée

GPU : encodage, petit processeur, gradients et scores.
CPU : génération des problèmes, oracles, tokenisation, préparation de lots, statistiques et solveur hybride.
RAM/SSD : cache borné des représentations réellement réutilisables.

Un seul job d'entraînement GPU. Les agents n'ont pas tous à lancer PyTorch. Prévoir une limite de threads et éviter que les workers de données saturent les mêmes cœurs que la tokenisation et les solveurs.

### Profiler avant d'offloader

Tester un microbatch plus grand si cela réduit réellement le temps par exemple. Distinguer microbatch physique et accumulation de gradients. Augmenter le contexte à 1024 n'est pas gratuit : le valider sur les longueurs réellement générées.

Ne pas copier H GPU -> CPU -> GPU à chaque transition. CPU et VRAM n'ont pas une mémoire unifiée équivalente ; remplir la RAM ne constitue pas une accélération.

### Cache de backbone gelé

Calcul théorique, hors index et autres objets :

```text
30 000 x 512 x 1024 x 2 octets = environ 29,3 GiB
30 000 x 1024 x 1024 x 2 octets = environ 58,6 GiB
```

Un cache dense complet de H ne tient donc pas confortablement dans les 32 Go de RAM.

Préférer les longueurs réelles, un cache SSD/memmap par shards, un plafond de cache RAM, ou des fenêtres/slots dont l'information est validée. Une compression apprise changeant pendant l'entraînement ne peut pas être figée en cache sans mettre à jour les dépendances.

Chaque clé de cache doit lier : révision du backbone, poids pertinents, tokenizer, sérialisation, texte, couche, dtype, masque et variante d'entrée. Une permutation ou un contrefactuel nécessitant un nouvel encodage ne doit pas réutiliser les états de l'original.

## 13. Contrat à donner au système d'agents

### Objectif

Démontrer ou réfuter qu'un petit processeur neuronal apprend une transition réutilisable, la compose à plusieurs profondeurs puis améliore une décision sur texte à coût mesuré. Ne pas optimiser le nombre de portes marquées « passées ».

### Ordre imposé

1. Lire cet audit et produire un registre distinguant observations, hypothèses et tests.
2. Préserver les artefacts V1 disponibles, sans les modifier ; noter ce qui a réellement été supprimé.
3. Construire seulement E0-E2 sur la famille relationnelle simplifiée.
4. Fournir des prédictions d'états, les tests mécanistes et une mesure de coût.
5. Autoriser E3-E5 seulement si les opérations de base sont apprises.
6. Exécuter la matrice de contrôles avant toute revendication de gain spécifique.
7. Reporter gate, calibration sophistiquée, multi-experts et export produit jusqu'à preuve d'utilité.

### Livrables minimums

```text
research_register.md
data_contract.md
experiment_registry.jsonl
configs/
src/
tests/
predictions/
metrics.json
mechanism_report.md
cost_report.md
decision_next_step.md
```

Une QA indépendante recalcule les métriques et peut bloquer le passage suivant. Les scripts d'analyse doivent être versionnés avant d'être utilisés pour sélectionner un modèle.

Ne jamais affirmer que « la mémoire est utilisée » sur la seule base d'un gradient non nul, ni que « la récurrence fonctionne » parce que le forward accepte k=4.

### Critères d'arrêt

- Pas de maîtrise d'une transition : arrêt de l'expérience de profondeur.
- Gain provenant uniquement de cibles auxiliaires également efficaces sur le direct : résultat utile, mais pas de victoire de la récurrence.
- Entrée structurée réussie, texte échoué : traiter l'extraction.
- Raisonnement exact CPU meilleur dans le domaine prévu : considérer l'hybride pour le produit.
- Gain nul à coût supérieur : ne pas développer un gate pour masquer ce résultat.
- Gain réel mais coûteux : publier la courbe coût/qualité, pas seulement le meilleur score.

## 14. Références publiques vérifiées pour cette revue

Ces travaux motivent des expériences ; leurs résultats ne sont pas transposés à la RTX 3070 ni au benchmark V1.

- **S01. Recurrent Relational Networks**, Palm, Paquet, Winther. arXiv:1711.08028. Référence de raisonnement relationnel itératif avec interactions entre entités.
- **S02. Compositional Attention Networks for Machine Reasoning**, Hudson et Manning, ICLR 2018. arXiv:1803.03067. Séparation du contrôle et de la mémoire dans des cellules de raisonnement ; évaluation visuelle CLEVR, pas un Jev linguistique.
- **S03. Neural Algorithmic Reasoning**, Veličković et Blundell, 2021. arXiv:2105.02761. Article de perspective sur l'apprentissage de calculs algorithmiques par des réseaux.
- **S04. The CLRS Algorithmic Reasoning Benchmark**, 2022. arXiv:2205.15659. Cadre fournissant entrées, sorties et états intermédiaires d'algorithmes. Les annotations ne doivent pas être confondues avec les informations disponibles en déploiement.
- **S05. Less is More: Recursive Reasoning with Tiny Networks**, Jolicoeur-Martineau, 2025. arXiv:2510.04871. TRM constitue un précédent de petit réseau récursif ; ses résultats sur puzzles ne garantissent pas l'extrapolation d'une tête post-Qwen.
- **S06. Latent Recurrent Thoughts: Recurrent Refinement of Proposed Latents for Reasoning with Frozen LLMs**, Chen et Fu, 1 septembre 2026. arXiv:2609.01117v1. Montage distinct de la V1, avec proposition et raffinement latents puis décodeur gelé.
- **S07. Fiche officielle Qwen/Qwen3-0.6B**, Hugging Face, consultée pour vérifier les modes de prompting et le mode non-thinking.

Identifiants de consultation :

```text
https://arxiv.org/abs/1711.08028
https://arxiv.org/abs/1803.03067
https://arxiv.org/abs/2105.02761
https://arxiv.org/html/2205.15659v2
https://arxiv.org/abs/2510.04871
https://arxiv.org/html/2609.01117v1
https://huggingface.co/Qwen/Qwen3-0.6B
```

## Conclusion

La V1 a construit une infrastructure de mesure et montré qu'un correcteur récurrent particulier ne donnait pas le gain recherché. Elle n'a pas établi un mécanisme de raisonnement multiétape puis découvert que ce mécanisme était inutile : le mécanisme visé n'a pas été démontré.

La V2 doit donc déplacer son premier objectif. Avant « améliorer un Jev », prouver qu'une transition est apprise, que son état évolue correctement, que sa répétition résout des dépendances supplémentaires et que ce calcul résiste aux interventions pertinentes.

Ensuite seulement, connecter ce processeur au langage et mesurer l'intérêt d'un coprocesseur de décision non génératif.
