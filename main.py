import pygame
import sys
import math
import random
import numpy as np
import noise  # Ensure you have the noise library installed: pip install noise
import collections

# Define a Star class to manage individual stars
class Star:
    def __init__(self, screen_width, screen_height, speed_range=(0.05, 0.2), size=1):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.reset_star(speed_range)

        self.size = size  # Fixed size for higher contrast
        self.color = (255, 255, 255)  # Pure white for maximum contrast

    def reset_star(self, speed_range):
        """Initialize or reset the star's position and speed."""
        self.x = random.uniform(0, self.screen_width)
        self.y = random.uniform(0, self.screen_height)
        self.vy = random.uniform(*speed_range)  # Vertical speed to simulate movement

    def update(self):
        """Update the star's position."""
        self.y += self.vy
        if self.y > self.screen_height:
            self.reset_star(speed_range=(0.05, 0.2))

    def draw(self, surface):
        """Draw the star onto the pygame.Surface."""
        ix = int(self.x)
        iy = int(self.y)
        if 0 <= ix < self.screen_width and 0 <= iy < self.screen_height:
            if self.size == 1:
                surface.set_at((ix, iy), self.color)
            else:
                # For size >1, draw a small circle
                pygame.draw.circle(surface, self.color, (ix, iy), self.size)

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Rotating Earth with Perlin Noise and Day-Night Cycle")
        self.screen_width, self.screen_height = 720, 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.display_width, self.display_height = 240, 200
        self.display = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()

        self.cx = self.display_width // 2
        self.cy = self.display_height // 2

        # Set Earth-like radii
        self.radius = random.randint(30, 50)  # Reduced from 100-105
        self.cloud_radius = random.randint(self.radius + 5, self.radius + 10)

        # Planet rotation angles for multi-axis rotation
        self.planet_angle_y = 0.0  # Rotation around Y-axis
        self.planet_angle_x = 0.0  # Rotation around X-axis

        # Noise settings for planet 
        self.noise_scale = 0.03    
        self.octaves = 3             
        self.persistence = 0.8
        self.lacunarity = 2.0

        # Noise settings for clouds
        self.cloud_noise_scale = 0.03  
        self.cloud_octaves = 3            
        self.cloud_persistence = 0.5
        self.cloud_lacunarity = 1.5

        # Seed for noise
        self.noise_seed = random.randint(900, 1000)

        # Cloud drift speed
        self.cloud_shift_speed = 0.25    

        # Render step: how many pixels to skip
        self.render_step = 1

        # Initialize stars
        self.num_stars = 300  # Increased number of stars for a denser starfield
        self.stars = [Star(self.display_width, self.display_height, speed_range=(0.05, 0.2), size=1) for _ in range(self.num_stars)]

        # Initialize Earth-like color palette for planet features
        self.generate_random_color_palette()

        # Define the light source direction (fixed)
        # For example, light coming from the left (-1, 0, 0)
        self.light_direction = np.array([-1, 0, 0])
        self.light_direction = self.light_direction / np.linalg.norm(self.light_direction)  # Normalize

        # Initialize a counter for h values (optional, for debugging)
        self.h_counter = collections.defaultdict(int)

    def generate_random_color_palette(self):
        """Generates completely random colors for all planet features, with deep ocean being a darker version of ocean."""
        # Ocean: Completely random color
        self.ocean_color = self.random_color()
        # Deep Ocean: Darker version of ocean_color by subtracting a fixed amount
        self.deep_ocean_color = self.darken_color(self.ocean_color, amount=60)
        # Beach: Completely random color
        self.beach_color = self.random_color()
        # Forest: Completely random color
        self.forest_color = self.random_color()
        # Mountains: Completely random color
        self.mountain_color = self.random_color()
        # Clouds: Completely random color
        self.cloud_color = self.random_color()

    @staticmethod
    def random_color():
        r = random.randint(0,255)
        g = random.randint(0,255)
        b = random.randint(0,255)
        return (r,g,b)

    @staticmethod
    def darken_color(color, amount=50):
        """Returns a darker version of the given RGB color by subtracting a fixed amount from each component."""
        return tuple(max(c - amount, 0) for c in color)

    def draw_stars(self, main_surface):
        """Draws all stars onto the main_surface."""
        for star in self.stars:
            star.draw(main_surface)

    def update_stars(self):
        """Updates the position of all stars."""
        for star in self.stars:
            star.update()

    def draw_planet_with_clouds(self, main_surface):
        """Draws the planet's surface onto the main_surface with day-night cycle."""
        # Calculate rotation matrices for planet
        cosA_y = math.cos(self.planet_angle_y)
        sinA_y = math.sin(self.planet_angle_y)
        cosA_x = math.cos(self.planet_angle_x)
        sinA_x = math.sin(self.planet_angle_x)

        # Iterate over each point on the planet's surface
        for sx in range(-self.radius, self.radius, self.render_step):
            for sy in range(-self.radius, self.radius, self.render_step):
                r2 = sx * sx + sy * sy
                if r2 <= self.radius * self.radius:
                    z = math.sqrt(self.radius * self.radius - r2)

                    # Original coordinates
                    x = sx
                    y = sy
                    z_orig = z

                    # Rotate around Y-axis
                    x1 = x * cosA_y - z_orig * sinA_y
                    y1 = y
                    z1 = x * sinA_y + z_orig * cosA_y

                    # Rotate around X-axis
                    x2 = x1
                    y2 = y1 * cosA_x - z1 * sinA_x
                    z2 = y1 * sinA_x + z1 * cosA_x

                    # Surface normal (normalized)
                    normal = np.array([x2, y2, z2])
                    normal = normal / np.linalg.norm(normal)

                    # Calculate dot product with light direction
                    dot = np.dot(normal, self.light_direction)
                    brightness = max(dot, 0)  # Clamp to [0, 1]

                    # Add ambient light
                    ambient = 0.1  # Reduced from 0.2 for darker nights
                    brightness = ambient + (1 - ambient) * brightness
                    brightness = min(brightness, 1.0)  # Ensure it doesn't exceed 1

                    # Noise coordinates based on rotated positions
                    nx = x2 * self.noise_scale
                    ny = y2 * self.noise_scale
                    nz = z2 * self.noise_scale

                    # Perlin noise for terrain
                    noise_val = noise.pnoise3(
                        nx, ny, nz,
                        octaves=self.octaves,
                        persistence=self.persistence,
                        lacunarity=self.lacunarity,
                        repeatx=999999,
                        repeaty=999999,
                        repeatz=999999,
                        base=self.noise_seed
                    )
                    h = (noise_val + 1) / 2.0  # Normalize to [0, 1]

                    # Increment h counter for debugging
                    self.h_counter[round(h, 1)] += 1

                    # Terrain color mapping using the Earth palette
                    if h < 0.35:
                        base_color = self.deep_ocean_color  # Deep Ocean (darker)
                    elif h < 0.5:
                        base_color = self.ocean_color       # Ocean
                    elif h < 0.52:
                        base_color = self.beach_color       # Beach
                    elif h < 0.65:
                        base_color = self.forest_color      # Forest
                    else:
                        base_color = self.mountain_color    # Mountains

                    # Apply brightness to base color
                    if base_color == self.beach_color:
                        # Ensure beaches are bright enough without exceeding 255
                        # Calculate a brightness multiplier capped at 1.0
                        brightness_multiplier = min(brightness + 0.2, 1.0)
                        shaded_color = tuple(
                            min(int(c * brightness_multiplier), 255) for c in base_color
                        )
                    else:
                        shaded_color = tuple(
                            min(int(c * brightness), 255) for c in base_color
                        )

                    # Fill the pixel with the shaded color
                    main_surface.set_at((self.cx + sx, self.cy + sy), shaded_color)

    def draw_clouds(self, main_surface):
        """Draws the clouds onto the main_surface, affected by lighting."""
        # Calculate rotation matrices for planet
        cosA_y = math.cos(self.planet_angle_y)
        sinA_y = math.sin(self.planet_angle_y)
        cosA_x = math.cos(self.planet_angle_x)
        sinA_x = math.sin(self.planet_angle_x)

        # Cloud rendering
        cloud_threshold = 0.6
        time_offset = pygame.time.get_ticks() * 0.001  # Convert milliseconds to seconds

        for sx in range(-self.cloud_radius, self.cloud_radius, self.render_step):
            for sy in range(-self.cloud_radius, self.cloud_radius, self.render_step):
                r2 = sx * sx + sy * sy
                if r2 <= self.cloud_radius * self.cloud_radius:
                    z = math.sqrt(self.cloud_radius * self.cloud_radius - r2)

                    # Original coordinates
                    x = sx
                    y = sy
                    z_orig = z

                    # Rotate around Y-axis
                    x1 = x * cosA_y - z_orig * sinA_y
                    y1 = y
                    z1 = x * sinA_y + z_orig * cosA_y

                    # Rotate around X-axis
                    x2 = x1
                    y2 = y1 * cosA_x - z1 * sinA_x
                    z2 = y1 * sinA_x + z1 * cosA_x

                    # Offset noise for cloud drift based on rotated positions
                    nx = (x2 * self.cloud_noise_scale
                          + time_offset * self.cloud_shift_speed)
                    ny = (y2 * self.cloud_noise_scale
                          + time_offset * self.cloud_shift_speed)
                    nz = z2 * self.cloud_noise_scale

                    # Perlin noise for clouds
                    noise_val = noise.pnoise3(
                        nx, ny, nz,
                        octaves=self.cloud_octaves,
                        persistence=self.cloud_persistence,
                        lacunarity=self.cloud_lacunarity,
                        repeatx=999999,
                        repeaty=999999,
                        repeatz=999999,
                        base=self.noise_seed
                    )
                    h_cloud = (noise_val + 1) / 2.0  # Normalize to [0, 1]

                    # Only draw clouds if noise exceeds threshold
                    if h_cloud > cloud_threshold:
                        # Calculate brightness for cloud pixel
                        normal_cloud = np.array([x2, y2, z2])
                        norm = np.linalg.norm(normal_cloud)
                        if norm == 0:
                            continue  # Avoid division by zero
                        normal_cloud = normal_cloud / norm

                        # Calculate dot product with light direction
                        dot_cloud = np.dot(normal_cloud, self.light_direction)
                        brightness_cloud = max(dot_cloud, 0)  # Clamp to [0,1]

                        # Add ambient light
                        ambient_cloud = 0.1
                        brightness_cloud = ambient_cloud + (1 - ambient_cloud) * brightness_cloud
                        brightness_cloud = min(brightness_cloud, 1.0)  # Ensure it doesn't exceed 1

                        # Apply brightness to cloud color
                        shaded_cloud_color = tuple(
                            min(int(c * brightness_cloud), 255) for c in self.cloud_color
                        )

                        # Blend shaded cloud color with existing color
                        alpha = 0.5  # Semi-transparent
                        screen_x = self.cx + sx
                        screen_y = self.cy + sy

                        # Boundary Check
                        if 0 <= screen_x < self.display_width and 0 <= screen_y < self.display_height:
                            existing_color = main_surface.get_at((screen_x, screen_y))[:3]
                            blended_color = tuple(
                                min(int(shaded_cloud_color[i] * alpha + existing_color[i] * (1 - alpha)), 255)
                                for i in range(3)
                            )

                            # Set the blended color
                            main_surface.set_at((screen_x, screen_y), blended_color)

    def main(self):
        while True:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Update planet rotation angles for multi-axis rotation
            rotation_speed_y = 0.02  # radians per frame around Y-axis
            rotation_speed_x = 0.01  # radians per frame around X-axis
            self.planet_angle_y += rotation_speed_y
            self.planet_angle_x += rotation_speed_x
            self.planet_angle_y %= 2 * math.pi  # Keep within [0, 2π]
            self.planet_angle_x %= 2 * math.pi  # Keep within [0, 2π]

            # Update star positions to simulate movement
            self.update_stars()

            # Create a Pygame surface for the frame
            main_surface = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA)
            main_surface.fill((0, 0, 0, 255))  # Fill with black

            # Draw stars first (background)
            self.draw_stars(main_surface)

            # Draw the planet with day-night cycle
            self.draw_planet_with_clouds(main_surface)

            # Draw clouds on top of the planet
            self.draw_clouds(main_surface)

            # Scale the display to the screen size
            scaled_display = pygame.transform.scale(main_surface, (self.screen_width, self.screen_height))
            self.screen.blit(scaled_display, (0, 0))

            # Update the display
            pygame.display.update()
            self.clock.tick(60)  # Limit to 60 FPS

if __name__ == "__main__":
    Game().main()
