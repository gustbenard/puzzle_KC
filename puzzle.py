import pygame
import sys
import random
from PIL import Image, ImageDraw
import time
from pathlib import Path
import json
import os
import numpy as np

# Initialisation de Pygame
pygame.init()

# Constantes
GRID_SIZE = (6, 8)  # Nombre de pièces
MARGIN = 2
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
ANIMATION_SPEED = 10
HIGHSCORES_FILE = "highscores.txt"

# Define the background color
BACKGROUND_COLOR = (250, 240, 202)  # RGB equivalent of #faf0ca

class PuzzlePiece:
    def __init__(self, surface, current_pos, correct_pos, piece_id):
        self.surface = surface
        self.current_pos = list(current_pos)
        self.correct_pos = correct_pos
        self.target_pos = list(current_pos)
        self.is_moving = False
        self.piece_id = piece_id
        
    def update(self):
        if self.is_moving:
            dx = (self.target_pos[0] - self.current_pos[0]) / ANIMATION_SPEED
            dy = (self.target_pos[1] - self.current_pos[1]) / ANIMATION_SPEED
            
            self.current_pos[0] += dx
            self.current_pos[1] += dy
            
            if abs(self.target_pos[0] - self.current_pos[0]) < 0.1 and abs(self.target_pos[1] - self.current_pos[1]) < 0.1:
                self.current_pos = list(self.target_pos)
                self.is_moving = False
                return True
        return False

class PuzzleGame:
    def __init__(self):
        # Obtenir le chemin absolu du dossier du script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(self.script_dir, "assets")
        
        # Vérifier si le dossier assets existe déjà
        if not os.path.exists(self.assets_dir):
            try:
                os.makedirs(self.assets_dir)
            except Exception as e:
                # print(f"Impossible de créer le dossier assets : {e}")
                # print("Le jeu continuera avec le dossier existant")
                pass
        
        # Initialisation de la fenêtre maximisée
        info = pygame.display.Info()
        self.window_size = (info.current_w - 20, info.current_h - 80)
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Puzzle - Menu Principal")
        
        self.clock = pygame.time.Clock()
        
        # États du jeu
        self.is_running = True
        self.in_menu = True
        self.current_image = None
        self.start_time = None
        self.elapsed_time = 0
        self.score = 0
        self.selected_piece = None
        self.animation_in_progress = False
        
        # Police pour le texte
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 74)
        
        # Bouton retour au menu
        self.home_button = pygame.Rect(10, 10, 150, 40)
        self.home_button_color = (250, 240, 202)
        
        # Charger les images disponibles
        self.available_images = self.load_available_images()
        self.image_buttons = self.create_image_buttons()
        
        # Charger les meilleurs scores
        self.highscores = self.load_highscores()
        if not isinstance(self.highscores, dict):
            self.highscores = {}

    def load_image(self, image_path):
        try:
            self.original_image = Image.open(image_path)
            # Ajuster la taille de l'image pour qu'elle rentre dans l'écran
            max_width = self.window_size[0] - 300  # Plus de marge pour les scores
            max_height = self.window_size[1] - 100
            
            # Calculer le ratio en préservant l'orientation
            width_ratio = max_width / self.original_image.width
            height_ratio = max_height / self.original_image.height
            ratio = min(width_ratio, height_ratio)
            
            new_width = int(self.original_image.width * ratio)
            new_height = int(self.original_image.height * ratio)
            
            self.original_image = self.original_image.resize((new_width, new_height))
            self.image_width = new_width
            self.image_height = new_height
            
            # Ajuster GRID_SIZE en fonction de l'orientation
            if new_width > new_height:  # Image en paysage
                global GRID_SIZE
                GRID_SIZE = (4, 6)  # Moins de pièces en hauteur
            else:  # Image en portrait
                GRID_SIZE = (6, 8)  # Plus de pièces en hauteur
                
        except Exception as e:
            # print(f"Erreur lors du chargement de l'image {image_path}: {e}")
            sys.exit(1)

    def create_puzzle_pieces(self):
        piece_width = self.image_width // GRID_SIZE[0]
        piece_height = self.image_height // GRID_SIZE[1]
        
        self.pieces = []
        piece_id = 0
        
        for i in range(GRID_SIZE[1]):
            for j in range(GRID_SIZE[0]):
                # Découpage de l'image
                piece = self.original_image.crop((
                    j * piece_width,
                    i * piece_height,
                    (j + 1) * piece_width,
                    (i + 1) * piece_height
                ))
                
                # Conversion en surface Pygame
                mode = piece.mode
                size = piece.size
                data = piece.tobytes()
                
                piece_surface = pygame.image.fromstring(data, size, mode)
                
                self.pieces.append(PuzzlePiece(
                    surface=piece_surface,
                    current_pos=[i, j],
                    correct_pos=(i, j),
                    piece_id=piece_id
                ))
                piece_id += 1

    def shuffle_pieces(self):
        # Création d'une grille de positions fixes
        positions = [(i, j) for i in range(GRID_SIZE[1]) for j in range(GRID_SIZE[0])]
        
        # Mélange des pièces tout en gardant la structure de la grille
        random.shuffle(self.pieces)
        
        # Attribution des positions fixes aux pièces mélangées
        for piece, (row, col) in zip(self.pieces, positions):
            piece.current_pos = [row, col]
            piece.target_pos = piece.current_pos.copy()

    def get_piece_rect(self, row, col):
        piece_width = self.image_width // GRID_SIZE[0]
        piece_height = self.image_height // GRID_SIZE[1]
        x = (self.window_size[0] - self.image_width) // 2 + col * (piece_width + MARGIN)
        y = (self.window_size[1] - self.image_height) // 2 + row * (piece_height + MARGIN)
        return pygame.Rect(x, y, piece_width, piece_height)

    def handle_click(self, pos):
        if self.in_menu:
            # Gérer les clics dans le menu
            for button in self.image_buttons:
                if button['rect'].collidepoint(pos):
                    self.start_game_with_image(button['name'])
                    return
            return
            
        # Vérifier si le bouton d'accueil a été cliqué
        if self.home_button.collidepoint(pos):
            self.reset_game()
            return

        if self.animation_in_progress or self.in_menu:
            return
            
        for i, piece in enumerate(self.pieces):
            rect = self.get_piece_rect(*piece.current_pos)
            if rect.collidepoint(pos):
                if self.selected_piece is None:
                    self.selected_piece = i
                else:
                    piece1 = self.pieces[self.selected_piece]
                    piece2 = piece
                    
                    pos1 = piece1.current_pos.copy()
                    pos2 = piece2.current_pos.copy()
                    
                    piece1.target_pos = pos2
                    piece2.target_pos = pos1
                    
                    piece1.is_moving = True
                    piece2.is_moving = True
                    self.animation_in_progress = True
                    
                    self.selected_piece = None
                    
                    # Afficher l'état du puzzle après le mouvement
                    # print("\nMouvement effectué !")
                    # self.print_pieces_grid()
                    return

    def check_win(self):
        for piece in self.pieces:
            current_row, current_col = piece.current_pos
            correct_row, correct_col = piece.correct_pos
            if current_row != correct_row or current_col != correct_col:
                return False
                
        # Si on arrive ici, c'est que le puzzle est complété
        self.score = max(1000 - int(self.elapsed_time), 0)
        self.save_score()
        
        # Afficher le message de victoire
        self.show_victory_message()
        return True
        
    def show_victory_message(self):
        # Créer une surface semi-transparente
        overlay = pygame.Surface(self.window_size)
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # Afficher le message de victoire
        victory_font = pygame.font.Font(None, 74)
        score_font = pygame.font.Font(None, 48)
        
        victory_text = victory_font.render("Félicitations !", True, (255, 255, 255))
        score_text = score_font.render(f"Score: {self.score} points", True, (255, 255, 255))
        menu_text = score_font.render("ESPACE : Menu Principal", True, (255, 255, 255))
        quit_text = score_font.render("ÉCHAP : Quitter", True, (255, 255, 255))
        
        victory_rect = victory_text.get_rect(center=(self.window_size[0]//2, self.window_size[1]//2 - 100))
        score_rect = score_text.get_rect(center=(self.window_size[0]//2, self.window_size[1]//2))
        menu_rect = menu_text.get_rect(center=(self.window_size[0]//2, self.window_size[1]//2 + 100))
        quit_rect = quit_text.get_rect(center=(self.window_size[0]//2, self.window_size[1]//2 + 150))
        
        self.screen.blit(victory_text, victory_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(menu_text, menu_rect)
        self.screen.blit(quit_text, quit_rect)
        
        pygame.display.flip()
        
        # Attendre la décision du joueur
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_SPACE:
                        self.reset_game()
                        waiting = False

    def load_highscores(self):
        score_file = os.path.join(self.script_dir, "high_score.json")
        try:
            if os.path.exists(score_file):
                with open(score_file, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            # print(f"Erreur lors du chargement des scores : {e}")
            return {}

    def save_score(self):
        if not self.current_image:
            return
            
        score_file = os.path.join(self.script_dir, "high_score.json")
        try:
            # Créer ou charger le fichier de scores
            if os.path.exists(score_file):
                with open(score_file, 'r') as f:
                    scores = json.load(f)
            else:
                scores = {}
            
            # Ajouter le nouveau score
            if self.current_image not in scores:
                scores[self.current_image] = []
            
            scores[self.current_image].append({
                "score": self.score,
                "date": time.strftime("%Y-%m-%d")
            })
            
            # Sauvegarder le fichier
            with open(score_file, 'w') as f:
                json.dump(scores, f, indent=4)
                
            # Mettre à jour les scores en mémoire
            self.highscores = scores
            
        except Exception as e:
            # print(f"Erreur lors de la sauvegarde du score : {e}")
            pass

    def draw_home_button(self):
        pygame.draw.rect(self.screen, self.home_button_color, self.home_button)
        text = self.font.render("Menu Principal", True, BLACK)
        text_rect = text.get_rect(center=self.home_button.center)
        self.screen.blit(text, text_rect)

    def load_available_images(self):
        # Ordre spécifique des images
        ordered_images = [
            "KC CANNA.jpg",
            "KC YIKE.webp",
            "KC VLADI.jpg",
            "KC CALISTE.jpg",
            "KC TARGAMAS.webp",
            "KC CANNA 2.jpg",
            "KC CANNA 3.jpg",
            "KC VLADI 2.jpg",
            "KC CALISTE 2.jpg"
        ]
        
        # Vérifier quelles images sont disponibles
        available = []
        try:
            files = os.listdir(self.assets_dir)
            for image in ordered_images:
                if image in files:
                    available.append(image)
            # print(f"Images trouvées : {available}")  # Debug
        except Exception as e:
            # print(f"Erreur lors de la lecture du dossier assets : {e}")
            # print("Vérifiez que le dossier assets existe et contient des images")
            sys.exit(1)
        return available

    def create_image_buttons(self):
        buttons = []
        preview_size = (180, 180)  # Légèrement plus petit pour tout faire tenir
        margin = 20
        
        # Calculer la position de départ pour centrer horizontalement toutes les images
        total_width = preview_size[0] * 5 + margin * 4  # 5 images avec 4 marges entre elles
        start_x = (self.window_size[0] - total_width) // 2
        # Placer les images au milieu verticalement
        start_y = self.window_size[1] // 2 - preview_size[1] // 2
        
        button_width = preview_size[0]
        button_height = preview_size[1]

        for i, image_name in enumerate(self.available_images):
            x = start_x + i % 5 * (preview_size[0] + margin)
            if i < 5:
                y = start_y - 150  # Décalage vers le haut pour la première ligne
            else:
                y = start_y + (i // 5) * (preview_size[1] + margin)
            
            # Créer une miniature de l'image
            image_path = os.path.join(self.assets_dir, image_name)
            try:
                # print(f"Chargement de l'image : {image_path}")  # Debug
                image = Image.open(image_path)
                # Conserver les proportions pour la miniature
                image.thumbnail(preview_size, Image.Resampling.LANCZOS)
                # Convertir en RGB si nécessaire (pour les images RGBA)
                if image.mode in ('RGBA', 'P'):
                    image = image.convert('RGB')
                image_surface = pygame.image.fromstring(
                    image.tobytes(), image.size, image.mode
                )
                buttons.append({
                    'rect': pygame.Rect(x, y, preview_size[0], preview_size[1]),
                    'image': image_surface,
                    'name': image_name
                })
                # print(f"Image {image_name} chargée avec succès")  # Debug
            except Exception as e:
                # print(f"Erreur lors du chargement de {image_name}: {e}")
                continue

        if not buttons:
            # print("Aucune image n'a pu être chargée. Vérifiez que le dossier assets contient des images valides.")
            sys.exit(1)
            
        # print(f"Nombre de boutons créés : {len(buttons)}")  # Debug
        return buttons

    def start_game_with_image(self, image_name):
        self.current_image = image_name
        image_path = os.path.join(self.assets_dir, image_name)
        self.load_image(image_path)
        
        # Ajuster la taille de l'image pour qu'elle rentre dans l'écran
        max_width = self.window_size[0] - 100
        max_height = self.window_size[1] - 100
        ratio = min(max_width / self.image_width, max_height / self.image_height)
        self.image_width = int(self.image_width * ratio)
        self.image_height = int(self.image_height * ratio)
        self.original_image = self.original_image.resize((self.image_width, self.image_height))
        
        # Création et mélange des pièces
        self.create_puzzle_pieces()
        self.shuffle_pieces()
        
        # Démarrer le chronomètre
        self.start_time = time.time()
        self.in_menu = False
        pygame.display.set_caption(f"Puzzle - {image_name}")

    def reset_game(self):
        self.in_menu = True
        self.current_image = None
        self.start_time = None
        self.elapsed_time = 0
        self.score = 0
        self.selected_piece = None
        self.animation_in_progress = False
        pygame.display.set_caption("Puzzle - Menu Principal")

    def draw_menu(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        # Titre
        title_text = self.title_font.render("Sélectionnez un Puzzle", True, BLACK)
        title_rect = title_text.get_rect(center=(self.window_size[0]//2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Dessiner les boutons d'images
        for button in self.image_buttons:
            # Afficher le nom de l'image au-dessus (sans l'extension)
            name = button['name'].rsplit('.', 1)[0]  # Enlever l'extension
            name_text = self.font.render(name, True, BLACK)
            name_rect = name_text.get_rect(midbottom=(button['rect'].centerx, button['rect'].top - 10))
            self.screen.blit(name_text, name_rect)
            
            button['rect'].size = button['image'].get_size()  # Ajuste la taille du bouton à celle de l'image
            pygame.draw.rect(self.screen, GRAY, button['rect'])  # Dessine le fond gris avec la nouvelle taille

            # Dessiner l'image
            image_rect = button['image'].get_rect(center=button['rect'].center)
            self.screen.blit(button['image'], image_rect)
            
            # Afficher le meilleur score ou "NA" en dessous
            if button['name'] in self.highscores and self.highscores[button['name']]:
                best_score = max(score['score'] for score in self.highscores[button['name']])
                score_text = self.font.render(f"{best_score} pts", True, BLACK)
            else:
                score_text = self.font.render("NA", True, BLACK)
            score_rect = score_text.get_rect(midtop=(button['rect'].centerx, button['rect'].bottom + 10))
            self.screen.blit(score_text, score_rect)
        
        # Add the score calculation message
        score_info_text = self.font.render("Le score est calculé comme 1000 moins le temps passé à résoudre le puzzle en secondes.", True, BLACK)
        self.screen.blit(score_info_text, (self.window_size[0] // 2 - 500, self.window_size[1] - 50))
        
        pygame.display.flip()

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        if self.in_menu:
            self.draw_menu()
            return
            
        # Dessin du bouton d'accueil
        self.draw_home_button()
        
        # Mise à jour des animations
        if self.animation_in_progress:
            all_done = True
            for piece in self.pieces:
                if piece.is_moving:
                    if piece.update():
                        continue
                    all_done = False
            
            if all_done:
                self.animation_in_progress = False
                if self.check_win():
                    return
        
        # Dessin des pièces
        for i, piece in enumerate(self.pieces):
            rect = self.get_piece_rect(*piece.current_pos)
            self.screen.blit(piece.surface, rect)
            if i == self.selected_piece:
                pygame.draw.rect(self.screen, (255, 0, 0), rect, 3)

        # Affichage du temps
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
            time_text = self.font.render(f"Temps: {int(self.elapsed_time)}s", True, BLACK)
            self.screen.blit(time_text, (200, 10))

        # Affichage du meilleur score pour l'image actuelle
        if self.current_image in self.highscores and self.highscores[self.current_image]:
            best_score = max(score['score'] for score in self.highscores[self.current_image])
            score_text = self.font.render(f"Meilleur score: {best_score} pts", True, BLACK)
            self.screen.blit(score_text, (400, 10))

        # Affichage du classement à droite
        if self.current_image in self.highscores and self.highscores[self.current_image]:
            scores = sorted(self.highscores[self.current_image], key=lambda x: x['score'], reverse=True)[:5]
            title_text = self.font.render("Top 5 Scores:", True, BLACK)
            self.screen.blit(title_text, (self.window_size[0] - 200, 50))
            
            for i, score in enumerate(scores):
                score_text = self.font.render(f"{score['score']} pts", True, BLACK)
                self.screen.blit(score_text, (self.window_size[0] - 200, 90 + i * 30))

        pygame.display.flip()

    def print_pieces_grid(self):
        # Créer une grille vide
        grid = [[None for _ in range(GRID_SIZE[0])] for _ in range(GRID_SIZE[1])]
        
        # Remplir la grille avec les IDs des pièces
        for piece in self.pieces:
            row, col = piece.current_pos
            grid[row][col] = piece.piece_id
            
        # print("\nÉtat actuel du puzzle:")
        # print("-" * (GRID_SIZE[0] * 4 + 1))
        # for row in grid:
        #     print("|", end=" ")
        #     for piece_id in row:
        #         print(f"{piece_id:2}", end=" |")
        #     print("\n" + "-" * (GRID_SIZE[0] * 4 + 1))

    def run(self):
        while self.is_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.animation_in_progress:
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not self.in_menu:
                            self.reset_game()
                        else:
                            self.is_running = False

            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    try:
        game = PuzzleGame()
        game.run()
    except Exception as e:
        # print("\nUne erreur s'est produite :")
        # print(e)
        # print("\nAppuyez sur Entrée pour fermer...")
        input()
    finally:
        pygame.quit()
        sys.exit()
