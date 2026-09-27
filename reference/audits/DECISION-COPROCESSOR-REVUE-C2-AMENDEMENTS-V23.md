# Decision Coprocessor : revue C0-C2 et amendements ciblés à V2.3

**Date : 26 septembre 2026.**  
**Statut : revue documentaire et recommandations. Aucun entraînement, aucune évaluation des modèles et aucune autorisation de dépense ne sont exécutés par ce document.**

## 0. Décision recommandée

**Conserver A2, considérer C0-C2 comme un jalon positif dans le domaine évalué, et poursuivre vers une V2.3 linguistique par étapes. Ne pas reconstruire l'architecture.**

La proposition V2.3 va dans une direction justifiée, mais son brouillon doit être amendé avant figement. Les points à régler concernent principalement la définition des données et des conclusions : identité du validateur, contrat d'entrée réellement public, séparation des phénomènes linguistiques, critères de déclenchement d'E2 et statut de l'extrapolation d'E3.

Mes recommandations aux quatre décisions ouvertes du dossier sont : L1 d'abord ; coréférence différée ; lot adverse distinct plutôt qu'intégré silencieusement à la métrique primaire ; E2 soumis à une décision séparée après le diagnostic E1. Ce sont des recommandations, pas un GO donné au nom de l'utilisateur.

### Périmètre de preuve

Les neuf compactions du dossier DELTA 2 sont la base de cette revue. Elles décrivent des tests, des scripts et des artefacts dont le code et les sorties brutes ne sont pas joints. L'audit ne constitue donc pas une certification indépendante du dépôt.

Les nombres sont repris des documents. La moyenne des trois deltas C2, la dispersion d'A2 et un petit contre-exemple mathématique de tie-break ont été vérifiés arithmétiquement, pas les prédictions des modèles.

**Convention :** « rapporté » désigne les documents ; « analyse » une déduction explicitée ; « proposition » un changement non encore réalisé.

## 1. Ce que C0-C2 apportent réellement

### C0 : les questions d'attribution principales sont clarifiées

Le chemin A2 est désormais décrit sans ambiguïté : lecteur adapté par LoRA, têtes fact-level, propagation `p @ A`. L'exécuteur neuronal S de 92 802 paramètres n'est pas invoqué dans cette voie. [D02 §2]

Le parser déterministe et le solveur exact atteignent 1,000 sur les 3 200 exemples du domaine à templates. Le « plafond parser 0,95 » était une confusion avec un autre diagnostic et a été retiré. Les formulations incorrectes sur la NLL et le Brier ont également été corrigées. [D02 §1 et §6]

Il n'est pas nécessaire de redemander ces expériences. Il faut conserver les artefacts et aligner les synthèses sur leurs versions définitives.

### C1 : l'ablation demandée a été exécutée

| Lecteur | Hard | Soft |
|---|---:|---:|
| R0, lecteur antérieur | 0,56 à 0,83 | 0,83 à 0,86 |
| R1, lecteur A2 | 0,78 à 0,875 | 0,995 à 1,000 |

Il s'agit de plages sur huit bancs, pas de moyennes appariées. D04 précise que les logits sont identiques entre les colonnes et que les politiques de départ, terminaux, candidats, horizon et rejet sont alignées.

**Conclusion soutenue :** conserver les distributions améliore le résultat par rapport à la projection hard testée, et le lecteur A2 est aussi meilleur que R0 une fois discrétisé. [D04 §1-3]

Ces deux effets peuvent interagir ; on ne doit pas additionner arbitrairement deux gains marginaux comme si leur indépendance était démontrée.

La comparaison ne prouve pas que les distributions internes soient des probabilités parfaitement calibrées de relations vraies, ni que le soft soit supérieur à toute procédure discrète possible. Elle établit son utilité face au contrôle précisément défini.

### C2-a : confirmation sur de nouvelles données et trois seeds

| Paire | A2 profond | A3 profond | Delta rapporté |
|---|---:|---:|---:|
| s17, paire existante | 0,9950 | 0,3419 | +65,30 points |
| s18 | 0,9983 | 0,3578 | +64,05 points |
| s19 | 0,9983 | 0,3169 | +68,14 points |

Le delta moyen rapporté, +65,83 points, correspond bien à la moyenne des trois deltas affichés. L'amplitude d'A2 est de 0,33 point. Les trois intervalles publiés du delta sont positifs. [D05 §2]

Ne pas appeler cela « trois seeds neuves » : s17 est la paire existante, s18 et s19 sont nouvelles. Les données de confirmation sont nouvelles selon le protocole décrit. La conclusion de réplication locale reste forte.

Le résultat dit quelque chose sur les seeds observées et les bancs considérés. Il ne rend pas la procédure indépendante de toutes les distributions et initialisations possibles.

### C2-b : extrapolation en profondeur sans sélection longue pour ce run

Train et sélection sont limités aux profondeurs 1 à 4. A2-s20-blind atteint 0,9867 en moyenne sur les cellules de profondeur 6, 8 et 10, contre 0,2710 pour A3-s21-blind. [D05 §1 et §3]

C'est un résultat particulièrement important. La restriction qui manquait à la sélection précédente a été appliquée.

Il faut cependant conserver deux précisions :
- cette variante blind est évaluée avec un entraînement par voie, pas avec trois seeds blind ;
- l'architecture avait été choisie dans un programme de recherche qui connaissait déjà les tâches longues. « Blind » qualifie ici l'entraînement et la sélection du run, pas une ignorance historique totale de la profondeur.

La formule « généralisation observée jusqu'aux profondeurs 6, 8 et 10 » est plus précise qu'une « invariance en profondeur » sans limite.

### Incident de longueur

Une exclusion commune sur 2 000 exemples, indépendante de la correction des réponses et liée à un rendu dépassant 512 tokens, a été documentée. Les évaluations ont été rejouées sur la population commune. [D05 §4]

Cela représente 0,05 % des items générés. Cette correction ne constitue pas une raison d'écarter les résultats, mais les futurs générateurs doivent appeler exactement le rendu et le tokenizer de chaque consommateur.

## 2. La bonne question V2.3

### Formulation du dossier

> A2 tient-il sur un langage où le parser déterministe casse ?

Le dossier précise E1 à poids figés, E2 conditionnel avec rendus diversifiés, et E3 croisant diversité et profondeur. [D06 §1-2]

### Amendement recommandé

> À graphe et réponse constants, quelle compréhension des formulations nouvelles A2 conserve-t-il, comparé à A3 et au parser figé ?

La chute du parser devient un résultat secondaire informatif, pas la condition de construction du domaine.

Le fait de battre un parser à templates particulier n'établit pas que « l'ingénierie de parsing plafonne » en général. Inversement, si le parser reste performant sur une transformation légitime, cela n'invalide pas cette transformation : elle doit rester dans le rapport.

Il faut distinguer :
- formulation jamais vue par les modèles ;
- nouvelle famille de templates contrôlés ;
- recombinaison de constructions déjà vues ;
- texte rédigé indépendamment ;
- langage naturel de terrain.

La V2.3 proposée peut évaluer les premières catégories. Elle ne devient pas automatiquement une validation générale du langage naturel.

## 3. Premier amendement indispensable : séparer parser évalué et validateur

D06 demande à la fois une couverture faible du parser sur L2/L3 et un « round-trip parseur == graphe sinon rejet ». Le texte mentionne aussi un validateur séparé et une revue manuelle. [D06 §3-4]

**Analyse :** si le parser du round-trip est celui du benchmark, cette règle exclut précisément les textes qu'il ne comprend pas. Si c'est un outil différent, la contradiction disparaît, mais son rôle et ses dépendances doivent être déclarés.

Noms proposés, à remplacer par les vrais noms du dépôt :

| Composant | Rôle | Informations autorisées |
|---|---|---|
| `P_eval` | Baseline figée qui participe au score | Texte et interface publique déclarée |
| `V_sem` | Vérification du sens des textes générés | Texte, graphe attendu pour comparaison, traces de génération |
| `Renderer` | Produit le texte depuis une structure choisie | Graphe de génération |
| `Evaluator` | Calcule les scores | Prédictions et réponses exactes |
| `PublicAdapter` | Prépare l'entrée des systèmes évalués | Seulement les informations publiques prévues |

Le validateur ne doit pas transmettre de relations, segmentation oracle, résolutions de pronoms ou réponses aux modèles. Il ne doit pas non plus être conditionné par leur réussite.

### Validation proposée

Pour des transformations fermées, utiliser une trace de génération et des contrôles de conservation des relations, puis une revue aveugle du texte seul sur un échantillon stratifié. Le relecteur reconstruit d'abord le sens, puis compare au graphe prévu.

La trace du générateur montre ce qu'il voulait exprimer, pas nécessairement ce qu'il a effectivement écrit. Un relecteur qui voit uniquement le graphe risque de confirmer l'intention plutôt que le texte.

Pour les phénomènes plus risqués, augmenter la revue indépendante et publier désaccords et rejets sémantiques. Toute exclusion doit venir d'une règle sémantique ou technique préfixée, jamais d'une erreur d'A2/A3 ou de `P_eval`.

## 4. Deuxième amendement : réduire le mélange de phénomènes

Le L1 proposé contient déjà pronoms et ellipses, alors que la coréférence est une décision encore ouverte. L3 contient des formulations dites ambiguës, alors que les mondes partiels et INCONNU sont reportés à V2.4. [D06 §2 et §6]

Voici une **proposition de découpage**, distincte du brouillon :

| Étape | Transformations | Ce qu'elle évite de confondre |
|---|---|---|
| L1-a, surface | Synonymes contrôlés, ponctuation, ordre des faits, variations locales ; toutes les entités explicites | Sens des noms et syntaxe simple sans résolution de référence |
| L2-a, syntaxe locale | Passive, relative simple, changement d'ordre syntaxique ; relation orientée conservée | Structure de phrase versus calcul de chemin |
| L2-b, empaquetage | Plusieurs relations dans une phrase ou une relation répartie sur plusieurs phrases | Segmentation et capacité d'interface |
| L2-c, référence | Pronoms/ellipses à antécédent unique | Coréférence, séparée et optionnelle |
| L3, challenge | Transformations composites difficiles mais à interprétation unique | Stress linguistique sans changement de vérité |

Ne pas présumer que ces niveaux sont monotones en difficulté pour tous les modèles. Rapporter les opérations individuellement avant une agrégation pondérée préfixée.

### Exemple illustratif, pas un item du dataset

```text
Canonique :
A pointe vers B. B pointe vers C.

L1-a :
A mène à B. B mène à C.

L2-a :
B est la destination indiquée depuis A.
C est la destination indiquée depuis B.

L2-b :
A mène à B, dont la destination suivante est C.
```

Les phrases doivent être validées dans le sens précis du domaine. « Relie », par exemple, peut évoquer une relation non orientée et n'est pas automatiquement un bon synonyme de « pointe vers ».

La vraie ambiguïté n'est pas simplement une difficulté supplémentaire. Si deux graphes incompatibles restent possibles à partir du texte, une réponse unique imposée par le générateur n'est pas justifiée. Pour V2.3, rejeter ces items selon une procédure indépendante ; ne pas les garder comme « adversariaux ». Les cas d'indétermination appartiennent au contrat ultérieur.

Les négations sur non-arêtes ne sont pas neutres pour un lecteur. Je les reporterais également hors du premier pilote, même si elles ne changent pas les arêtes positives du graphe.

## 5. Troisième amendement : documenter l'interface publique et sa capacité

L'anti-fuite C0 randomise edges, trace, answer et terminals, mais garde `private.graph.options`, `nodes` et `query.start` fixes. Le dossier décrit aussi des replays « publique seule » sur 64 exemples par voie. [D02 §2-3 ; D04 §3]

**Ce n'est pas une preuve de fuite.** Les champs peuvent représenter une indexation de données publiques. Mais la suppression de labels privés ne prouve pas, à elle seule, que toute information linguistique nécessaire est reconstruite sans assistance.

Pour V2.3, répondre concrètement :
- les entités candidates sont-elles extraites du texte ou fournies par un inventaire public ?
- le départ vient-il de la question brute ou d'un pointeur déjà résolu ?
- qu'est-ce qu'une unité fact-level : ligne, phrase, fenêtre ou span ?
- une unité peut-elle produire plusieurs relations ?
- des spans ou regroupements de mentions proviennent-ils du générateur ?

La compaction ne donne pas ces réponses. Il ne faut pas inventer un défaut de code pour combler ce manque.

### Test d'entrée proposé

Construire l'entrée d'inférence depuis une vue JSON publique explicite. Une API peut légitimement fournir un inventaire d'entités ou un départ structuré, à condition de le dire et de donner la même information pertinente aux comparateurs.

Conserver séparément :
1. score texte brut ;
2. éventuel score avec assistance structurée déclarée, utilisé pour le diagnostic.

Ne pas mélanger les deux.

### Capacité à représenter L2-b

Si une tête produit exactement une relation par unité et que cette unité est une phrase, une phrase à deux relations peut sortir de son contrat. Un entraînement plus long ne répare pas une absence de sortie adéquate.

Il faut alors soit garder ce phénomène hors E1, soit introduire un adaptateur public explicite et le tester comme une nouvelle variante. Une correction de segmentation n'est pas une preuve de nouvel apprentissage du backbone.

L'information exacte du générateur peut servir à mesurer la perte due à la segmentation, mais uniquement dans une cellule privilégiée de diagnostic.

## 6. Quatrième amendement : séparer les conclusions et les déclencheurs

D06 propose un primaire L2 composite : A2 doit dépasser parser+solveur et A3 de cinq points, avec IC favorable. Il propose aussi E2 si A2 échoue au critère ou si la couverture L3 du parser dépasse 0,5. [D06 §3]

Ces règles sont des choix possibles de succès comparatif, pas des définitions suffisantes d'une défaillance d'A2.

### Trois questions distinctes

**Robustesse absolue :** A2 répond-il correctement aux nouvelles formulations ?

**Robustesse relative :** sa dégradation par rapport au rendu canonique est-elle plus faible que celle d'A3 ?

**Utilité comparative :** dans ces conditions, le coût et la qualité justifient-ils A2 plutôt que les autres voies ?

Contre-exemple illustratif :
- A2 = 99 % ;
- A3 = 98 % ;
- parser = 20 %.

Le système généralise très bien, mais échoue au seuil « A2 doit dépasser A3 de cinq points ». Cela n'est pas une raison de le réentraîner pour corriger une prétendue casse.

Inversement, A2 peut gagner largement sur un parser presque toujours muet tout en restant trop peu fiable pour l'usage visé.

### Déclenchement proposé

| Observation E1 | Suite |
|---|---|
| A2 reste fiable, A3 également | Publier absence de gain relatif suffisant ; pas d'E2 automatique |
| A2 se dégrade, données et interface sont valides | E2 devient une hypothèse justifiée |
| A2 se dégrade à cause d'un défaut de segmentation ou d'indexation | Corriger/versionner l'interface avant d'évaluer la nécessité d'un entraînement |
| Texte ambigu ou sens non conservé | Corriger le générateur ; résultat concerné invalide |
| Parser reste performant | Garder ce résultat ; ne pas durcir le jeu pour le faire perdre |
| A3 dépasse A2 | Publier le renversement local et analyser, sans masquer la cellule |

La couverture du parser doit être définie : fraction de textes sur lesquels il produit une structure complète, par exemple. Ce n'est ni son exactitude ni une mesure universelle de difficulté linguistique.

Mesurer couverture, exactitude sur réponses émises et exactitude sur l'ensemble des items. Les sous-groupes définis par le succès du parser restent descriptifs ; ils ne remplacent pas l'analyse complète.

## 7. Le marqueur hard/soft ne diagnostique pas à lui seul un raccourci positionnel

D06 présente un écart hard/soft d'au moins cinq points comme marqueur d'un raccourci positionnel. [D06 §3-4]

**Analyse :** un avantage soft peut venir de l'agrégation d'hypothèses, même sans raccourci de position. Une absence d'avantage n'exclut pas non plus un raccourci partagé par les deux voies.

Conserver l'ablation comme diagnostic de sensibilité à la discrétisation. Tester la position par une intervention de position :
- permutation des faits ;
- permutation des options ;
- réindexation interne puis inversion du mapping ;
- renommage des entités avec bijection déclarée.

Mesurer séparément distributions et actions sélectionnées. Une égalité de scores agrégés peut cacher des flips compensés.

Ces tests prolongent l'idée de tests comportementaux par capacité, illustrée par CheckList. Ils n'exigent pas de remplacer votre harnais par une nouvelle bibliothèque. [S02]

## 8. Plan V2.3 recommandé, borné

### Préparation : aucun réentraînement

Geler A2, A3, le parser, les adaptateurs publics et les décodeurs. Corriger les définitions ci-dessus avant les nouveaux runs. Finaliser le manifeste dont la complétude reste à vérifier selon D08.

Un petit lot de mise au point du générateur peut exister, explicitement non confirmatoire et distinct des évaluations finales. Il ne faut pas déboguer un générateur sur un test supposé scellé.

Publier une table par famille : sens conservé, segmentation requise, références implicites, longueur, informations publiques, raison de rejet possible. Ne pas conditionner cette table à la couverture obtenue par le parser.

### E1-a : commencer par L1 sans coréférence

Créer des groupes de graphes neufs et appariés entre le rendu canonique et les variantes L1-a. Les graphes sont identiques à l'intérieur d'une paire, pas nécessairement ceux des anciens tests.

Un format raisonnable est un pilote diagnostique de 30 à 50 groupes, puis une taille d'évaluation définie avant mesure, par exemple 400 groupes. Ce sont des propositions de budget, pas des tailles déjà adoptées ou une garantie de précision.

Exécuter les modèles figés et le parser sur tous les items valides. Conserver les sorties locales d'A2, afin de calculer l'ablation hard/soft sans repasser le backbone.

Mesures essentielles :
- exactitude du rendu canonique et de chaque famille de transformation ;
- différence appariée transformation moins canonique ;
- deltas A2-A3 et A2-parser ;
- première divergence : préparation publique, relation, propagation, choix ;
- couverture et erreurs sémantiques du parser ;
- longueurs et coûts en mode C0.

Ne pas affirmer qu'une chute de plus de dix points est forcément de la « plomberie ». Cela doit déclencher un diagnostic entre interface et compréhension.

### E1-b : L2 avec structure explicite

Ajouter la syntaxe locale. Garder les entités nommées, le départ explicite, la sémantique de graphe inchangée et la capacité de sortie vérifiée.

Le regroupement de faits L2-b et la coréférence L2-c doivent avoir leurs propres cellules. Ils peuvent attendre si leur préparation absorbe l'essentiel de l'effort.

### E2 : conditionnel, avec un vrai test nouveau

La mixture 30 % canonique / 45 % L1 / 25 % L2 est celle du brouillon, pas une proportion démontrée optimale. La conserver comme recette candidate est acceptable si elle est figée avant l'essai. [D06 §2]

A3 reçoit les mêmes données et les annotations prévues. Les historiques d'initialisation, l'exposition cumulée et le budget doivent rester explicites.

Une fois E1 utilisé pour orienter E2, il reste un jeu diagnostique. La confirmation d'E2 doit employer d'autres groupes de graphes et, pour revendiquer une nouveauté linguistique, des familles de rendu ou combinaisons réservées.

Avec du rendu déterministe à la volée, définir la seed à partir de run, groupe, époque et indice de rendu. L'ordre des workers ne doit pas modifier silencieusement le corpus. La sélection doit rester fixe.

E2 n'est pas préautorisé par ce document. Ma recommandation est un GO séparé après le diagnostic, avec une seule recette et un budget borné.

### E3 : croiser les deux axes sans changer leur définition

| | Formulations canoniques | Formulations nouvelles |
|---|---|---|
| Profondeurs courtes | Contrôle | Généralisation linguistique |
| Profondeurs longues | Généralisation en profondeur | Généralisation croisée |

Pour parler d'extrapolation aveugle, sélectionner seulement sur des profondeurs courtes. Les s17-s19 de confirmation utilisent la sélection du système actuel ; ils ne suffisent pas à eux seuls pour cette revendication. Le s20-blind est un diagnostic utile, mais ne représente pas trois seeds blind.

Une évaluation croisée de poids figés peut être utile sans nouvel entraînement. Sa portée doit suivre l'historique de sélection réel.

E3 reste une expérience future : le brouillon ne doit pas qualifier la généralisation linguistique de « démontrée » avant E1/E2.

## 9. Protéger la validité du benchmark

### Indépendance des rendus

Changer uniquement les seeds de génération peut produire de nouveaux exemples avec les mêmes patrons. Ce n'est pas nécessairement un défaut, mais cela mesure une généralisation à de nouvelles instances.

Pour mesurer la recombinaison, réserver des constructions ou leurs combinaisons. COGS fournit un précédent méthodologique : il distingue des combinaisons nouvelles de mots et de structures pourtant familiers. Il porte sur un autre domaine et ne prédit pas vos résultats. [S01]

Éviter les paraphrases générées puis sélectionnées en fonction des échecs d'A2, A3 ou du parser. Un lot adverse ciblé reste possible, mais doit être étiqueté et évalué séparément.

### Groupes et statistique

L'unité de regroupement est le graphe sous-jacent avec ses variantes. Plusieurs textes d'un même graphe ne constituent pas autant d'observations indépendantes.

Rapporter les seeds séparément et les différences appariées par groupe. Fixer les poids des familles dans les agrégats avant les scores. Une famille dotée de davantage de rendus ne doit pas dominer accidentellement le résultat.

Pour un lot adverse à 25 %, publier les résultats standard et adverse séparément. Une moyenne avec ce poids n'est représentative d'un produit que si ce mélange correspond à l'usage visé.

### Longueur et équité

Appeler les collates réels pour chaque voie avant l'évaluation. En cas de dépassement, publier la couverture et l'exclusion commune prévue.

Si beaucoup d'exemples L2/L3 dépassent la limite, ne pas conclure « A2 ne comprend pas le langage » sur la base d'un échantillon filtré différent. Le problème peut être la couverture de contexte. Un changement de limite ou de segmentation crée une configuration distincte à mesurer.

Conserver autant que possible des strates où longueur et nombre de faits se recouvrent entre familles. Ne pas appeler « effet de syntaxe » un mélange non contrôlé de syntaxe, longueur et distracteurs.

## 10. Quelques réserves résiduelles : précises, pas un nouveau chantier C2

### A. Tie-break alphabétique et renommage

D03 indique que la clé alpha gagne dans une quasi-égalité, puis associe le renommage à l'équivariance. La propriété dépend de ce qui est renommé.

Contre-exemple mathématique si la clé est le nom visible :
- scores A = B = 0,5 ; la règle choisit A ;
- bijection A -> Z et B -> C ;
- l'équivariance demanderait Z ;
- le nouvel ordre alphabétique choisit C.

La règle peut être stable à une permutation d'ordre sans être équivariante à tout renommage. Si la clé est un identifiant public stable que l'on ne renomme pas, c'est une autre transformation et elle doit être nommée comme telle.

Ce contre-exemple a été vérifié sur un petit calcul indépendant ; ce n'est pas une reproduction du code du projet. Demander deux tests unitaires ciblés et limiter la formulation au domaine effectivement testé. Ne pas relancer C2 pour une propriété documentaire non utilisée sur les cas évalués.

### B. Brier : une incohérence persiste entre deux synthèses

D03 §R-A donne R1 = 0,0118 et R0 = 0,4632, avec prise en compte du résidu.
D04 §2 annonce 0,0008 à 0,008 sur « les cellules soft ».

Ces chiffres ne sont pas présentés avec suffisamment de conventions pour être réconciliés. Il peut s'agir de populations, normalisations ou anciennes métriques distinctes, mais l'audit ne doit pas choisir une explication sans source.

Publier une seule table canonique, avec formule, espace des classes, masse résiduelle, budget, dénominateur et hash des prédictions. Le fait que le calcul soit désormais rejouable permet une correction documentaire ciblée.

### C. Plage hard/soft

D04 donne un maximum R1-hard de 0,875 et un maximum soft de 1,000, tout en parlant d'un gain minimal de quatorze points. Sur le banc où hard atteint 0,875, le gain ne peut dépasser 12,5 points.

Cela n'annule pas l'avantage soft. Cela impose seulement de publier les huit différences appariées de la version définitive, plutôt qu'une plage narrative éventuellement antérieure aux corrections des décodeurs.

### D. Numérique

La localisation de divergences dans les activations et le replay sans flips dans l'environnement figé sont des éléments utiles. Ils n'établissent pas un « plancher de bruit » universel de 0,5 %.

Un écart relatif d'activations, une marge de sortie et un pourcentage de flips sont des quantités différentes. Le dossier constate aussi une queue de petites marges plus importante pour s20-blind. [D03 §R-C/R-D ; D05 §5]

Conserver la toolchain comme partie du système évalué. Formuler les garanties à partir des replays réalisés, sans extrapoler à tous les environnements.

### E. Coûts

C0 a bien ajouté batch 1 et batch 8, avec qualité dans le même mode. Le dossier assume que le plafond initial n'est pas validé. [D02 §5]

Ne pas redemander la mesure comme si elle n'avait jamais eu lieu. Pour une décision produit, récupérer sa table chiffrée dans les artefacts : les compactions seules ne permettent pas ici de vérifier toutes les médianes finales. Les coûts V2.3 annoncés sont des estimations, pas des mesures d'expériences déjà réalisées.

## 11. Recommandations aux quatre choix ouverts

| Choix du brouillon | Ma recommandation | Raison |
|---|---|---|
| L1 d'abord ou tout-en-un | L1-a d'abord, puis L2 | Un diagnostic rapide et interprétable avant de complexifier les données |
| Coréférence L2c | Différée | Éviter de tester simultanément paraphrase, segmentation et résolution de référence |
| 25 % d'adversarial L3 | Lot séparé ; pas dans le primaire initial | Préserver une lecture claire du domaine standard et du stress |
| E2 préautorisé ou GO séparé | GO séparé après E1 | Un échec relatif ou une forte couverture parser n'est pas une casse d'A2 |

Ces décisions n'empêchent pas le scénario complet ultérieur. Elles réduisent le risque de dépenser le budget prévu dans une expérience dont plusieurs explications seraient indissociables.

## 12. Prompt prêt à transmettre aux agents

```text
Poursuivre le projet à partir des résultats C0-C2 existants.
Ne pas reconstruire A2, ne pas relancer les confirmations déjà effectuées sans cause
précise et ne pas lancer E2 sans nouvelle autorisation.

1. Préserver les scores C2 et leur portée :
   - C2-a = confirmation sur trois seeds, dont s17 réutilisée ;
   - C2-b = train et sélection courts, un run par voie ;
   - A2 = lecteur LoRA + têtes fact-level + propagation, sans exécuteur S.

2. Amender V2.3 avant figement :
   - question primaire : robustesse linguistique à graphe constant ;
   - nommer séparément parser évalué, validateur sémantique et adaptateur public ;
   - aucun rejet d'item basé sur l'erreur du parser ou des modèles ;
   - L1 sans coréférence, sans vraie ambiguïté et sans changement du contrat logique ;
   - vérifier la capacité fact-level avant plusieurs faits par phrase ;
   - déclarer entités, départ, spans et mapping candidats réellement publics ;
   - distinguer robustesse absolue, gain relatif et déclenchement d'E2.

3. Réaliser d'abord E1-a avec poids figés après autorisation :
   - groupes de graphes neufs appariés canonique/L1 ;
   - contrôle sémantique indépendant ;
   - mêmes informations publiques pour les voies ;
   - longueurs vérifiées via les collates consommateurs ;
   - exactitude, dégradation appariée, couverture parser, hard/soft et coûts C0 ;
   - localiser la première divergence au lieu de l'attribuer immédiatement au raisonnement.

4. Corriger seulement les incohérences documentaires résiduelles :
   - Brier complet canonique par cellule ;
   - deltas hard/soft itemisés ;
   - domaine exact de la propriété de tie-break ;
   - compléter le manifeste final.
   Ne pas qualifier ces corrections d'échec général de C2.

5. Après E1, livrer une décision :
   - robuste : passer au niveau suivant sans réentraînement ;
   - défaut de données/interface : corriger et versionner ;
   - compréhension insuffisante démontrée : proposer une recette E2 bornée ;
   - A3 meilleur ou parser toujours fort : publier ce résultat également.

6. Pour E2, prévoir un test neuf et des familles réservées.
   Pour E3 dit "aveugle", aucune profondeur longue dans la sélection.
   Une autre variante peut mesurer la robustesse croisée sans cette appellation.

Le résultat recherché n'est pas de faire perdre le parser.
Il est de savoir quel langage public le système traite réellement, à quel coût,
et ce que le calcul de propagation apporte dans ce domaine.
```

## 13. Conclusion publiable

Les résultats rapportés permettent maintenant une note technique bornée : une interface relationnelle apprise et une propagation explicite produisent une généralisation en profondeur très supérieure aux comparateurs directs étudiés, confirmée sur de nouvelles données et plusieurs seeds pour le système principal.

V2.3 ne doit pas devenir une condition indéfiniment repoussée pour reconnaître cette réussite locale. C'est une nouvelle question, portant sur la variation linguistique et la dépendance aux templates.

**Poursuivre cette question est pertinent. La priorité est un contrat de données clair, pas une nouvelle architecture.**

## Références

### Pièces du dossier

- D00 : `00-INDEX.md`.
- D01 : `01-AUDIT-V22-CONFIRMATION.md`.
- D02 : `02-C0-FIGER-CLARIFIER.md`.
- D03 : `03-RESERVES-RA-A-RE.md`.
- D04 : `04-C1-ABLATION-2x2.md`.
- D05 : `05-C2-CONFIRMATION-EXTRAPOLATION.md`.
- D06 : `06-V2.3-PROPOSITION.md`.
- D07 : `07-ETAT-DEPOT.md`.
- D08 : `08-GUIDE-VERIFICATION.md`.

Le guide D08 cite les artefacts de preuve du dépôt. Leur présence dans ce guide ne signifie pas qu'ils ont été inspectés indépendamment dans cet audit.

### Éclairage externe, distinct des résultats du projet

**S01.** Najoung Kim et Tal Linzen, *COGS: A Compositional Generalization Challenge Based on Semantic Interpretation*, EMNLP 2020. Consulté le 26 septembre 2026 pour la distinction entre instances nouvelles et recombinaisons réservées de mots/structures.  
`https://aclanthology.org/2020.emnlp-main.731/`

**S02.** Marco Tulio Ribeiro, Tongshuang Wu, Carlos Guestrin et Sameer Singh, *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList*, ACL 2020. Consulté le 26 septembre 2026 pour le principe de tests comportementaux organisés par capacité.  
`https://aclanthology.org/2020.acl-main.442/`

Ces sources ne valident pas les mesures A2/A3 et ne prédisent pas le succès de V2.3.
