# Decision Coprocessor : audit du delta V2.1 / V2.2 et confirmation ciblée

**Date : 25 septembre 2026.**  
**Destinataire : orchestrateur et agents du projet.**  
**Décision recommandée : conserver A2, consolider l'attribution du gain et faire une confirmation bornée. Ne pas reconstruire le projet.**

## 0. Périmètre et statut de ce document

Cet audit porte sur les neuf fichiers du dossier delta, qui couvrent la période du 25 septembre 2026 vers 11 h jusqu'à 19 h 06. Les dossiers V1 et V2 antérieurs servent de contexte, sans remplacer les mises à jour.

C'est une **revue documentaire**, pas une reproduction des entraînements ni une inspection du dépôt exécutable. Les scores ci-dessous sont ceux des compactions. Seuls les écarts arithmétiques entre nombres publiés ont été revérifiés ici ; aucun intervalle de confiance n'a été recalculé depuis les prédictions originales.

Les références D00 à D08 renvoient aux pièces jointes, recensées en fin de document. Les références S01 à S05 sont des vérifications méthodologiques externes. Les sections « analyse », « hypothèse » et « expérience proposée » ne sont pas des résultats du projet.

Ce document n'annule ni les résultats négatifs locaux de V1/V2, ni le résultat positif du delta. Il précise les conditions de chacun.

## 1. Verdict principal

**Le projet dispose maintenant d'un résultat positif important dans son domaine expérimental.**

Deux avancées doivent être distinguées :

1. **V2.1 : renversement avec checkpoints figés.** Les anciens modèles, sans réentraînement, montrent que la voie décomposée dépasse le direct sur les chaînes textuelles de profondeurs 6, 8 et 10. Le résultat négatif sur les chaînes courtes ne se généralisait pas à ce domaine. [D02 §1-2]
2. **V2.2 : un lecteur adapté connecté à une propagation explicite atteint des scores presque parfaits sur les huit bancs.** Le contrôle A3 reçoit lui aussi une supervision relationnelle auxiliaire et reste très inférieur en profondeur. [D04 §1-2]

La formulation recommandée est :

> Sur huit bancs synthétiques français de suivi de relations, le système A2, qui apprend des distributions relationnelles puis applique une propagation explicite, dépasse les modèles directs comparés, y compris un direct bénéficiant d'une supervision auxiliaire relationnelle. Les écarts les plus importants apparaissent sur les chaînes longues. La variabilité entre entraînements, une confirmation finale indépendante et l'apport spécifique de la conservation des distributions restent à établir.

Cela soutient un **système de décision spécialisé sans raisonnement textuel généré**, pas un coprocesseur universel prêt à brancher sur n'importe quel modèle Jev.

### 1.1 Résultats publiés à conserver

Chaque banc comporte 400 exemples. Tableau descriptif, conditionnel aux entraînements effectués :

| Banc | A2 propagation | A3 direct + auxiliaire | Direct V2.1 | A2 moins A3, points |
|---|---:|---:|---:|---:|
| B1, profondeur 1 à 4 | 99,50 % | 96,25 % | 93,75 % | +3,25 |
| B2, profondeur 6 | 99,75 % | 49,25 % | 52,50 % | +50,50 |
| B3, profondeur 8 | 99,75 % | 24,75 % | 28,00 % | +75,00 |
| B4, profondeur 10 | 99,75 % | 28,25 % | 30,75 % | +71,50 |
| B5, surface | 100,00 % | 95,75 % | 94,00 % | +4,25 |
| B6, distracteurs | 100,00 % | 94,50 % | 93,75 % | +5,50 |
| B7, options | 99,50 % | 96,00 % | 94,00 % | +3,50 |
| B8, autre départ | 99,75 % | 85,50 % | 84,00 % | +14,25 |

Sources : D00 §3, D04 §1-2. Les huit différences ponctuelles sont arithmétiquement cohérentes. La QA rapporte des bornes inférieures d'IC positives sur les huit bancs ; ce document ne certifie pas leur calcul.

Les scores d'A2 correspondent arithmétiquement à 2, 1, 1, 1, 0, 0, 2 et 1 erreurs par banc. Il faut conserver les huit évaluations séparées, plutôt que traiter automatiquement leurs 3 200 lignes comme des unités indépendantes.

### 1.2 Ce que V2.1 établit séparément

Avant tout nouveau training, les gains du pipeline filtré sur le direct sont :
- profondeur 6 : +14,25 points ;
- profondeur 8 : +31,75 points ;
- profondeur 10 : +25,25 points.

Sur les nouveaux exemples courts, le direct reste supérieur : 93,75 % contre 80,00 %. [D02 §2]

Il n'y a pas contradiction avec le résultat de développement antérieur : le domaine et l'échantillon évalués ont changé. Le croisement est observé entre les profondeurs évaluées 4 et 6 ; sa position précise n'a pas été mesurée.

## 2. Ce qui fonctionne architecturalement, et ce qui reste à attribuer

### 2.1 Le montage gagnant a changé

La description de V2.2 donne :

```text
Texte public
    -> lecteur neuronal adapté
    -> distributions de successeurs
    -> matrice A et état initial p0
    -> p_(t+1) = p_t @ A
    -> distribution sur les réponses
```

Les terminaux ont une auto-transition ; INCONNU est un état absorbant distinct. [D03 §1 et §4]

La composition est ici assurée par **un opérateur explicite choisi par les concepteurs**, appliqué à des représentations apprises. Ce n'est pas la même proposition que « un petit réseau récurrent libre découvre une procédure dans les états cachés ».

Ce n'est pas un défaut. C'est une description plus exacte de la contribution : faire apprendre une interface exploitable par un calcul de composition simple.

**Vérification de dépôt demandée :** publier le chemin d'inférence exact d'A2 et le décompte de ses modules. La compaction ne suffit pas à déterminer si l'exécuteur neuronal S de 92 802 paramètres intervient encore dans ce chemin, en parallèle, ou seulement comme référence. Ne pas attribuer les scores A2 à cet exécuteur sans tracer son invocation.

Les opérations différentiables de raisonnement sur relations ont des précédents, notamment Neural LP. [S05] L'originalité éventuelle doit donc porter sur une méthode précise, une intégration, un protocole ou un résultat, pas sur la seule multiplication `p @ A`.

### 2.2 A3 est un contrôle utile, pas la fermeture de toutes les explications

Le contrôle A3 donne au direct des têtes auxiliaires et des cibles relationnelles comparables. C'est nettement plus informatif qu'une comparaison contre un direct privé de ces annotations. [D04 §2]

Il affaiblit fortement l'explication simple « A2 gagne uniquement parce qu'il reçoit plus d'annotations ».

Il ne démontre cependant pas, à lui seul, que :
- conserver des probabilités bat un graphe discret construit depuis les mêmes sorties ;
- un exécuteur neuronal est nécessaire ;
- tous les modèles directs comparables échoueraient ;
- les deux optimisations ont convergé ;
- les historiques d'initialisation et d'exposition aux données sont parfaitement identiques.

Un gradient de réponse qui traverse la propagation est légitimement une différence architecturale. Il ne faut pas exiger des gradients identiques entre deux architectures différentes. En revanche, il faut documenter les **mêmes possibilités d'apprentissage** et les différences voulues.

Table à publier pour A2/A3 :
- base et révision ;
- checkpoint d'initialisation, adaptateurs et têtes conservés ou réinitialisés ;
- étapes cumulées avant et pendant V2.2 ;
- exemples et annotations effectivement vus ;
- paramètres entraînables par module ;
- pertes appliquées et masques, pas uniquement leurs coefficients ;
- teacher forcing pendant le training et déroulement utilisé à l'évaluation ;
- protocole de sélection, courbes train/sélection, meilleur et dernier checkpoint.

La compaction contient une partie de ces éléments, pas l'intégralité. Ne pas inventer les éléments absents.

### 2.3 L'ablation essentielle : même lecteur, discret ou continu

A1-bis réutilise les poids du lecteur, mais lit les têtes fact-level correctes après découverte d'une mauvaise utilisation de la tête bilinéaire dans A1. [D03 §2-3]

Il faut distinguer trois facteurs :
1. choisir la bonne sortie du lecteur ;
2. changer la conversion de cette sortie en relations ;
3. changer l'exécution et la validation.

Sans comparaison contrôlant ces facteurs, « l'incertitude conservée explique tout le gain » est trop fort.

**Expérience proposée, sans nouveau training :**

| Lecteur | Relations discrètes + parcours exact | Relations continues + propagation |
|---|---|---|
| Lecteur E5v3-A, sorties fact-level figées | R0-hard | R0-soft |
| Lecteur A2, sorties fact-level figées | R1-hard | R1-soft |

Conditions :
- les logits du lecteur sont calculés une seule fois et identiques pour les deux colonnes ;
- même extraction publique du départ et des entités ;
- même définition des terminaux, INCONNU, candidats, horizon et tie-break ;
- « hard » = projection déterministe des mêmes distributions, puis parcours ;
- pas de retour implicite à une autre tête bilinéaire ;
- pas de rejet global supplémentaire dans une seule colonne ;
- les politiques de rejet sont une ablation séparée ;
- sauvegarder masse hors candidats et masse INCONNU avant tout calcul conditionnel.

Interprétation :
- R1-soft > R1-hard : conservation des distributions utile dans cette comparaison ;
- R1-soft ≈ R1-hard et les deux excellents : gain principal compatible avec une meilleure lecture locale et l'exécution explicite ; garder la méthode la plus simple au coût mesuré ;
- R0-hard ≈ R0-soft > ancien discret : une partie du gain vient vraisemblablement de la conversion des sorties ou de la politique de validation ;
- écart seulement avec rejet global : le validateur contribue au résultat.

Un résultat hard ≈ soft **n'annulerait pas** le succès du système. Il changerait l'explication à publier.

## 3. Portée des tests : ce qu'il faut nommer correctement

### 3.1 V2.1 indépendant pour les checkpoints V2, V2.2 après observation de ces bancs

V2.1 utilise des bancs nouvellement générés après figement des checkpoints, conformément au protocole. [D02 §1]

Les mêmes bancs sont ensuite évalués dans la campagne V2.2. Leurs résultats précédents ont déjà servi au diagnostic et à la décision de travailler l'interface. A1, A1-bis, A2 puis A3 sont des étapes successives. [D00 §2 ; D05 §2]

La sélection de checkpoint sur 2213 évite une sélection directe sur B1-B8. Mais elle n'efface pas l'information déjà obtenue sur ces bancs lors des décisions d'architecture.

Formulation recommandée :

> Bancs tenus hors entraînement et hors sélection des checkpoints, mais réutilisés pendant une campagne adaptative de développement.

Ce n'est ni une accusation de fuite des labels dans les gradients, ni une raison de jeter les scores. C'est la distinction entre une évaluation hors entraînement et une confirmation entièrement indépendante. Le biais de sélection peut concerner les choix de modèles, pas seulement leurs paramètres. [S01]

### 3.2 Le banc de sélection inclut des chaînes longues

D03 §4 indique que le banc 2213 contient 400 exemples, dont **50 % aux profondeurs 6/8**.

Il faut distinguer :
- profondeur absente des gradients d'entraînement ;
- profondeur utilisée pour choisir un checkpoint ;
- profondeur utilisée pour choisir une architecture ;
- profondeur jamais exposée avant l'évaluation finale.

A2 n'est donc pas une démonstration aveugle de généralisation aux profondeurs 6/8 si la sélection s'y appuie. La portée de la profondeur 10 doit également tenir compte de la campagne antérieure, et pas seulement des gradients du run A2.

Le résultat V2.1 avec checkpoints figés reste une observation importante d'extrapolation en profondeur. Pour A2, publier les distributions exactes du train, de la sélection et des tests avant toute qualification supplémentaire.

### 3.3 Une seed d'entraînement n'est pas huit réplications

Les huit bancs ne remplacent pas plusieurs entraînements indépendants. Les IC rapportés ne mesurent pas la variabilité entre initialisations si une seule paire A2/A3 est utilisée. [D06 §4]

Ne pas multiplier artificiellement la taille statistique en empilant les seeds. Dans une confirmation :
- apparier les modèles sur les mêmes problèmes ;
- regrouper les variantes d'un même problème par `base_group_id` ;
- rapporter chaque seed et leur dispersion ;
- calculer le delta moyen par groupe sur les seeds, puis un intervalle groupé, tout en précisant qu'avec trois seeds l'incertitude inter-run reste imparfaitement estimée.

Les IC par banc ne constituent pas automatiquement des intervalles simultanés. Une hypothèse principale préfixée est préférable à une sélection a posteriori du plus bel écart. Pour une revendication conjointe sur plusieurs bancs, préciser le cadre statistique plutôt que multiplier des règles sans nécessité.

## 4. Trois corrections documentaires importantes

### 4.1 Le « plafond parser 0,95 » contredit une autre mesure publiée

D02 §4 annonce pour le parser déterministe :
- couverture : 1,000 ;
- accord : 1,000 ;
- 3 200 exemples sur 3 200.

D03 §3 et D04 §1 parlent pourtant d'un « plafond parser 0,95 » dépassé par A2. Les diagnostics « chemin seul » sont, eux, proches de 0,95 à 0,98. [D02 §3]

Les valeurs ne doivent pas être réconciliées par supposition. Demander :
- quelle métrique vaut 0,95 ;
- quel chemin d'exécution elle mesure ;
- quels exemples, quelle version, quel dénominateur ;
- si « parser » désigne l'extraction exacte ou une composition aval.

Si le parser public + solveur exact résout effectivement tout le domaine, il faut le montrer dans le tableau des **solutions au problème**, avec ses limites de templates et ses coûts. Il peut rester séparé du tableau des seuls modèles neuronaux, mais pas disparaître de l'analyse produit.

A2 proche de 100 % face à un parser exact est une réussite d'apprentissage, pas la preuve qu'un réseau est nécessaire sur ce langage synthétique.

### 4.2 Le direct n'est plus le meilleur en court dans V2.2

D06 §1 juxtapose « le direct reste dominant en court » et des écarts positifs pour A2. C'était vrai pour la comparaison V2.1, pas pour les tableaux A2/A3 de V2.2. Corriger en distinguant versions et comparateurs.

### 4.3 Les intervalles doivent provenir d'un artefact canonique

Les points A2-A3 concordent, mais certaines bornes diffèrent légèrement entre D00 et D04 : par exemple B3 est donné avec [+71,0 ; +79,25] dans l'index et [+70,50 ; +79,01] dans le fichier détaillé.

La signification pratique ne change pas, mais choisir et citer un calcul canonique : prédictions hashées, script, seed du bootstrap, unité groupée, version. Ne pas inventer la raison de cette différence.

## 5. Probabilités : deux formulations incorrectes, un résultat encourageant

### 5.1 Une NLL élevée ne signifie pas que le modèle sait qu'il échoue

D02 §3 et D04 §4 utilisent cette interprétation pour le direct.

Pour une cible y :

```text
NLL = moyenne(-log p(y))
```

Une NLL élevée signifie que la bonne réponse reçoit peu de probabilité en moyenne logarithmique. Elle ne mesure pas directement la capacité à détecter ses propres erreurs.

Contre-exemple mathématique, pas un exemple du dataset :

```text
probabilités = [0,999 ; 0,001]
bonne réponse = deuxième classe
NLL ≈ 6,908
```

Le modèle est très confiant dans la mauvaise réponse. La NLL publiée de 8,85 nats est compatible avec de la surconfiance, mais sa moyenne ne permet pas d'affirmer que tous les échecs sont de ce type.

À mesurer : confiance maximale sur erreurs et succès, courbe risque/couverture et qualité de détection des erreurs. La confiance disponible à l'inférence ne peut pas utiliser `p(y_gold)`.

### 5.2 La NLL très basse d'A2 est positive, pas une certification complète de calibration

D04 §4 rapporte NLL 0,0044 à 0,0294 avec identité des prédictions vérifiée sur les huit bancs.

C'est une bonne qualité probabiliste observée sur ces exemples. La calibration concerne l'accord entre probabilités annoncées et fréquences de réussite. [S02]

Compléter avec :
- confiance moyenne contre exactitude ;
- courbe de fiabilité et effectifs par intervalle ;
- NLL et Brier complets ;
- mesures par profondeur et par type d'ambiguïté ;
- résultats INCONNU sur un banc dédié ;
- incertitudes, surtout dans les rares erreurs.

Ne pas prétendre qu'une faible NLL sur un domaine presque saturé garantit une détection fiable des cas hors domaine.

### 5.3 Le Brier « gold-class » n'est pas le Brier multiclasse standard

La QA précise que le score publié est :

```text
moyenne((1 - p_gold)^2)
```

[D05 §5]

Le score multiclasse usuel comporte toutes les classes :

```text
moyenne_sur_exemples(
    somme_sur_classes((p_classe - indicatrice_classe_gold)^2)
)
```

[S03]

Conserver l'ancien nombre sous un nom explicite, par exemple `gold_class_squared_error`. Calculer séparément le Brier multiclasse complet. Une convention de division éventuelle doit être annoncée et constante.

**Test de métrique conseillé :** deux distributions qui ont le même `p_gold` mais répartissent différemment le reste auront la même erreur gold-class, pas nécessairement le même Brier complet.

## 6. Coûts : le résultat est intéressant, l'unité doit être explicite

D05 §4 indique batch 8, warmup 2 et synchronisation CUDA :

| Banc | A2 p50 | A3 p50 | Ratio calculé | Différence |
|---|---:|---:|---:|---:|
| B1 | 40,32 ms | 32,65 ms | 1,235 | +7,67 ms |
| B3 | 51,59 ms | 40,52 ms | 1,273 | +11,07 ms |

Propagation seule : environ 0,59 à 0,66 ms. VRAM allouée indiquée : environ 1 472 à 1 512 MiB dans ce montage.

Ces ratios sont arithmétiquement cohérents. Il faut toutefois préciser si la durée chronométrée est celle d'un lot complet ou une quantité ramenée à un exemple. `it/s` n'est pas forcément `requêtes/s`.

Si, et seulement si, une itération traite un batch complet de 8 :
- 22,6 it/s correspond à 180,8 exemples/s ;
- le temps moyen amorti par exemple n'est pas la latence d'une requête isolée.

Ne pas utiliser cette conversion comme résultat sans vérifier le harnais.

Mesures à ajouter, sans réutiliser les latences V1 :
- batch 1 et batch 8, mêmes entrées et même mode d'exécution ;
- durée depuis texte public, extraction et transferts inclus ;
- nombre d'appels au backbone et nombre de faits traités ;
- échauffement jusqu'à régime stable, répétitions alternées ou ordre randomisé ;
- p50/p95, effectifs, temps par lot, débit en exemples/s ;
- qualité mesurée dans le même mode que le coût ;
- VRAM de pic et état de coexistence éventuelle A2/A3.

Ne pas qualifier 0,6 ms de « gratuit ». Dire « faible dans ce profil ». Le surcoût complet de 23 à 27 % reste la métrique opérationnelle principale.

Si l'objectif initial est un plafond moyen de 1,25, le point B3 à 1,273 n'est pas, seul, une validation de ce plafond. Il faut conserver la règle d'agrégation préfixée, pas en choisir une favorable après observation.

## 7. Routeur : distinction exactitude et économie de calcul

La borne oracle A2 OU A3 apporte seulement 0 à 0,5 point au-dessus d'A2. [D04 §3]

Cela soutient la décision de **ne pas construire un routeur pour augmenter l'exactitude sur ces bancs**.

Cela ne prouve pas qu'un routeur serait inutile pour économiser du calcul. Une politique pourrait, en principe, utiliser une voie moins chère sur certains cas tout en conservant presque la qualité d'A2.

Mais cette possibilité ne justifie pas de le construire maintenant :
- deux adaptateurs distincts peuvent rendre le partage coûteux ;
- un routeur peut ajouter un encodage ;
- le coût de propagation seul est très faible ;
- la marge de gain réelle doit être calculée sur le chemin public complet.

Définir un objectif de latence ou de coût avant d'ouvrir cette branche. Pas de nouveau gate par défaut.

## 8. Les incidents corrigés appellent un audit de dépendances, pas une accusation générale

Les comptes rendus documentent :
- un accès à une tête non entraînée pour l'usage A1 ;
- un loader LoRA qui ne chargeait que 28 clés sur 224 ;
- une évaluation ancrée sur des informations gold au lieu du chemin prédit ;
- le gradient checkpointing non activé dans un run annulé ;
- une archive écrasée lors d'un import sans garde ;
- une différence CPU/GPU d'environ 6 points sur l'ancien lecteur. [D02 §5 ; D03 §2 ; D04 §1 ; D05 §3]

La transparence des correctifs est positive. Il faut néanmoins attacher les correctifs aux résultats précis qu'ils couvrent.

### 8.1 Manifestes de chargement

Pour chaque chemin d'évaluation publié :
- checkpoint, code, tokenizer, données, adaptateur et têtes ;
- liste exacte des noms attendus, chargés, manquants et inattendus ;
- valeurs des tenseurs après chargement comparées au checkpoint, après conversion de dtype attendue ;
- initialisation et adaptateur actifs ;
- prédictions d'un processus neuf comparées à celles de référence.

Un compte 224/224 est nécessaire pour ce checkpoint, pas une preuve suffisante si les noms ou les valeurs ne correspondent pas.

Ne pas déclarer tous les anciens résultats invalides sans preuve. Produire une matrice `run -> loader -> correctif -> replay ou non affecté`.

### 8.2 Inférence strictement publique

La fonction d'inférence doit accepter uniquement une vue publique. Les cibles et traces oraculaires restent dans l'évaluateur ou la loss de training.

Tests proposés :
- retirer ou randomiser les labels, traces et métadonnées privées sans changer la prédiction ;
- vérifier la provenance publique de `p0`, des listes d'entités, spans et masques ;
- distinguer explicitement teacher forcing d'entraînement et prédiction autonome ;
- une erreur de parse doit être déclarée, jamais réparée silencieusement avec la structure privée ;
- supprimer toute normalisation qui cacherait une masse INCONNU/hors candidats sans la rapporter.

Les gardes déjà décrites dans le delta ne sont pas présumées inefficaces. La demande est leur preuve attachée au chemin final, après les changements.

### 8.3 Stabilité numérique et identifiants

PyTorch ne garantit pas des résultats bit-à-bit identiques entre CPU/GPU ou entre certains calculs batchés et non batchés. [S04] Cela n'explique pas automatiquement un écart de plusieurs points.

Comparer à entrées tokenisées identiques :
- sortie du backbone ;
- logits locaux ;
- matrice A ;
- états propagés ;
- réponse finale.

Documenter le premier endroit où la divergence apparaît.

Un tie-break par epsilon peut rendre une décision déterministe, mais peut aussi introduire une préférence pour un index ou un identifiant. Tester :
- permutation des candidats ;
- permutation des faits ;
- bijection de renommage des entités ;
- réindexation interne avec inversion du mapping ;
- cas synthétiques d'égalité réelle.

La stabilité à l'ordre et la stabilité au renommage ne doivent pas être confondues.

## 9. Programme suivant : quatre lots bornés, pas une V3 géante

### Lot C0 : figer et clarifier

Sans entraînement :
1. préserver les checkpoints A2, A3 et V2 ;
2. committer les rapports QA encore modifiés/non suivis ;
3. archiver les prédictions et configs avec hashes ;
4. publier le graphe de dépendances des loaders et la vue d'inférence publique ;
5. corriger NLL, Brier, parser, latences et statut des bancs ;
6. retrouver les prédictions exactes autoritaires si les bornes d'IC diffèrent.

Sorties :
- `v22_release_manifest.json`
- `v22_scope_erratum.md`
- `v22_loader_impact_matrix.md`
- `v22_public_inference_audit.md`

Ne pas modifier silencieusement les anciens scores. Une correction changeant une prédiction crée une nouvelle version identifiée.

### Lot C1 : attribution sans réentraîner

Exécuter R0-hard/R0-soft/R1-hard/R1-soft sur les mêmes représentations enregistrées. Ajouter le parser + solveur exact, avec périmètre de templates explicite.

Mesurer accuracy, relation utile, première divergence, masse INCONNU, effet du validateur et coûts. Vérifier que les informations exactes des oracles restent hors des entrées.

Tracer quelques trajectoires et budgets fixes 0/1/2/4/8/16 sur les mêmes poids et mêmes problèmes. Ce balayage sert au diagnostic ; ne pas utiliser la profondeur privée pour choisir le budget de chaque requête.

Le plateau après atteinte d'un terminal est attendu. Une itération n'est pas une « pensée » par définition : c'est l'application d'une transition.

### Lot C2 : confirmation indépendante

Après C0/C1, figer la méthode finale et sa comparaison principale, puis générer un lot totalement neuf. Les anciens B1-B8 deviennent explicitement des bancs de développement historique.

**Proposition de budget, à figer avant les résultats :**
- une cellule courte et des cellules profondeur 6/8/10 ;
- 400 à 1 000 groupes par cellule selon la précision visée, sans traiter les variantes comme indépendantes ;
- une paire A2/A3 existante pour le premier test de transport ;
- deux paires d'entraînements supplémentaires pour viser trois seeds par voie si l'objectif est une revendication robuste ;
- même protocole de sélection préfixé, sans ajustement après ouverture ;
- aucune extension de domaine simultanée.

Choisir explicitement entre :
- **confirmation du système actuel**, en conservant sa sélection mixte incluant 6/8 ;
- **extrapolation aveugle en profondeur**, avec train ET sélection limités aux profondeurs courtes. Ce second objectif exige de nouveaux entraînements et doit être nommé séparément.

Exemple de critères proposés, non résultats :
- gain principal pratique fixé avant run sur chaînes longues ;
- borne inférieure du delta apparié positive ;
- non-régression courte avec marge préfixée ;
- aucune fuite d'information ni divergence de chargement ;
- qualité et coûts publiés, même si un objectif opérationnel n'est pas atteint.

Il n'est pas nécessaire d'attendre un score parfait ni de continuer jusqu'à obtenir PASS. Publier les résultats et la dispersion, y compris si une seed échoue.

### Lot C3 : une seule extension utile

Uniquement après la confirmation locale, choisir un axe :
- INCONNU avec terminaux explicitement distinguables dans le texte ;
- nouveaux rendus linguistiques indépendants ;
- plusieurs questions sur le même contexte ;
- graphe plus grand, après suppression ou explicitation de la limite d'index.

Ne pas ajouter simultanément cycles, négation, arithmétique, multi-relations, experts, routage et world model.

Pour INCONNU :
- distinguer état terminal déclaré, relation absente, référence absente et horizon épuisé ;
- une absence de relation ne révèle pas à elle seule si le monde est incomplet ou si l'entité est terminale ;
- évaluer faux connus, faux inconnus et masse de probabilité ;
- une augmentation d'entraînement masquée ne remplace pas ce benchmark.

Le score actuel ne permet pas de revendiquer une gestion robuste des mondes partiellement observés. [D05 §6 ; D06 §4]

## 10. Ce qu'il est raisonnable de publier

### Formulation positive, bornée

> Nous étudions une architecture de décision sans génération de raisonnement textuel pour le suivi de relations dans des textes synthétiques. Après avoir observé l'échec d'un correcteur latent libre et les limites d'une interface de graphe discret, nous apprenons des distributions relationnelles utilisées par une propagation explicite. Sur les bancs évalués, cette architecture atteint 99,5 à 100 % d'exactitude et dépasse un modèle direct doté d'une supervision auxiliaire comparable, particulièrement en profondeur. Les mesures de coût réalisées dans le profil batch 8 montrent un surcoût complet d'environ 23 à 27 %. Les résultats sont conditionnels à une seed et à une campagne adaptative ; une confirmation indépendante et une attribution hard/soft restent prévues.

### Formulations à éviter

- « Une preuve universelle que les LLM directs ne composent pas. »
- « Un clone de Jev plus intelligent que Jev. »
- « Une nouvelle découverte de la multiplication de matrices. »
- « Un modèle qui sait toujours quand il se trompe. »
- « Le raisonnement est gratuit. »
- « Toute la différence vient forcément de la conservation de l'incertitude. »
- « Les huit bancs sont huit réplications indépendantes d'entraînement. »
- « OOD aveugle » pour une profondeur utilisée dans la sélection.
- « Le parser est dépassé » avant résolution du conflit 100 %/95 %.

Un compte rendu exploratoire ou une note technique peut être publié avec ces limites. La confirmation renforce la portée, elle ne doit pas devenir un prétexte pour retarder indéfiniment toute communication honnête.

## 11. Prompt de lancement pour l'orchestrateur

```text
Tu reprends le projet Decision Coprocessor après le delta V2.1/V2.2.
A2 est un candidat positif à conserver. Ne reconstruis pas l'architecture.

Lis les neuf documents delta et cet audit. Distingue :
1) résultats rapportés ;
2) interprétations ;
3) inconnues nécessitant lecture du dépôt ;
4) nouvelles expériences.

Commence par C0 :
- identifie le chemin d'inférence réel A2, y compris le rôle éventuel de l'exécuteur S ;
- audite les chargements de tous les checkpoints comparés ;
- relie le bug LoRA 28/224 et les correctifs gold/pred aux runs réellement concernés ;
- prouve que l'inférence n'accède qu'aux données publiques ;
- résous les incohérences parser 100 %/95 %, bornes d'IC et unités de coût ;
- renomme l'erreur gold-class, calcule le Brier multiclasse, retire l'interprétation
  « NLL élevée = sait qu'il échoue » ;
- archive la release et les prédictions autoritaires sans écraser l'historique.

Puis C1, sans entraînement :
- calcule une seule fois les logits fact-level de chaque lecteur ;
- compare hard+solveur et soft+propagation avec p0, terminal, INCONNU, horizon,
  candidats et politiques de validation identiques ;
- ajoute le parser public + solveur comme solution bornée aux templates ;
- mesure les effets par groupe et publie toutes les cellules, même nulles ou négatives.

Après C0/C1, rédige un protocole C2 unique avant de générer de nouveaux tests :
- modèle final figé ;
- comparaison principale figée ;
- données, annotations, initialisation et coûts cumulés documentés ;
- jeux entièrement neufs, hors de la campagne adaptative B1-B8 ;
- critères pratiques et statistiques explicites ;
- distinguer confirmation du système actuel et extrapolation aveugle en profondeur.

Aucun changement d'architecture, routeur, world model ou banque d'experts dans cette
phase. Ne remplace pas une conclusion locale par un verdict universel.
Si hard et soft sont équivalents, publie-le : cela ne nie pas la valeur d'une interface
apprise suivie d'un calcul explicite.

Utilise CPU pour données/solveurs/statistiques et GPU pour lecture/entraînement.
Un seul job GPU à la fois. Chaque script est versionné avant usage, chaque run est
enregistré, les probabilités sont sauvegardées et les métriques sont recalculables.

Livre un rapport qui répond :
- A2 se reproduit-il avec le chargement strict ?
- quel facteur explique le gain mesuré ?
- conserve-t-on un avantage sur un test final indépendant ?
- quel est le coût réel batch 1 et batch 8 ?
- quelle formulation exacte peut-on soutenir ?
```

## 12. Références documentaires

| ID | Pièce jointe | Utilisation |
|---|---|---|
| D00 | `00-INDEX-DELTA.md` | périmètre, synthèse et tableau central |
| D01 | `01-AUDIT-VALIDATION-V2.md` | prescriptions de l'audit précédent |
| D02 | `02-V2.1-VALIDATION-INDEPENDANTE.md` | tests figés, diagnostics, parser et R7 |
| D03 | `03-V2.2-A1-A1BIS.md` | changement d'interface, mauvais accès A1, sélection 2213 |
| D04 | `04-V2.2-A2-A3-ROUTEUR.md` | entraînements A2/A3, résultats, borne oracle et probabilités |
| D05 | `05-V2.2-CLOTURE-COUTS-QA.md` | coûts, incidents, QA et limites |
| D06 | `06-RENVERSEMENT-ET-PORTEE.md` | interprétations et suites |
| D07 | `07-ETAT-DEPOT-DELTA.md` | commits et état non committé |
| D08 | `08-GUIDE-VERIFICATION-DELTA.md` | artefacts sources à retrouver dans le dépôt |

## 13. Vérifications méthodologiques externes

Ces sources éclairent les distinctions de cet audit. Elles ne vérifient pas les expériences du projet.

- **S01.** Cawley & Talbot, *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*, JMLR, 2010. Le choix d'un modèle sur un critère fini peut lui-même surajuster.  
  `https://www.jmlr.org/papers/v11/cawley10a.html`
- **S02.** Guo et al., *On Calibration of Modern Neural Networks*, ICML/PMLR, 2017. Définition opérationnelle de la calibration et méthodes de calibration.  
  `https://proceedings.mlr.press/v70/guo17a.html`
- **S03.** Documentation officielle scikit-learn, `brier_score_loss`, consultée le 25 septembre 2026. Formule multiclasse et conventions d'échelle.  
  `https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html`
- **S04.** Documentation officielle PyTorch, *Numerical accuracy*, consultée le 25 septembre 2026. Différences possibles entre plateformes et calculs batchés.  
  `https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html`
- **S05.** Yang, Yang & Cohen, *Differentiable Learning of Logical Rules for Knowledge Base Reasoning*, NeurIPS 2017, arXiv:1702.08367. Raisonnement différentiable par composition d'opérations, dans un autre cadre expérimental.  
  `https://arxiv.org/abs/1702.08367`

## Conclusion

Il ne manque plus une idée vaguement prometteuse : un système positif a été observé.
Il manque surtout une attribution plus propre, un chargement vérifié de bout en bout et
une confirmation finale distincte de la campagne exploratoire.

**Conserver A2. Comparer discret et continu à lecteur fixé. Confirmer une fois proprement.
Puis publier la réussite locale et étendre un seul axe.**

## Annexe : identité des neuf fichiers reçus

SHA-256 des pièces jointes accessibles lors de cet audit. Ces empreintes ne sont pas celles des runs du dépôt.

| Fichier | SHA-256 |
|---|---|
| `00-INDEX-DELTA.md` | `c286745c7c8282ebe230cc0a50151d8173a401321edc569ef04d7a489a8e08e8` |
| `01-AUDIT-VALIDATION-V2.md` | `e56ddb6804a6d7297ec14e4a48387b08dc836edc6607acde3cdebf5094f3a350` |
| `02-V2.1-VALIDATION-INDEPENDANTE.md` | `044eea1c099ac5e7f86b1fe51fbb4cb479391b37b2ab24f8cd254cc2aa1417ce` |
| `03-V2.2-A1-A1BIS.md` | `f64d2411597b0dc25452845b8cca5ac94959e6c18cf1523d080c7bfe746d6ba1` |
| `04-V2.2-A2-A3-ROUTEUR.md` | `f0b11c5241bfc5ff2b531bf46a73e26b0cb6070093652acf582c48a2da89ede3` |
| `05-V2.2-CLOTURE-COUTS-QA.md` | `559bea0e3584ccb63d289b8daa97889b6e808ff88a39dcd9e39f2ab4607f6212` |
| `06-RENVERSEMENT-ET-PORTEE.md` | `5ab10906dc873dc9585ea36a4bb24e3df8eaefd1fcc790f253fa0ead230d36cb` |
| `07-ETAT-DEPOT-DELTA.md` | `84f6cb31d3a086812db66cde578c1830f51f44f045284850deddbf29bc42ea5e` |
| `08-GUIDE-VERIFICATION-DELTA.md` | `2886a390e69914795475c8f946d9d91393ce72b56a0f34a3b9eb8319d6aa1081` |
