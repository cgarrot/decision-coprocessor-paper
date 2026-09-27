# AUDIT DE CLÔTURE FINALE : Decision Coprocessor, V1 à E2-bis

## Verdict : CLOS AVEC RÉSIDUS

**Non : le dossier ne permet pas d'attester « entièrement terminé, cohérent et sans résidu ». La campagne expérimentale peut rester arrêtée, mais sa clôture documentaire n'est pas complète.**

Les résidus bloquants ci-dessous bloquent l'attestation **sans résidu**, pas l'arrêt des entraînements et pas l'existence des résultats positifs. Aucun ne justifie de réclamer une nouvelle expérience.

L'inspection porte sur les comptes rendus accessibles, jusqu'à l'état du **27 septembre 2026 vers 06:00**, et sur les recommandations retracées dans notre conversation. Je n'ai ni inspecté le dépôt ni rejoué les modèles. Les recherches et tentatives de relecture n'ont pas permis de récupérer intégralement certaines pièces anciennes de V1/V2 : les déclarations historiques correspondantes ne sont donc pas une certification renouvelée de leurs archives.

Le dernier guide contient lui-même une rubrique « Ce qui reste en suspens » : documents non figés, comptes d'évaluations à préciser et livrables à consolider. Il interdit à lui seul une attestation documentaire sans réserve. [D5]

## 1. Exhaustivité des clôtures

| Phase | Constat de clôture | Limite de l'attestation |
|---|---|---|
| **V1** | Le résultat négatif et la clôture sont repris dans l'historique final. | Le triplet originel verdict + validation QA + registre, ainsi que le bundle complet, ne sont pas reconsultables dans les pièces récupérées pour cette inspection. **Clôture déclarée, non recertifiée ici.** |
| **V2** | L'historique conserve « S démontré ; T réfuté sur dev court ». | Même limite documentaire sur la clôture d'origine. Ne pas transformer ce résultat local en réfutation générale de la décomposition. |
| **V2.1** | Le renversement en profondeur est conservé dans l'historique et l'audit suivant. | La validation QA et le registre de cette phase d'origine ne sont pas directement vérifiables dans les pièces récupérées. |
| **V2.2** | La clôture est corroborée rétrospectivement par C0/C1 : attribution, ablation, chargement et identité des sorties. | Cela n'équivaudrait pas à certifier chaque ancien run annulé ou chaque conclusion plus générale. |
| **C0/C1** | Clôture documentée, avec références REG-82 à REG-85 et artefacts de contrôle. | La complétude du manifeste de release demeure un sujet distinct. |
| **C2** | Clôture étayée : protocole, rapport, REG-86, confirmation sur trois seeds et expérience blind séparée. | Trois seeds pour C2-a, une par voie pour C2-b ; ne pas fusionner ces effectifs. |
| **V2.3 E1/E2/E3** | Verdicts et QA REG-87/88/89/91/92 documentés. P0 restaure ensuite les 24 évaluations manquantes et le total 120/120. | La synthèse finale doit utiliser les deux seeds restaurées, pas seulement l'ancienne courbe à 0,680. |
| **P2** | Exécution, registre et avis QA REG-93 documentés. | **Clôture avec réserves**, pas démonstration causale intégrale : les réserves QA contredisent encore certains résumés. |
| **E2-bis** | Fin d'exécution et QA REG-94 explicites ; porte d'exactitude passée sur les deux seeds A2. | Le seuil INCONNU échoue, le domaine d'entraînement est décrit de façon contradictoire et le compte d'évaluations reste à préciser. **Clôture à résultat partiel.** |

Les déclarations historiques des premières phases figurent dans l'index final. Les références précises des contrôles C0/C1/C2 sont données dans le guide précédent. [D6] [D8]

Les validations V2.3 et la restauration P0 sont explicitement tracées ; je ne les remets donc pas en attente. Les réserves finales P2 et E2-bis figurent également dans les documents, et doivent rester attachées à leurs verdicts. [D11] [D7] [D2] [D1]

**Réponse au point 1 : toutes les phases sont annoncées terminées, mais toutes ne disposent pas d'un certificat de clôture complet reconstituable ici. P2 et E2-bis ont, en outre, des réserves explicites.**

## 2. Suivi des recommandations des audits

Je couvre les quatre familles d'audits demandées, ainsi que la revue intermédiaire C2 → V2.3, que les documents numérotent comme quatrième revue. Une proposition de recherche n'est pas automatiquement une obligation de clôture.

### Audit V1-relance

Le passage d'un correcteur libre à une représentation structurée, l'apprentissage des transitions et la séparation entre lecture et exécution sont bien présents dans la suite retracée. Le résultat négatif V1 n'a pas été effacé.

En revanche, **je ne peux pas signer un suivi exhaustif, point par point, du premier audit et de son bundle à partir des seules pièces anciennes récupérables**. C'est une limite documentaire, pas la preuve que ces travaux ont été omis. Les addenda V1 sont encore indiqués comme non committés à l'état final. [D2] [D2]

### Audit V2-validation

Les suites retracent la validation sur nouveaux bancs, la comparaison avec un direct adapté, puis la confirmation et la distinction entre sélection courte et sélection mixte. Ces demandes ont bien produit des travaux ; elles ne doivent pas être relancées au titre d'un audit de clôture.

La même limite subsiste pour l'exhaustivité des recommandations initiales : leur traitement fonctionnel est largement retracé, mais les deux premiers audits complets et leurs pièces de clôture ne sont pas tous reconsultables. L'audit V2.2 rappelle les résultats V2.1/V2.2 ; C2 fournit ensuite les contrôles de confirmation. [D9] [D12]

### Audit V2.2-confirmation

**Traités selon les documents :** rôle exact de l'exécuteur S, ablation hard/soft à lecteur fixé, comparaison A3, anti-fuite, correction NLL/Brier, clarification du parser, attribution des IC, coûts batch 1 et 8, contrôle des loaders, confirmation sur nouveaux bancs et séparation C2-a/C2-b. Le plafond de coût non validé est assumé, ce qui est une clôture honnête de cet objectif, pas un oubli à réparer. [D13] [D13] [D14] [D12]

**Résidus :** la release consolidée et la complétude finale de son manifeste ne sont pas attestées. L'ancien contrôle hard/soft n'établit pas automatiquement la même attribution pour tous les checkpoints ultérieurs.

### Revue intermédiaire C2 → V2.3

La séparation des rôles `P_eval`, `V_sem`, `Renderer` et `PublicAdapter`, l'interdiction du round-trip circulaire, les niveaux linguistiques séparés, le lot adverse distinct, le GO E2 séparé et les trois questions d'évaluation sont documentés. Coréférence, négation et plusieurs relations par unité ont été explicitement différées : **ce ne sont pas des oublis**. [D10] [D15]

**Résidu :** la description sémantique et technique du parser/adaptateur étendu reste incomplètement soldée dans l'état final.

### Audit V2.3-diagnostic-V24

**Traités :** restauration sans réentraînement, retour à deux seeds E2 par voie, diagnostic avant l'expérience suivante, non-mélange avec les mondes partiels, conservation des résultats négatifs locaux et correction annoncée des formulations excessives.

**Partiellement traités :** anti-écrasement, manifeste de provenance et schéma du parser. Le refus de réécriture avec `FORCE_EVAL` est documenté ; la conservation de chaque tentative distincte et la publication atomique demandées ne sont pas attestées dans la synthèse finale. [D7] [D4]

**Écarts explicitement acceptés par la QA :** O1 indisponible ou partiel, V4 non exécuté, H-A seulement partiellement soutenue. Ils peuvent être clos comme limites acceptées, sans les exécuter maintenant ; ils ne peuvent pas être décrits comme des contrôles entièrement réussis. [D2]

**Report correctement identifié :** la contrainte de cohérence can↔inv n'a pas été exécutée et reste une option ultérieure. Aucun reliquat expérimental n'en découle dans le périmètre clos. [D1]

## 3. Cohérence interne des chiffres et des critères

### Chiffres centraux cohérents

Les calculs suivants sont cohérents avec les nombres publiés :

| Élément | Vérification |
|---|---|
| C2-a : +65,30 / +64,05 / +68,14 points | Moyenne **+65,83 points** |
| A2 C2-a : 0,9950 / 0,9983 / 0,9983 | Étendue **0,33 point** |
| E3 restauré : 0,797 contre 0,680 à p10 | Étendue **11,7 points**, cohérente avec « environ 12 » |
| E2-bis : 0,930 et 0,900 à p10 | Porte 0,85 passée dans les deux cas ; étendue **3 points** |

La dispersion de 0,33 point concerne **l'exactitude d'A2 dans C2-a**, pas toutes les expériences du projet ni la dispersion des gains A2-A3, qui est de 4,09 points dans ce tableau. Les pièces distinguent les seeds lorsqu'elles présentent les tableaux complets. [D12] [D7] [D1]

### Incohérence majeure : le domaine réel d'E2-bis

Le protocole résumé annonce une **couverture « in-domaine » des inversions profondes**, mais décrit des re-rendus d'E5v2_train aux seules profondeurs **1 à 4**, avec sélection courte. Le titre et la recommandation parlent pourtant d'entraîner les inversions « aux profondeurs variées » pour couvrir le profond. [D1] [D3]

Deux explications sont possibles : le résumé de l'entraînement est erroné, ou la qualification « in-domaine » l'est. **Je ne choisis pas à la place des artefacts exécutés.**

Il faut solder cette contradiction par les configurations et données déjà utilisées. Si elles sont effectivement limitées à 1-4, on ne peut pas dire que la profondeur 10 a été couverte à l'entraînement. Cela n'autorise pas non plus à rebaptiser rétroactivement E2-bis « aveugle » : la campagne avait déjà observé les bancs profonds.

### Résultat partiel : un seuil préfixé n'est pas atteint

| Critère E2-bis annoncé | État attesté |
|---|---|
| Exactitude inv×p10 ≥ 0,85 | **Passé : 0,930 / 0,900** |
| Masse INCONNU ≤ 0,25 | **Échoué : 0,38-0,41** |
| Non-régression, marge de deux points | **Validée selon REG-94**, mais les différences appariées et leur référence ne sont pas reproduites dans le résumé |
| Gain A2-A3 profond avec IC bas > 0 | Critère annoncé ; **bornes finales non reproduites dans ces pièces** |

Le seuil échoué est publié honnêtement. Ce qui reste à préciser est **la règle de verdict préfixée** : « PASS COUVERTURE » est-il un verdict limité à l'exactitude, avec échec d'un objectif mécaniste secondaire, ou certains critères étaient-ils requis conjointement ? Une validation QA ne permet pas de déduire cette hiérarchie lorsqu'elle n'est pas donnée. [D1] [D1]

Le bilan peut parfaitement rester clos avec un objectif échoué. Il doit seulement porter un verdict explicite de **succès partiel**, sans requalifier après coup le seuil manqué.

### Autres écarts à solder

Le compte **83 répertoires contre 76 annoncés** demeure ouvert en REG-94. Il faut les classer en évaluations officielles, pilotes, reprises ou résultats invalidés ; il n'est pas démontré que sept évaluations requises manquent. [D1]

La chronologie P2 indique une exécution vers **21:55** et un diagnostic à **22:01**, alors que le texte annonce environ **40 minutes GPU**. Le périmètre temporel ou l'unité est à préciser ; je n'en déduis pas une violation du préenregistrement. [D3] [D2]

« Doubler » la part d'inversions est inexact : **25 % → 45 % = ×1,8**, soit +20 points. C'est une correction rédactionnelle, pas une contestation des scores. [D1] [D1]

## 4. Incidents : documentés et soldés jusqu'où ?

| Incident | Statut documentaire de clôture |
|---|---|
| **Tags et évaluations écrasées** | Corrigés puis restaurés : les 24 évaluations perdues sont rejouées, 120/120 annoncé. Ne plus conserver « mono-seed » comme état final. |
| **Fixes remplacés, double définition de `parse_state_v2`, arrêt exit-99** | Incidents et correctifs décrits ; anciens résultats L3 remplacés. Le contrôle d'exécution existe selon les comptes rendus. |
| **Longueur >512 dans C2** | Cause précisée, exclusion commune d'un exemple, huit évaluations rejouées. |
| **Chemin de sélection E2-bis** | Refus strict puis correction tracée. La correspondance finale chemin → contenu → seed → hash n'est pas explicitée dans le delta. |
| **LoRA partiellement chargé** | Matrice d'impact et contrôles de chargement référencés par C0. |
| **CPU/GPU et toolchain** | Divergence localisée ; environnement de publication déclaré et rejoué. Cela ne certifie pas toute plateforme. |
| **Ancien OOM et selftest V1** | Pas de dossier complet de résolution reconsultable ici : **non recertifiables**, pas déclarés non corrigés. |

Les restaurations et correctifs récents sont étayés. Les sources distinguent aussi la toolchain de publication rejouée sans flip et une autre version donnant des différences. [D7] [D15] [D12] [D13] [D17]

**Je ne peux pas attester la phrase universelle « aucun chiffre n'a jamais été publié depuis un état cassé ».** Des chiffres antérieurs ont été remplacés et certaines anomalies n'étaient plus rejouables par la QA. La formulation défendable est : **les résultats finaux doivent être ceux explicitement conservés après correction, avec les anciens résultats marqués comme remplacés**. [D15] [D16]

Je n'identifie pas, dans le dernier delta, de nouveau score final **démontré** comme issu d'un chargement cassé. Ce n'est pas une preuve exhaustive d'absence d'incident.

## 5. Résidus et portes encore ouvertes

### Ce qui est réellement un résidu de clôture

L'état final signale toujours des registres modifiés, des rapports QA non suivis, l'audit non tracké et les addenda V1 non committés. Certains livrables de provenance restent « à vérifier » ou « à consolider ». **Le dernier commit nommé n'est donc pas attesté comme contenant tout l'état publié.** [D2] [D2]

Il n'est pas nécessaire de tout mettre dans Git. Une archive externe complète et identifiée conviendrait. Mais le dossier n'atteste pas cette substitution finale.

Le schéma `v23_adapter_flow.md` reste lui aussi parmi les sorties à consolider. La mention « parser étendu P1 » dans la chronologie ne décrit pas quelles informations il fournit effectivement à l'inférence. **C'est un manque de traçabilité, pas une preuve de fuite.** [D2] [D5]

### Ce qui n'est pas un résidu bloquant

La cohérence can↔inv, la sémantique des mondes partiels, la coréférence et les extensions ultérieures peuvent rester non réalisées. Les documents les placent hors périmètre ou en attente d'un nouvel arbitrage. **Leur non-exécution n'empêche pas de fermer le projet présent.** [D10] [D1]

La fuite résiduelle INCONNU n'oblige pas non plus à poursuivre l'entraînement. Elle doit être classée comme **limitation mesurée et objectif non atteint**, puis laissée telle quelle.

Enfin, « en attente d'arbitrage V2.4 » ne constitue pas une porte d'exécution déjà autorisée. Aucune nouvelle expérience ne doit être implicitement incluse dans la présente clôture.

## 6. Les formulations sont-elles maintenant toutes correctes ?

**Non. La hiérarchie est largement respectée, mais trois surinterprétations subsistent.**

### P2 : le résumé est plus affirmatif que l'avis QA

Le fichier P2 annonce H-B rejetée, les variations contrôlées archivées et un mécanisme identifié. Mais le commit QA suivant précise : **H-A partielle, O1 indisponible et rejet H-B plus faible parce que V4 n'a pas été exécuté**. [D3] [D2]

Le verdict final doit suivre cette réserve :

> Les mesures sont compatibles avec une composition d'erreurs relationnelles et une accumulation de masse INCONNU ; l'attribution reste partielle, certains contrôles prévus n'ayant pas été exécutés ou disponibles.

Le rejet de H-C ne réfute pas toute perte de masse : il concerne la version particulière supposant un top-1 supérieur à 0,99. Le dossier peut donc constater une accumulation INCONNU tout en rejetant cette hypothèse particulière.

### « Un plafond de données existe » n'est pas établi

Le résidu 0,38-0,41 est une observation de l'expérience. **Il ne démontre pas l'existence d'un plafond de données**, alors que le rapport emploie cette formulation. Une amélioration possible par cohérence reste une piste non testée, non une conséquence établie. [D1]

De même, l'argmax correct malgré une masse INCONNU importante ne certifie pas une distribution calibrée ni une politique d'abstention satisfaisante.

### Les conclusions globales doivent garder leur périmètre

« Décomposition réfutée » ne vaut que pour la comparaison locale concernée ; « supériorité architecturale » vaut pour les modèles et bancs comparés ; la borne oracle du routeur ne tranche pas tous les objectifs de coût ; « non-régression totale » ne signifie pas identité des scores lorsque la marge autorisée est de deux points.

Ces restrictions n'amoindrissent pas les résultats : elles évitent de transférer une conclusion d'une phase vers toutes les autres. Les formulations plus fortes laissées dans des documents historiques peuvent rester comme archives, **à condition qu'une synthèse finale fasse explicitement foi et les remplace**.

## 7. Reproductibilité : les éléments suffisent-ils à rejouer chaque verdict ?

**Pas suffisamment attesté dans l'état final.**

Les préenregistrements, hashes, checkpoints référencés, fichiers de prédictions, outils de QA et replay constituent une base sérieuse. P0 prouve notamment que les checkpoints existants ont permis de restaurer les évaluations perdues ; C1 rapporte également un replay exact dans l'environnement de publication. [D7] [D14]

Mais une empreinte identifie un fichier ; elle ne prouve ni sa disponibilité dans la release ni la complétude de toutes ses dépendances.

Pour le verdict « chaque phase rejouable », il manque encore une référence finale qui relie **le verdict, les fichiers faisant autorité, le code, les poids, les données, l'environnement, la commande et les exclusions**. Les comptes 83/76, le schéma d'adaptateur et les fichiers non figés empêchent d'attester cette chaîne intégrale. Le manifeste V2.2 était encore indiqué comme à compléter dans le dossier précédent, sans preuve de fermeture définitive ici. [D5] [D11]

Il s'agit de **rassembler et qualifier les artefacts existants**, pas de refaire les entraînements, de refaire C2 ou d'exiger un nouveau benchmark.

## Liste priorisée des résidus

### Bloquants pour l'attestation « sans résidu »

| ID | Résidu | Ce qui permet de le solder sans expérience nouvelle |
|---|---|---|
| **B1** | **Domaine E2-bis contradictoire** : couverture « in-domaine » profonde, mais entraînement décrit en 1-4 seulement. | Faire foi à partir des configurations/données exécutées et corriger titre, protocole résumé et conclusion. Référence : `04-E2BIS.md`, §1. |
| **B2** | **Verdict multi-critères incomplet** : seuil INCONNU échoué ; hiérarchie de succès partiel non explicitée ; tableau de non-régression et IC non repris. | Rattacher les critères à leur statut préfixé et aux résultats déjà archivés ; fermer explicitement l'objectif échoué. Référence : `04-E2BIS.md`, §1-4. |
| **B3** | **Réserves QA P2 non propagées aux résumés** : V4 non exécuté et H-A partielle, contre récit de rejet du contexte et causalité entièrement élucidée. | Publier un verdict canonique avec contrôles non réalisés et limite acceptée. Références : `03-P2-DIAGNOSTIC-DECISIF.md`, §2-4 ; `05-ETAT-DEPOT.md`, commit `20a29e54`. |
| **B4** | **Release et inventaire non soldés** : fichiers non figés, manifeste incomplet ou non attesté, 83/76 non réconcilié, premières clôtures non recertifiables. | Désigner l'archive finale, classer les évaluations officielles/reprises, rattacher les pièces de clôture existantes. Références : `05-ETAT-DEPOT.md`, §3-4 ; `06-GUIDE-VERIFICATION.md`, §3. |
| **B5** | **Flux parser/adaptateur toujours non consolidé** : attribution des entrées publiques et des rôles sémantiques non complètement traçable. | Joindre le schéma existant ou documenter le chemin réellement exécuté, sans inventer une fuite ni une capacité. Référence : `06-GUIDE-VERIFICATION.md`, §3. |

Ces cinq points sont des obstacles à la certification documentaire complète. Les pièces citées les attestent directement ou signalent explicitement leur statut encore ouvert. [D1] [D1] [D2] [D5]

### Mineurs

**M1. Définition des masses et de la règle de décision.** Le tableau donne 0,38-0,41 pour INCONNU et 0,46-0,69 pour le terminal correct sans associer explicitement populations, profondeur, checkpoint et normalisation. Si les bornes décrivaient exactement les mêmes populations normalisées, 0,69 + 0,38 dépasserait 1 ; ce n'est pas une preuve de tenseurs invalides, mais la preuve que leurs périmètres doivent être explicités. Même nécessité pour l'argmax : candidats seuls ou candidats avec INCONNU ? Référence : `04-E2BIS.md`, §3. [D1]

**M2. Portée du dispositif anti-écrasement.** Blocage et `FORCE_EVAL` sont documentés ; la conservation des versions antérieures, l'identité par hashes et la publication atomique ne le sont pas complètement. Références : `02-P0-RESTAURATION.md`, §1 ; audit 5, contrat anti-écrasement. [D7] [D4]

**M3. Chronologie et conventions récapitulatives.** Réconcilier les 40 minutes GPU de P2 avec la fenêtre indiquée ; ne pas mélanger dispersion A2 de C2, dispersion des gains et dispersion E3 ; étiqueter les tableaux historiques comme remplacés. Les chiffres centraux vérifiés ne sont pas contestés.

### Cosmétique

**C1. « Doubler » 25 % → 45 %.** Remplacer par « augmenter de 25 % à 45 % » ou « multiplier par 1,8 ». Aucun impact sur le verdict expérimental. [D1] [D1]

## Les trois questions pour une éventuelle reprise V2.4

1. **Fuite résiduelle :** le prochain objectif serait-il d'améliorer la décision top-1, la distribution complète ou la réduction de masse INCONNU, et quel compromis accepterait-on entre ces trois objectifs ?
2. **Sémantique d'INCONNU :** distingue-t-on explicitement un terminal déclaré, un fait manquant, une incertitude de lecture et un budget de calcul épuisé, ou ces situations sont-elles actuellement regroupées ?
3. **Cohérence can↔inv :** quel invariant relationnel veut-on imposer entre formulations équivalentes, tout en restant sensible aux reformulations qui inversent réellement la relation ?

Ces questions appartiennent à une reprise éventuelle. Elles ne sont ni des conditions nouvelles de clôture ni des expériences demandées maintenant.

## Une phrase sur ce qui a été établi

**Dans un domaine synthétique français de suivi de relations, un lecteur adapté couplé à une propagation explicite de distributions a dépassé les modèles directs comparés, avec confirmation et généralisation en profondeur dans les conditions documentées, puis atteint 90 à 93 % sur les inversions à profondeur 10 après E2-bis, sans éliminer la masse INCONNU résiduelle ni établir une capacité générale de raisonnement ou une validation produit.** [D12] [D1]


## Références documentaires de cette inspection

Les codes renvoient aux comptes rendus transmis, pas à une lecture du dépôt original. Les documents historiques sont datés pour éviter de confondre leur état avec celui du dernier delta.

- [D1] `04-E2BIS.md` : Delta 4, E2-bis.
- [D2] `05-ETAT-DEPOT.md` : Delta 4, état au 27 septembre vers 06:00.
- [D3] `03-P2-DIAGNOSTIC-DECISIF.md` : Delta 4, P2.
- [D4] `01-AUDIT-V23-DIAGNOSTIC-V24.md` : Delta 4, compte rendu de l'audit 5.
- [D5] `06-GUIDE-VERIFICATION.md` : Delta 4, guide final.
- [D6] `00-INDEX(2).md` : Delta 4, index final.
- [D7] `02-P0-RESTAURATION.md` : Delta 4, restauration P0.
- [D8] `08-GUIDE-VERIFICATION.md` : Delta C0-C2, guide.
- [D9] `01-AUDIT-V22-CONFIRMATION.md` : Delta C0-C2, compte rendu de l'audit 3.
- [D10] `01-REVUE-C2-AMENDEMENTS-V23.md` : Delta V2.3, compte rendu de l'audit 4.
- [D11] `07-GUIDE-VERIFICATION.md` : Delta V2.3, guide.
- [D12] `05-C2-CONFIRMATION-EXTRAPOLATION.md` : Delta C0-C2, confirmation.
- [D13] `02-C0-FIGER-CLARIFIER.md` : Delta C0-C2, C0.
- [D14] `04-C1-ABLATION-2x2.md` : Delta C0-C2, C1.
- [D15] `02-V23-E1.md` : Delta V2.3, E1.
- [D16] `04-V23-E3.md` : Delta V2.3, E3 avant restauration P0.
- [D17] `03-RESERVES-RA-A-RE.md` : Delta C0-C2, réserves.
