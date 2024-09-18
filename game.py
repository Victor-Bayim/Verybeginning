import pygame
import random
import sys
import threading
import time
import json
import os

# 获取脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pygame.init()

# 屏幕尺寸
WIDTH, HEIGHT = 1024, 768  # 增大屏幕尺寸

# 游戏状态常量
STATE_MAIN_MENU = 'main_menu'
STATE_GAME = 'game'
STATE_CONTINUE_GAME_SELECTION = 'continue_game_selection'
STATE_LEADERBOARD = 'leaderboard'
STATE_GAME_OVER = 'game_over'
STATE_GAME_WIN = 'game_win'
STATE_CHARACTER_SELECTION = 'character_selection'  # 角色选择
STATE_NAME_INPUT = 'name_input'  # 名字输入

# 初始化当前状态为主菜单
current_state = STATE_MAIN_MENU

# 文件路径
LEADERBOARD_FILE = os.path.join(BASE_DIR, 'leaderboard.json')
SAVEGAME_FILE = os.path.join(BASE_DIR, 'savegame.json')

# 游戏设置
TILE_SIZE = 60  # 图案大小
ROWS, COLS = 8, 8  # 行数和列数
LAYER_COUNT = 3  # 层数
MAX_STACK_SIZE = 7  # 栈的最大容量
MAX_LEVEL = 5  # 最大关卡数

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_COLOR = (245, 245, 220)  # 米色背景
BUTTON_COLOR = (70, 130, 180)  # Steel Blue
BUTTON_HOVER_COLOR = (100, 160, 210)
BUTTON_TEXT_COLOR = WHITE
HINT_BUTTON_COLOR = (34, 139, 34)  # Forest Green
UNDO_BUTTON_COLOR = (178, 34, 34)  # Firebrick

# 初始化屏幕
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("投喂精灵")

# 时钟对象
clock = pygame.time.Clock()
FPS = 60  # 提高帧率，使动画更流畅

# 加载字体
font_path = os.path.join(BASE_DIR, 'fonts', 'NotoSansCJKsc-VF.otf')  # 使用绝对路径
try:
    font = pygame.font.Font(font_path, 24)       # 普通字体
    title_font = pygame.font.Font(font_path, 48) # 标题字体
    big_font = pygame.font.Font(font_path, 36)   # 大号字体
    info_font = pygame.font.Font(font_path, 32)  # 用于分数和关卡
except FileNotFoundError:
    print(f"无法加载字体文件: {font_path}")
    pygame.quit()
    sys.exit()

# 加载图案图片
pattern_images = []
for i in range(1, 9):  # 假设有8种图案
    image_path = os.path.join(BASE_DIR, f"pattern_{i}.png")
    if not os.path.exists(image_path):
        print(f"图案图片不存在: {image_path}")
        pygame.quit()
        sys.exit()
    try:
        image = pygame.image.load(image_path).convert_alpha()
        image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
        pattern_images.append(image)
    except pygame.error:
        print(f"无法加载图案图片: {image_path}")
        pygame.quit()
        sys.exit()

# 加载主菜单背景图片
menu_background_path = os.path.join(BASE_DIR, 'menu_background.png')
try:
    menu_background = pygame.image.load(menu_background_path).convert()
    menu_background = pygame.transform.scale(menu_background, (WIDTH, HEIGHT))  # 缩放至屏幕大小
except pygame.error:
    print(f"无法加载主菜单背景图片: {menu_background_path}")
    pygame.quit()
    sys.exit()

# 加载胜利界面背景图片
victory_background_path = os.path.join(BASE_DIR, 'victory_background.png')
try:
    victory_background = pygame.image.load(victory_background_path).convert()
    victory_background = pygame.transform.scale(victory_background, (WIDTH, HEIGHT))  # 缩放至屏幕大小
except pygame.error:
    print(f"无法加载胜利界面背景图片: {victory_background_path}")
    pygame.quit()
    sys.exit()

# 加载角色图片
character_images = [
    {'normal': os.path.join(BASE_DIR, 'character1_normal.png'), 'happy': os.path.join(BASE_DIR, 'character1_happy.png')},
    {'normal': os.path.join(BASE_DIR, 'character2_normal.png'), 'happy': os.path.join(BASE_DIR, 'character2_happy.png')}
]
selected_character = 0  # 默认选择第一个角色

# 加载背景图片
background_images = [
    os.path.join(BASE_DIR, 'bg1.png'),
    os.path.join(BASE_DIR, 'bg2.png'),
    os.path.join(BASE_DIR, 'bg3.png')
]
for bg in background_images:
    if not os.path.exists(bg):
        print(f"背景图片不存在: {bg}")
        pygame.quit()
        sys.exit()

# 加载剧情图片
story_images = [
    os.path.join(BASE_DIR, 'story1.png'),
    os.path.join(BASE_DIR, 'story2.png'),
    os.path.join(BASE_DIR, 'story3.png')
]
for story in story_images:
    if not os.path.exists(story):
        print(f"剧情图片不存在: {story}")
        pygame.quit()
        sys.exit()

# 全局变量
stack = []  # 存放玩家点击的图案
board_layers = []  # 存放多层的图案
score = 0  # 玩家得分
level = 1  # 当前关卡

# 角色名和玩家相关
player_name = ''

# 定义每层的偏移量，使层与层之间错开
layer_offsets = [
    {'x': 0, 'y': 0},  # 底层不偏移
    {'x': TILE_SIZE // 4, 'y': TILE_SIZE // 4},  # 第二层偏移
    {'x': TILE_SIZE // 2, 'y': TILE_SIZE // 2},  # 第三层偏移
]

# 定义全局变量，存储游戏区域和栈区域的边界矩形
game_area_rect = None
stack_area_rect = None

# 角色状态
character_state = 'normal'  # 'normal' or 'happy'
character_reaction_time = 0  # 角色互动状态的剩余时间

# 提示功能
hint_sequence = []  # 当前提示的图案序列
hint_calculating = False  # 是否正在计算提示

# 按钮尺寸
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50

# 主菜单按钮尺寸和位置
start_game_button = pygame.Rect(WIDTH / 2 - BUTTON_WIDTH / 2, HEIGHT / 2 - 150, BUTTON_WIDTH, BUTTON_HEIGHT)
continue_game_button = pygame.Rect(WIDTH / 2 - BUTTON_WIDTH / 2, HEIGHT / 2 - 70, BUTTON_WIDTH, BUTTON_HEIGHT)
leaderboard_button = pygame.Rect(WIDTH / 2 - BUTTON_WIDTH / 2, HEIGHT / 2 + 10, BUTTON_WIDTH, BUTTON_HEIGHT)
quit_game_button = pygame.Rect(WIDTH / 2 - BUTTON_WIDTH / 2, HEIGHT / 2 + 90, BUTTON_WIDTH, BUTTON_HEIGHT)

# 游戏内按钮
hint_button_rect = pygame.Rect(WIDTH - BUTTON_WIDTH - 40, 20, BUTTON_WIDTH, BUTTON_HEIGHT)
undo_button_rect = pygame.Rect(WIDTH - BUTTON_WIDTH - 40, 90, BUTTON_WIDTH, BUTTON_HEIGHT)

# 加载和保存排行榜数据
def load_leaderboard():
    global leaderboard
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                leaderboard = json.load(f)
        except json.JSONDecodeError:
            leaderboard = []
    else:
        leaderboard = []

def save_leaderboard():
    global leaderboard
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=4)

# 加载和保存游戏进度
def load_game():
    global player_name, score, level, stack, board_layers, selected_character
    if os.path.exists(SAVEGAME_FILE):
        try:
            with open(SAVEGAME_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                saved_games = data.get('saved_games', [])
                if not saved_games:
                    print("没有可继续的游戏。")
                    return False
                # 此函数只检查是否有保存的游戏
                return True
        except (json.JSONDecodeError, KeyError, TypeError):
            print("保存的游戏数据有误，无法加载。")
    return False

def load_specific_game(index):
    global player_name, score, level, stack, board_layers, selected_character
    if os.path.exists(SAVEGAME_FILE):
        try:
            with open(SAVEGAME_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                saved_games = data.get('saved_games', [])
                if index < 0 or index >= len(saved_games):
                    print("选择的游戏不存在。")
                    return False
                game_data = saved_games[index]
                player_name = game_data.get('player_name', '')
                score = game_data.get('score', 0)
                level = game_data.get('level', 1)
                stack_numbers = game_data.get('stack', [])
                
                # 重置 stack
                stack.clear()
                
                # 重置 board_layers
                board_layers_data = game_data.get('board_layers', [])
                board_layers = []  # 清空现有的 board_layers
                
                for layer_data in board_layers_data:
                    layer = []
                    for row_data in layer_data:
                        row = []
                        for number in row_data:
                            if number is not None:
                                tile = {
                                    'number': number,
                                    'image': pattern_images[number - 1],
                                    'rect': None,  # 需要重新计算位置
                                    'layer': None,  # 需要重新设置
                                    'original_position': None
                                }
                                row.append(tile)
                            else:
                                row.append(None)
                        layer.append(row)
                    board_layers.append(layer)
                
                # 重新计算每个 tile 的 rect 和 layer
                for layer_num, layer in enumerate(board_layers):
                    offset = layer_offsets[layer_num]
                    for row_num, row in enumerate(layer):
                        for col_num, tile in enumerate(row):
                            if tile:
                                rand_offset_x = random.randint(-TILE_SIZE // 8, TILE_SIZE // 8)
                                rand_offset_y = random.randint(-TILE_SIZE // 8, TILE_SIZE // 8)
                                tile['rect'] = pygame.Rect(
                                    col_num * TILE_SIZE + offset['x'] + rand_offset_x + 150,  # 右移，避免遮挡角色
                                    row_num * TILE_SIZE + offset['y'] + rand_offset_y,
                                    TILE_SIZE,
                                    TILE_SIZE
                                )
                                tile['layer'] = layer_num
                
                # 重新构建 stack based on saved numbers
                for number in stack_numbers:
                    # 查找一个未在 stack 中的 tile
                    found = False
                    for layer in board_layers:
                        for row in layer:
                            for tile in row:
                                if tile and tile['number'] == number and tile not in stack:
                                    stack.append(tile)
                                    remove_tile(tile)
                                    found = True
                                    break
                            if found:
                                break
                        if found:
                            break
                    if not found:
                        print(f"无法在棋盘中找到编号为 {number} 的图案以加入栈中。")
                
                # 恢复角色选择
                selected_character = game_data.get('selected_character', 0)
                return True
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"加载游戏数据时出错: {e}")
    return False

def save_game():
    global player_name, score, level, stack, board_layers, selected_character
    data = {}
    if os.path.exists(SAVEGAME_FILE):
        try:
            with open(SAVEGAME_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, KeyError, TypeError):
            data = {}
    saved_games = data.get('saved_games', [])
    
    # 检查当前角色是否已经保存
    existing_index = None
    for idx, game in enumerate(saved_games):
        if game['player_name'] == player_name and game['selected_character'] == selected_character:
            existing_index = idx
            break
    # 保存 stack 作为 number 列表
    stack_numbers = [tile['number'] for tile in stack]
    # 保存 board_layers 作为 number 列表
    board_layers_data = [
        [
            [tile['number'] if tile else None for tile in row]
            for row in layer
        ]
        for layer in board_layers
    ][:LAYER_COUNT]
    game_data = {
        'player_name': player_name,
        'score': score,
        'level': level,
        'stack': stack_numbers,
        'board_layers': board_layers_data,
        'selected_character': selected_character  # 保存角色选择
    }
    if existing_index is not None:
        saved_games[existing_index] = game_data
    else:
        saved_games.append(game_data)
    
    data['saved_games'] = saved_games
    with open(SAVEGAME_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 显示剧情介绍并可按空格键跳过
def show_story():
    for image_file in story_images:
        try:
            story_image = pygame.image.load(image_file).convert()
            story_image = pygame.transform.scale(story_image, (WIDTH, HEIGHT))
        except pygame.error:
            print(f"无法加载剧情图片: {image_file}")
            pygame.quit()
            sys.exit()
        showing = True
        while showing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        showing = False  # 跳过当前剧情图片
            screen.blit(story_image, (0, 0))
            pygame.display.flip()
            clock.tick(FPS)

# 角色选择功能
def select_character():
    global selected_character
    character_options = []
    for idx, image_dict in enumerate(character_images):
        try:
            character_image = pygame.image.load(image_dict['normal']).convert_alpha()
            character_image = pygame.transform.scale(character_image, (200, 200))
        except pygame.error:
            print(f"无法加载角色图片: {image_dict['normal']}")
            pygame.quit()
            sys.exit()
        rect = character_image.get_rect(center=(WIDTH / (len(character_images)+1) * (idx + 1), HEIGHT / 2))
        character_options.append({'image': character_image, 'rect': rect, 'index': idx})
    
    selecting = True
    while selecting:
        # 使用主菜单背景图片
        screen.blit(menu_background, (0, 0))
        
        # 绘制角色选项
        for char in character_options:
            screen.blit(char['image'], char['rect'])
        
        # 绘制提示文字
        prompt_text = font.render("请选择一个角色", True, BLACK)
        screen.blit(prompt_text, (WIDTH / 2 - prompt_text.get_width() / 2, HEIGHT / 2 - 250))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                for char in character_options:
                    if char['rect'].collidepoint(pos):
                        selected_character = char['index']
                        selecting = False  # 玩家已选择角色
                        break
        clock.tick(FPS)

# 输入角色名功能
def input_character_name():
    global player_name
    input_box = pygame.Rect(WIDTH / 2 - 100, HEIGHT / 2, 200, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    user_text = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            elif event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        if user_text.strip() != '':
                            player_name = user_text.strip()
                            done = True
                    elif event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    else:
                        if len(user_text) < 12:  # 限制角色名长度
                            user_text += event.unicode

        # 使用主菜单背景图片
        screen.blit(menu_background, (0, 0))
        
        # 绘制提示文字
        prompt_text = font.render("请输入角色名:", True, BLACK)
        screen.blit(prompt_text, (WIDTH / 2 - prompt_text.get_width() / 2, HEIGHT / 2 - 60))

        # 绘制输入框
        pygame.draw.rect(screen, color, input_box, 2)
        text_surface = font.render(user_text, True, BLACK)
        screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))

        pygame.display.flip()
        clock.tick(30)


# 启动新游戏
def start_new_game(name):
    global player_name, current_state, score, level, stack
    player_name = name
    score = 0
    level = 1
    stack = []
    create_board()
    current_state = STATE_GAME
    save_game()  # 保存游戏进度

# 创建棋盘
def create_board():
    global board_layers, game_area_rect
    board_layers = []
    
    # 动态调整图案种类数量
    max_tile_kinds = 8  # 最大图案种类数
    tile_kinds = min(6 + level - 1, max_tile_kinds)  # 随着关卡提升增加图案种类
    print(f"第 {level} 关，图案种类数：{tile_kinds}")

    # 动态调整每种图案的数量
    base_tiles_per_kind = 6  # 基础每种图案数量
    tiles_per_kind = base_tiles_per_kind + (level - 1) * 2  # 每关增加2个

    # 确保每种图案的数量是3的倍数
    tiles_per_kind = max(3, tiles_per_kind)  # 确保至少为3
    tiles_per_kind = ((tiles_per_kind + 2) // 3) * 3  # 调整为3的倍数

    # 生成图案序列
    total_tiles = []
    for i in range(1, tile_kinds + 1):
        total_tiles.extend([i] * tiles_per_kind)

    # 计算总的图案数量
    total_tiles_count = len(total_tiles)

    # 检查总的图案数量是否超过可用位置数量
    total_positions = ROWS * COLS * LAYER_COUNT
    if total_tiles_count > total_positions:
        # 需要减少每种图案的数量
        reduction_factor = total_positions / total_tiles_count
        tiles_per_kind = int(tiles_per_kind * reduction_factor) // 3 * 3  # 调整为3的倍数
        tiles_per_kind = max(3, tiles_per_kind)  # 确保至少为3

        # 重新生成图案序列
        total_tiles = []
        for i in range(1, tile_kinds + 1):
            total_tiles.extend([i] * tiles_per_kind)
        total_tiles_count = len(total_tiles)

    # 打乱图案序列
    random.shuffle(total_tiles)

    # 初始化层列表
    for _ in range(LAYER_COUNT):
        board_layers.append([[None for _ in range(COLS)] for _ in range(ROWS)])

    # 定义所有可能的位置
    positions = []
    for layer_num in range(LAYER_COUNT):
        offset = layer_offsets[layer_num]
        for row in range(ROWS):
            for col in range(COLS):
                positions.append({
                    'layer': layer_num,
                    'row': row,
                    'col': col,
                    'offset_x': offset['x'],
                    'offset_y': offset['y']
                })

    # 打乱位置列表
    random.shuffle(positions)

    # 放置图案到棋盘上
    index = 0
    for tile_number in total_tiles:
        if index >= len(positions):
            break  # 没有更多位置了

        pos = positions[index]
        index += 1
        layer = pos['layer']
        row = pos['row']
        col = pos['col']

        if board_layers[layer][row][col] is None:
            # 随机小偏移，增加自然感
            rand_offset_x = random.randint(-TILE_SIZE // 8, TILE_SIZE // 8)
            rand_offset_y = random.randint(-TILE_SIZE // 8, TILE_SIZE // 8)
            tile = {
                'number': tile_number,
                'image': pattern_images[tile_number - 1],
                'rect': pygame.Rect(
                    col * TILE_SIZE + pos['offset_x'] + rand_offset_x + 150,  # 右移，避免遮挡角色
                    row * TILE_SIZE + pos['offset_y'] + rand_offset_y,
                    TILE_SIZE,
                    TILE_SIZE
                ),
                'layer': layer,
                'original_position': None
            }
            board_layers[layer][row][col] = tile

    # 在放置图案后，计算游戏区域的边界
    all_tiles_rects = []
    for layer in board_layers:
        for row in layer:
            for tile in row:
                if tile:
                    all_tiles_rects.append(tile['rect'])
    # 合并所有图案的矩形，得到游戏区域的边界
    if all_tiles_rects:
        game_area_rect = all_tiles_rects[0].copy()
        for rect in all_tiles_rects[1:]:
            game_area_rect.union_ip(rect)
    else:
        game_area_rect = pygame.Rect(0, 0, 0, 0)

# 检查图案是否未被覆盖
def is_tile_uncovered(tile):
    tile_rect = tile['rect']
    tile_layer = tile['layer']
    for higher_layer in board_layers[tile_layer + 1:]:
        for row in higher_layer:
            for other_tile in row:
                if other_tile:
                    other_rect = other_tile['rect']
                    # 判断上层图案的四个角是否在当前图案的范围内
                    for corner in [(other_rect.left, other_rect.top),
                                   (other_rect.right, other_rect.top),
                                   (other_rect.left, other_rect.bottom),
                                   (other_rect.right, other_rect.bottom)]:
                        if tile_rect.collidepoint(corner):
                            return False
    return True

# 绘制背景
def draw_background():
    bg_image_file = background_images[(level - 1) % len(background_images)]
    try:
        bg_image = pygame.image.load(bg_image_file).convert()
        bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
    except pygame.error:
        print(f"无法加载背景图片: {bg_image_file}")
        pygame.quit()
        sys.exit()
    screen.blit(bg_image, (0, 0))

# 绘制棋盘
def draw_board():
    for layer in board_layers:
        for row in layer:
            for tile in row:
                if tile:
                    screen.blit(tile['image'], tile['rect'])
                    # 如果是提示的图案，绘制高亮边框
                    if hint_sequence and tile == hint_sequence[0]:
                        pygame.draw.rect(screen, (255, 0, 0), tile['rect'], 3)

# 绘制栈
def draw_stack():
    global stack_area_rect
    x = WIDTH / 2 - (TILE_SIZE + 5) * MAX_STACK_SIZE / 2
    y = HEIGHT - TILE_SIZE - 150  # 上移，避免遮挡信息
    stack_area_rect = pygame.Rect(x - 10, y - 10, (TILE_SIZE + 5) * MAX_STACK_SIZE + 20, TILE_SIZE + 20)
    pygame.draw.rect(screen, (100, 150, 200), stack_area_rect, 5, border_radius=15)
    for i, tile in enumerate(stack):
        screen.blit(tile['image'], (x + i * (TILE_SIZE + 5), y))

# 绘制角色和信息
def draw_game_elements():
    # 绘制背景
    draw_background()
    # 绘制游戏区域边框
    if game_area_rect:
        pygame.draw.rect(screen, (200, 100, 50), game_area_rect.inflate(20, 20), 5, border_radius=15)
    # 绘制栈区域边框
    if stack_area_rect:
        pygame.draw.rect(screen, (100, 150, 200), stack_area_rect, 5, border_radius=15)
    # 绘制棋盘和栈
    draw_board()
    draw_stack()
    # 绘制角色
    if character_state == 'normal':
        character_image_file = character_images[selected_character]['normal']
    else:
        character_image_file = character_images[selected_character]['happy']
    if not os.path.exists(character_image_file):
        print(f"角色图片不存在: {character_image_file}")
        pygame.quit()
        sys.exit()
    try:
        character_image = pygame.image.load(character_image_file).convert_alpha()
        character_image = pygame.transform.scale(character_image, (150, 150))
    except pygame.error:
        print(f"无法加载角色图片: {character_image_file}")
        pygame.quit()
        sys.exit()
    screen.blit(character_image, (20, HEIGHT - 170))  # 左下角显示角色
    # 绘制分数和关卡信息
    score_text = info_font.render(f"分数: {score}", True, BLACK)
    level_text = info_font.render(f"关卡: {level}", True, BLACK)
    
    # 添加边框背景
    score_rect = score_text.get_rect(topleft=(WIDTH - 220, HEIGHT - 100))
    level_rect = level_text.get_rect(topleft=(WIDTH - 220, HEIGHT - 60))
    
    # 绘制背景框
    pygame.draw.rect(screen, WHITE, score_rect.inflate(10, 10))
    pygame.draw.rect(screen, WHITE, level_rect.inflate(10, 10))
    
    # 绘制边框
    pygame.draw.rect(screen, BLACK, score_rect.inflate(10, 10), 2)
    pygame.draw.rect(screen, BLACK, level_rect.inflate(10, 10), 2)
    
    # 绘制文本
    screen.blit(score_text, (score_rect.left + 5, score_rect.top + 5))
    screen.blit(level_text, (level_rect.left + 5, level_rect.top + 5))
    # 绘制按钮
    # 绘制提示按钮
    if hint_calculating:
        hint_text = font.render("计算中...", True, BUTTON_TEXT_COLOR)
    else:
        hint_text = font.render("提示", True, BUTTON_TEXT_COLOR)
    pygame.draw.rect(screen, HINT_BUTTON_COLOR, hint_button_rect, border_radius=10)
    screen.blit(hint_text, (hint_button_rect.centerx - hint_text.get_width() / 2,
                            hint_button_rect.centery - hint_text.get_height() / 2))
    # 绘制撤销按钮
    undo_text = font.render("撤销", True, BUTTON_TEXT_COLOR)
    pygame.draw.rect(screen, UNDO_BUTTON_COLOR, undo_button_rect, border_radius=10)
    screen.blit(undo_text, (undo_button_rect.centerx - undo_text.get_width() / 2,
                            undo_button_rect.centery - undo_text.get_height() / 2))

# 获取点击位置的图案
def get_tile_at_pos(pos):
    for layer in reversed(board_layers):  # 从顶层开始检测
        for row in layer:
            for tile in row:
                if tile and tile['rect'].collidepoint(pos):
                    return tile
    return None

# 移除图案
def remove_tile(tile):
    for layer in board_layers:
        for row in layer:
            for i in range(len(row)):
                if row[i] == tile:
                    row[i] = None
                    return

# 处理点击事件
def handle_click(pos):
    global hint_sequence
    tile = get_tile_at_pos(pos)
    if tile:
        # 检查图案是否被覆盖
        if is_tile_uncovered(tile):
            # 检查玩家是否点击了提示的图案
            if hint_sequence and tile == hint_sequence[0]:
                hint_sequence.pop(0)  # 移除已提示的图案
                if not hint_sequence:
                    hint_sequence = []  # 提示序列已用完
            else:
                hint_sequence = []  # 玩家未点击提示的图案，清空提示序列

            # 记录原始位置
            tile['original_position'] = {'layer': tile['layer'], 'row': None, 'col': None}
            # 找到该 tile 在 board_layers 中的位置
            for row_idx, row in enumerate(board_layers[tile['layer']]):
                for col_idx, t in enumerate(row):
                    if t == tile:
                        tile['original_position']['row'] = row_idx
                        tile['original_position']['col'] = col_idx
                        break
            stack.append(tile)
            remove_tile(tile)

            if len(stack) > MAX_STACK_SIZE:
                game_over("栈已满，游戏失败！")
            else:
                if len(stack) >= 3:
                    check_match()
                # 检查游戏状态
                if is_game_won():
                    if level >= MAX_LEVEL:
                        game_win("恭喜您完成所有关卡，游戏胜利！")
                    else:
                        next_level()
                elif is_game_over():
                    game_over("无法继续，游戏失败！")
        else:
            pass  # 图案被覆盖，无法点击

# 检查匹配
def check_match():
    global stack, score, character_state, character_reaction_time, hint_sequence
    changed = True
    while changed and len(stack) >= 3:
        changed = False
        counts = {}
        for tile in stack:
            counts[tile['number']] = counts.get(tile['number'], 0) + 1
        for number, count in counts.items():
            while count >= 3:
                # 移除三个相同的图案
                remove_count = 0
                i = len(stack) - 1
                while i >= 0 and remove_count < 3:
                    if stack[i]['number'] == number:
                        del stack[i]
                        remove_count += 1
                        count -= 1
                    i -= 1
                score += 100
                # 角色互动动画
                character_state = 'happy'
                character_reaction_time = int(FPS * 1)  # 互动状态持续1秒
                # 清空提示序列
                hint_sequence = []
                changed = True
                break  # 重新检查
        if changed:
            continue
        else:
            break

# 判断游戏是否胜利
def is_game_won():
    # 如果棋盘上没有任何图案，且栈为空，游戏胜利
    for layer in board_layers:
        for row in layer:
            for tile in row:
                if tile:
                    return False
    if len(stack) == 0:
        return True
    else:
        return False

# 判断游戏是否失败
def is_game_over():
    # 如果棋盘上没有图案，但栈中有剩余图案无法匹配，游戏失败
    for layer in board_layers:
        for row in layer:
            for tile in row:
                if tile:
                    return False  # 仍有图案，游戏未结束
    if len(stack) > 0:
        # 检查栈中的图案能否再匹配
        counts = {}
        for tile in stack:
            counts[tile['number']] = counts.get(tile['number'], 0) + 1
        for count in counts.values():
            if count >= 3:
                return False  # 仍有可能匹配
        return True  # 无法匹配，游戏失败
    return False

# 进入下一关
def next_level():
    global level, stack, hint_sequence
    level += 1
    if level > MAX_LEVEL:
        game_win("恭喜您完成所有关卡，游戏胜利！")
    else:
        stack = []  # 重置栈
        hint_sequence = []
        create_board()
        save_game()  # 保存游戏进度

# 游戏结束
def game_over(message):
    global leaderboard, current_state
    screen.fill(BG_COLOR)
    message_text = big_font.render(message, True, (178, 34, 34))  # Firebrick
    rect = message_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 50))
    screen.blit(message_text, rect)

    # 记录分数到排行榜
    leaderboard.append({'name': player_name, 'score': score})
    save_leaderboard()

    # 显示返回主菜单的提示
    return_text = font.render("返回主菜单...", True, BLACK)
    return_rect = return_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 50))
    screen.blit(return_text, return_rect)

    pygame.display.flip()
    pygame.time.delay(3000)
    current_state = STATE_MAIN_MENU
    save_game()  # 保存游戏进度

# 游戏胜利
def game_win(message):
    global leaderboard, current_state

    # 绘制胜利界面背景图片
    screen.blit(victory_background, (0, 0))

    # 绘制胜利消息
    message_text = big_font.render(message, True, (34, 139, 34))  # Forest Green
    rect = message_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 50))
    screen.blit(message_text, rect)

    # 记录分数到排行榜
    leaderboard.append({'name': player_name, 'score': score})
    save_leaderboard()

    # 显示返回主菜单的提示
    return_text = font.render("返回主菜单...", True, BLACK)
    return_rect = return_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 50))
    screen.blit(return_text, return_rect)

    pygame.display.flip()
    pygame.time.delay(3000)
    current_state = STATE_MAIN_MENU
    save_game()  # 保存游戏进度


# 提示功能
def show_hint():
    global hint_sequence, hint_calculating
    if hint_calculating:
        return  # 已经在计算中，避免重复计算
    hint_sequence = []
    hint_calculating = True
    threading.Thread(target=calculate_hint).start()

def calculate_hint():
    global hint_sequence, hint_calculating
    hint_sequence = []
    print("Calculating hint...")
    # 首先使用贪心算法寻找直接可消除的三个图案
    hint_sequence = find_greedy_hint()
    if not hint_sequence:
        # 如果找不到，使用 DFS 算法计算提示
        root_state = (stack.copy(), copy_board_layers(board_layers))
        hint_sequence = find_hint_sequence(root_state)
    hint_calculating = False
    if hint_sequence:
        print("Hint sequence generated:")
        for tile in hint_sequence:
            print(f"Number: {tile['number']}")
    else:
        print("无法找到可行的提示序列")

def find_greedy_hint():
    available_tiles = get_all_uncovered_tiles(board_layers)
    if not available_tiles:
        return []
    # 统计可点击图案中每种图案的数量
    tile_counts = {}
    for tile in available_tiles:
        tile_counts[tile['number']] = tile_counts.get(tile['number'], 0) + 1

    # 查找数量达到 3 的图案
    for number, count in tile_counts.items():
        if count >= 3:
            matching_tiles = [tile for tile in available_tiles if tile['number'] == number]
            return matching_tiles[:3]  # 返回可以直接消除的三个图案

    return []

def find_hint_sequence(root_state):
    max_depth = MAX_STACK_SIZE - len(stack)
    time_limit = 1.0  # 秒
    start_time = time.time()
    _, board_layers_param = root_state
    available_tiles = get_all_uncovered_tiles(board_layers_param)
    if not available_tiles or max_depth <= 0:
        return []

    # 启发式排序
    tile_counts = {}
    for tile in available_tiles:
        tile_counts[tile['number']] = tile_counts.get(tile['number'], 0) + 1

    unmatched_numbers_in_stack = [tile['number'] for tile in stack]
    def tile_priority(tile):
        priority = 0
        if tile['number'] in unmatched_numbers_in_stack:
            priority += 100
        priority += tile_counts[tile['number']]
        return -priority  # 负号使得数值越大优先级越高

    available_tiles.sort(key=tile_priority)

    # 迭代加深搜索
    for depth in range(1, max_depth + 1):
        visited_states = set()
        success, result = dfs_search(root_state, [], depth, start_time, time_limit, visited_states, root_state)
        if success:
            return result
    return []

def dfs_search(state, path, max_depth, start_time, time_limit, visited_states, root_state):
    # 检查时间限制
    if time.time() - start_time > time_limit:
        return False, []
    # 检查深度限制
    if len(path) >= max_depth:
        return False, []
    stack_param, board_layers_param = state
    # 检查是否发生了消除
    if len(stack_param) < len(root_state[0]):
        return True, path
    # 序列化状态
    state_key = serialize_state(state)
    if state_key in visited_states:
        return False, []
    visited_states.add(state_key)
    if len(stack_param) >= MAX_STACK_SIZE:
        return False, []
    # 获取可点击的图案
    available_tiles = get_all_uncovered_tiles(board_layers_param)
    if not available_tiles:
        return False, []
    for tile in available_tiles:
        new_path = path + [tile]
        new_stack = stack_param.copy()
        new_board_layers = copy_board_layers(board_layers_param)
        new_stack.append(tile)
        remove_tile_in_layers(new_board_layers, tile)
        if len(new_stack) > MAX_STACK_SIZE:
            continue  # 栈溢出，剪枝
        new_stack, eliminated = simulate_check_match_in_stack(new_stack)
        new_state = (new_stack, new_board_layers)
        success, result = dfs_search(new_state, new_path, max_depth, start_time, time_limit, visited_states, root_state)
        if success:
            return True, result
    return False, []

def simulate_check_match_in_stack(stack_param):
    new_stack = stack_param.copy()
    eliminated = False
    changed = True
    while changed and len(new_stack) >= 3:
        changed = False
        counts = {}
        for tile in new_stack:
            counts[tile['number']] = counts.get(tile['number'], 0) + 1
        for number, count in counts.items():
            if count >= 3:
                # 找到三个相同的图案，移除它们
                remove_indices = [i for i, tile in enumerate(new_stack) if tile['number'] == number][-3:]
                for index in sorted(remove_indices, reverse=True):
                    del new_stack[index]
                eliminated = True
                changed = True
                break  # 重新检查
    return new_stack, eliminated

def get_all_uncovered_tiles(board_layers_param):
    tiles = []
    for layer in board_layers_param:
        for row in layer:
            for tile in row:
                if tile and is_tile_uncovered(tile):
                    tiles.append(tile)
    return tiles

def copy_board_layers(board_layers_original):
    # 创建一个新的棋盘层数据，保持对原始图案对象的引用
    new_board_layers = []
    for layer in board_layers_original:
        new_layer = []
        for row in layer:
            new_row = row.copy()  # 浅拷贝行
            new_layer.append(new_row)
        new_board_layers.append(new_layer)
    return new_board_layers

def serialize_state(state):
    stack_param, board_layers_param = state
    stack_state = tuple(sorted([tile['number'] for tile in stack_param]))
    # 对于 board_layers，只需要序列化图案的存在性和编号
    board_state = tuple(
        tuple(
            tuple(tile['number'] if tile else None for tile in row)
            for row in layer
        )
        for layer in board_layers_param
    )
    return (stack_state, board_state)

def remove_tile_in_layers(board_layers_param, tile_to_remove):
    for layer in board_layers_param:
        for row in layer:
            for idx, tile in enumerate(row):
                if tile and tile['number'] == tile_to_remove['number'] and tile == tile_to_remove:
                    row[idx] = None  # 不修改 tile 对象
                    return

# 撤销功能
def undo_move():
    global hint_sequence
    if not stack:
        return  # 栈为空，无法撤销
    tile = stack.pop()
    pos = tile.get('original_position', None)
    if pos:
        # 将图案放回原来的位置
        layer = pos['layer']
        row = pos['row']
        col = pos['col']
        if board_layers[layer][row][col] is None:
            board_layers[layer][row][col] = tile
            # 清除 tile 的原始位置
            tile['original_position'] = None
        else:
            print("无法撤销，此位置已被占用。")
    else:
        print("无法撤销此图案，没有原始位置记录")

    # 撤销操作后，清空提示序列
    hint_sequence = []
    save_game()  # 保存游戏进度

# 绘制主菜单界面
def draw_main_menu():
    screen.fill(BG_COLOR)

    # 绘制标题
    title_text = title_font.render("投喂精灵小游戏", True, BLACK)
    screen.blit(title_text, (WIDTH / 2 - title_text.get_width() / 2, HEIGHT / 2 - 300))

    # 绘制按钮
    for button in [start_game_button, continue_game_button, leaderboard_button, quit_game_button]:
        pygame.draw.rect(screen, BUTTON_COLOR, button, border_radius=10)

    # 绘制按钮文字
    buttons_text = ["开始游戏", "继续游戏", "排行榜", "退出游戏"]
    for i, button in enumerate([start_game_button, continue_game_button, leaderboard_button, quit_game_button]):
        text = font.render(buttons_text[i], True, BUTTON_TEXT_COLOR)
        screen.blit(text, (button.centerx - text.get_width() / 2,
                           button.centery - text.get_height() / 2))

# 处理主菜单按钮点击
def handle_main_menu_click(pos):
    global current_state
    if start_game_button.collidepoint(pos):
        current_state = STATE_CHARACTER_SELECTION
    elif continue_game_button.collidepoint(pos):
        if os.path.exists(SAVEGAME_FILE):
            if load_game():
                current_state = STATE_CONTINUE_GAME_SELECTION  # 进入选择继续游戏的界面
            else:
                show_no_continue_game_message()
        else:
            show_no_continue_game_message()
    elif leaderboard_button.collidepoint(pos):
        current_state = STATE_LEADERBOARD
    elif quit_game_button.collidepoint(pos):
        pygame.quit()
        sys.exit()

# 提示排行榜为空时的信息
def show_no_continue_game_message():
    screen.fill(BG_COLOR)
    message = "暂无可继续的游戏，请先开始新游戏。"
    message_text = font.render(message, True, BLACK)
    rect = message_text.get_rect(center=(WIDTH / 2, HEIGHT / 2))
    screen.blit(message_text, rect)
    pygame.display.flip()
    pygame.time.delay(2000)
    # 返回主菜单
    global current_state
    current_state = STATE_MAIN_MENU

def draw_main_menu():
    # 绘制主菜单背景图片
    screen.blit(menu_background, (0, 0))

    # 绘制标题
    title_text = title_font.render("投喂精灵小游戏", True, BLACK)
    screen.blit(title_text, (WIDTH / 2 - title_text.get_width() / 2, HEIGHT / 2 - 300))

    # 绘制按钮
    for button in [start_game_button, continue_game_button, leaderboard_button, quit_game_button]:
        pygame.draw.rect(screen, BUTTON_COLOR, button, border_radius=10)

    # 绘制按钮文字
    buttons_text = ["开始游戏", "继续游戏", "排行榜", "退出游戏"]
    for i, button in enumerate([start_game_button, continue_game_button, leaderboard_button, quit_game_button]):
        text = font.render(buttons_text[i], True, BUTTON_TEXT_COLOR)
        screen.blit(text, (button.centerx - text.get_width() / 2,
                           button.centery - text.get_height() / 2))


# 继续游戏界面绘制
def draw_continue_game_selection():
    screen.fill(BG_COLOR)
    # 绘制标题
    title_text = big_font.render("选择要继续的游戏", True, BLACK)
    screen.blit(title_text, (WIDTH / 2 - title_text.get_width() / 2, 50))

    # 加载所有保存的游戏
    if os.path.exists(SAVEGAME_FILE):
        try:
            with open(SAVEGAME_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                saved_games = data.get('saved_games', [])
                if not saved_games:
                    raise ValueError("没有可继续的游戏。")
                # 显示每个保存的游戏
                for idx, game in enumerate(saved_games):
                    name = game.get('player_name', '未知')
                    score_val = game.get('score', 0)
                    level_val = game.get('level', 1)
                    selected_char = game.get('selected_character', 0)
                    entry_text = font.render(f"{idx + 1}. {name} - 分数: {score_val} - 关卡: {level_val}", True, BLACK)
                    entry_rect = pygame.Rect(WIDTH / 2 - 200, 150 + idx * 60, 400, 50)
                    pygame.draw.rect(screen, BUTTON_COLOR, entry_rect, border_radius=10)
                    screen.blit(entry_text, (entry_rect.centerx - entry_text.get_width() / 2,
                                             entry_rect.centery - entry_text.get_height() / 2))
            # 显示返回提示
            return_text = font.render("按 ESC 返回主菜单", True, BLACK)
            screen.blit(return_text, (WIDTH / 2 - return_text.get_width() / 2, HEIGHT - 100))
        except (json.JSONDecodeError, KeyError, ValueError):
            message = "暂无可继续的游戏，请先开始新游戏。"
            message_text = font.render(message, True, BLACK)
            rect = message_text.get_rect(center=(WIDTH / 2, HEIGHT / 2))
            screen.blit(message_text, rect)
    else:
        message = "暂无可继续的游戏，请先开始新游戏。"
        message_text = font.render(message, True, BLACK)
        rect = message_text.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        screen.blit(message_text, rect)

    pygame.display.flip()

# 处理继续游戏选择点击
def handle_continue_game_selection_click(pos):
    global current_state
    if os.path.exists(SAVEGAME_FILE):
        try:
            with open(SAVEGAME_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                saved_games = data.get('saved_games', [])
                if not saved_games:
                    show_no_continue_game_message()
                    return
                # 每个保存的游戏占用一个区域，假设每个区域高度为60，起始y为150
                for idx, game in enumerate(saved_games):
                    entry_rect = pygame.Rect(WIDTH / 2 - 200, 150 + idx * 60, 400, 50)
                    if entry_rect.collidepoint(pos):
                        if load_specific_game(idx):
                            current_state = STATE_GAME
                        else:
                            show_no_continue_game_message()
                        return
        except (json.JSONDecodeError, KeyError, ValueError):
            show_no_continue_game_message()
    else:
        show_no_continue_game_message()

# 主游戏循环
def main_loop():
    global character_state, character_reaction_time, current_state

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if current_state == STATE_MAIN_MENU:
                    handle_main_menu_click(pos)
                elif current_state == STATE_LEADERBOARD:
                    pass  # 目前无交互
                elif current_state == STATE_CONTINUE_GAME_SELECTION:
                    handle_continue_game_selection_click(pos)
                elif current_state == STATE_CHARACTER_SELECTION:
                    select_character()  # 直接调用角色选择函数
                    # 角色选择完成后，进入名字输入界面
                    current_state = STATE_NAME_INPUT
                elif current_state == STATE_NAME_INPUT:
                    pass  # 处理名字输入已集成到状态转换
                elif current_state == STATE_GAME:
                    if hint_button_rect.collidepoint(pos):
                        show_hint()
                    elif undo_button_rect.collidepoint(pos):
                        undo_move()
                    else:
                        handle_click(pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_state in [STATE_LEADERBOARD, STATE_CONTINUE_GAME_SELECTION, STATE_CHARACTER_SELECTION, STATE_NAME_INPUT]:
                        current_state = STATE_MAIN_MENU
                    elif current_state == STATE_GAME:
                        # 确认退出游戏
                        confirm_quit_game()

        # 更新角色状态计时器
        if current_state == STATE_GAME:
            if character_state == 'happy':
                character_reaction_time -= 1
                if character_reaction_time <= 0:
                    character_state = 'normal'
            save_game()  # 定期保存游戏进度

        # 根据当前状态绘制相应界面
        if current_state == STATE_MAIN_MENU:
            draw_main_menu()
        elif current_state == STATE_GAME:
            draw_game_elements()
            handle_animations()
        elif current_state == STATE_LEADERBOARD:
            draw_leaderboard()
        elif current_state == STATE_CONTINUE_GAME_SELECTION:
            draw_continue_game_selection()
        elif current_state == STATE_CHARACTER_SELECTION:
            pass  # 已在选择点击中处理
        elif current_state == STATE_NAME_INPUT:
            input_character_name()
            # 启动新游戏后，进入游戏状态
            start_new_game(player_name)
        elif current_state == STATE_GAME_OVER:
            pass  # 已在 game_over 函数中处理
        elif current_state == STATE_GAME_WIN:
            pass  # 已在 game_win 函数中处理

        pygame.display.flip()

    pygame.quit()

# 确认退出游戏
def confirm_quit_game():
    confirm_box = pygame.Rect(WIDTH / 2 - 200, HEIGHT / 2 - 75, 400, 150)
    yes_button = pygame.Rect(WIDTH / 2 - 170, HEIGHT / 2 - 25, 100, 40)
    no_button = pygame.Rect(WIDTH / 2 + 70, HEIGHT / 2 - 25, 100, 40)
    save_button = pygame.Rect(WIDTH / 2 - 35, HEIGHT / 2 + 30, 70, 40)
    selecting = True
    while selecting:
        # 使用主菜单背景图片
        screen.blit(menu_background, (0, 0))
        
        pygame.draw.rect(screen, BUTTON_COLOR, confirm_box, border_radius=10)
        confirm_text = font.render("确定退出游戏吗？", True, BLACK)
        screen.blit(confirm_text, (confirm_box.centerx - confirm_text.get_width() / 2,
                                   confirm_box.centery - confirm_text.get_height() / 2 - 30))
        pygame.draw.rect(screen, (34, 139, 34), yes_button, border_radius=5)  # Forest Green
        pygame.draw.rect(screen, (178, 34, 34), no_button, border_radius=5)   # Firebrick
        pygame.draw.rect(screen, (255, 215, 0), save_button, border_radius=5) # Gold for save
        
        yes_text = font.render("是", True, WHITE)
        no_text = font.render("否", True, WHITE)
        save_text = font.render("保存并退出", True, BLACK)
        
        screen.blit(yes_text, (yes_button.centerx - yes_text.get_width() / 2,
                               yes_button.centery - yes_text.get_height() / 2))
        screen.blit(no_text, (no_button.centerx - no_text.get_width() / 2,
                              no_button.centery - no_text.get_height() / 2))
        screen.blit(save_text, (save_button.centerx - save_text.get_width() / 2,
                                save_button.centery - save_text.get_height() / 2))
        
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if yes_button.collidepoint(pos):
                    save_game()  # 自动保存
                    pygame.quit()
                    sys.exit()
                elif no_button.collidepoint(pos):
                    selecting = False
                elif save_button.collidepoint(pos):
                    save_game()
                    pygame.quit()
                    sys.exit()
        clock.tick(FPS)

# 绘制和处理动画效果
def handle_animations():
    global character_state, character_reaction_time
    if character_state == 'happy':
        # 这里可以添加更多动画效果，如角色表情变化、闪烁等
        pass

# 保存排行榜时确保保存多个分数
def add_to_leaderboard(name, score_val):
    global leaderboard
    leaderboard.append({'name': name, 'score': score_val})
    save_leaderboard()

# 主函数入口
def prepare_game():
    load_leaderboard()
    show_story()          # 显示剧情介绍
    # 角色选择和名字输入现在在主菜单点击“开始游戏”后进行
    # create_board()        # 创建棋盘现在在 start_new_game 中进行

# 启动游戏
if __name__ == "__main__":
    prepare_game()
    main_loop()
