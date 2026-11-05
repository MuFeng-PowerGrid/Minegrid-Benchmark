<!-- This README is one language at a time. Other versions are linked below. -->

[English](../../README.md) · [中文](README.zh.md) · **Français** · [Español](README.es.md) · [Русский](README.ru.md) · [العربية](README.ar.md)

<p align="center">
  <img src="../assets/logo_brand.png" width="760" alt="MINEGRID — Power System Made Simple">
</p>

# MINEGRID

### Des modèles de réseaux électriques au raisonnement multimodal

MINEGRID réunit des descriptions non linéaires détaillées d’équipements, des images associées à leurs annotations et des instructions sur les réseaux. La bibliothèque de modèles sert de base à un petit simulateur de recherche ; le benchmark multimodal permet d’étudier la compréhension des schémas de commande et des réseaux électriques par les modèles vision-langage.

## Explorer la collection

- **[Équipements types](../../Multimodal/Alpaca%20Data/Apparatus/index.html)** — 14 familles · 46 configurations · descriptions HTML
- **[Benchmark multimodal](../../JSON%20Index/README.md)** — 1 429 paires image–annotation · 2 tâches · 3 difficultés
- **[Instructions complémentaires](../../Multimodal/Alpaca%20Data/README.md)** — Instructions réseau et un fichier exemple de connaissances générales

## Équipements types : contenu des modèles

Chaque page décrit les états, paramètres, entrées/sorties, équations différentielles et algébriques, limites non linéaires et hypothèses. Les configurations détaillées et les variantes de commande sont présentées séparément. Ces fichiers HTML constituent une référence de modélisation, pas un simulateur exécutable fourni.

| Équipement | Contenu du modèle | Configurations |
|---|---|---|
| [Générateur synchrone détaillé](../../Multimodal/Alpaca%20Data/Apparatus/sg.html) | Dynamique électromagnétique à six enroulements, rotor, régulateur de vitesse, excitation, PSS et saturations/limites selon la configuration. | 3 |
| [Convertisseur formant le réseau : VSG](../../Multimodal/Alpaca%20Data/Apparatus/gfm_vsg.html) | Inertie virtuelle, amortissement, régulation puissance/tension, boucles internes, filtre LCL, bus continu et anti-saturation. | 4 |
| [Commande grid-forming par statisme](../../Multimodal/Alpaca%20Data/Apparatus/gfm_droop.html) | Filtrage de puissance, statisme P–f, commande tension/réactif, boucles internes, LCL, bus continu et variantes de séquence. | 3 |
| [Commande grid-forming matching](../../Multimodal/Alpaca%20Data/Apparatus/gfm_matching.html) | Synchronisation par tension continue, bilan énergétique, régulation tension/courant, filtre et actionneurs. | 3 |
| [Commande grid-forming dVOC](../../Multimodal/Alpaca%20Data/Apparatus/gfm_dvoc.html) | Amplitude et phase de l’oscillateur, régulation de puissance, dynamique électrique et limitations. | 3 |
| [Convertisseur grid-following PQ](../../Multimodal/Alpaca%20Data/Apparatus/gfl_pq.html) | PLL, boucles de puissance active/réactive, courant, LCL/bus continu, tenue aux défauts et reprise de puissance. | 4 |
| [Convertisseur grid-following PU](../../Multimodal/Alpaca%20Data/Apparatus/gfl_pu.html) | PLL, puissance active et tension alternative, boucles de courant et variantes de soutien lors des défauts. | 4 |
| [Éolienne DFIG grid-forming](../../Multimodal/Alpaca%20Data/Apparatus/gfm_dfig.html) | Aérodynamique, transmission à deux masses, flux machine, convertisseurs, bus continu, pas, crowbar/chopper et soutien aux défauts. | 2 |
| [Éolienne DFIG grid-following](../../Multimodal/Alpaca%20Data/Apparatus/gfl_dfig.html) | Turbine, transmission, machine asynchrone, PLL et commandes rotor/réseau, pas, crowbar et reprise après défaut. | 2 |
| [Éolienne PMSG directe grid-forming](../../Multimodal/Alpaca%20Data/Apparatus/gfm_pmsg.html) | Machine à aimants, mécanique, convertisseurs dos à dos, bus continu ; VSG ou matching, pas et tenue aux défauts. | 4 |
| [Éolienne PMSG directe grid-following](../../Multimodal/Alpaca%20Data/Apparatus/gfl_pmsg.html) | Commande vitesse/courant côté machine, PLL et tension continue côté réseau, dynamique électromagnétique et pas. | 2 |
| [Charge de centre de données](../../Multimodal/Alpaca%20Data/Apparatus/data_center.html) | Chaîne AFE–UPS–VSI–PSU, charge de calcul équivalente, mesures/actionneurs et énergie de batterie de secours. | 2 |
| [Moteur asynchrone](../../Multimodal/Alpaca%20Data/Apparatus/induction_motor.html) | Flux stator/rotor, vitesse, couple de charge, mesure de tension, indicateur thermique et protection contre la sous-tension. | 2 |
| [Convertisseur d’interconnexion CA/CC](../../Multimodal/Alpaca%20Data/Apparatus/ic.html) | Échange d’énergie CA/CC, PLL, filtre et bus continu ; modes PQ, EQ, PU, EU et commandes de séquence. | 8 |

[Répertoire des équipements](../../Multimodal/Alpaca%20Data/Apparatus/index.html) · [Conventions des modèles](../../Multimodal/Alpaca%20Data/Apparatus/model_conventions.html)

## Benchmark multimodal

| Tâche | Facile | Moyen | Difficile | Total | Lots JSONL |
|---|---|---|---|---|---|
| Commande d’équipement | 76 | 593 | 366 | 1035 | 64 |
| Topologie du réseau | 38 | 222 | 134 | 394 | 25 |
| Total | 114 | 815 | 500 | 1429 | 89 |

Les chiffres proviennent des fichiers actuels : 1 429 exemples, 1 429 images référencées et 89 lots JSONL. Les niveaux de difficulté ne constituent pas des ensembles d’entraînement, de validation et de test.

| Collection complémentaire | Fichiers | Instructions |
|---|---|---|
| Network (JSON) | 32000 | 335517 |
| General Knowledge (exemple JSON) | 1 | 39 |

Les instructions complémentaires ne sont pas incluses dans le benchmark d’images. Apparatus contient 16 pages HTML, dont le répertoire et les conventions ; General Knowledge ne conserve qu’un fichier exemple.

## Aperçu visuel

Neuf exemples représentatifs par tâche et difficulté, en planches compactes de 3 × 3. Une rangée présente la commande des équipements, la suivante la topologie des réseaux, avec les trois difficultés côte à côte. Cliquez sur une planche pour la voir en pleine résolution ; les identifiants assurent la traçabilité.

### Commande d’équipement

| Facile | Moyen | Difficile |
|---|---|---|
| [![Commande d’équipement · Facile](../assets/apparatus_easy.png)](../assets/apparatus_easy.png) | [![Commande d’équipement · Moyen](../assets/apparatus_medium.png)](../assets/apparatus_medium.png) | [![Commande d’équipement · Difficile](../assets/apparatus_hard.png)](../assets/apparatus_hard.png) |

### Topologie du réseau

| Facile | Moyen | Difficile |
|---|---|---|
| [![Topologie du réseau · Facile](../assets/network_easy.png)](../assets/network_easy.png) | [![Topologie du réseau · Moyen](../assets/network_medium.png)](../assets/network_medium.png) | [![Topologie du réseau · Difficile](../assets/network_hard.png)](../assets/network_hard.png) |

## Construire un premier simulateur de réseau électrique

Utilisez les descriptions HTML pour concevoir un premier outil de simulation de taille réduite : interface commune, unités et repères cohérents, limites conservées, équations des équipements couplées aux contraintes du réseau, initialisation et gestion des événements. Cette démarche sert au prototypage et à l’implémentation assistée par LLM, puis à une validation d’ingénierie indépendante.

### Alignement dynamique avec PSCAD et PowerFactory

Lorsqu’un alignement dynamique de haute fidélité avec les modèles de PSCAD, PowerFactory ou de logiciels similaires est nécessaire, les descriptions TypicalApparatus peuvent servir de point de départ structurel. Les méthodes de [Guo et Shi (2024)](https://doi.org/10.1109/CIEEC60922.2024.10583352) et de [Shi, Guo et al. (2026)](https://doi.org/10.1109/TSTE.2025.3621702) permettent de rechercher des expressions analytiques explicites des équations du modèle à partir de données transitoires et de contraintes physiques, par identification de modèle et régression symbolique.

Conservez les mêmes unités, repères et conditions aux limites que le modèle de référence. Vérifiez la généralisation sur des points de fonctionnement et des perturbations non utilisés pour l’identification, en comparant les réponses transitoires obtenues à celles du logiciel de référence. Le code associé est disponible dans [DSIPS — Dynamic Sparse Identification of Power System](https://github.com/gdg1999/DSIPS).

## Exemples de prompts

### 1 · Transformer un modèle en composant

```text
Utilise le modèle HTML MINEGRID VSG joint comme spécification. Énumère tous les états, variables algébriques, entrées, sorties, paramètres, unités et repères. Définis ensuite une interface pour f(x,z,u;p), g(x,z,u;p) et le courant injecté. Conserve toutes les limites et tous les termes anti-saturation. Distingue les valeurs fournies des informations manquantes ; n’invente aucun paramètre. Présente le plan et la correspondance équations-code avant de programmer.
```

### 2 · Assembler un premier simulateur dynamique

```text
À partir des descriptions jointes du générateur synchrone, des unités GFM/GFL et de la charge, conçois un simulateur de recherche à trois nœuds. Définis les bases, les équations réseau, les interfaces et une initialisation cohérente. Ajoute une petite variation de charge, l’enregistrement des états/courants/tensions, des contrôles de résidu et une étude de convergence du pas. Liste les paramètres et hypothèses absents des documents. Sépare fonctions implémentées et comportements non vérifiés.
```

## Évaluer les VLM et étudier leurs mécanismes

- Évaluation : reconnaissance des blocs de commande, signes de rétroaction, états et équations DAE ; extraction des nœuds/branches, connectivité et reconstruction des tables réseau.
- Mécanismes : expériences contrôlées sur la langue, la résolution, l’occultation et la position des symboles ; classification des erreurs de perception et de raisonnement physique ; analyse des activations lorsque les états internes sont accessibles.
- Protocole : garder les réponses de référence hors des entrées, fixer la distribution des tâches/difficultés, comparer les structures et la cohérence physique, et regrouper les sources communes pour limiter les fuites. Une égalité textuelle stricte ne suffit pas pour des équations équivalentes.

## Organisation et format des annotations

```text
JSON Index/
├── device_control_*/      # JSONL
└── network_topology_*/     # JSONL
Multimodal/
├── Alpaca Data/
│   ├── Apparatus/          # HTML
│   ├── Network/            # JSON
│   └── General Knowledge/  # JSON
├── apparatus_{easy,medium,hard}/
└── network_{easy,medium,hard}/
Scripts/
docs/
├── assets/
└── readme/
```

Chaque ligne JSONL contient id, image, conversations et annotations. Les chemins d’image partent de la racine. La valeur de la réponse de l’assistant doit être décodée une seconde fois en JSON. Le prompt original est chinois ; annotations contient en, es, ar, fr et ru. Les six langues du README ne signifient pas six traductions indépendantes des réponses. Les fichiers JSON complémentaires sont des tableaux instruction/input/output.

[Guide des annotations](../../JSON%20Index/README.md) · [Guide d’évaluation](../../Scripts/LLM%20Evaluation/README.md)

## Référence bibliographique

Si cette ressource contribue à vos travaux, veuillez citer l’article associé :

D. Guo, S. Li, X. Shi, S. Jiang, G. Konstantinou and Y. Cao, "A Large Language Model-Based Framework for Automated Dynamic Simulation of Power Systems," in *IEEE Transactions on Smart Grid*, doi: [10.1109/TSG.2026.3731592](https://doi.org/10.1109/TSG.2026.3731592).

```bibtex
@article{guo2026automated,
  author  = {Guo, D. and Li, S. and Shi, X. and Jiang, S. and Konstantinou, G. and Cao, Y.},
  title   = {A Large Language Model-Based Framework for Automated Dynamic Simulation of Power Systems},
  journal = {IEEE Transactions on Smart Grid},
  year    = {2026},
  doi     = {10.1109/TSG.2026.3731592}
}
```

Méthodes connexes d’identification à partir de données transitoires et d’agrégation sous contraintes physiques :

1. D. Guo and X. Shi, "Model Identification of Grid-following System for Stability Evaluation with Transient Data," *2024 IEEE 7th International Electrical and Energy Conference (CIEEC)*, Harbin, China, 2024, pp. 01–06, doi: [10.1109/CIEEC60922.2024.10583352](https://doi.org/10.1109/CIEEC60922.2024.10583352).

2. X. Shi, D. Guo *et al*., "Physical-Informed Detailed Aggregation of Wind Farm Based on Symbolic Regression: Structure, Solution and Generalizability," in *IEEE Transactions on Sustainable Energy*, vol. 17, no. 2, pp. 1511–1524, April 2026, doi: [10.1109/TSTE.2025.3621702](https://doi.org/10.1109/TSTE.2025.3621702).

```bibtex
@inproceedings{guo2024identification,
  author    = {Guo, D. and Shi, X.},
  title     = {Model Identification of Grid-following System for Stability Evaluation with Transient Data},
  booktitle = {2024 IEEE 7th International Electrical and Energy Conference (CIEEC)},
  address   = {Harbin, China},
  year      = {2024},
  pages     = {01--06},
  doi       = {10.1109/CIEEC60922.2024.10583352}
}

@article{shi2026aggregation,
  author  = {Shi, X. and Guo, D. and others},
  title   = {Physical-Informed Detailed Aggregation of Wind Farm Based on Symbolic Regression: Structure, Solution and Generalizability},
  journal = {IEEE Transactions on Sustainable Energy},
  volume  = {17},
  number  = {2},
  pages   = {1511--1524},
  month   = apr,
  year    = {2026},
  doi     = {10.1109/TSTE.2025.3621702}
}
```

## Site Minegrid

**Site Minegrid : en cours de test et de maintenance…**
