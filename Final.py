
import pygame
import random
import sys
from collections import deque
import asyncio

# --- General Settings ---
INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT = 400, 400
INFO_PANEL_HEIGHT = 70
MAX_LIVES = 1 # تم تغيير عدد المحاولات إلى 1 (مهم لجزء اللعب)
MIN_MAZE_SIZE = 15  # أقل حجم للمتاهة
MAX_MAZE_SIZE = 35  # أكبر حجم للمتاهة

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0) # Used for background in some older draws, less used now
YELLOW = (255, 255, 0) # Color for the correct path
PATH_COLOR = (230, 230, 250) # Background color for the maze area
VISITED_COLOR = (150, 150, 150) # Color for visited cells during BFS visualization

# --- Movement Directions ---
DIRECTIONS = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}

# --- Maze Class ---
class Maze:
    # (الكود الخاص بفئة Maze لم يتغير وهو مطابق للكود الأصلي)
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        # Ensure odd dimensions for maze generation algorithm
        if self.cols % 2 == 0: self.cols += 1
        if self.rows % 2 == 0: self.rows += 1
        self.grid = [[{'N': True, 'S': True, 'E': True, 'W': True} for _ in range(self.cols)] for _ in range(self.rows)]
        self.visited = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self._generate_maze()

    def _generate_maze(self):
        # Recursive backtracker algorithm for maze generation
        self.visited = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        stack = [(0, 0)]  # Start generation from top-left
        self.visited[0][0] = True
        while stack:
            x, y = stack[-1]
            neighbors = []
            # Check adjacent cells
            for direction, (dx, dy) in DIRECTIONS.items():
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and not self.visited[ny][nx]:
                    neighbors.append((nx, ny, direction))

            if neighbors:
                # Choose a random neighbor
                nx, ny, direction = random.choice(neighbors)
                current_cell_walls = self.grid[y][x]
                neighbor_cell_walls = self.grid[ny][nx]

                # Knock down the wall between current cell and neighbor
                if direction == 'N': current_cell_walls['N'], neighbor_cell_walls['S'] = False, False
                elif direction == 'S': current_cell_walls['S'], neighbor_cell_walls['N'] = False, False
                elif direction == 'E': current_cell_walls['E'], neighbor_cell_walls['W'] = False, False
                elif direction == 'W': current_cell_walls['W'], neighbor_cell_walls['E'] = False, False

                self.visited[ny][nx] = True
                stack.append((nx, ny)) # Move to the neighbor
            else:
                stack.pop() # Backtrack if no unvisited neighbors

    def is_wall(self, x, y, direction_key):
        # Check if there's a wall in a given direction from cell (x, y)
        if 0 <= y < self.rows and 0 <= x < self.cols:
            if direction_key in self.grid[y][x]:
                return self.grid[y][x][direction_key]
        return True # Treat out-of-bounds as a wall

    def draw(self, screen, cell_w, cell_h, visited_cells=None, path=None):
        # Draw the maze structure, optionally highlighting visited cells and the solution path
        screen.fill(PATH_COLOR) # Background color

        # Highlight visited cells during BFS (light gray)
        if visited_cells:
            for (x, y) in visited_cells:
                 # Don't overwrite path color if a cell is both visited and on path
                if not path or (x, y) not in path:
                    pygame.draw.rect(screen, VISITED_COLOR, (x * cell_w, y * cell_h, cell_w, cell_h))

        # Highlight the solution path (yellow)
        if path:
            for (x, y) in path:
                pygame.draw.rect(screen, YELLOW, (x * cell_w, y * cell_h, cell_w, cell_h))

        # Draw the walls
        for y in range(self.rows):
            for x in range(self.cols):
                cell_walls = self.grid[y][x]
                px, py = x * cell_w, y * cell_h # Top-left pixel coordinates of the cell
                if cell_walls['N']: pygame.draw.line(screen, BLACK, (px, py), (px + cell_w, py), 2)
                if cell_walls['S']: pygame.draw.line(screen, BLACK, (px, py + cell_h), (px + cell_w, py + cell_h), 2)
                if cell_walls['W']: pygame.draw.line(screen, BLACK, (px, py), (px, py + cell_h), 2)
                if cell_walls['E']: pygame.draw.line(screen, BLACK, (px + cell_w, py), (px + cell_w, py + cell_h), 2)


# --- Game Class ---
class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.Font(None, 30)
        self.info_font = pygame.font.Font(None, 24)
        self.level = 0 # Start at level 0
        self.lives = MAX_LIVES # Initialize lives (will be reset in play_mode)
        # Initialize screen and level settings asynchronously
        asyncio.run(self.setup_level()) # Run setup once initially
        pygame.display.set_caption("Maze Game")

    async def setup_level(self):
        # (الكود الخاص بدالة setup_level لم يتغير)
        # Configure maze dimensions and screen size for the current level
        # Ensure maze dimensions are odd
        self.cols = random.randint(MIN_MAZE_SIZE, MAX_MAZE_SIZE)
        self.rows = random.randint(MIN_MAZE_SIZE, MAX_MAZE_SIZE)
        if self.rows % 2 == 0: self.rows += 1
        if self.cols % 2 == 0: self.cols += 1

        # Calculate screen dimensions based on maze size
        base_cell_size = INITIAL_SCREEN_WIDTH // 20
        self.screen_width = self.cols * base_cell_size
        self.screen_height = self.rows * base_cell_size
        self.total_height = self.screen_height + INFO_PANEL_HEIGHT

        # Calculate cell dimensions
        self.cell_width = self.screen_width // self.cols
        self.cell_height = self.screen_height // self.rows

        # Set up the display window
        self.screen = pygame.display.set_mode((self.screen_width, self.total_height))
        # Create a new maze instance
        self.maze = Maze(self.cols, self.rows)
        # Define start and goal positions
        self.start_pos = (0, 0) # Top-left corner
        self.goal_pos = (self.cols - 1, self.rows - 1) # Bottom-right corner
        self.player_pos = self.start_pos # Player starts at the beginning
        self.message = f"Level {self.level + 1}" # Initial message
        # self.correct_path = await self.compute_correct_path() # No longer needed here for play mode logic


    async def compute_correct_path(self):
        # (الكود الخاص بدالة compute_correct_path لم يتغير - تُستخدم في وضع الحل)
        # Use Breadth-First Search (BFS) to find the shortest path from start to goal
        queue = deque([(self.start_pos, [self.start_pos])]) # Queue stores (position, path_so_far)
        visited = {self.start_pos} # Keep track of visited cells to avoid cycles

        while queue:
            (x, y), path = queue.popleft()

            if (x, y) == self.goal_pos:
                return path # Goal reached, return the path

            # Explore neighbors
            for direction_key, (dx, dy) in DIRECTIONS.items():
                if not self.maze.is_wall(x, y, direction_key): # Check if move is possible
                    nx, ny = x + dx, y + dy
                    # Check if neighbor is valid and not visited
                    if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_path = path + [(nx, ny)] # Extend the path
                        queue.append(((nx, ny), new_path))
        return None # Should not happen in a generated maze, but return None if no path found

    def draw_message_box(self, message, options):
        # (الكود الخاص بدالة draw_message_box لم يتغير)
        # Draw a message box with options (buttons) in the center of the maze area
        box_width, box_height = 350, 180 # Adjusted size
        box_x = (self.screen_width - box_width) // 2
        box_y = (self.screen_height - box_height) // 2 # Center vertically in the maze area
        # Draw box background and border
        pygame.draw.rect(self.screen, GRAY, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, BLACK, (box_x, box_y, box_width, box_height), 2)

        # Render and display the message text
        lines = message.split('\n') # Allow multi-line messages
        line_y = box_y + 30
        for line in lines:
            text = self.font.render(line, True, BLACK)
            text_rect = text.get_rect(center=(self.screen_width // 2, line_y))
            self.screen.blit(text, text_rect)
            line_y += 35 # Spacing between lines

        # Create and draw buttons for the options
        buttons = []
        num_options = len(options)
        button_total_width = num_options * 100 + (num_options - 1) * 20 # Width of buttons + spacing
        start_x = box_x + (box_width - button_total_width) // 2

        for i, option in enumerate(options):
            btn_width, btn_height = 100, 40
            btn_x = start_x + i * (btn_width + 20) # Position buttons horizontally with spacing
            btn_y = box_y + box_height - btn_height - 25 # Position buttons near the bottom
            # Draw button background and border
            pygame.draw.rect(self.screen, WHITE, (btn_x, btn_y, btn_width, btn_height))
            pygame.draw.rect(self.screen, BLACK, (btn_x, btn_y, btn_width, btn_height), 1)
            # Render and display button text
            btn_text = self.font.render(option, True, BLACK)
            btn_text_rect = btn_text.get_rect(center=(btn_x + btn_width // 2, btn_y + btn_height // 2))
            self.screen.blit(btn_text, btn_text_rect)
            # Store button rectangle and its corresponding option text
            buttons.append((pygame.Rect(btn_x, btn_y, btn_width, btn_height), option))

        pygame.display.flip() # Update the screen to show the message box
        return buttons # Return button data for click detection

    async def show_final_message(self, message, options=["Exit"]):
        # (الدالة المساعدة الجديدة لعرض الرسالة النهائية في وضع اللعب)
        # Display a final message (Win/Lose) and wait for user action (Exit)
        # Draw the final game state before showing the message box
        self.screen.fill(PATH_COLOR) # Use PATH_COLOR
        self.maze.draw(self.screen, self.cell_width, self.cell_height)
        # Draw player (at goal if won, current pos if lost)
        pygame.draw.rect(self.screen, BLUE, (self.player_pos[0] * self.cell_width, self.player_pos[1] * self.cell_height, self.cell_width, self.cell_height))
        # Draw goal
        pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
        # Update info panel with the final message
        self.message = message # Set the message to be displayed
        self._draw_info_panel()

        # Draw the message box over the game state
        buttons = self.draw_message_box(message, options)

        # Wait for user interaction
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                     if event.key == pygame.K_ESCAPE: # Allow exiting with ESC key
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if any button was clicked
                    for btn_rect, option in buttons:
                        if btn_rect.collidepoint(event.pos):
                            if option == "Exit":
                                pygame.quit()
                                sys.exit()
                            # Add handling for other options if needed in the future
            await asyncio.sleep(0.016) # Reduce CPU usage while waiting


    async def start_menu(self):
        # (الكود الخاص بدالة start_menu لم يتغير)
        # Display the initial menu with "Play" and "Solution" options
        self.screen.fill(BLACK) # Black background for menu
        buttons = self.draw_message_box("Choose an option:", ["Play", "Solution"])
        # Wait for the user to click a button
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check which button was clicked
                    for btn_rect, option in buttons:
                        if btn_rect.collidepoint(event.pos):
                            return option # Return the text of the clicked button
            await asyncio.sleep(0.016) # Keep the loop responsive without high CPU usage

    async def bfs(self):
         # (الكود الخاص بدالة bfs لم يتغير وهو مطابق للكود الأصلي - يستخدم لوضع الحل)
        queue = deque([(self.start_pos, [self.start_pos])])
        visited = {self.start_pos}
        clock = pygame.time.Clock() # Use clock for potential FPS limiting if needed

        while queue:
            # Handle window closing during visualization
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit() # Exit directly if window is closed

            (x, y), path = queue.popleft()

            # --- Drawing during BFS ---
            self.screen.fill(PATH_COLOR) # Clear screen using path color
            # Draw maze, visited cells, and current path being explored
            # Use VISITED_COLOR for visited cells, YELLOW for current path
            self.maze.draw(self.screen, self.cell_width, self.cell_height, visited_cells=visited, path=path)
            # Draw start (blue) and goal (green) markers
            pygame.draw.rect(self.screen, BLUE, (self.start_pos[0] * self.cell_width, self.start_pos[1] * self.cell_height, self.cell_width, self.cell_height))
            pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
            # Draw the info panel (shows "Level X | Lives: Y" or status)
            self.message = "Finding solution..." # Update status message for BFS
            self._draw_info_panel()
            pygame.display.flip() # Update the display
            # --- End Drawing ---

            # Check if the goal is reached
            if (x, y) == self.goal_pos:
                self.message = "Path found!" # Update message
                # Final draw showing the complete path
                self.screen.fill(PATH_COLOR)
                # Draw maze only with the final path highlighted in YELLOW
                self.maze.draw(self.screen, self.cell_width, self.cell_height, path=path)
                pygame.draw.rect(self.screen, BLUE, (self.start_pos[0] * self.cell_width, self.start_pos[1] * self.cell_height, self.cell_width, self.cell_height))
                pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
                self._draw_info_panel()
                pygame.display.flip()
                return path # Return the found path

            # Explore neighbors
            for direction_key, (dx, dy) in DIRECTIONS.items():
                if not self.maze.is_wall(x, y, direction_key):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_path = path + [(nx, ny)]
                        queue.append(((nx, ny), new_path))

            # Slow down visualization slightly (adjust delay as needed)
            await asyncio.sleep(0.01) # Shorter delay for faster visualization
            # clock.tick(60) # Optional FPS limit

        self.message = "No path found!" # Should not happen for these mazes
        self._draw_info_panel() # Update message if no path found
        pygame.display.flip()
        return None

    async def play_mode(self):
        # (الكود الخاص بوضع اللعب play_mode كما تم تعديله في الرد السابق)
        # Handle player movement and game logic in Play mode (single attempt)
        clock = pygame.time.Clock()
        self.player_pos = self.start_pos # Ensure player starts at the beginning
        # self.lives = MAX_LIVES # Lives already set to 1 globally
        self.message = f"Level {self.level + 1} - Find the exit!" # Updated message

        while True:
            moved = False # Flag to check if player moved in this frame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    new_pos = list(self.player_pos) # Copy current position
                    direction = None # Store direction key pressed

                    # Check arrow key presses and if move is valid (no wall)
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

                    # Process the move if a valid key was pressed and the move is possible
                    if direction is not None:
                        # Check bounds (redundant if edges are walls, but good practice)
                        if 0 <= new_pos[0] < self.cols and 0 <= new_pos[1] < self.rows:
                           self.player_pos = new_pos
                           moved = True

            # --- Game Logic after potential move ---
            if moved:
                 # Check win condition
                if self.player_pos == self.goal_pos:
                    return True # Player reached the goal, return True immediately


            # --- Drawing ---
            self.screen.fill(PATH_COLOR) # Clear screen with path color
            self.maze.draw(self.screen, self.cell_width, self.cell_height) # Draw maze structure
            # Draw player (blue) at current position
            pygame.draw.rect(self.screen, BLUE, (self.player_pos[0] * self.cell_width, self.player_pos[1] * self.cell_height, self.cell_width, self.cell_height))
            # Draw goal (green)
            pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
            # Draw the info panel
            self._draw_info_panel()
            pygame.display.flip() # Update the display
            # --- End Drawing ---

            # clock.tick(60) # Limit frame rate
            await asyncio.sleep(1.0 / 60) # Use asyncio sleep for better async behavior

    def _draw_info_panel(self):
        # (الكود الخاص بدالة _draw_info_panel لم يتغير)
        # Draw the information panel at the bottom of the screen
        info_rect = pygame.Rect(0, self.screen_height, self.screen_width, INFO_PANEL_HEIGHT)
        pygame.draw.rect(self.screen, GRAY, info_rect) # Background color
        # Draw a line separating the maze from the info panel
        pygame.draw.line(self.screen, BLACK, (0, self.screen_height), (self.screen_width, self.screen_height), 2)
        # Render and display the current message (Level, Lives, Status)
        msg_surface = self.font.render(self.message, True, BLACK)
        msg_rect = msg_surface.get_rect(center=(self.screen_width // 2, self.screen_height + INFO_PANEL_HEIGHT // 2))
        self.screen.blit(msg_surface, msg_rect)

    async def run(self):
        # --- Main Game Loop - تم دمج منطق الحل الأصلي مع منطق اللعب المعدل ---
        while True:
            # Show start menu and get user choice
            await self.setup_level() # Setup level before showing menu/starting mode
            choice = await self.start_menu()

            if choice == "Solution":
                # --- Solution Mode (الكود الأصلي الذي طلبته) ---
                path = await self.bfs() # Run BFS visualization first
                self.message = "Solution shown. Press ESC to exit or SPACE for next level." # Set initial message for this loop

                # Loop to keep showing the solution or generate next level
                solution_loop_active = True
                while solution_loop_active:
                    # --- Drawing the solved state ---
                    self.screen.fill(PATH_COLOR) # Clear screen with path color
                    # Draw maze with the found path highlighted
                    self.maze.draw(self.screen, self.cell_width, self.cell_height, path=path if path else [])
                    # Draw start and goal markers
                    pygame.draw.rect(self.screen, BLUE, (self.start_pos[0] * self.cell_width, self.start_pos[1] * self.cell_height, self.cell_width, self.cell_height))
                    pygame.draw.rect(self.screen, GREEN, (self.goal_pos[0] * self.cell_width, self.goal_pos[1] * self.cell_height, self.cell_width, self.cell_height))
                    # Update and draw the info panel
                    self._draw_info_panel()
                    pygame.display.flip()
                    # --- End Drawing ---

                    # --- Event handling for Solution Mode ---
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                pygame.quit()
                                sys.exit()
                            elif event.key == pygame.K_SPACE:
                                # Go to the next level
                                self.level += 1
                                await self.setup_level() # Setup the new level
                                path = await self.bfs() # Find the solution for the new level
                                self.message = "Solution shown. Press ESC to exit or SPACE for next level." # Reset message
                                # No need to set solution_loop_active to False,
                                # just let the loop continue with the new path/maze
                                # If BFS returns None (error), path will be empty list for drawing

                    # --- End Event Handling ---
                    await asyncio.sleep(1.0 / 60) # Keep responsive

            elif choice == "Play":
                # --- Play Mode (المنطق المعدل لمحاولة واحدة) ---
                # Level setup is already done before the menu
                won = await self.play_mode() # Start the single play attempt

                if won:
                    # Player won the single attempt
                    await self.show_final_message("You Won!", options=["Exit"])
                else:
                    # Player lost (e.g., closed window) or quit
                    # Since MAX_LIVES = 1, no 'lose life' message needed
                     await self.show_final_message("Game Over!", options=["Exit"])

                # After show_final_message handles exit, the main loop restarts,
                # effectively returning to the main menu.


# --- Start Game ---
if __name__ == "__main__":
    try:
        game = Game()
        asyncio.run(game.run())
    except Exception as e:
        print(f"An error occurred: {e}")
        pygame.quit()
        sys.exit()
    finally:
         pygame.quit() # Ensure pygame quits properly if loop exits unexpectedly