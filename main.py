import pygame
import random
import heapq
from enum import Enum

# Константы
CELL_SIZE = 8
GRID_WIDTH, GRID_HEIGHT = 101, 101
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE

# Цвета
class Colors(Enum):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREY = (150, 150, 150)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    PURPLE = (160, 32, 240)
    YELLOW = (255, 255, 0)

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Enhanced Maze Generator")
clock = pygame.time.Clock()

class MazeGenerator:
    """Класс для генерации лабиринта с использованием алгоритма backtracking."""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[1 for _ in range(width)] for _ in range(height)]
        self.directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
    
    def generate(self, animate=False):
        """Генерирует лабиринт с возможностью анимации процесса."""
        start = (1, 1)
        self.grid[start[1]][start[0]] = 0
        stack = [start]
        
        while stack:
            x, y = stack[-1]
            random.shuffle(self.directions)
            carved = False
            
            for dx, dy in self.directions:
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.width-1 and 1 <= ny < self.height-1:
                    if self.grid[ny][nx] == 1:
                        self.grid[ny][nx] = 0
                        self.grid[y + dy//2][x + dx//2] = 0
                        stack.append((nx, ny))
                        carved = True
                        if animate:
                            yield (nx, ny)  # Для анимации
                        break
            if not carved:
                stack.pop()
                if animate:
                    yield None  # Обновление экрана

class PathFinder:
    """Класс для поиска пути с использованием алгоритма A* и визуализации."""
    
    @staticmethod
    def heuristic(a, b):
        """Манхэттенское расстояние для эвристики A*."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    @classmethod
    def astar(cls, grid, start, end, visualize=False):
        """Выполняет поиск пути с визуализацией процесса."""
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        visited = set()
        
        while frontier:
            current = heapq.heappop(frontier)[1]
            
            if current == end:
                break
            
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = current[0]+dx, current[1]+dy
                if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid):
                    if grid[ny][nx] == 0:
                        neighbor = (nx, ny)
                        new_cost = cost_so_far[current] + 1
                        if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                            cost_so_far[neighbor] = new_cost
                            priority = new_cost + cls.heuristic(end, neighbor)
                            heapq.heappush(frontier, (priority, neighbor))
                            came_from[neighbor] = current
            
            visited.add(current)
            if visualize:
                yield visited.copy(), frontier.copy(), None
            
        # Восстановление пути
        path = []
        current = end
        while current != start:
            path.append(current)
            current = came_from.get(current)
            if current is None:
                path = []
                break
            if visualize:
                yield visited.copy(), frontier.copy(), path.copy()
        path.append(start)
        path.reverse()
        yield visited.copy(), frontier.copy(), path

class GameState:
    """Класс для управления состоянием игры и взаимодействием с пользователем."""
    
    def __init__(self):
        self.maze = MazeGenerator(GRID_WIDTH, GRID_HEIGHT)
        self.grid = self.maze.grid
        self.start = None
        self.end = None
        self.path = None
        self.visited = set()
        self.frontier = []
        self.generating = False
        self.solving = False
        self.animation_speed = 0
        
        # Для анимации
        self.gen_iterator = None
        self.astar_iterator = None
        
    def handle_events(self):
        """Обрабатывает пользовательский ввод."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event)
            if event.type == pygame.KEYDOWN:
                self.handle_key_press(event)
        return True
    
    def handle_mouse_click(self, event):
        """Обрабатывает клики мыши для выбора старта/финиша."""
        x, y = event.pos
        grid_x = x // CELL_SIZE
        grid_y = y // CELL_SIZE
        
        if event.button == 1:  # ЛКМ
            if self.grid[grid_y][grid_x] == 0:
                self.start = (grid_x, grid_y)
        elif event.button == 3:  # ПКМ
            if self.grid[grid_y][grid_x] == 0:
                self.end = (grid_x, grid_y)
    
    def handle_key_press(self, event):
        """Обрабатывает нажатия клавиш."""
        if event.key == pygame.K_SPACE:
            self.regenerate_maze()
        elif event.key == pygame.K_RETURN and self.start and self.end:
            self.start_solving()
    
    def regenerate_maze(self):
        """Перегенерирует лабиринт и сбрасывает состояние"""
        self.generating = True
        self.start = None
        self.end = None
        self.path = None
        self.gen_iterator = self.maze.generate(animate=True)
    
    def start_solving(self):
        """Запускает алгоритм поиска пути"""
        self.solving = True
        self.astar_iterator = PathFinder.astar(
            self.grid, self.start, self.end, visualize=True
        )
    
    def update(self):
        """Обновляет состояние игры"""
        if self.generating:
            try:
                next(self.gen_iterator)
            except StopIteration:
                self.generating = False
                self.grid = self.maze.grid
        
        if self.solving:
            try:
                self.visited, self.frontier, self.path = next(self.astar_iterator)
            except StopIteration:
                self.solving = False
    
    def draw(self):
        """Отрисовывает текущее состояние"""
        screen.fill(Colors.BLACK.value)
        
        # Отрисовка сетки
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = Colors.WHITE.value if self.grid[y][x] == 0 else Colors.BLACK.value
                pygame.draw.rect(screen, color, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        # Отрисовка посещенных ячеек
        for x, y in self.visited:
            pygame.draw.rect(screen, Colors.GREY.value, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        # Отрисовка фронтера
        for _, (x, y) in self.frontier:
            pygame.draw.rect(screen, Colors.PURPLE.value, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        # Отрисовка пути
        if self.path:
            for x, y in self.path:
                pygame.draw.rect(screen, Colors.BLUE.value, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        # Отрисовка старта и финиша
        if self.start:
            pygame.draw.rect(screen, Colors.GREEN.value, 
                            (self.start[0]*CELL_SIZE, self.start[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        if self.end:
            pygame.draw.rect(screen, Colors.RED.value, 
                            (self.end[0]*CELL_SIZE, self.end[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        pygame.display.flip()

def main():
    """Основная функция игры"""
    game = GameState()
    game.regenerate_maze()
    
    running = True
    while running:
        clock.tick(game.animation_speed)
        running = game.handle_events()
        game.update()
        game.draw()
    
    pygame.quit()

if __name__ == "__main__":
    main()