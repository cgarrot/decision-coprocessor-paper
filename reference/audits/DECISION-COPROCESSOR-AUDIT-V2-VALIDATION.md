# Decision Coprocessor : audit de la V2 et programme de validation ciblée

Date : 25 septembre 2026.

## 0. Portée

Revue des douze fichiers de compaction V1+V2 remis le 25 septembre. Les sources sont les comptes rendus fournis, pas le code exécuté, les poids ou les prédictions originales. Aucun entraînement ni benchmark du projet n’a été reproduit ici. Les chiffres sont ceux du dossier, sauf les calculs explicitement présentés comme illustratifs.

Ce document distingue les observations documentées, leur interprétation, les hypothèses à tester et les propositions d’expériences. Les références D00 à D11 désignent les pièces du dossier ; les références S01 à S04 sont des recherches externes ciblées.

**Ce document ne recommande pas de reconstruire tout le projet.** Il recommande de préserver V1 et V2, de clarifier la portée des conclusions et de réaliser quelques expériences discriminantes avant de modifier l’architecture.

## 1. Conclusion principale

La V2 est un progrès expérimental, pas un second échec total.

L’étage S démontre, dans le domaine expérimenté, qu’un petit exécuteur entraîné peut réutiliser une transition et suivre des chaînes plus longues. L’étage T montre que, sur le développement E5v2 et pour les checkpoints mesurés, le direct adapté est nettement meilleur que la voie texte vers graphe vers exécuteur. [D07 ; D08]

La formulation précise devrait être :

> Le calcul récurrent fonctionne sur des relations structurées dans le domaine étudié. La chaîne de traitement décomposée testée reste inférieure au direct adapté sur un développement synthétique à chaînes courtes. La généralisation textuelle, la variabilité entre entraînements et l’intérêt d’un coprocesseur complémentaire restent à évaluer.

Cela ne prouve ni que toute décomposition textuelle est inutile, ni que le direct est un produit validé. L’arrêt de cette branche exploratoire est raisonnable ; une réfutation générale ne l’est pas.

## 2. Ce qui a effectivement progressé

### 2.1 Exécution structurée

| Expérience | Résultat rapporté | Portée correcte |
|---|---:|---|
| E1 | 128/128 trajectoires et réponses correctes | Contrôle de surapprentissage |
| E2 | 919/919 transitions conditionnelles correctes | Transition sur graphes inédits avec état d’entrée exact |
| E3 | 1,000 en trajectoire autonome | Composition dans le pool décrit |
| E3, budget k | 0,188 à k=0 ; 1,000 à k=4 | Utilité des itérations pour cette expérience |
| E4 | 1,000 aux profondeurs 6, 8 et 10 | Extrapolation structurée ; 369/399 exemples évaluables |
| E4b | 399/399 après passage à pad20 | Réentraînement sur E3_train avec réindexation, puis évaluation de profondeur |

Sources : D06 §2 ; D07 §2 à §5.

Les corrections E0 du pointeur non réinjecté et des terminaux gelés trop tôt sont importantes. Les tests d’état ont permis de localiser des erreurs que le score final ne suffisait pas à expliquer. Elles ne prouvent pas rétrospectivement que la V1 contenait les mêmes bugs. [D07 §1]

L’exécuteur n’a pas appris sans structure préalable : graphe, pointeur initial, dynamique locale, supervision des états et comportement absorbant définissent fortement le problème. C’est une conception raisonnable. Le résultat est une preuve de concept d’exécution bornée, pas une preuve de raisonnement général. [D06 §2 et §3]

**Nuance E4b :** la réindexation aléatoire pendant le réentraînement expose les nouvelles colonnes d’identité. Ce n’est donc pas une démonstration que des colonnes jamais vues sont correctement traitées. Distinguer nouvelles combinaisons de graphes, nouvelle profondeur et nouvelle dimension d’entrée. [D07 §5]

La comparaison S avec le direct à 0,204 porte sur ce contrôle précis. La compaction ne décrit pas assez son architecture pour conclure que toute solution directe sur graphe est incapable de résoudre la tâche. Un parcours déterministe du graphe reste le contrôle de référence.

### 2.2 Connexion au langage

Développement E5v2, n=411, seed 17 :

| Voie ou mesure | Résultat |
|---|---:|
| Mémoire exacte vers exécuteur | 100 % |
| Mémoire prédite vers solveur exact | 76,16 % |
| Pipeline avec abstention préenregistrée | 76,16 % |
| Pipeline naked | Environ 82 %, d’après le delta arrondi publié |
| Direct adapté | 100 % |
| F1 d’arêtes du lecteur | 0,9278 |
| Validité / abstention | 0,917 / 0,083 |

Source : D08 §4.

L’adaptation a aidé les deux voies. Le direct passe de 0,287 dans le comparateur gelé concerné à 1,000 ; la voie avec graphe progresse de 0,248 à 0,762. Ce n’est pas une victoire du pipeline, mais le lecteur a effectivement appris davantage. [D08 §3 et §4]

### 2.3 Le point mixed de l’audit précédent est résolu

L’annexe V1 précise que le mélange portait sur l’axe batch, chaque exemple recevant la mémoire d’un autre. L’hypothèse d’une simple permutation invariante des positions ne décrit donc pas cette intervention. Ce point de mon audit précédent est résolu par l’information nouvelle. La distinction entre branche H inutilisée et faits absents reste valable. [D05 §3]

## 3. Les conclusions à corriger

### 3.1 Développement, confirmation et décision de travail

Le résultat final T utilise 411 exemples de développement et une seed par voie. Le test E5v2_eval est resté scellé. Les checkpoints ont été sélectionnés et plusieurs itérations ont été examinées sur Dev. [D08 §3 et §4 ; D09 §5 et §6]

Le delta de −23,84 points suffit à ne pas privilégier ce pipeline dans les conditions mesurées. Il ne transforme pas Dev en test indépendant.

Un intervalle obtenu en rééchantillonnant des exemples ou des groupes, pour des checkpoints fixés, ne mesure pas :

- la variabilité entre graines d’entraînement ;
- le changement de domaine ;
- l’incertitude introduite par la sélection adaptative sur Dev.

La phrase de D09 selon laquelle la borne du delta rend la conclusion robuste à la seed doit être corrigée. Un écart important n’est pas une mesure de la variabilité non observée.

Figer chaque configuration avant son run assure de la traçabilité. Cela ne transforme pas une campagne adaptative en protocole confirmatoire unique. Le biais de sélection sur validation est un phénomène documenté. [S01]

Formulation recommandée : **résultat exploratoire négatif net pour ce pipeline ; direct candidat prioritaire à validation indépendante**.

### 3.2 Interventions textuelles et mécanisme interne

Le direct suit les interventions rapportées : 0,996/0,996 sur la modification décisive, 0,996 de stabilité sur distracteur et 0,988 sous permutation. [D08 §4]

Cela soutient une sensibilité fonctionnelle pertinente. Cela n’identifie pas, à soi seul, une séquence interne de transitions et n’exclut pas toutes les stratégies alternatives. Plusieurs fonctions peuvent coïncider sur les interventions d’un même générateur.

Distinguer intervention sur le texte, intervention sur un état interne connu et démonstration d’une abstraction algorithmique sur un domaine plus large.

**Absence de CoT textuel ne signifie pas absence de composition.** Un passage avant traverse plusieurs transformations internes. Une stratégie efficace et correcte ne devient pas illégitime parce qu’elle ne suit pas les états que nous avions imaginés.

### 3.3 La généralisation textuelle reste ouverte

D09 limite T à des chaînes de 1 à 4 arêtes et précise que l’OOD textuel n’est pas testé. Le 100 % du direct ne prédit donc pas son score aux profondeurs 6, 8 ou 10. Inversement, S à profondeur 10 ne prouve pas que texte vers S fonctionne à profondeur 10. [D07 §5 ; D09 §5]

Sur un développement où le direct atteint 100 %, aucun pipeline ne peut améliorer son exactitude. D’autres bénéfices restent possibles : coût, quantité de données nécessaire, réutilisation d’une mémoire, robustesse ou domaine plus large. Ils demandent leurs propres mesures.

### 3.4 Ni plafond d’extraction ni produit validé

Le lecteur est best=last à 1 200 mises à jour et sa courbe d’arêtes monte encore au dernier point. C’est le meilleur résultat obtenu dans ce budget, pas un plafond démontré. [D08 §4]

Les compactions V2 ne fournissent pas une comparaison end-to-end direct/pipeline avec latence p50/p95, débit et qualité probabiliste sur test indépendant. Les latences V1 ne remplacent pas ces mesures V2. [D04 §4 ; D09 §4 ; D10 §4]

Dire « candidat produit » plutôt que « produit validé ». Un modèle spécialisé à chaînes courtes n’est pas encore un Jev généraliste.

### 3.5 Ne pas construire le prochain test pour faire perdre le direct

D10 propose des interventions « invisibles au direct » ou que le direct « ne peut pas suivre ». Il faut remplacer cette formulation.

On peut préenregistrer des transformations non vues à l’entraînement, mais l’information modifiée doit être accessible aux deux voies. Ne pas sélectionner le test en fonction des erreurs du direct. Un ensemble adversarial choisi contre un modèle doit être étiqueté comme tel et complété par une évaluation indépendante.

L’OOD n’est pas le seul terrain où la décomposition pourrait être utile. C’est un terrain particulièrement pertinent pour l’hypothèse de réutilisation d’un calcul appris.

## 4. Diagnostic prioritaire : l’interface et ses objectifs

### 4.1 Une tâche supplémentaire imposée au pipeline

Le direct doit répondre. Le lecteur doit reconstruire entités et arêtes, puis passer la validation avant exécution. Si cette validation est globale, une erreur sans rapport avec le chemin utile peut provoquer une abstention. [D08 §1 et §4]

**Hypothèse à vérifier :** une partie du handicap vient d’une reconstruction trop large et de la perte d’incertitude à l’interface, plutôt que d’une incapacité de l’exécuteur à composer.

La compaction ne détaille pas tous les seuils, argmax et conversions en graphe. Tracer ces opérations avant d’attribuer l’échec à une discrétisation précise.

Mêmes LoRA, données et plafonds : comparaison pertinente à budget donné. Cela ne rend pas les objectifs également difficiles et ne prouve pas la convergence des deux voies. L’extraction exhaustive est néanmoins un choix d’architecture : son coût fait bien partie du résultat opérationnel.

### 4.2 F1 d’arêtes et fiabilité du chemin

Illustration, pas estimation du projet : si chaque lien nécessaire est correct avec probabilité 0,95 et que ces événements sont indépendants, la probabilité d’une chaîne entièrement correcte vaut :

```text
4 liens  : 0,95^4  = 81,45 %
10 liens : 0,95^10 = 59,87 %
```

Ne pas remplacer 0,95 par le F1 0,9278 et présenter le produit comme une prédiction. F1 n’est pas une probabilité locale de transition et les erreurs peuvent être dépendantes.

Mesurer plutôt : exactitude du successeur pour le nœud actif, rappel des arêtes du chemin utile, terminal, première divergence, longueur de préfixe correct et rejets causés par des erreurs hors chemin. Séparer également les liens réels de la prédiction de FIN.

### 4.3 Le coût de l’abstention

La voie naked atteint environ 82 %, contre 76,16 % avec la politique préenregistrée : environ 5,8 points de différence. Même sans ce filtrage, le direct conserve environ 18 points d’avance. [D08 §4]

Le rapport 0,7616 / 0,917 donne environ 83,1 % d’exactitude parmi les non-abstentions, à condition que les taux arrondis portent sur les mêmes lignes et conventions. Recalculer depuis les JSONL avant publication.

Publier couverture et risque séparément, en conservant la métrique all-in historique. Les scores identiques de (b) et (c) n’établissent pas à eux seuls que les prédictions sont identiques ligne par ligne : archiver les désaccords solveur/exécuteur.

### 4.4 Permutations : localiser la première divergence

D09 rapporte une stabilité de permutation de 1,000 pour cn, contre 0,932 pour c ; le direct atteint 0,988. [D08 §4 ; D09 §6]

Tracer successivement : entrée, entités, arêtes, masques, validation, trajectoire, scores par candidat et abstention. L’écart c/cn suggère une dépendance introduite par la politique ou son interface ; il ne prouve pas quel code est en cause.

Un score partagé ne garantit pas l’invariance si l’encodage voit les options ordonnées. Si l’architecture est effectivement équivariante et les candidats indépendants, tester quasi-égalités, précision et règles de départage par identifiant stable.

## 5. Programme prioritaire V2.1 : pas de nouvelle architecture

### Q0. Provenance et évaluateur

Préserver V1/V2 et leurs prédictions. Fournir scripts, configurations, versions, scores bruts et cartes de permutation. Terminer les commits documentaires V1 encore en attente. Les gros runs peuvent rester hors Git s’ils sont archivés et accessibles par hash. [D11]

Chaque exemple doit avoir un `example_uid` unique, un `base_group_id` pour les variantes et un hash du contenu public. L’appariement positionnel seul est fragile : s’il est conservé, vérifier longueurs, contenus et candidats ligne par ligne.

Tests minimaux : tailles 1, 7, 8, 9, 16, 17 et 411 ; dernier minibatch incomplet ; ordre mélangé ; traitement explicite des ids dupliqués ; batch contre unitaire ; chaque exemple exactement une fois.

Les incidents 814/411 et OOM1 sont documentés comme corrigés. Ne pas les présenter comme bugs encore actifs. [D08 §6]

### Q1. Validation indépendante des checkpoints existants

Avant de retoucher un modèle, produire un jeu indépendant avec groupes et graines distincts. Préciser l’unité de généralisation : nouveaux noms seulement, nouveaux graphes, nouvelles combinaisons, templates ou profondeurs. Ne pas confondre renommage et nouveauté structurelle.

Ne pas rouvrir E5v2_eval, déclaré scellé à jamais par le protocole historique. Créer un nouveau test sous contrat explicite. Figer checkpoints, politiques et métriques avant les prédictions.

Comparer direct LoRA, pipeline figé, naked et solveur sur graphe prédit. La seed existante suffit pour une première vérification descriptive indépendante. Avant une revendication générale, entraîner plusieurs seeds selon une recette fixe et publier toutes leurs valeurs.

### Q2. Cartographier le domaine

| Cellule | Variable modifiée | Contrôles nécessaires |
|---|---|---|
| Court indépendant | nouveaux exemples, profondeur 1 à 4 | tailles et formats connus |
| Profondeur | 6, 8 et 10 | taille du graphe et longueur contrôlées |
| Surface | paraphrases et noms | logique identique |
| Distracteurs | faits inutiles supplémentaires | chemin et réponse identiques |
| Options | permutation et distracteurs admissibles | question inchangée |
| Départ | autre nœud du même graphe | faits inchangés |

Rester d’abord dans les 20 nœuds supportés. Ne pas confondre profondeur et dimension d’entrée. Couvrir la longueur tokenisée par construction ; aucune exclusion massive découverte après le test.

Cycles, successeurs multiples, contradictions et observations incomplètes changent les hypothèses du solveur : ce sont des extensions de tâche, pas de simples tests interchangeables.

Pour une chaîne cassée, définir si une arête absente signifie terminal, information manquante ou entrée invalide. Dans un monde partiellement observé, absence d’information ne signifie pas terminal.

### Q3. Attribution des erreurs

Pour chaque erreur, enregistrer :

1. Entités et départ corrects ou non.
2. Liens du chemin utile corrects ou non.
3. Terminal, FIN ou INCONNU correctement identifiés.
4. Validité du graphe et motif du rejet.
5. Sortie du solveur sur le graphe prédit.
6. Sortie et première divergence de l’exécuteur.
7. Réponse naked et effet du filtre.
8. Réponse directe sur le même exemple.

Diagnostics privilégiés, hors benchmark déployable : corriger seulement le départ, seulement les liens du chemin, seulement les liens hors chemin, puis fournir le graphe exact. L’oracle sert à localiser le goulot, pas à augmenter artificiellement le score.

Ajouter, si faisable, un parser déterministe borné aux templates synthétiques qui lit exclusivement le texte public. C’est un contrôle d’ingénierie, pas un lecteur général. Donner directement le graphe gold au solveur ne remplace pas cette baseline.

### Q4. Décision après diagnostic

| Observation | Suite |
|---|---|
| Direct robuste sur le domaine, aucune complémentarité | Conserver le direct, arrêter l’ajout de calcul pour ce domaine |
| Direct baisse en profondeur, S fonctionne, lecture se dégrade | Travailler sur l’interface |
| Direct et pipeline chutent ensemble | Isoler compréhension, taille et composition |
| Gain seulement avec graphe exact | Publier comme diagnostic, pas comme solution textuelle |
| Complémentarité réelle sur certains cas | Étudier ensuite un routeur sur partitions distinctes |

Un routeur oracle constitue une borne d’utilité potentielle, pas un système réalisable. Un expert médiocre en moyenne peut être utile sur certains cas, mais cette complémentarité doit être mesurée avant de construire le routage.

## 6. Piste ciblée si les diagnostics la justifient

### 6.1 Changer le contrat d’interface

Passer de « reconstruire exactement tout le graphe avant de calculer » à « fournir des transitions locales incertaines, réutilisables et supervisées ».

Ce n’est ni une nouveauté revendiquée ni un gain garanti. Lectures multiples d’une mémoire différentiable, mémoire clé-valeur et composition différentiable d’opérations ont des précédents. [S02 ; S03 ; S04]

### 6.2 Première ablation : conserver les distributions de successeurs

Encoder le texte une fois. Le lecteur prédit des distributions de successeurs plutôt que de décider immédiatement chaque arête.

```text
Texte public -> représentations partagées
                    |
                    +-> tête directe
                    |
                    +-> relations incertaines
                                |
                         état p_t -> p_(t+1)
                                |
                         réponse probabiliste
```

Pour le domaine simple à successeur unique, tester un opérateur explicite :

```text
p_0 = distribution de départ issue de l’entrée publique
A = matrice stochastique des transitions prédite depuis le texte
p_(t+1) = p_t @ A
```

Un terminal doit conserver sa propre identité via une auto-transition. Fusionner tous les terminaux en une classe FIN empêcherait de répondre lequel est atteint. Ajouter INCONNU seulement avec une sémantique et des annotations adaptées.

Ne pas renormaliser silencieusement toute masse restante sur les seuls candidats. La distribution obtenue n’est pas automatiquement calibrée, ni un posterior exact sur des graphes fixes incertains : dépendances entre arêtes et revisites demandent des hypothèses supplémentaires.

C’est une propagation différentiable à règle explicite, pas une transition apprise nouvelle. Son intérêt est de tester si le lecteur peut alimenter un calcul simple. Comparer, autant que possible avec le même lecteur :

- graphe discret et solveur ;
- graphe discret et exécuteur existant ;
- transitions incertaines et propagation ;
- direct adapté ;
- direct avec la même supervision auxiliaire.

Ne changer qu’une hypothèse à la fois. Si les scores de relations ne sont pas conservés dans l’implémentation actuelle, documenter précisément où ils sont perdus.

### 6.3 Variante ultérieure : lecture locale pilotée par l’état

Si les erreurs hors chemin dominent, utiliser le pointeur pour demander à la mémoire quel est le successeur de l’entité courante, puis actualiser l’état. Réutiliser les représentations, sans relancer Qwen à chaque étape.

Cette variante évite de reconstruire tous les faits, mais peut encore accumuler les erreurs, diffuser sa masse ou apprendre un raccourci. Conserver traces d’état, interventions et contrôle à une étape.

### 6.4 Entraînement et équité

Commencer par la transition locale, puis le déroulement autonome :

```text
L = CE(réponse finale)
  + alpha * CE(transitions ou preuves locales)
  + beta * moyenne_t CE(état prédit, état cible)
```

Introduire les termes progressivement. Les cibles exactes ne sont jamais données à l’inférence. La baseline directe doit recevoir une tête auxiliaire avec les mêmes cibles si l’on revendique un bénéfice spécifique de la récurrence.

Distinguer amélioration de représentation à l’entraînement et calcul supplémentaire au test. Évaluer le même checkpoint aux budgets 0, 1, 2, 4 et plus lorsque le domaine le justifie.

L’anti-raccourci était une contrainte de diagnostic. L’application finale n’a pas à interdire une voie directe qui marche. En revanche, un gain du système combiné ne prouve pas l’utilité du coprocesseur sans ablations.

## 7. Mesures opérationnelles

### Qualité

Exactitude all-in ; risque et couverture ; NLL/Brier ; calibration sur partition distincte ; trajectoires ; rappel du chemin ; interventions décisives ; distracteurs ; permutations. Publier les numérateurs, dénominateurs et groupes effectifs.

Une bonne invariance peut être triviale chez un modèle qui s’abstient toujours : l’accompagner de couverture et d’exactitude appariée.

### Machine

La machine rapportée est un i7-11800H, environ 29,3 Gio de RAM utilisables, une RTX 3070 Laptop 8 Go et Debian. Le pic V2 annoncé est autour de 2,1 Gio avec LoRA et checkpointing. Ce ne sont pas des mesures refaites ici. [D01, section Machine ; D09 §4]

Mesurer du texte brut à la décision, tokenisation, transferts, lecture, exécution et validation inclus. Rapporter p50/p95, batch, longueur, échauffement, température, mémoire allouée/réservée et RSS. CPU pour données, solveurs et statistiques ; un seul travail GPU à la fois.

Ne pas transporter les latences de la V1 dans le tableau V2. Une marge VRAM n’est pas une obligation de choisir un modèle plus gros.

Plusieurs questions sur le même texte peuvent permettre d’amortir la mémoire. Donner au direct le même droit au batch, cache et encodage partagé. Un avantage de cache artificiellement refusé au contrôle n’est pas un gain scientifique.

## 8. Corrections documentaires

| Expression actuelle | Formulation recommandée |
|---|---|
| T réfuté définitivement | Pipeline testé nettement inférieur sur Dev E5v2 |
| IC robuste à la seed | IC conditionnel aux runs mesurés ; variabilité entre seeds inconnue |
| Extraction au plafond réaliste | Meilleur lecteur dans le budget, courbe encore montante |
| Direct prouve la composition interne | Direct suit les interventions textuelles testées |
| Produit direct validé | Candidat prioritaire à validation indépendante |
| E4b généralise à des index jamais vus | Index exposés par réentraînement ; profondeur testée séparément |
| Interventions invisibles au direct | Transformations nouvelles, information équitable pour les deux voies |

Ces corrections concernent la portée, pas les chiffres ou les archives.

## 9. Prompt de transmission aux agents

> Lis cet audit et vérifie les observations dans les artefacts du dépôt. Ne reconstruis pas le projet. Conserve V1 et V2. Commence par Q0 à Q3 : provenance, test indépendant des checkpoints, profils de profondeur, attribution des erreurs. Corrige la portée des conclusions concernant Dev, les seeds, le mécanisme, le plafond d’extraction et le produit. Aucun test ne doit être choisi à partir des erreurs du direct. Ne rouvre pas E5v2_eval historiquement scellé : définis un nouveau test. Avant toute architecture, fournis la première divergence de chaque erreur, l’effet de l’abstention et les coûts end-to-end. Si l’interface est le goulot, propose une seule ablation entre graphe discret et transitions incertaines, avec contrôles équitables. Les diagnostics utilisant l’oracle doivent rester séparés du benchmark déployable. Ne revendique ni nouveauté ni gain prévu. Ne construis un routeur qu’après avoir mesuré une complémentarité exploitable.

## 10. Sources documentaires

- D00 : `00-INDEX(2).md`
- D01 : `01-CONTEXTE-QUESTIONS-RECHERCHE.md`
- D02 : `02-ORGANISATION-ORCHESTRATION-AGENTS(1).md`
- D03 : `03-CHRONOLOGIE-COMPLETE-24-25-SEPT.md`
- D04 : `04-V1-RECAP-DONNEES-MODELE-RESULTATS.md`
- D05 : `05-AUDIT-EXTERNE-POST-CLOTURE-V1.md`
- D06 : `06-V2-DECISION-ARCHITECTURE-CONTRAT-DONNEES.md`
- D07 : `07-V2-ETAGE-S-E0-E4.md`
- D08 : `08-V2-ETAGE-T-E5.md`
- D09 : `09-V2-CLOTURE-RESULTAT-FINAL.md`
- D10 : `10-LECONS-TRANSVERSALES-PIVOT-SUITES.md`
- D11 : `11-INVENTAIRE-REPRODUCTION-ETAT-ACTUEL.md`

## 11. Références externes vérifiées

Ces sources éclairent les pistes, sans valider les résultats privés du projet. Aucune performance de ces articles n’est extrapolée à la RTX 3070 ou au banc V2.

- S01 : Cawley et Talbot, 2010. *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*. `https://www.jmlr.org/papers/v11/cawley10a.html`
- S02 : Sukhbaatar et al., 2015. *End-To-End Memory Networks*. `https://arxiv.org/html/1503.08895v5`
- S03 : Miller et al., 2016. *Key-Value Memory Networks for Directly Reading Documents*. `https://arxiv.org/abs/1606.03126`
- S04 : Yang, Yang et Cohen, 2017. *Differentiable Learning of Logical Rules for Knowledge Base Reasoning*. `https://arxiv.org/abs/1702.08367`

## 12. Conclusion

La V1 n’avait pas établi une récurrence utile. La V2 l’établit sur des relations structurées, mais sa voie textuelle ajoute une interface faillible que le direct adapté peut éviter dans le domaine testé.

Le prochain travail est de valider la frontière du direct et d’attribuer la perte du pipeline. Une nouvelle architecture doit répondre à ce diagnostic, pas à l’obligation de sauver l’idée initiale.
