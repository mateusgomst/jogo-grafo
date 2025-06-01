import pygame
import networkx as nx
import math
import random
import time

# Inicializar pygame
pygame.init()
WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RPG Boss Battle - Caminho de 5 Nós!")
FONT = pygame.font.SysFont("Arial", 18)
BIG_FONT = pygame.font.SysFont("Arial", 24, bold=True)
TITLE_FONT = pygame.font.SysFont("Arial", 36, bold=True)

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 200, 100)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)
DARK_RED = (139, 0, 0)
LIGHT_GREEN = (144, 238, 144)

# Configurações do jogo
TIME_LIMIT = 15
BOSS_MAX_HP = 100
PLAYER_MAX_HP = 150
REQUIRED_PATH_LENGTH = 5
BOSS_ATTACK_DAMAGE = 50

# Estados do jogo
MENU = 0
PLAYING = 1
GAME_OVER = 2

# Estado do jogo
class GameState:
    def __init__(self):
        self.boss_hp = BOSS_MAX_HP
        self.player_hp = PLAYER_MAX_HP
        self.start_time = time.time()
        self.game_over = False
        self.victory = False
        self.attempts = 0
        self.total_damage_dealt = 0
        self.state = MENU
        self.round_number = 1

game_state = GameState()

# Grafo
G = nx.Graph()
positions = {}
node_radius = 20
path_selected = []
optimal_path_fixed_length = []
checked = False # True if player made a valid suboptimal attack, to show optimal path
message = ""
max_possible_damage = 0


# Gerar nós em posições fixas para 15 vértices
fixed_positions = [
    (WIDTH // 2, 180),          # 0 (Player) - Top center

    (WIDTH // 2 - 200, 270),    # 1
    (WIDTH // 2, 270),          # 2
    (WIDTH // 2 + 200, 270),    # 3

    (WIDTH // 2 - 300, 360),    # 4
    (WIDTH // 2 - 150, 360),    # 5
    (WIDTH // 2, 360),          # 6
    (WIDTH // 2 + 150, 360),    # 7
    (WIDTH // 2 + 300, 360),    # 8

    (WIDTH // 2 - 200, 450),    # 9
    (WIDTH // 2, 450),          # 10
    (WIDTH // 2 + 200, 450),    # 11

    (WIDTH // 2 - 100, 540),    # 12
    (WIDTH // 2 + 100, 540),    # 13
    (WIDTH // 2, 610)           # 14 (Boss) - Bottom center
]

for i, pos in enumerate(fixed_positions):
    G.add_node(i)
    positions[i] = pos

# Adicionar arestas para o grafo de 15 nós
edges = []
# Layer 0 (Player) to Layer 1
edges.extend([(0,1), (0,2), (0,3)])
# Layer 1 to Layer 2
edges.extend([(1,4), (1,5), (2,5), (2,6), (2,7), (3,7), (3,8)])
# Layer 2 to Layer 3
edges.extend([(4,9), (5,9), (5,10), (6,10), (7,10), (7,11), (8,11)])
# Layer 3 to Layer 4 (nodes 12, 13)
edges.extend([(9,12), (10,12), (10,13), (11,13)])
# Layer 4 to Boss (node 14)
edges.extend([(12,14), (13,14)])

# Add some intra-layer edges for more path variety
edges.extend([(1,2), (2,3)]) # Layer 1
edges.extend([(4,5), (5,6), (6,7), (7,8)]) # Layer 2
edges.extend([(9,10), (10,11)]) # Layer 3
edges.extend([(12,13)]) # Layer 4

# *** MODIFICATION: Add direct edges from Layer 3 to Boss for 5-node paths ***
edges.extend([(9,14), (10,14), (11,14)])


def randomize_weights():
    """Gerar pesos aleatórios para todas as arestas"""
    G.remove_edges_from(list(G.edges())) 
    for u, v_node in edges: 
        damage = random.randint(8, 25)
        G.add_edge(u, v_node, weight=damage)

randomize_weights()

player_node = 0
boss_node = 14

def calculate_weight(path):
    """Calcular o peso total de um caminho"""
    total = 0
    for i in range(len(path)-1):
        u, v_node = path[i], path[i+1]
        if G.has_edge(u, v_node):
            total += G[u][v_node]['weight']
        else:
            return 0
    return total

def find_best_path_of_length(graph, start, end, length_req):
    """Encontrar o caminho com maior peso para um comprimento específico de nós"""
    all_valid_paths = []
    # print(f"DEBUG: Finding paths from {start} to {end} of length {length_req}")
    for path in nx.all_simple_paths(graph, source=start, target=end):
        if len(path) == length_req:
            all_valid_paths.append(path)
    
    # print(f"DEBUG: Found {len(all_valid_paths)} paths of length {length_req}")
    if not all_valid_paths:
        # print(f"DEBUG: No paths of length {length_req} found.")
        return []
    
    max_w = -1
    best_p = []
    
    for p in all_valid_paths:
        w = calculate_weight(p)
        if w > max_w:
            max_w = w
            best_p = p
            
    # print(f"DEBUG: Best path of length {length_req} is {best_p} with weight {max_w}")
    return best_p

def update_optimal_path_info():
    """Atualizar o caminho ótimo de comprimento fixo e seu dano"""
    global optimal_path_fixed_length, max_possible_damage
    optimal_path_fixed_length = find_best_path_of_length(G, player_node, boss_node, REQUIRED_PATH_LENGTH)
    max_possible_damage = calculate_weight(optimal_path_fixed_length) if optimal_path_fixed_length else 0

start_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 150, 200, 60)

def draw_menu():
    screen.fill((20, 20, 40))
    title_text = TITLE_FONT.render("RPG BOSS BATTLE", True, YELLOW)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 200))
    screen.blit(title_text, title_rect)
    
    subtitle_text = BIG_FONT.render(f"Encontre o Caminho de {REQUIRED_PATH_LENGTH} Nós de Maior Dano!", True, WHITE)
    subtitle_rect = subtitle_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 150))
    screen.blit(subtitle_text, subtitle_rect)
    
    instructions = [
        f"- Clique em {REQUIRED_PATH_LENGTH} nós conectados para traçar um caminho.",
        "- Pressione ENTER para atacar o boss.",
        "- Encontre o caminho com MAIOR peso para maximizar dano.",
        "- Você tem 15 segundos por rodada.",
        "- O Boss ataca com 50 de dano após sua ação!",
        "- Cronômetro reinicia a cada ataque bem-sucedido.",
        f"- Sua HP inicial: {PLAYER_MAX_HP}.",
        "- Derrote o boss antes que sua HP chegue a zero!"
    ]
    
    for i, instruction in enumerate(instructions):
        inst_text = FONT.render(instruction, True, WHITE)
        inst_rect = inst_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100 + i * 25))
        screen.blit(inst_text, inst_rect)
    
    pygame.draw.rect(screen, LIGHT_GREEN, start_button)
    pygame.draw.rect(screen, WHITE, start_button, 3)
    button_text = BIG_FONT.render("INICIAR JOGO", True, BLACK)
    button_rect = button_text.get_rect(center=start_button.center)
    screen.blit(button_text, button_rect)
    
    pygame.display.flip()

def draw_hud():
    pygame.draw.rect(screen, (50, 50, 50), (10, 10, WIDTH-20, 120))
    pygame.draw.rect(screen, WHITE, (10, 10, WIDTH-20, 120), 2)
    
    round_text = BIG_FONT.render(f"Rodada: {game_state.round_number}", True, YELLOW)
    screen.blit(round_text, (20, 20))
    
    elapsed = time.time() - game_state.start_time
    remaining = max(0, TIME_LIMIT - elapsed)
    time_color = RED if remaining < 5 else WHITE
    time_text = BIG_FONT.render(f"Tempo: {remaining:.1f}s", True, time_color)
    screen.blit(time_text, (220, 20))
    
    boss_hp_percent = game_state.boss_hp / BOSS_MAX_HP if BOSS_MAX_HP > 0 else 0
    bar_width = 200
    bar_height = 20
    pygame.draw.rect(screen, RED, (20, 50, bar_width, bar_height))
    pygame.draw.rect(screen, GREEN, (20, 50, bar_width * boss_hp_percent, bar_height))
    pygame.draw.rect(screen, WHITE, (20, 50, bar_width, bar_height), 2)
    boss_text = FONT.render(f"Boss HP: {game_state.boss_hp}/{BOSS_MAX_HP}", True, WHITE)
    screen.blit(boss_text, (230, 52))
    
    player_hp_percent = game_state.player_hp / PLAYER_MAX_HP if PLAYER_MAX_HP > 0 else 0
    pygame.draw.rect(screen, RED, (20, 80, bar_width, bar_height))
    pygame.draw.rect(screen, BLUE, (20, 80, bar_width * player_hp_percent, bar_height))
    pygame.draw.rect(screen, WHITE, (20, 80, bar_width, bar_height), 2)
    player_text = FONT.render(f"Sua HP: {game_state.player_hp}/{PLAYER_MAX_HP}", True, WHITE)
    screen.blit(player_text, (230, 82))
    
    attempts_text = FONT.render(f"Tentativas: {game_state.attempts}", True, WHITE)
    screen.blit(attempts_text, (450, 25))
    
    damage_text = FONT.render(f"Dano Total: {game_state.total_damage_dealt}", True, WHITE)
    screen.blit(damage_text, (450, 50))
    
    hint_text = FONT.render(f"Dano Max. ({REQUIRED_PATH_LENGTH} nós): {max_possible_damage}", True, YELLOW)
    screen.blit(hint_text, (450, 75))
    
    reset_text = FONT.render("ESPACO para novos pesos", True, CYAN)
    screen.blit(reset_text, (680, 25))

def draw_game():
    screen.fill((20, 20, 40))
    draw_hud()

    for u, v_node in G.edges():
        pygame.draw.line(screen, GRAY, positions[u], positions[v_node], 2)
        mx = (positions[u][0] + positions[v_node][0]) // 2
        my = (positions[u][1] + positions[v_node][1]) // 2
        weight = G[u][v_node]['weight']
        
        text_surf = FONT.render(str(weight), True, WHITE)
        text_rect = text_surf.get_rect(center=(mx, my))
        screen.blit(text_surf, text_rect)

    # Player's currently selected path
    for i in range(len(path_selected)-1):
        pygame.draw.line(screen, CYAN, positions[path_selected[i]], positions[path_selected[i+1]], 5)

    # Show optimal path in yellow if 'checked' is true (player made a valid suboptimal attack)
    if checked and optimal_path_fixed_length and not game_state.victory :
        for i in range(len(optimal_path_fixed_length)-1):
            start_pos = positions[optimal_path_fixed_length[i]]
            end_pos = positions[optimal_path_fixed_length[i+1]]
            num_dashes = 10
            for j in range(num_dashes):
                if j % 2 == 0: 
                    t0 = j / num_dashes
                    t1 = (j + 0.5) / num_dashes 
                    pt1 = (start_pos[0] * (1-t0) + end_pos[0] * t0, 
                           start_pos[1] * (1-t0) + end_pos[1] * t0)
                    pt2 = (start_pos[0] * (1-t1) + end_pos[0] * t1, 
                           start_pos[1] * (1-t1) + end_pos[1] * t1)
                    pygame.draw.line(screen, YELLOW, pt1, pt2, 3)

    for node, pos in positions.items():
        is_selected = node in path_selected
        is_player = node == player_node
        is_boss = node == boss_node
        
        color = GREEN
        text_color = BLACK
        
        if is_player: color = CYAN
        elif is_boss: color = DARK_RED if game_state.boss_hp > 0 else GRAY; text_color = WHITE
        elif is_selected: color = YELLOW
            
        pygame.draw.circle(screen, color, pos, node_radius)
        pygame.draw.circle(screen, WHITE, pos, node_radius, 2)
        
        node_label = "P" if is_player else ("B" if is_boss else str(node))
        text = FONT.render(node_label, True, text_color)
        text_rect = text.get_rect(center=pos)
        screen.blit(text, text_rect)

    if message:
        msg_surface = FONT.render(message, True, WHITE)
        msg_rect = msg_surface.get_rect()
        msg_rect.center = (WIDTH // 2, HEIGHT - 30) 
        bg_surface = pygame.Surface((msg_rect.width + 20, msg_rect.height + 10), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        screen.blit(bg_surface, (msg_rect.left - 10, msg_rect.top - 5))
        screen.blit(msg_surface, msg_rect)

    pygame.display.flip()

def draw_game_over():
    screen.fill((20, 20, 40))
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    if game_state.victory:
        end_text = TITLE_FONT.render("VITORIA!", True, GREEN)
        sub_text = BIG_FONT.render("Boss Derrotado!", True, GREEN)
    else:
        end_text = TITLE_FONT.render("DERROTA!", True, RED)
        sub_text = BIG_FONT.render("Tempo Esgotado ou HP Zerada!", True, RED)
    
    end_rect = end_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
    screen.blit(end_text, end_rect)
    sub_rect = sub_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
    screen.blit(sub_text, sub_rect)
    
    stats_text = BIG_FONT.render(f"Tentativas: {game_state.attempts} | Dano Total: {game_state.total_damage_dealt}", True, WHITE)
    stats_rect = stats_text.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(stats_text, stats_rect)
    
    rounds_text = BIG_FONT.render(f"Rodadas Completadas: {game_state.round_number -1 if game_state.round_number > 1 else game_state.round_number}", True, WHITE)
    rounds_rect = rounds_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))
    screen.blit(rounds_text, rounds_rect)
    
    restart_text = BIG_FONT.render("Pressione R para Voltar ao Menu", True, YELLOW)
    restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80))
    screen.blit(restart_text, restart_rect)
    
    pygame.display.flip()

def get_node_clicked(pos):
    for node, coord in positions.items():
        dist = math.hypot(pos[0] - coord[0], pos[1] - coord[1])
        if dist <= node_radius:
            return node
    return None

def check_time():
    elapsed = time.time() - game_state.start_time
    if elapsed >= TIME_LIMIT and game_state.state == PLAYING:
        game_state.player_hp = max(0, game_state.player_hp - BOSS_ATTACK_DAMAGE)
        global message
        timeout_msg = f"Tempo esgotado! Boss atacou ({BOSS_ATTACK_DAMAGE} dano)."
        if game_state.player_hp <= 0:
             message = timeout_msg + " Sua HP chegou a zero!"
        else:
             message = timeout_msg + " Você perdeu a chance de atacar."
        game_state.state = GAME_OVER
        return True
    return False

def reset_timer():
    game_state.start_time = time.time()

def start_new_round():
    global checked, path_selected, message
    randomize_weights()
    update_optimal_path_info()
    reset_timer()
    game_state.round_number += 1
    path_selected = []
    checked = False # Reset checked flag for new round
    # Message is set by the K_RETURN logic or start_game

def reset_game():
    global game_state, path_selected, checked, message
    game_state = GameState()
    randomize_weights()
    update_optimal_path_info()
    path_selected = []
    checked = False # Reset checked flag
    game_state.state = MENU
    message = ""

def start_game():
    global game_state, message, checked
    if game_state.state == MENU: 
        game_state = GameState()
    
    game_state.state = PLAYING
    randomize_weights()
    update_optimal_path_info()
    reset_timer()
    checked = False # Reset checked flag
    message = f"Rodada {game_state.round_number}! Encontre o caminho de {REQUIRED_PATH_LENGTH} nós de MAIOR DANO!"

update_optimal_path_info()

running = True
clock = pygame.time.Clock()

while running:
    if game_state.state == MENU:
        draw_menu()
    elif game_state.state == PLAYING:
        if check_time(): 
            draw_game_over() 
        else:
            draw_game()
    elif game_state.state == GAME_OVER:
        draw_game_over()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state.state == MENU:
                if start_button.collidepoint(event.pos):
                    start_game()
            elif game_state.state == PLAYING:
                node = get_node_clicked(event.pos)
                if node is not None:
                    if not path_selected and node == player_node:
                        path_selected.append(node)
                        message = f"Nó inicial {node} selecionado. Continue até o Boss ({boss_node})."
                        checked = False # Player is building a new path
                    elif path_selected and node not in path_selected: 
                        if G.has_edge(path_selected[-1], node):
                             path_selected.append(node)
                             message = f"Caminho atual: {' -> '.join(map(str, path_selected))}"
                             if len(path_selected) == REQUIRED_PATH_LENGTH:
                                 message += ". Pressione ENTER para atacar!"
                             checked = False # Player is building a new path
                        else:
                            message = "Nó não conectado ao anterior!"
                    elif node in path_selected:
                        message = "Nó já selecionado no caminho atual."


        elif event.type == pygame.KEYDOWN:
            if game_state.state == PLAYING:
                if event.key == pygame.K_RETURN:
                    if len(path_selected) < 2 : 
                        message = "Caminho muito curto para atacar!"
                        path_selected = [] # Clear invalid path
                        checked = False # No valid attempt
                        continue 

                    game_state.attempts += 1
                    
                    action_message = ""
                    damage_this_turn = 0
                    penalty_this_turn = 0
                    
                    player_submitted_path = list(path_selected) # Store current path for checks

                    if len(player_submitted_path) != REQUIRED_PATH_LENGTH:
                        action_message = f"Falha! Caminho deve ter {REQUIRED_PATH_LENGTH} nós."
                        checked = False # Invalid attempt
                    elif player_submitted_path[0] != player_node or player_submitted_path[-1] != boss_node:
                        action_message = f"Falha! Caminho de P ({player_node}) para B ({boss_node})."
                        checked = False # Invalid attempt
                    else:
                        # Caminho Válido para ataque
                        damage_this_turn = calculate_weight(player_submitted_path)
                        game_state.total_damage_dealt += damage_this_turn
                        game_state.boss_hp = max(0, game_state.boss_hp - damage_this_turn)

                        if player_submitted_path != optimal_path_fixed_length:
                            penalty_this_turn = 15 
                            game_state.player_hp = max(0, game_state.player_hp - penalty_this_turn)
                            action_message = f"Dano: {damage_this_turn}. Perdeu {penalty_this_turn} HP (não ótimo)."
                            if optimal_path_fixed_length: # Only set checked if there IS an optimal path to show
                                checked = True # Suboptimal valid attack, show optimal
                            else:
                                checked = False # No optimal path to compare against
                        else:
                            action_message = f"CRÍTICO! Dano: {damage_this_turn}. Caminho perfeito!"
                            checked = False # Optimal attack, no need to highlight
                    
                    current_message_parts = [action_message]
                    path_selected = [] # Clear path AFTER all checks and message determination

                    if game_state.boss_hp <= 0:
                        game_state.victory = True
                        game_state.state = GAME_OVER
                        current_message_parts.append("BOSS DERROTADO!")
                        message = " ".join(filter(None, current_message_parts))
                    else:
                        game_state.player_hp = max(0, game_state.player_hp - BOSS_ATTACK_DAMAGE)
                        current_message_parts.append(f"Boss revidou: -{BOSS_ATTACK_DAMAGE} HP.")

                        if game_state.player_hp <= 0:
                            game_state.state = GAME_OVER
                            current_message_parts.append("Sua HP chegou a zero!")
                            message = " ".join(filter(None, current_message_parts))
                        else:
                            old_round_number = game_state.round_number
                            start_new_round() # This will reset 'checked' to False
                            
                            new_round_msg = f"Rodada {game_state.round_number}! Novos pesos. Encontre o caminho de {REQUIRED_PATH_LENGTH} nós!"
                            current_message_parts.append(new_round_msg)
                            message = " ".join(filter(None, current_message_parts))


                elif event.key == pygame.K_SPACE:
                    start_new_round() # This will reset 'checked' to False
                    message = f"Pesos randomizados manualmente! Rodada {game_state.round_number}."


            elif game_state.state == GAME_OVER: 
                 if event.key == pygame.K_r:
                    reset_game() 

    clock.tick(60)

pygame.quit()
