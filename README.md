# Puzzle Game KC

Un jeu de puzzle mettant en vedette les joueurs de la Karmine Corp de l'équipe LEC!

# Comment jouer?

1. **Menu Principal**
   - Sélectionnez un puzzle parmi les 5 joueurs de la KC disponibles
   - Les noms des joueurs sont affichés au-dessus de leurs images

2. **Pendant le jeu**
   - Cliquez sur une pièce pour la sélectionner
   - Cliquez sur une autre pièce pour les échanger
   - Le temps est affiché en haut à gauche
   - Utilisez le bouton "Menu" en haut à gauche pour revenir au menu principal

3. **Victoire**
   - Une fois le puzzle complété, un message de victoire s'affiche
   - Appuyez sur ESPACE pour retourner au menu
   - Appuyez sur ÉCHAP pour quitter le jeu

# Structure des fichiers

- `puzzle.py` : Le code principal du jeu
- `assets/` : Dossier contenant les images des puzzles
  - KC CANNA.jpg
  - KC YIKE.webp
  - KC VLADI.jpg
  - KC CALISTE.jpg
  - KC TARGAMAS.webp
  - KC CANNA 2.jpg
  - KC CANNA 3.jpg
  - KC VLADI 2.jpg
  - KC CALISTE 2.jpg

# Contrôles

- **Clic gauche** : Sélectionner/échanger des pièces
- **ESPACE** : Retour au menu après une victoire
- **ÉCHAP** : Retour au menu pendant le jeu / Quitter depuis le menu

# Prérequis

- Python 3.x
- Pygame
- Pillow (PIL)

# Installation des dépendances

Pour installer les bibliothèques nécessaires, exécutez les commandes suivantes :

## Vous pouvez installer les dépendances à partir du fichier requirements.txt

Windows:
pip install -r requirements.txt

macOS/Linux:
pip3 install -r requirements.txt


## Alternativement:

Windows:
pip install pygame
pip install pillow

macOS/Linux:
pip3 install pygame
pip3 install pillow