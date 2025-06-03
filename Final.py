
import pygame
import random
import sys
from collections import deque
import asyncio


INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT = 400, 400
INFO_PANEL_HEIGHT = 70
MAX_LIVES = 1 
MIN_MAZE_SIZE = 15  
MAX_MAZE_SIZE = 35  
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0) 
YELLOW = (255, 255, 0) 
PATH_COLOR = (230, 230, 250) 
VISITED_COLOR = (150, 150, 150) 
# --- Movement Directions ---
DIRECTIONS = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}

# --- Maze Class ---
class Maze:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        if self.cols % 2 == 0: self.cols += 1
        if self.rows % 2 == 0: self.rows += 1
        self.grid = [[{'N': True, 'S': True, 'E': True, 'W': True} for _ in range(self.cols)] for _ in range(self.rows)]
        self.visited = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self._generate_maze()

    def _generate_maze(self):
        self.visited = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        stack = [(0, 0)]  # Start generation from top-left
        self.visited[0][0] = True
        while stack:
            x, y = stack[-1]
            neighbors = []
            for direction, (dx, dy) in DIRECTIONS.items():
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and not self.visited[ny][nx]:
                    neighbors.append((nx, ny, direction))

            if neighbors:
                nx, ny, direction = random.choice(neighbors)
                current_cell_walls = self.grid[y][x]
                neighbor_cell_walls = self.grid[ny][nx]
                if direction == 'N': current_cell_walls['N'], neighbor_cell_walls['S'] = False, False
                elif direction == 'S': current_cell_walls['S'], neighbor_cell_walls['N'] = False, False
                elif direction == 'E': current_cell_walls['E'], neighbor_cell_walls['W'] = False, False
                elif direction == 'W': current_cell_walls['W'], neighbor_cell_walls['E'] = False, False

                self.visited[ny][nx] = True
                stack.append((nx, ny)) # Move to the neighbor
            else:
                stack.pop() # Backtrack if no unvisited neighbors

    def is_wall(self, x, y, direction_key):
        if 0 <= y < self.rows and 0 <= x < self.cols:
            if direction_key in self.grid[y][x]:
                return self.grid[y][x][direction_key]
        return True 

    def draw(self, screen, cell_w, cell_h, visited_cells=None, path=None):
        screen.fill(PATH_COLOR) 
        # Highlight visited cells during BFS (light gray)
        if visited_cells:
            for (x, y) in visited_cells:
                if not path or (x, y) not in path:
                    pygame.draw.rect(screen, VISITED_COLOR, (x * cell_w, y * cell_h, cell_w, cell_h))
        if path:
            for (x, y) in path:
                pygame.draw.rect(screen, YELLOW, (x * cell_w, y * cell_h, cell_w, cell_h))
        for y in range(self.rows):
            for x in range(self.cols):
                cell_walls = self.grid[y][x]
                px, py = x * cell_w, y * cell_h # Top-left pixel coordinates of the cell
                if cell_walls['N']: pygame.draw.line(screen, BLACK, (px, py), (px + cell_w, py), 2)
                if cell_walls['S']: pygame.draw.line(screen, BLACK, (px, py + cell_h), (px + cell_w, py + cell_h), 2)
                if cell_walls['W']: pygame.draw.line(screen, BLACK, (px, py), (px, py + cell_h), 2)
                if cell_walls['E']: pygame.draw.line(screen, BLACK, (px + cell_w, py), (px + cell_w, py + cell_h), 2)
class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.Font(None, 30)
        self.info_font = pygame.font.Font(None, 24)
        self.level = 0 
        self.lives = MAX_LIVES 
        asyncio.run(self.setup_level()) 
        pygame.display.set_caption("Maze Game")

    async def setup_level(self):
        self.cols = random.randint(MIN_MAZE_SIZE, MAX_MAZE_SIZE)
        self.rows = random.randint(MIN_MAZE_SIZE, MAX_MAZE_SIZE)
        if self.rows % 2 == 0: self.rows += 1
        if self.cols % 2 == 0: self.cols += 1
        base_cell_size = INITIAL_SCREEN_WIDTH // 20
        self.screen_width = self.cols * base_cell_size
        self.screen_height = self.rows * base_cell_size
        self.total_height = self.screen_height + INFO_PANEL_HEIGHT
        self.cell_width = self.screen_width // self.cols
        self.cell_height = self.screen_height // self.rows
        self.screen = pygame.display.set_mode((self.screen_width, self.total_height))
        self.maze = Maze(self.cols, self.rows)
        self.start_pos = (0, 0) # Top-left corner
        self.goal_pos = (self.cols - 1, self.rows - 1) 
        self.player_pos = self.start_pos 
        self.message = f"Level {self.level + 1}"
      
    async def compute_correct_path(self):
    
        queue = deque([(self.start_pos, [self.start_pos])]) # Queue stores (position, path_so_far)
        visited = {self.start_pos} # Keep track of visited cells to avoid cycles

        while queue:
            (x, y), path = queue.popleft()

            if (x, y) == self.goal_pos:
                return path 
            for direction_key, (dx, dy) in DIRECTIONS.items():
                if not self.maze.is_wall(x, y, direction_key): 
                    nx, ny = x + dx, y + dy
                    # Check if neighbor is valid and not visited
                    if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_path = path + [(nx, ny)] # Extend the path
                        queue.append(((nx, ny), new_path))
        return None 

    def draw_message_box(self, message, options):
        box_width, box_height = 350, 180
        box_x = (self.screen_width - box_width) // 2
        box_y = (self.screen_height - box_height) // 2 
        pygame.draw.rect(self.screen, GRAY, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, BLACK, (box_x, box_y, box_width, box_height), 2)
        lines = message.split('\n') # Allow multi-line messages
        line_y = box_y + 30
        for line in lines:
            text = self.font.render(line, True, BLACK)
            text_rect = text.get_rect(center=(self.screen_width // 2, line_y))
            self.screen.blit(text, text_rect)
            line_y += 35
        buttons = []
        num_options = len(options)
        button_total_width = num_options * 100 + (num_options - 1) * 20 
        start_x = box_x + (box_width - button_total_width) // 2
        for i, option in enumerate(options):
            btn_width, btn_height = 100, 40
            btn_x = start_x + i * (btn_width + 20) 
            btn_y = box_y + box_height - btn_height - 25 
            pygame.draw.rect(self.screen, WHITE, (btn_x, btn_y, btn_width, btn_height))
            pygame.draw.rect(self.screen, BLACK, (btn_x, btn_y, btn_width, btn_height), 1)
            btn_text = self.font.render(option, True, BLACK)
            btn_text_rect = btn_text.get_rect(center=(btn_x + btn_width // 2, btn_y + btn_height // 2))
            self.screen.blit(btn_text, btn_text_rect)
            buttons.append((pygame.Rect(btn_x, btn_y, btn_width, btn_height), option))

        pygame.display.flip() 
        return buttons 

    async def show_final_message(self, message, options=["Exit"]):
        self.screen.fill(PATH_COLOR) # Use PATH_COLOR
        self.maze.draw(self.screen, self.cell_width, self.cell_height)
        pygame.draw.rect(self.screen, BLUE, (self.player_pos[0] * self.cell_width, self.player_pos[1] * self.cell_height, self.cell_width, self.cell_height))
        pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
        self.message = message # Set the message to be displayed
        self._draw_info_panel()
        buttons = self.draw_message_box(message, options)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                     if event.key == pygame.K_ESCAPE: 
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for btn_rect, option in buttons:
                        if btn_rect.collidepoint(event.pos):
                            if option == "Exit":
                                pygame.quit()
                                sys.exit()
            await asyncio.sleep(0.016)

    async def start_menu(self):
        self.screen.fill(BLACK) # Black background for menu
        buttons = self.draw_message_box("Choose an option:", ["Play", "Solution"])
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for btn_rect, option in buttons:
                        if btn_rect.collidepoint(event.pos):
                            return option 
            await asyncio.sleep(0.016)
    async def bfs(self):
        queue = deque([(self.start_pos, [self.start_pos])])
        visited = {self.start_pos}
        clock = pygame.time.Clock() # Use clock for potential FPS limiting if needed

        while queue:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            (x, y), path = queue.popleft()

            self.screen.fill(PATH_COLOR) 
            self.maze.draw(self.screen, self.cell_width, self.cell_height, visited_cells=visited, path=path)
            pygame.draw.rect(self.screen, BLUE, (self.start_pos[0] * self.cell_width, self.start_pos[1] * self.cell_height, self.cell_width, self.cell_height))
            pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
            # Draw the info panel (shows "Level X | Lives: Y" or status)
            self.message = "Finding solution..."
            self._draw_info_panel()
            pygame.display.flip() 
            if (x, y) == self.goal_pos:
                self.message = "Path found!" 
                self.screen.fill(PATH_COLOR)
                self.maze.draw(self.screen, self.cell_width, self.cell_height, path=path)
                pygame.draw.rect(self.screen, BLUE, (self.start_pos[0] * self.cell_width, self.start_pos[1] * self.cell_height, self.cell_width, self.cell_height))
                pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
                self._draw_info_panel()
                pygame.display.flip()
                return path 
            for direction_key, (dx, dy) in DIRECTIONS.items():
                if not self.maze.is_wall(x, y, direction_key):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_path = path + [(nx, ny)]
                        queue.append(((nx, ny), new_path))
            await asyncio.sleep(0.01) 

        self.message = "No path found!" 
        self._draw_info_panel() 
        pygame.display.flip()
        return None

    async def play_mode(self):
        clock = pygame.time.Clock()
        self.player_pos = self.start_pos 
        self.message = f"Level {self.level + 1} - Find the exit!" 
        while True:
            moved = False 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    new_pos = list(self.player_pos) 
                    direction = None 
                    if event.key == pygame.K_UP and not self.maze.is_wall(*self.player_pos, 'N'):
                        new_pos[1] -= 1
                        direction = 'N'
                    elif event.key == pygame.K_DOWN and not self.maze.is_wall(*self.player_pos, 'S'):
                        new_pos[1] += 1
                        direction = 'S'
                    elif event.key == pygame.K_LEFT and not self.maze.is_wall(*self.player_pos, 'W'):
                        new_pos[0] -= 1
                        direction = 'W'
                    elif event.key == pygame.K_RIGHT and not self.maze.is_wall(*self.player_pos, 'E'):
                        new_pos[0] += 1
                        direction = 'E'
                    new_pos = tuple(new_pos) # Convert back to tuple
                    if direction is not None:
                        if 0 <= new_pos[0] < self.cols and 0 <= new_pos[1] < self.rows:
                           self.player_pos = new_pos
                           moved = True
            if moved:
                if self.player_pos == self.goal_pos:
                    return True 
            self.screen.fill(PATH_COLOR) 
            self.maze.draw(self.screen, self.cell_width, self.cell_height) 
            pygame.draw.rect(self.screen, BLUE, (self.player_pos[0] * self.cell_width, self.player_pos[1] * self.cell_height, self.cell_width, self.cell_height))
            pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
            self._draw_info_panel()
            pygame.display.flip()
            await asyncio.sleep(1.0 / 60) 
    def _draw_info_panel(self):
        info_rect = pygame.Rect(0, self.screen_height, self.screen_width, INFO_PANEL_HEIGHT)
        pygame.draw.rect(self.screen, GRAY, info_rect) 
        pygame.draw.line(self.screen, BLACK, (0, self.screen_height), (self.screen_width, self.screen_height), 2)
        msg_surface = self.font.render(self.message, True, BLACK)
        msg_rect = msg_surface.get_rect(center=(self.screen_width // 2, self.screen_height + INFO_PANEL_HEIGHT // 2))
        self.screen.blit(msg_surface, msg_rect)
    async def run(self):
        while True:
            await self.setup_level() 
            choice = await self.start_menu()
            if choice == "Solution":
                path = await self.bfs()
                self.message = "Solution shown. Press ESC to exit or SPACE for next level." 
                solution_loop_active = True
                while solution_loop_active:
                    self.screen.fill(PATH_COLOR) 
                    self.maze.draw(self.screen, self.cell_width, self.cell_height, path=path if path else [])
                    pygame.draw.rect(self.screen, BLUE, (self.start_pos[0] * self.cell_width, self.start_pos[1] * self.cell_height, self.cell_width, self.cell_height))
                    pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
                    self._draw_info_panel()
                    pygame.display.flip()
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                pygame.quit()
                                sys.exit()
                            elif event.key == pygame.K_SPACE:
                                self.level += 1
                                await self.setup_level() 
                                path = await self.bfs() 
                                self.message = "Solution shown. Press ESC to exit or SPACE for next level." 

                   
                    await asyncio.sleep(1.0 / 60) 

            elif choice == "Play":
                won = await self.play_mode() 

                if won:
                    await self.show_final_message("You Won!", options=["Exit"])
                else:
                     await self.show_final_message("Game Over!", options=["Exit"])

if __name__ == "__main__":
    try:
        game = Game()
        asyncio.run(game.run())
    except Exception as e:
        print(f"An error occurred: {e}")
        pygame.quit()
        sys.exit()
    finally:
         pygame.quit() 
