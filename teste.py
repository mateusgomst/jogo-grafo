import pygame
import networkx as nx
import math
import random
import time

# Inicializar pygame
pygame.init()
WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PvP Graph Battle - Encontre o Melhor Caminho!")
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
PINK = (255, 192, 203)

# CONFIGURAÇÕES PRINCIPAIS DO JOGO
TIME_LIMIT = 20  # Tempo limite por turno em segundos
PLAYER_MAX_HP = 150  # HP máximo de cada jogador
BONUS_4_NODES = 5  # Bônus para caminhos de exatamente 4 nós
PENALTY_PER_EXTRA_NODE = 10  # Penalidade por cada nó extra além de 5

# ESTADOS DO JOGO - Controla o fluxo do jogo
MENU = 0
PLAYER1_TURN = 1
PLAYER2_TURN = 2
COMPARISON = 3
GAME_OVER = 4

# CLASSE PRINCIPAL QUE GERENCIA O ESTADO DO JOGO
class GameState:
    def __init__(self):
        self.player1_hp = PLAYER_MAX_HP
        self.player2_hp = PLAYER_MAX_HP
        self.start_time = time.time()  # Para controle do timer
        self.current_player = 1
        self.state = MENU
        self.round_number = 1
        
        # Armazena os caminhos escolhidos pelos jogadores
        self.player1_path = []
        self.player2_path = []
        self.player1_damage = 0
        self.player2_damage = 0
        
        # Resultado da rodada
        self.round_winner = 0
        self.damage_dealt = 0

game_state = GameState()

# CONFIGURAÇÃO DO GRAFO
G = nx.Graph()  # Grafo não-direcionado usando NetworkX
positions = {}  # Posições dos nós na tela
node_radius = 20
path_selected = []  # Caminho atual sendo construído
message = ""

# POSIÇÕES FIXAS DOS NÓS - Layout estratégico em camadas
fixed_positions = [
    (WIDTH // 2, 180),          # 0 (Start) - Top center
    (WIDTH // 2 - 200, 270),    # 1
    (WIDTH // 2 + 200, 270),    # 2
    (WIDTH // 2 - 300, 320),    # 3
    (WIDTH // 2, 320),          # 4
    (WIDTH // 2 + 300, 320),    # 5
    (WIDTH // 2 - 200, 390),    # 6
    (WIDTH // 2 + 200, 390),    # 7
    (WIDTH // 2 - 300, 450),    # 8
    (WIDTH // 2, 450),          # 9
    (WIDTH // 2 + 300, 450),    # 10
    (WIDTH // 2 - 200, 540),    # 11
    (WIDTH // 2 + 200, 540),    # 12
    (WIDTH // 2, 610)           # 13 (End) - Bottom center
]

# Criar nós no grafo
for i, pos in enumerate(fixed_positions):
    G.add_node(i)
    positions[i] = pos

# DEFINIÇÃO DAS CONEXÕES DO GRAFO - Estrutura em camadas
edges = []
# Layer 0 (Start) to Layer 1
edges.extend([(0,1), (0,2), (0,4)])
# Layer 1 to Layer 2
edges.extend([(1,3), (1,6), (1,4), (2,5), (2,4)])
# Layer 2 to Layer 3
edges.extend([(3,8), (3,6), (4,6), (4,7), (4,5), (5,7), (5,10)])
# Layer 3 to Layer 4
edges.extend([(6,7), (6,8), (6,11), (6,9), (7,9), (7,10), (7,12)])
# Layer 4 to Layer 5
edges.extend([(8,11), (9,11), (9,12), (9,13), (10,12)])
# Layer 5 to End
edges.extend([(11,13), (12,13)])

def randomize_weights():
    """FUNÇÃO CRÍTICA: Gera pesos aleatórios para as arestas a cada rodada"""
    G.remove_edges_from(list(G.edges())) 
    for u, v_node in edges: 
        damage = random.randint(8, 25)  # Dano aleatório entre 8-25
        G.add_edge(u, v_node, weight=damage)

randomize_weights()

start_node = 0  # Nó inicial
end_node = 13   # Nó final

def calculate_weight(path):
    """Calcula o peso total (dano base) de um caminho"""
    if len(path) < 2:
        return 0
    
    total = 0
    for i in range(len(path)-1):
        u, v_node = path[i], path[i+1]
        if G.has_edge(u, v_node):
            total += G[u][v_node]['weight']
        else:
            return 0  # Caminho inválido
    return total

def calculate_final_damage(path):
    """FUNÇÃO ESTRATÉGICA: Calcula dano final com bônus/penalidades"""
    base_damage = calculate_weight(path)
    if base_damage == 0:
        return 0
    
    path_length = len(path)
    
    # Sistema de bônus/penalidades baseado no comprimento do caminho
    if path_length == 4:
        return base_damage + BONUS_4_NODES  # Bônus para caminhos curtos
    elif path_length == 5:
        return base_damage  # Comprimento ideal
    elif path_length > 5:
        penalty = (path_length - 5) * PENALTY_PER_EXTRA_NODE
        return max(0, base_damage - penalty)  # Penalidade para caminhos longos
    else:
        return base_damage

start_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 150, 200, 60)

def draw_menu():
    """Desenha a tela do menu com instruções"""
    screen.fill((20, 20, 40))
    title_text = TITLE_FONT.render("PvP GRAPH BATTLE", True, YELLOW)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 200))
    screen.blit(title_text, title_rect)
    
    subtitle_text = BIG_FONT.render("Duelo de Caminhos!", True, WHITE)
    subtitle_rect = subtitle_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 150))
    screen.blit(subtitle_text, subtitle_rect)
    
    # Instruções do jogo
    instructions = [
        "- Jogador 1 (AZUL) vs Jogador 2 (ROSA)",
        "- Cada jogador faz seu caminho do nó 0 ao nó 13",
        "- O caminho com MAIOR peso vence a rodada",
        "- Apenas o perdedor recebe dano",
        "- Bônus: Caminhos de 4 nós (+5 dano)",
        "- Normal: Caminhos de 5 nós (dano normal)",
        "- Penalidade: Caminhos >5 nós (-10 por nó extra)",
        "- 20 segundos por turno"
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

def get_current_player_color():
    """Retorna a cor do jogador atual"""
    return BLUE if game_state.current_player == 1 else PINK

def draw_hud():
    """Desenha a interface com HP, timer e informações"""
    pygame.draw.rect(screen, (50, 50, 50), (10, 10, WIDTH-20, 120))
    pygame.draw.rect(screen, WHITE, (10, 10, WIDTH-20, 120), 2)
    
    # Rodada e turno atual
    round_text = BIG_FONT.render(f"Rodada: {game_state.round_number}", True, YELLOW)
    screen.blit(round_text, (20, 20))
    
    current_player_color = get_current_player_color()
    turn_text = BIG_FONT.render(f"Turno: Jogador {game_state.current_player}", True, current_player_color)
    screen.blit(turn_text, (200, 20))
    
    # TIMER - Controle de tempo por turno
    elapsed = time.time() - game_state.start_time
    remaining = max(0, TIME_LIMIT - elapsed)
    time_color = RED if remaining < 5 else WHITE
    time_text = BIG_FONT.render(f"Tempo: {remaining:.1f}s", True, time_color)
    screen.blit(time_text, (420, 20))
    
    # BARRAS DE HP - Visualização da vida dos jogadores
    bar_width = 180
    bar_height = 20
    
    # Player 1 HP
    player1_hp_percent = game_state.player1_hp / PLAYER_MAX_HP if PLAYER_MAX_HP > 0 else 0
    pygame.draw.rect(screen, RED, (20, 50, bar_width, bar_height))
    pygame.draw.rect(screen, BLUE, (20, 50, bar_width * player1_hp_percent, bar_height))
    pygame.draw.rect(screen, WHITE, (20, 50, bar_width, bar_height), 2)
    player1_text = FONT.render(f"Jogador 1: {game_state.player1_hp}/{PLAYER_MAX_HP}", True, WHITE)
    screen.blit(player1_text, (210, 52))
    
    # Player 2 HP
    player2_hp_percent = game_state.player2_hp / PLAYER_MAX_HP if PLAYER_MAX_HP > 0 else 0
    pygame.draw.rect(screen, RED, (20, 80, bar_width, bar_height))
    pygame.draw.rect(screen, PINK, (20, 80, bar_width * player2_hp_percent, bar_height))
    pygame.draw.rect(screen, WHITE, (20, 80, bar_width, bar_height), 2)
    player2_text = FONT.render(f"Jogador 2: {game_state.player2_hp}/{PLAYER_MAX_HP}", True, WHITE)
    screen.blit(player2_text, (210, 82))
    
    # Dicas estratégicas
    bonus_text = FONT.render("4 nós: +5 | 5 nós: normal | >5 nós: -10/extra", True, CYAN)
    screen.blit(bonus_text, (420, 52))
    
    reset_text = FONT.render("ESPAÇO: novos pesos", True, GRAY)
    screen.blit(reset_text, (420, 82))

def draw_game():
    """Desenha a tela principal do jogo durante os turnos"""
    screen.fill((20, 20, 40))
    draw_hud()

    # Desenhar arestas e seus pesos
    for u, v_node in G.edges():
        pygame.draw.line(screen, GRAY, positions[u], positions[v_node], 2)
        mx = (positions[u][0] + positions[v_node][0]) // 2
        my = (positions[u][1] + positions[v_node][1]) // 2
        weight = G[u][v_node]['weight']
        
        # Mostrar peso da aresta
        text_surf = FONT.render(str(weight), True, WHITE)
        text_rect = text_surf.get_rect(center=(mx, my))
        screen.blit(text_surf, text_rect)

    # Desenhar caminho atual sendo construído
    current_color = get_current_player_color()
    for i in range(len(path_selected)-1):
        pygame.draw.line(screen, current_color, positions[path_selected[i]], positions[path_selected[i+1]], 5)

    # Desenhar nós com cores específicas
    for node, pos in positions.items():
        is_selected = node in path_selected
        is_start = node == start_node
        is_end = node == end_node
        
        color = GREEN
        text_color = BLACK
        
        if is_start: 
            color = CYAN
        elif is_end: 
            color = ORANGE
        elif is_selected: 
            color = current_color
            
        pygame.draw.circle(screen, color, pos, node_radius)
        pygame.draw.circle(screen, WHITE, pos, node_radius, 2)
        
        node_label = "S" if is_start else ("E" if is_end else str(node))
        text = FONT.render(node_label, True, text_color)
        text_rect = text.get_rect(center=pos)
        screen.blit(text, text_rect)

    # Mostrar informações do caminho atual
    if path_selected:
        base_damage = calculate_weight(path_selected)
        final_damage = calculate_final_damage(path_selected)
        path_info = f"Caminho: {' -> '.join(map(str, path_selected))} | Base: {base_damage} | Final: {final_damage}"
        info_text = FONT.render(path_info, True, current_color)
        screen.blit(info_text, (20, 140))

    # Mostrar mensagem de feedback
    if message:
        msg_surface = FONT.render(message, True, WHITE)
        msg_rect = msg_surface.get_rect()
        msg_rect.center = (WIDTH // 2, HEIGHT - 30) 
        bg_surface = pygame.Surface((msg_rect.width + 20, msg_rect.height + 10), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        screen.blit(bg_surface, (msg_rect.left - 10, msg_rect.top - 5))
        screen.blit(msg_surface, msg_rect)

    pygame.display.flip()

def draw_comparison():
    """Desenha a tela de comparação dos caminhos dos dois jogadores"""
    screen.fill((20, 20, 40))
    draw_hud()

    # Desenhar arestas
    for u, v_node in G.edges():
        pygame.draw.line(screen, GRAY, positions[u], positions[v_node], 2)

    # Desenhar ambos os caminhos simultaneamente
    if game_state.player1_path:
        for i in range(len(game_state.player1_path)-1):
            pygame.draw.line(screen, BLUE, positions[game_state.player1_path[i]], positions[game_state.player1_path[i+1]], 4)

    if game_state.player2_path:
        for i in range(len(game_state.player2_path)-1):
            pygame.draw.line(screen, PINK, positions[game_state.player2_path[i]], positions[game_state.player2_path[i+1]], 4)

    # Desenhar nós
    for node, pos in positions.items():
        is_start = node == start_node
        is_end = node == end_node
        
        color = GREEN
        text_color = BLACK
        
        if is_start: 
            color = CYAN
        elif is_end: 
            color = ORANGE
            
        pygame.draw.circle(screen, color, pos, node_radius)
        pygame.draw.circle(screen, WHITE, pos, node_radius, 2)
        
        node_label = "S" if is_start else ("E" if is_end else str(node))
        text = FONT.render(node_label, True, text_color)
        text_rect = text.get_rect(center=pos)
        screen.blit(text, text_rect)

    # COMPARAÇÃO DOS RESULTADOS
    y_offset = 140
    
    # Jogador 1
    p1_text = f"Jogador 1 (AZUL): {' -> '.join(map(str, game_state.player1_path)) if game_state.player1_path else 'SEM CAMINHO'}"
    p1_damage_text = f"Dano Final: {game_state.player1_damage}"
    screen.blit(FONT.render(p1_text, True, BLUE), (20, y_offset))
    screen.blit(FONT.render(p1_damage_text, True, BLUE), (20, y_offset + 25))
    
    # Jogador 2
    p2_text = f"Jogador 2 (ROSA): {' -> '.join(map(str, game_state.player2_path)) if game_state.player2_path else 'SEM CAMINHO'}"
    p2_damage_text = f"Dano Final: {game_state.player2_damage}"
    screen.blit(FONT.render(p2_text, True, PINK), (20, y_offset + 60))
    screen.blit(FONT.render(p2_damage_text, True, PINK), (20, y_offset + 85))
    
    # Resultado da rodada
    if game_state.round_winner > 0:
        winner_color = BLUE if game_state.round_winner == 1 else PINK
        winner_text = f"VENCEDOR: Jogador {game_state.round_winner}! Dano causado: {game_state.damage_dealt}"
        screen.blit(BIG_FONT.render(winner_text, True, winner_color), (20, y_offset + 120))
    elif game_state.player1_damage == game_state.player2_damage and game_state.player1_damage > 0:
        screen.blit(BIG_FONT.render("EMPATE! Nenhum jogador recebe dano.", True, YELLOW), (20, y_offset + 120))
    
    continue_text = "Pressione ENTER para continuar..."
    screen.blit(FONT.render(continue_text, True, WHITE), (20, HEIGHT - 60))

    pygame.display.flip()

def draw_game_over():
    """Desenha a tela de fim de jogo"""
    screen.fill((20, 20, 40))
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    # Determinar vencedor
    if game_state.player1_hp <= 0:
        winner_text = TITLE_FONT.render("JOGADOR 2 VENCEU!", True, PINK)
        loser_text = "Jogador 1 foi derrotado!"
    elif game_state.player2_hp <= 0:
        winner_text = TITLE_FONT.render("JOGADOR 1 VENCEU!", True, BLUE)
        loser_text = "Jogador 2 foi derrotado!"
    else:
        winner_text = TITLE_FONT.render("TEMPO ESGOTADO!", True, RED)
        loser_text = "Jogo encerrado por tempo!"
    
    winner_rect = winner_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
    screen.blit(winner_text, winner_rect)
    
    loser_surface = BIG_FONT.render(loser_text, True, WHITE)
    loser_rect = loser_surface.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
    screen.blit(loser_surface, loser_rect)
    
    stats_text = BIG_FONT.render(f"Rodadas Completadas: {game_state.round_number}", True, WHITE)
    stats_rect = stats_text.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(stats_text, stats_rect)
    
    hp_text = BIG_FONT.render(f"HP Final - J1: {game_state.player1_hp} | J2: {game_state.player2_hp}", True, WHITE)
    hp_rect = hp_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))
    screen.blit(hp_text, hp_rect)
    
    restart_text = BIG_FONT.render("Pressione R para Voltar ao Menu", True, YELLOW)
    restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80))
    screen.blit(restart_text, restart_rect)
    
    pygame.display.flip()

def get_node_clicked(pos):
    """Detecta qual nó foi clicado baseado na posição do mouse"""
    for node, coord in positions.items():
        dist = math.hypot(pos[0] - coord[0], pos[1] - coord[1])
        if dist <= node_radius:
            return node
    return None

def check_time():
    """Verifica se o tempo do turno esgotou"""
    elapsed = time.time() - game_state.start_time
    if elapsed >= TIME_LIMIT:
        return True
    return False

def reset_timer():
    """Reinicia o timer para o próximo turno"""
    game_state.start_time = time.time()

def is_valid_path(path):
    """Verifica se o caminho é válido (conectado e vai do início ao fim)"""
    if len(path) < 2:
        return False
    if path[0] != start_node or path[-1] != end_node:
        return False
    
    for i in range(len(path)-1):
        if not G.has_edge(path[i], path[i+1]):
            return False
    return True

def compare_paths():
    """FUNÇÃO CENTRAL: Compara os caminhos e determina o vencedor da rodada"""
    global message
    
    # Calcular danos finais para ambos os jogadores
    game_state.player1_damage = calculate_final_damage(game_state.player1_path) if is_valid_path(game_state.player1_path) else 0
    game_state.player2_damage = calculate_final_damage(game_state.player2_path) if is_valid_path(game_state.player2_path) else 0
    
    # Determinar vencedor (maior dano vence)
    if game_state.player1_damage > game_state.player2_damage:
        game_state.round_winner = 1
        game_state.damage_dealt = game_state.player1_damage
        game_state.player2_hp = max(0, game_state.player2_hp - game_state.damage_dealt)
    elif game_state.player2_damage > game_state.player1_damage:
        game_state.round_winner = 2
        game_state.damage_dealt = game_state.player2_damage
        game_state.player1_hp = max(0, game_state.player1_hp - game_state.damage_dealt)
    else:
        game_state.round_winner = 0  # Empate
        game_state.damage_dealt = 0

def next_turn():
    """Gerencia a transição entre turnos"""
    global path_selected, message
    
    if game_state.state == PLAYER1_TURN:
        # Salvar caminho do jogador 1
        game_state.player1_path = list(path_selected)
        path_selected = []
        game_state.current_player = 2
        game_state.state = PLAYER2_TURN
        reset_timer()
        message = f"Turno do Jogador 2! Faça seu melhor caminho."
        
    elif game_state.state == PLAYER2_TURN:
        # Salvar caminho do jogador 2 e comparar
        game_state.player2_path = list(path_selected)
        path_selected = []
        compare_paths()
        game_state.state = COMPARISON
        message = "Comparando caminhos..."

def start_new_round():
    """Inicia uma nova rodada com pesos randomizados"""
    global message, path_selected
    
    randomize_weights()  # Novos pesos aleatórios
    game_state.round_number += 1
    game_state.current_player = 1
    game_state.state = PLAYER1_TURN
    game_state.player1_path = []
    game_state.player2_path = []
    game_state.player1_damage = 0
    game_state.player2_damage = 0
    game_state.round_winner = 0
    game_state.damage_dealt = 0
    path_selected = []
    reset_timer()
    message = f"Rodada {game_state.round_number}! Turno do Jogador 1."

def reset_game():
    """Reinicia o jogo completamente"""
    global game_state, path_selected, message
    game_state = GameState()
    randomize_weights()
    path_selected = []
    message = ""

def start_game():
    """Inicia o jogo a partir do menu"""
    global message
    game_state.state = PLAYER1_TURN
    game_state.current_player = 1
    randomize_weights()
    reset_timer()
    message = f"Rodada {game_state.round_number}! Turno do Jogador 1 - Encontre o melhor caminho!"

# Inicialização
running = True
clock = pygame.time.Clock()

while running:
    if game_state.state == MENU:
        draw_menu()
    elif game_state.state in [PLAYER1_TURN, PLAYER2_TURN]:
        if check_time():
            next_turn()
        else:
            draw_game()
    elif game_state.state == COMPARISON:
        draw_comparison()
    elif game_state.state == GAME_OVER:
        draw_game_over()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state.state == MENU:
                if start_button.collidepoint(event.pos):
                    start_game()
            elif game_state.state in [PLAYER1_TURN, PLAYER2_TURN]:
                node = get_node_clicked(event.pos)
                if node is not None:
                    if not path_selected and node == start_node:
                        path_selected.append(node)
                        message = f"Jogador {game_state.current_player}: Nó inicial selecionado. Continue até o nó final ({end_node})."
                    elif path_selected and node not in path_selected: 
                        if G.has_edge(path_selected[-1], node):
                             path_selected.append(node)
                             message = f"Jogador {game_state.current_player}: {' -> '.join(map(str, path_selected))}"
                             if node == end_node:
                                 message += ". Pressione ENTER para confirmar!"
                        else:
                            message = f"Jogador {game_state.current_player}: Nó não conectado ao anterior!"
                    elif node in path_selected:
                        message = f"Jogador {game_state.current_player}: Nó já selecionado no caminho atual."

        elif event.type == pygame.KEYDOWN:
            if game_state.state in [PLAYER1_TURN, PLAYER2_TURN]:
                if event.key == pygame.K_RETURN:
                    if len(path_selected) < 2 or path_selected[0] != start_node or path_selected[-1] != end_node:
                        message = f"Jogador {game_state.current_player}: Caminho deve ir do nó {start_node} ao nó {end_node}!"
                        continue
                    
                    next_turn()
                    
                elif event.key == pygame.K_SPACE:
                    randomize_weights()
                    message = f"Jogador {game_state.current_player}: Pesos randomizados!"
                    
            elif game_state.state == COMPARISON:
                if event.key == pygame.K_RETURN:
                    # Verificar se alguém morreu
                    if game_state.player1_hp <= 0 or game_state.player2_hp <= 0:
                        game_state.state = GAME_OVER
                    else:
                        start_new_round()

            elif game_state.state == GAME_OVER: 
                 if event.key == pygame.K_r:
                    reset_game()

    clock.tick(60)

pygame.quit()