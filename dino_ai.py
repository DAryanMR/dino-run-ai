import time
import cv2
import numpy as np
import pyautogui
import os
import math


def capture_screen(capture_area=None):
    # Get screen dimensions
    screen = pyautogui.screenshot()
    screen = np.array(screen)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    if capture_area is not None:
        x, y, width, height = capture_area
        screen = screen[y:y+height, x:x+width]

    return screen


def match_template(template_path, screen):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc


def draw_rectangle(image, top_left, bottom_right, color=(0, 255, 0), thickness=2):
    cv2.rectangle(image, top_left, bottom_right, color, thickness)


def draw_line_with_distance(image, player_rect, obstacle_rect):
    player_center = (player_rect[0] + player_rect[2] //
                     2, player_rect[1] + player_rect[3] // 2)
    obstacle_center = (
        obstacle_rect[0] + obstacle_rect[2] // 2, obstacle_rect[1] + obstacle_rect[3] // 2)
    cv2.line(image, player_center, obstacle_center, (255, 0, 0), 2)

    distance = math.sqrt((player_center[0] - obstacle_center[0])
                         ** 2 + (player_center[1] - obstacle_center[1]) ** 2)
    distance_text = f"Distance: {distance:.2f}"
    text_size, _ = cv2.getTextSize(
        distance_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
    text_pos = (player_center[0] + obstacle_center[0]
                ) // 2, (player_center[1] + obstacle_center[1]) // 2 - text_size[1]
    cv2.putText(image, distance_text, text_pos,
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)


def simulate_keypress():
    pyautogui.press('up')


# Folder path containing obstacle images
obstacles_folder = 'obstacles'

# Path to the player image
player_image_path = 'player.png'

# Define the coordinates of the specific area to capture
capture_area = (0, 0, 1366, 300)  # (x, y, width, height)

# Capture screen dimensions
screen = capture_screen(capture_area)
screen_height, screen_width, _ = screen.shape

# Define the video writer
output_file = 'output.avi'
fourcc = cv2.VideoWriter_fourcc(*'XVID')
output = cv2.VideoWriter(output_file, fourcc, 10.0,
                         (screen_width, screen_height))

get_alert = False

# Capture the desktop screen continuously
while True:
    # Capture the screen
    screen = capture_screen(capture_area)

    # Detect and draw bounding rectangle around player
    player_max_val, player_max_loc = match_template(player_image_path, screen)

    if player_max_val > 0.2:
        player_rect = (player_max_loc[0], player_max_loc[1], cv2.imread(
            player_image_path).shape[1], cv2.imread(player_image_path).shape[0])
        draw_rectangle(screen, (player_rect[0], player_rect[1]), (
            player_rect[0] + player_rect[2], player_rect[1] + player_rect[3]))

    # Detect and draw bounding rectangles around obstacles
    for obstacle_file in os.listdir(obstacles_folder):
        obstacle_path = os.path.join(obstacles_folder, obstacle_file)
        max_val, max_loc = match_template(obstacle_path, screen)

        if max_val > 0.5:
            obstacle_rect = (max_loc[0], max_loc[1], cv2.imread(
                obstacle_path).shape[1], cv2.imread(obstacle_path).shape[0])

            draw_rectangle(screen, (obstacle_rect[0], obstacle_rect[1]), (
                obstacle_rect[0] + obstacle_rect[2], obstacle_rect[1] + obstacle_rect[3]), color=(0, 0, 255))

            

            # Check if distance is less than or equal to 400 and obstacle is on the right side
            if obstacle_rect[0] > player_rect[0] and obstacle_rect[0] > player_rect[0] + player_rect[2]:
                distance = math.sqrt(
                    (player_rect[0] - obstacle_rect[0]) ** 2 + (player_rect[1] - obstacle_rect[1]) ** 2)
                if distance <= 400:
                    get_alert = True
            if get_alert:
                draw_line_with_distance(screen, player_rect, obstacle_rect)
                if distance <= 200:

                    simulate_keypress()
                    get_alert = False
                    break

    # Write the frame to the output video file
    output.write(screen)

    # Display the screen with bounding rectangles
    cv2.imshow('Screen', screen)
    if cv2.waitKey(1) == ord('q'):
        break


# Release the video writer and close the windows
output.release()
cv2.destroyAllWindows()
