from .gamedata import *
from .utils import *


class Pacman:
    def __init__(self):
        self._score = 0
        self._skill_status_current = [0, 0, 0, 0, 0]
        self._skill_status = [0, 0, 0, 0, 0]
        self._coord = np.array([-1, -1])
        self._level = 1
        self._board_size = 20
        self._portal_coord = np.array([-1, -1])
        self._invulnerable_time = 0
        self._eaten_bean_count = 0

    def invulnerable(self):
        return self._invulnerable_time > 0

    def set_invulnerable_time(self, time=1):
        self._invulnerable_time = time
        
    def decrease_invulnerable_time(self):
        self._invulnerable_time -= 1

    def update_bonus(self, points):
        self._score += points
        return points

    def update_score(self, points):
        reward = (
            2 * points
            if self._skill_status_current[Skill.DOUBLE_SCORE.value] > 0
            else points
        )
        self._score += reward
        return reward

    def just_eat(self, board, x, y):
        reward = 0
        if not in_movable_board([x, y], self._level):
            return 0

        if board[x][y] == Space.REGULAR_BEAN.value:
            board[x][y] = Space.EMPTY.value
            self._eaten_bean_count += 1
            reward += self.update_score(1)

        elif board[x][y] == Space.BONUS_BEAN.value:
            board[x][y] = Space.EMPTY.value
            self._eaten_bean_count += 1
            reward += self.update_score(2)

        elif board[x][y] == Space.SPEED_BEAN.value:
            board[x][y] = Space.EMPTY.value
            self.acquire_skill(Skill.SPEED_UP)

        elif board[x][y] == Space.MAGNET_BEAN.value:
            board[x][y] = Space.EMPTY.value
            self.acquire_skill(Skill.MAGNET)

        elif board[x][y] == Space.SHIELD_BEAN.value:
            board[x][y] = Space.EMPTY.value
            self.acquire_skill(Skill.SHIELD)

        elif board[x][y] == Space.DOUBLE_BEAN.value:
            board[x][y] = Space.EMPTY.value
            self.acquire_skill(Skill.DOUBLE_SCORE)

        elif board[x][y] == Space.FROZE_BEAN.value:
            board[x][y] = Space.EMPTY.value
            self.acquire_skill(Skill.FROZE)

        return reward

    def eat_bean(self, board):
        reward = 0
        x, y = self._coord
        if self._skill_status_current[Skill.MAGNET.value] == 0:
            reward += self.just_eat(board, x, y)

        else:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    reward += self.just_eat(board, x + i, y + j)

        return reward

    def get_skills_status(self):
        return self._skill_status.copy()

    def acquire_skill(self, skill_index: Skill):
        if skill_index == Skill.SHIELD:
            self._skill_status[Skill.SHIELD.value] += 1
        else:
            self._skill_status[skill_index.value] = DEFAULT_SKILL_TIME[
                skill_index.value
            ]

    def update_current_skill(self):
        self._skill_status_current = self._skill_status.copy()

    def set_level(self, level):
        self._level = level

    def set_size(self, size):
        self._board_size = size

    def get_coord(self):
        return self._coord.copy()

    def set_coord(self, coord):
        self._coord = coord

    def set_portal_coord(self, portal_coord):
        self._portal_coord = portal_coord

    def get_portal_coord(self):
        return self._portal_coord.copy()

    def decrease_skill_time(
        self,
        skill_list: list[Skill] = [Skill.DOUBLE_SCORE, Skill.MAGNET, Skill.SPEED_UP],
    ):  # Note: reset the skill status when a new round starts
        for skill in skill_list:
            if self._skill_status[skill.value] > 0:
                self._skill_status[skill.value] -= 1

    def get_score(self):
        return self._score

    def try_break_shield(self):
        if self._skill_status_current[Skill.SHIELD.value] > 0:
            self._skill_status[Skill.SHIELD.value] -= 1
            return False
        else:
            return True

    def try_move(self, board, direction: Direction):
        offset = direction_to_offset(direction)
        new_coord = self._coord + offset
        if board[new_coord[0], new_coord[1]] == Space.WALL.value:
            return False
        self._coord = new_coord
        return True

    def clear_skills(self):
        self._skill_status = [0, 0, 0, 0, 0]
        self._skill_status_current = [0, 0, 0, 0, 0]
        
    def reset_eaten_bean_count(self):
        self._eaten_bean_count = 0

    def get_eaten_bean_count(self):
        return self._eaten_bean_count
