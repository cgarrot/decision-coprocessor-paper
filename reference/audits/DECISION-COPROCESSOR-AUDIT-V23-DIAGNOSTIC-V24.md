# Revue V2.3 : préserver le résultat et diagnostiquer la limite croisée avant V2.4

**Date : 26 septembre 2026.**  
**Statut : revue documentaire et propositions expérimentales non exécutées.**  
**Matériel conservé : Debian, i7 11e génération, 32 Go de RAM, RTX 3070 Laptop 8 Go.**

## 0. Décision recommandée

Conserver A2 et les acquis C0-C2. Conserver également le résultat négatif local E1 sur les inversions et la récupération E2 : ils sont tous deux informatifs.

Avant un nouvel entraînement :
1. restaurer les évaluations E3 perdues à partir des checkpoints déjà entraînés ;
2. préciser le rôle de l'adaptateur public étendu aux inversions ;
3. distinguer erreurs relationnelles locales, effet de contexte et sensibilité de la propagation.

Ne pas ouvrir simultanément « inversions longues » et « mondes partiels ». La première branche change la distribution d'entraînement ; la seconde change le contrat sémantique de la tâche. Les mélanger empêcherait d'attribuer un gain ou une régression.

Le résultat C0-C2 n'est pas conditionné à la réussite de cette nouvelle recherche. Une publication technique bornée reste possible sans attendre une capacité de raisonnement universelle.

### Portée de la revue

Les sources principales sont les huit fichiers du dossier DELTA 3, couvrant le 26 septembre de 11:16 à 21:10. Ce sont des comptes rendus. Le dépôt exécutable, les checkpoints, les sorties locales et les prédictions brutes ne sont pas inspectés ici.

Les scores cités sont **rapportés par le dossier**. Les différences explicitement calculées le sont depuis des valeurs publiées arrondies. Aucun intervalle statistique n'a été recalculé.

Notation :
- **Dossier** : observation ou conclusion des fichiers fournis.
- **Analyse** : interprétation ou déduction proposée par cette revue.
- **À vérifier** : information absente des compactions.
- **Expérience proposée** : procédure nouvelle, sans résultat annoncé.

Les références D00-D07 sont définies en fin de document. Les trois références externes S01-S03 servent uniquement de contexte méthodologique.

## 1. Ce que V2.3 apporte réellement

### 1.1 E1 : robustesse sélective à poids figés

Le dossier rapporte :
- L1-a : 1,000 pour les trois checkpoints A2 ; le parser couvre également ces paraphrases.
- L2-inv : 0,545 pour A2, contre environ 0,72 pour A3.
- L3-lbl : variations lexicales peu coûteuses dans les cellules évaluées.
- L3-adv : 0,998 à 1,000 pour A2 dans le lot évalué.

Source : D02 §2 et §4.

Le renversement local A3 > A2 doit être conservé. Il indique que la voie structurée n'est pas automatiquement plus robuste à toute variation linguistique.

La syntaxe inversée modifie l'ordre de surface, pas l'orientation réelle de l'arête lorsque le rendu préserve le sens :

```text
A pointe vers B.
B est pointé par A.
```

Ces deux formulations expriment A -> B.

À l'inverse :

```text
A est pointé par B.
```

exprime B -> A. Confondre ces deux transformations dans une augmentation créerait des cibles incompatibles.

### 1.2 E2 : récupération forte, mais pas universelle

Mixture publiée : 30 % canonique, 45 % L1, 25 % L2. Deux entraînements A2, s22/s24, et deux A3, s23/s25. « Quatre seeds » signifie ici quatre entraînements au total, pas quatre par architecture. Source : D03 §1.

A2 atteint 0,9375 et 0,9400 sur L2-inv, soit des gains calculés de 39,25 et 39,50 points par rapport à 0,545. A3 atteint 0,8700 et 0,8675. Le dossier annonce des deltas A2-A3 positifs dans les 16 comparaisons cellule/paire. Source : D03 §2.

Conclusion soutenue :
> La configuration réparée est capable d'apprendre ces formulations à courte profondeur avec la mixture testée.

Conclusion trop large :
> Toutes les limites structurelles de l'interface sont exclues.

La tête produit toujours une relation par unité et les phrases à plusieurs relations sont explicitement hors E1. Cette limite demeure distincte de la capacité à apprendre une orientation inversée. Source : D02 §5.

La récupération après augmentation ne démontre pas non plus une généralisation à toute syntaxe hors templates. Il faut connaître les formes vues pendant l'entraînement et les formes réservées avant de revendiquer cette propriété.

### 1.3 E3 : résultat principal et limite de réplication

| Rendu pour A2-E2 | Court | Profondeur 6 | Profondeur 8 | Profondeur 10 |
|---|---:|---:|---:|---:|
| Canonique | 0,993 | 1,000 | 0,993 | 0,993 |
| L1 | 1,000 | 0,993 | 0,997 | 1,000 |
| L2-inv | 0,927 | 0,823 | 0,753 | 0,680 |

Source : D04 §3.

La pénalité de l'inversion face au canonique vaut, à partir des valeurs arrondies :
- court : 6,6 points ;
- profondeur 10 : 31,3 points ;
- différence de ces deux pénalités : 24,7 points.

Ce contraste descriptif soutient une interaction entre les conditions évaluées. Il ne constitue ni une décomposition causale, ni un test statistique d'interaction recalculé par cet audit.

**Réserve essentielle :** les sorties E3 de s22/s23 ont été écrasées par celles de s24/s25 selon le rapport. La courbe E2 ci-dessus repose donc sur **un checkpoint par voie dans l'archive finale**. La monotonie des quatre valeurs est observée, pas encore répliquée entre seeds E2. Source : D04 §4.

## 2. Priorité P0 : récupérer les évaluations, pas refaire les entraînements

### 2.1 Pourquoi c'est la réparation au meilleur rapport information/coût

D06 recense encore les répertoires d'entraînement s22/s24 et s23/s25. La présence dans un inventaire n'est pas une preuve de disponibilité des poids : vérifier les fichiers et leurs hashes.

Si les checkpoints sont intacts, aucune nouvelle optimisation n'est nécessaire. Il suffit de rejouer les deux checkpoints dont les évaluations manquent sur les douze cellules E3.

Cela représente **24 cellules checkpoint × benchmark** à restaurer sous cette hypothèse. Ce calcul doit être confirmé par un manifeste, pas déduit uniquement d'un nombre de fichiers.

Ne pas entraîner une « seed de remplacement » en prétendant restaurer la même expérience. Si un poids a réellement été perdu, déclarer la perte et identifier le nouveau run comme une réplication.

### 2.2 Comprendre les comptes 120 et 96

Une explication compatible avec les comptes est :
- 6 checkpoints E1 × 12 cellules = 72 ;
- 4 checkpoints E2 × 12 cellules = 48 ;
- total attendu = 120 ;
- deux checkpoints E2 conservés × 12 = 24 ;
- 72 + 24 = 96 résultats conservés.

C'est une **reconstruction à vérifier**. Le dossier ne fournit pas le manifeste exhaustif dans les pièces jointes.

« 96/96 conformes » établit au mieux que les 96 résultats examinés sont conformes à leur référence. Cela n'établit pas la complétude d'un plan qui attendait 120 cellules.

La QA doit comparer l'ensemble des identités attendues à l'ensemble réellement présent, et pas seulement contrôler les fichiers trouvés.

### 2.3 Bloquer structurellement les écrasements

Le dossier documente trois collisions ainsi que des correctifs remplacés pendant l'exécution. Source : D05 §2. Le schéma lisible `era-seed-mode-cellule` est utile, mais insuffisant si les écritures finales restent silencieusement remplaçables.

Contrat recommandé :
- identité d'évaluation issue du checkpoint, des données, du code, de la configuration d'inférence et de l'adaptateur ;
- répertoire créé exclusivement ; refuser de réutiliser une identité avec un contenu différent ;
- une tentative de rejeu reçoit un identifiant de tentative distinct ;
- écriture dans un emplacement propre à la tentative, validation, puis publication atomique ;
- vérification des identifiants d'exemples, de leur unicité et de l'identité du checkpoint dans chaque résultat ;
- index de release indiquant quel essai est autoritaire et lequel est rejeté.

Aucun nettoyage ne doit supprimer l'historique au profit du dernier essai.

Exemple de manifeste, schématique :

```json
{
  "schema_version": 1,
  "evaluation_identity": {
    "checkpoint_sha256": "<hash>",
    "dataset_sha256": "<hash>",
    "code_commit": "<commit>",
    "public_adapter_sha256": "<hash>",
    "inference_config_sha256": "<hash>",
    "environment_lock_sha256": "<hash>",
    "model_family": "A2",
    "training_seed": 22,
    "cell": "L2-inv-depth10"
  },
  "attempt_id": "<identifiant-unique>",
  "expected_examples": "<nombre-du-manifeste>",
  "observed_examples": "<nombre-verifie>",
  "status": "complete"
}
```

Tests de régression minimaux : même seed avec modes différents ; même modèle avec seeds différentes ; même cellule avec checkpoints différents ; tentative d'écrasement ; cellule manquante ; exemples dupliqués malgré un nombre de lignes correct.

`grep` est un contrôle de présence de texte, pas une preuve du comportement de la fonction active. Ajouter des tests appelant effectivement les fonctions importées, puis enregistrer le chemin du module exécuté.

Pour le travail multi-agent, figer le code consommé par un run. Une branche ou un worktree de travail ne doit pas pouvoir changer sous un processus déjà lancé. Un seul agent possède le lanceur et la publication des résultats ; les autres proposent des modifications relues avant intégration.

## 3. Clarifier l'adaptateur étendu aux inversions

### 3.1 Ce que dit le dossier

E1-L2 était initialement impossible à évaluer pour A2 car `parse_state_v2`, appelée via `targets_from_problem`, refusait les formes inversées. L'adaptateur de collation publique a été étendu à huit formes. `P_eval` est resté figé. Après correction, A2 reste à 0,545. Source : D02 §3-4.

Ce n'est pas, en soi, une preuve de fuite d'étiquette ou une invalidation des scores. Un parseur public peut légitimement préparer les entrées ou calculer des cibles d'évaluation.

En revanche, « poids figés » ne signifie pas « système entier inchangé » lorsque son adaptateur a été modifié. Nommer la version d'adaptateur dans toutes les comparaisons E1.

### 3.2 La question non résolue par le compte rendu

Quelles sorties de `parse_state_v2` atteignent :
- les seuls labels et métriques ;
- la tokenisation et les frontières d'unités ;
- les spans et masques fournis au lecteur ;
- les rôles source/destination ;
- la matrice de transition ou le readout final ?

Le nom d'une fonction ne suffit pas à trancher. Produire la chaîne de dépendances depuis le texte public jusqu'à la réponse.

Un test utile est un point d'entrée d'inférence autonome qui accepte uniquement `state`, `question` et `options` publiques, sans fonction de targets ni objet de vérité terrain. Les cibles seront construites ailleurs pour le calcul des métriques.

Cela ne demande pas de réexécuter toute l'ancienne anti-fuite sans raison : le contrôle porte sur **le chemin modifié par l'extension aux inversions**.

### 3.3 Comparateur parser : garder l'histoire et ajouter la bonne cellule

Si le parser étendu reconstruit déjà les arêtes orientées depuis le texte, tester sa sortie avec le solveur exact comme **nouvelle baseline versionnée**. Ne pas annoncer son score avant mesure.

Conserver en parallèle `P_eval` ancien : son échec montre la limite de sa grammaire figée.

Si l'adaptateur ne fournit pas les relations, mais seulement les unités textuelles, ne pas prétendre qu'il résout déjà la tâche. Dans les deux cas, déclarer le travail effectué par les règles.

La bonne conclusion n'est pas automatiquement « le neuronal dépasse tout parsing », mais « la chaîne complète versionnée conserve telle performance sur telles formulations ».

## 4. La baisse 0,927 -> 0,680 ne désigne pas encore sa cause

La propagation explicite ne reçoit pas directement la syntaxe : elle reçoit une représentation issue de la lecture. Si deux textes donnent le même état initial, la même matrice alignée, les mêmes règles d'arrêt et le même readout, un calcul déterministe doit donner le même résultat.

**Déduction :** une différence canonique/inversé doit passer par un de ces éléments ou par le pipeline qui les produit. Elle n'implique pas immédiatement une incapacité de l'opérateur à appliquer dix transitions.

### Hypothèse H1 : erreurs locales qui s'accumulent

Illustration mathématique, **pas une mesure du projet** : si chacune de dix relations nécessaires était correcte avec probabilité 0,96, indépendamment des autres, la probabilité que toutes le soient serait `0.96**10 = 0.6648`.

La proximité éventuelle avec 0,680 ne prouve rien : l'indépendance, le taux local, le caractère nécessaire de chaque relation et le lien avec une décision soft ne sont pas établis. Ne pas convertir un score final en « exactitude par saut » observée.

Mesure requise : qualité des relations du chemin utile, distribution des erreurs, dépendance entre erreurs et première étape de divergence.

### Hypothèse H2 : la lecture se dégrade dans un contexte plus chargé

Les exemples profonds peuvent aussi contenir davantage de nœuds, de faits, de tokens, de formulations inversées ou de positions tardives. Le dossier ne fournit pas les distributions permettant de séparer ces facteurs.

Une relation simple pourrait être bien lue isolément mais mal lue dans un long texte. Ce serait une limite du lecteur ou de ses représentations contextualisées, pas nécessairement de l'enchaînement.

### Hypothèse H3 : perte de masse, mauvaise terminaison ou sensibilité du décodage

Un successeur correct peut rester top-1 tout en recevant trop peu de masse. Des transitions parasites, des erreurs de terminal ou un horizon inadapté peuvent modifier le résultat après répétition.

Mesurer la masse sur le bon état, la masse inconnue, la masse sur les autres terminaux et l'effet du budget. Ne pas confondre stabilité de l'argmax local et fiabilité de la distribution propagée.

### Hypothèse H4 : représentation ou évaluation incorrecte

Des mappings, masks, spans ou sorties mal associés peuvent produire une dégradation sans erreur de compréhension. Les incidents déjà trouvés justifient des contrôles ciblés, pas l'affirmation que tout résultat gênant serait un bug.

## 5. Diagnostic proposé sans réentraîner

### 5.1 Comparaison de représentations appariées

Sur les triples existants et une petite série de diagnostic neuve, pour chaque graphe :
- aligner les entités par identifiant sémantique local avant toute comparaison ;
- extraire la matrice canonique et la matrice inversée ;
- distinguer les lignes utiles, les distracteurs et les terminaux ;
- enregistrer les scores locaux, rangs des bonnes relations et confusions d'orientation ;
- tracer `p_t` avant renormalisation conditionnelle sur les seuls candidats.

L'alignement de vérité terrain est autorisé pour l'analyse. Il ne doit pas être utilisé comme information cachée par le forward de déploiement.

### 5.2 Interventions oraculaires uniquement diagnostiques

Comparer la réponse obtenue après correction :
- des seules relations utiles ;
- des seules relations hors chemin ;
- du seul départ ;
- des seuls terminaux ;
- de toute la matrice.

Garder les conventions d'horizon, de candidats et de normalisation identiques. Une matrice exacte qui ne réussit pas dans cette cellule impose de vérifier le pipeline avant d'entraîner.

Les scores réparés doivent être nommés « oracle diagnostic » et séparés des performances autonomes. Ils mesurent ce qu'expliquerait une correction donnée, pas une capacité produit.

### 5.3 Distinguer profondeur, inversions et contexte

Notations proposées :
- `d` : profondeur logique jusqu'au terminal ;
- `m` : nombre de faits exprimés à l'envers sur le chemin utile ;
- `u` : nombre d'inversions hors chemin ;
- `N` : nombre total de faits/nœuds ;
- `L` : longueur tokenisée ;
- `h` : horizon de propagation choisi par la politique publique.

Construire un petit diagnostic contrôlé, pas une grille exhaustive coûteuse :
1. même graphe et même question, faire varier `m` : zéro, une inversion, plusieurs, toutes ;
2. déplacer l'unique inversion au début, au milieu, à la fin du chemin ;
3. à chemin fixé, transformer seulement les distracteurs ;
4. à profondeur courte fixée, augmenter le contexte ;
5. à contexte fixé, changer publiquement le départ pour obtenir différentes profondeurs.

Respecter le domaine actuel, la capacité en nœuds et le collate réel. Un départ différent peut conduire au même terminal ; équilibrer les cas entre graphes et réponses afin d'éviter qu'un terminal unique résolve tout le diagnostic.

Conserver des variantes à texte plus long : contrôler la longueur ne signifie pas éliminer après coup les cas qui font perdre A2. Définir les buckets et exclusions avant calcul.

### 5.4 Traces prioritaires

Rapporter :
- exactitude locale source/destination ;
- score de la bonne relation et marge avec la relation inversée ;
- exactitude de trajectoire autonome ;
- premier rang où la masse quitte le chemin correct ;
- différence de distribution finale entre rendus alignés ;
- masse INCONNU et hors candidats ;
- couverture, longueur, taux d'exclusion ;
- résultats par forme inversée et par seed.

Aucune mesure seule ne certifie un mécanisme. Leur combinaison doit distinguer les hypothèses H1-H4.

## 6. Une piste d'entraînement plus ciblée que « ajouter des exemples longs »

**Proposition nouvelle, non évaluée : apprendre explicitement une représentation relationnelle cohérente entre deux formulations équivalentes.**

Exemple :

```text
x_can : A pointe vers B.
x_inv : B est pointé par A.
cible relationnelle : A -> B
```

La relation attendue est identique. En revanche, le modèle ne doit pas être invariant à `A est pointé par B`, qui exprime la relation inverse.

### 6.1 Première étape : vérifier les cibles locales existantes

Le dossier indique déjà une supervision relationnelle. Ne pas ajouter aveuglément une deuxième perte identique.

Vérifier si les cibles :
- supervisent bien l'orientation, pas seulement les entités présentes ;
- sont alignées sur la même représentation entre versions ;
- couvrent équitablement les huit formulations ;
- sont appliquées au chemin utile comme aux autres faits pertinents ;
- restent correctes sous permutation et sous rendu à la volée.

Examiner le nombre réel de présentations de chaque construction, pas seulement la mixture nominale 30/45/25.

### 6.2 Variante de cohérence appariée

Sur une interface relationnelle alignée, une recette candidate est :

```text
L = L_reponse_existante
  + lambda * L_relations_supervisees
  + mu * divergence(P_rel(x_can), P_rel(x_inv))
```

La divergence peut être une Jensen-Shannon sur les distributions locales normalisées. Choisir l'espace de sortie avant le run. Ne pas rapprocher arbitrairement tous les états cachés : deux syntaxes différentes n'ont pas à partager toutes leurs représentations.

Garder les cibles supervisées : une cohérence seule peut être obtenue en donnant systématiquement la même mauvaise réponse, voire une distribution uniforme.

Les paires servent à l'entraînement. L'inférence reçoit un seul texte, conserve le même nombre de passages et le même opérateur. Un avantage éventuel doit être mesuré ; aucun gain n'est garanti.

### 6.3 Contrôles nécessaires

Comparer à :
- poursuite de la recette E2 ordinaire au même budget de mises à jour ;
- mêmes exemples appariés sans terme de cohérence ;
- mêmes exemples avec le terme de cohérence.

C'est le contrôle « paires sans cohérence » qui sépare l'effet de l'objectif de celui d'un plus grand nombre d'expositions.

A3 doit bénéficier des mêmes rendus et cibles auxiliaires dans la comparaison prédictive. Il peut recevoir la même contrainte sur ses têtes auxiliaires ; l'impossibilité de comparer un module absent doit être décrite, pas compensée avec des scores inventés.

Commencer par un pilote de développement borné. Répliquer seulement si un signal utile apparaît.

### 6.4 Variante sensible au contexte

Si H2 est soutenue, entraîner des faits inversés dans des contextes longs mais avec une requête courte est une autre expérience. Elle expose le lecteur à la charge contextuelle sans nécessairement superviser une trajectoire longue.

Il faut cependant l'étiqueter correctement : généralisation en nombre de sauts et généralisation en longueur de contexte ne sont pas la même chose. La sélection doit respecter l'objectif annoncé.

Une lecture locale indépendante par fait est également possible, mais change l'architecture et le batching. Elle n'est pas recommandée avant que le diagnostic montre que le contexte global est la cause pertinente.

## 7. E2-bis reste possible, avec une autre portée scientifique

La proposition du dossier, entraîner sur des inversions à profondeurs variées, est raisonnable **pour améliorer le domaine d'utilisation**. Source : D05 §6.

Elle n'est pas automatiquement l'expérience la plus informative pour expliquer l'échec croisé.

Si l'entraînement comprend des chaînes inversées de profondeur 10, une réussite sur de nouvelles chaînes de profondeur 10 mesure la généralisation à de nouvelles instances. Ce n'est plus l'extrapolation à cette profondeur.

Deux voies à nommer séparément :
- **voie mécaniste** : conserver des trajectoires d'entraînement courtes, travailler la lecture et sa cohérence, puis tester plus long ;
- **voie opérationnelle E2-bis** : élargir les profondeurs d'entraînement, déclarer cette exposition, puis choisir un test indépendant correspondant.

Même pour la voie opérationnelle, contrôler la sélection, les rendus, les budgets et les annotations. Ne pas attribuer à la seule profondeur un gain dû à un plus grand nombre total de tokens vus.

Ne pas changer en même temps profondeur, loss, lecteur et sémantique INCONNU. Une seule modification principale par comparaison.

## 8. Données, sélection et statistiques : points à préserver

Les comparaisons E1 canonique/variante et E3 triples utilisent des graphes appariés. Les variantes doivent rester dans le même groupe statistique. Source : D02 §1 ; D04 §1.

À clarifier dans les artefacts, sans accusation de fuite :
- E2 a-t-il été sélectionné sur un jeu neuf distinct des 400 cas qui avaient déclenché son développement ?
- quels checkpoints d'initialisation et quelles étapes cumulées ont été utilisés ?
- la mixture change-t-elle par exemple, par époque ou à chaque présentation ?
- quelles constructions sont inédites à l'évaluation, plutôt que seulement de nouvelles entités ?
- quels intervalles et marges supportent les conclusions de non-régression ?

Le résumé ne permet pas de répondre à tout. Conserver les comptes rendus comme tels et compléter depuis les artefacts.

Un delta positif dans 16 cellules n'est pas, à lui seul, une garantie de significativité ni 16 expériences indépendantes. La mention « aucune régression significative » ne démontre pas une non-infériorité à une marge pratique fixée. Les reculs de 1,2 et 2,2 points sur L3-lbl doivent rester visibles.

Les points E3 sont arrondis. Ne pas reconstruire des nombres exacts d'erreurs ou des intervalles depuis ces seuls décimaux.

Le prochain protocole peut définir une interaction descriptive principale :

```text
I = [acc_can(profond) - acc_inv(profond)]
  - [acc_can(court)   - acc_inv(court)]
```

Calculer son intervalle depuis les prédictions groupées et les cellules préfixées. Rapporter séparément la dispersion entre seeds, sans assimiler une nouvelle seed de bootstrap à un nouvel entraînement.

## 9. Corrections de formulation, sans effacer les résultats

| Formulation du dossier | Limite | Formulation proposée |
|---|---|---|
| « Invariance parfaite », « imperméable » | Scores finis, parfois 0,993 ; domaine restreint | Très forte robustesse sur les variantes et profondeurs évaluées |
| « A3 ≤ 0,37 partout en profondeur » | Tableau E3 : maximum 0,50 à prof6 et 0,40 à prof8 | Rapporter la cellule et le checkpoint ; conserver les plages exactes |
| Robustesse des pièges lexicaux et du noyage « à toutes profondeurs » | E3 ne croise que can/L1/L2-inv | L3-lbl et L3-adv robustes sur leurs cellules E1/E2 ; extension profonde non documentée |
| « Quatre seeds » | Deux A2, deux A3 en E2 ; un par voie conservé en E3 | Publier les effectifs par modèle et par étape |
| « Gain spécifique à la propagation » après E2 | A2 et A3 restent des systèmes entraînés différemment | A2-E2 dépasse A3-E2 ; C1 était l'ablation dédiée de l'ancienne configuration |
| « L'échec n'était pas structurel » | La recette réparée apprend ces formes, pas toutes les constructions | Pas d'impossibilité de représenter/apprendre les inversions courtes évaluées dans cette configuration |
| « La seule vraie limite » | Beaucoup de domaines explicitement hors périmètre | Limite principale mise en évidence dans les axes explorés |
| ≈9 h GPU comme performance produit | Coût total de campagne, pas latence d'une décision | Temps de campagne ; mesure d'inférence séparée |

Sources : D03 §3-4 ; D04 §3-5 ; D05 §3-5.

La plage A3 contredisant « ≤0,37 » ne change pas la supériorité observée d'A2 dans les cellules longues publiées. Il faut corriger la phrase, pas reconstruire une explication favorable.

Les anciennes réserves Brier/tie-break/deltas hard-soft sont explicitement corrigées dans D06, commit `c04c679e`. Ne pas les présenter comme toujours ouvertes en recopiant les anciens audits.

## 10. Matériel et organisation du prochain cycle

La machine a exécuté la campagne ; D05 rapporte environ neuf heures GPU au total. Ce nombre ne garantit ni une latence d'inférence spécifique, ni la consommation d'une nouvelle loss appariée.

Ordre économique :
1. réévaluations et diagnostics des poids existants ;
2. diagnostic local sur un sous-ensemble déterministe, puis couverture complète du constat utile ;
3. un seul pilote d'entraînement ciblé ;
4. réplication si ce pilote justifie la dépense.

CPU : solveurs, oracles diagnostiques, génération, statistiques, vérifications d'identité. GPU : encodage et apprentissage.

Avec des paires canonique/inversé, deux forward avec gradients peuvent augmenter la mémoire. Mesurer avant de doubler le batch. Une variante à branche canonique figée sans gradient peut limiter le coût, mais devient une forme de distillation distincte : ne pas la présenter comme identique à une divergence symétrique à deux branches entraînées.

Les représentations d'un lecteur figé peuvent être cachées ; invalider le cache si ses poids, tokenizer, adaptateur, sérialisation ou précision changent.

Conserver la mesure end-to-end existante et la refaire seulement si le chemin d'inférence change. Une modification exclusivement de loss peut garder le même calcul d'inférence, mais cette propriété doit être vérifiée sur le code effectif.

## 11. Séquence de reprise proposée aux agents

### J0 : artefacts et limites

Produire :
- `v23_e3_expected_manifest.json` ;
- `v23_e3_observed_manifest.json` ;
- `v23_e3_restored_results.json` ;
- `v23_adapter_flow.md` ;
- `v23_scope_addendum.md`.

La publication ne doit plus réduire silencieusement le nombre de seeds attendues. Une cellule absente rend le tableau explicitement incomplet jusqu'au rejeu ou à une modification de protocole documentée.

### J1 : diagnostic causal borné

Produire un rapport séparant H1-H4 à l'aide des représentations alignées, des interventions oraculaires diagnostiques et du petit plan d,m,u,N,L.

Aucun entraînement requis. Aucun score oracle dans la table produit.

### J2 : choisir une seule modification

- Localisation syntaxique mal apprise : augmenter les exemples locaux discriminants ou tester la cohérence appariée.
- Lecture sensible au contexte : tester l'exposition contextuelle sans modifier simultanément le raisonnement.
- Masse mal propagée : examiner terminaison, normalisation, horizon, calibration ; une température change aussi les prédictions et demande une sélection propre.
- Pipeline incorrect : corriger puis rejouer les checkpoints, sans masquer l'ancienne version.
- Diagnostic non tranché : publier la limite sans inventer une cause.

E2-bis long reste une décision d'élargissement opérationnel, pas un remède présenté comme déjà validé.

### J3 : confirmation et arrêt

Après sélection de la modification sur développement, utiliser de nouvelles instances et des cellules préfixées. Publier le résultat même si la modification échoue.

La réussite C0-C2 et la carte V2.3 peuvent être publiées sans attendre J3. INCONNU, multi-relations, cycles, coréférence et world model restent des branches distinctes.

## 12. Prompt prêt à transmettre à l'orchestrateur

```text
Reprendre Decision Coprocessor après la clôture V2.3.
Ne pas raser le projet et ne pas lancer immédiatement E2-bis + INCONNU.

Le résultat positif A2 et la limite croisée sont conservés. La mission immédiate
est de rendre les évaluations E3 complètes et de localiser la cause de cette limite.

1. Geler code, poids, données, adaptateurs et prédictions de la release actuelle.
   Construire la matrice exhaustive des évaluations attendues.
   Vérifier si les checkpoints s22/s23 existent encore et, si oui, rejouer leurs
   douze cellules chacun. Aucun réentraînement pour remplacer une évaluation.
   Archiver les tentatives distinctes sans écrasement.

2. Introduire l'identité d'évaluation fondée sur hashes et le refus d'écrasement.
   Ajouter des tests de collision, de cellule manquante et de mauvais checkpoint.
   Contrôler le comportement importé, pas seulement la présence d'un correctif par grep.

3. Tracer le rôle exact de parse_state_v2 et targets_from_problem :
   cibles seules, segmentation, spans, rôles, masks, ou matrice d'inférence.
   Vérifier le chemin public modifié par les huit formes inversées.
   Si le parser étendu fournit déjà un graphe exploitable, ajouter sa sortie avec
   solveur exact comme nouvelle baseline versionnée. Ne pas inventer son score.

4. Sur des textes canoniques/inversés du même graphe, exporter représentations
   relationnelles alignées, distributions locales et trajectoires.
   Séparer profondeur logique, nombre d'inversions utiles, inversions distractrices,
   longueur du contexte et horizon de propagation.
   Utiliser les corrections oracle uniquement comme diagnostics privilégiés.

5. Choisir une seule expérience en fonction du diagnostic :
   supervision locale mieux contrôlée, cohérence entre formulations équivalentes,
   exposition au contexte long, ou élargissement opérationnel aux profondeurs longues.
   Comparer au même budget et mêmes données sans la modification.
   A3 conserve des avantages de données et de supervision comparables.

6. Toute expérimentation exposant aux profondeurs longues doit renoncer à qualifier
   ces mêmes profondeurs d'extrapolation aveugle. Train, sélection et test sont décrits
   séparément. E2/E3 existants deviennent du développement si leurs résultats orientent
   la nouvelle recette. Confirmation sur de nouvelles instances après figement.

7. Corriger les formulations : pas d'invariance universelle, pas de L3 validé en
   profondeur sans cellule correspondante, pas de quatre seeds par voie, pas de
   garantie de non-régression tirée d'une simple absence de significativité.

Livrer un addendum sourcé et une décision bornée. Ne pas créer une nouvelle phase
de recherche uniquement pour prolonger le projet. Les résultats négatifs sont publiés.
```

## 13. Références et provenance

### Dossier principal fourni

- D00 : `00-INDEX(1).md`, DELTA 3.
- D01 : `01-REVUE-C2-AMENDEMENTS-V23.md`.
- D02 : `02-V23-E1.md`.
- D03 : `03-V23-E2.md`.
- D04 : `04-V23-E3.md`.
- D05 : `05-V23-CLOTURE.md`.
- D06 : `06-ETAT-DEPOT.md`.
- D07 : `07-GUIDE-VERIFICATION.md`.

### Contexte de recherche extérieur, distinct du dossier

**S01.** Min, McCoy, Das, Pitler et Linzen. *Syntactic Data Augmentation Increases Robustness to Inference Heuristics*, ACL 2020. Les auteurs étudient des augmentations syntaxiques pour l'inférence textuelle avec BERT. Ce précédent motive la pertinence d'un entraînement syntaxiquement discriminant, pas une performance attendue d'A2.
Source primaire : `https://aclanthology.org/2020.acl-main.212/`

**S02.** Kim et Linzen. *COGS: A Compositional Generalization Challenge Based on Semantic Interpretation*, EMNLP 2020. Sépare certaines combinaisons syntaxiques/lexicales vues de combinaisons nouvelles. Utile pour nommer les dimensions d'exposition ; ce n'est pas un diagnostic automatique de V2.3.
Source primaire : `https://aclanthology.org/2020.emnlp-main.731/`

**S03.** Wu, Manning et Potts. *ReCOGS: How Incidental Details of a Logical Form Overshadow an Evaluation of Semantic Interpretation*, TACL 2023. Montre, sur COGS, l'importance de détails de représentation qui ne correspondent pas nécessairement à la capacité sémantique visée. Cela justifie de tester l'interface avant d'attribuer tout échec à un manque de raisonnement.
Source primaire : `https://aclanthology.org/2023.tacl-1.96/`

Ces sources ont été consultées en ligne pour le contexte méthodologique. Aucun nouveau papier ni score externe n'est présenté comme une validation du projet.

## Annexe A. Propriété mathématique utile au diagnostic

Cette annexe est une déduction, pas une mesure des modèles.

Soient A et B deux matrices stochastiques par lignes, définies sur les mêmes états, et p une distribution initiale. Pour un nombre entier de pas t :

```text
|| p A^t - p B^t ||_1 <= min(2, t * epsilon)
epsilon = max_i || A[i, :] - B[i, :] ||_1
```

Justification : développer `A^t - B^t` par une somme télescopique ; chaque multiplication par une matrice stochastique contracte la norme L1 des vecteurs-lignes signés, et chaque terme introduit au plus epsilon. La distance entre deux distributions est au plus 2.

Cette borne explique pourquoi mesurer les différences de matrices peut être pertinent. Elle ne prédit pas l'accuracy ni une dégradation exponentielle. Elle ne s'applique pas directement après une renormalisation conditionnelle non linéaire sur un sous-ensemble de candidats. Des états initiaux différents ajoutent un terme de différence initiale.

La valeur maximale sur toutes les lignes est souvent pessimiste ; une analyse pondérée par les états réellement visités peut être plus informative, mais doit rester séparée d'une preuve de fiabilité.

## Annexe B. Identité des pièces jointes analysées

Ces SHA-256 identifient les fichiers reçus ici, pas les artefacts d'entraînement du dépôt.

| Fichier | SHA-256 |
|---|---|
| `00-INDEX(1).md` | `8cf6b5af411979a9838e67e155f389cf1084a3efd3c12329f0a7ef67089d2777` |
| `01-REVUE-C2-AMENDEMENTS-V23.md` | `6e1627a86d8969a3ef65ef792b19f14ebf1d7f5e991a2111a1a287aa75921d1c` |
| `02-V23-E1.md` | `228ae0d842459278b299368fa16f3f8b299f1943631fd7deda6f4d99634acbba` |
| `03-V23-E2.md` | `341c10f8c6d4b7ed217396933f4bf37c539f116cbf260b8837bd3e3391320b34` |
| `04-V23-E3.md` | `ded1cc9e8e24a5713ff9fead03507d6dd147a2985eec7c6d1d6b0cd2a4f6b124` |
| `05-V23-CLOTURE.md` | `7b64505da00493c54f4d282827773f0d5f9f336ab3364c692e1d13e21dfb8337` |
| `06-ETAT-DEPOT.md` | `afb5ddd18d933b0a0c2975ca723ed4ad9019e1f1972c3145a60a7481502bfc3e` |
| `07-GUIDE-VERIFICATION.md` | `0596705ffba0c8d97c66bd9cd3c4ed427312d8a1f90f37457f44501dc2bf2d57` |
