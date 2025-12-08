# Platform-Level-Generator
Ce projet explore la génération procédurale de contenu (PCG) dans le contexte des jeux vidéo de plateforme 2D. L'objectif est de créer un système capable de générer automatiquement des niveaux jouables, variés et intéressants, sans intervention manuelle.

# Représentation du Niveau
Un niveau est représenté comme une grille 2D de tuiles :
Dimensions : 40 colonnes × 22 lignes (1280×720 pixels)
Taille d'une tuile : 32×32 pixels
Types de tuiles : EMPTY (0), GROUND (1), COIN (2), SPIKE (3)

# Algorithme Constructif
Principe : Génération Colonne par Colonne
L'algorithme parcourt le niveau de gauche à droite et construit chaque colonne en 4 étapes :
- Étape 1 - Gestion des trous
  Probabilité : 12%
  Largeur maximale : 3 tuiles (franchissable par un saut)"
- Étape 2 - Variation de hauteur
  Changement maximum : ±1 tuile entre colonnes adjacentes
  Crée des escaliers naturels
- Étape 3 - Remplissage du sol
- Étape 4 - Placement des objets

# Architecture du Code
    
    ┌─────────────────┐
    │  LevelConfig    │ ← Paramètres de génération
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ LevelGenerator  │ ← Algorithme de génération
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │     Level       │ ← Conversion grille → objets de collision
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │     Player      │ ← Physique et contrôles
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │      Game       │ ← Boucle principale
    └─────────────────┘

# Classes Principales
  - LevelConfig : Centralise tous les paramètres ajustables pour la génération.
  - LevelGenerator : Génère la structure abstraite du niveau (grille de nombres).
  - Level : Transforme la représentation abstraite en objets concrets pour le moteur physique.
  - Player : Implémente la physique du personnage jouable.

# Système de Score
- +1 point : collecter une pièce
- -3 points : toucher un spike (danger majeur)
- -1 point : tomber dans le vide (erreur de navigation)
- Nouveau niveau : atteindre le bord droit de l'écran

# Exemples de Niveaux Générés
  ## Niveau 1 - Facile
  - 2 trous de 2 tuiles
  - 3 spikes espacés
  - 12 pièces
  - Terrain majoritairement plat
  ## Niveau 5 - Moyen
  - 4 trous (dont 1 de 3 tuiles)
  - 6 spikes regroupés
  - Escaliers montants/descendants
  - 8 pièces stratégiquement placées
  ## Niveau 12 - Difficile
  - Plusieurs trous consécutifs
  - Spikes avant/après les trous
  - Terrain accidenté
  - Pièces en positions risquées

# Améliorations Possibles
1. Difficulté Dynamique
2. Nouveaux Types de Structures
3. Fonction de Fitness (pour recherche heuristique)
4. Wave Function Collapse

