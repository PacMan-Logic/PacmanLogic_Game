import json
import random
import time
import os

from core.GymEnvironment import PacmanEnv
from logic.utils import *
from core.gamedata import *

ERROR_MAP = ["RE", "TLE", "OLE"]
replay_file = None

class Player():
    def __init__(
        self,
        id,
        type,
    ):
        self.id = id
        self.action = []
        self.type = type
        self.role = Role.PACMAN.value

def get_ai_info( env: PacmanEnv , player: Player , another_player: Player ):
    '''
    获取ai或播放器用户的操作

    env: 游戏逻辑维护的唯一局面
    玩家0和玩家1的类型: 1 为 AI, 2 为网页播放器。
    '''
    ai_info = receive_ai_info()

    while ai_info["player"] != -1 and ai_info["player"] != player.id:
        ai_info = receive_ai_info()
    # 判定交互对象状态
    # 如果交互对象异常则退出
    if ai_info["player"] == -1: 
        # judger 监听列表中的某个 AI 超时或发生错误 -> 终止游戏，返回错误信息
        return_dict = env.render()
        error_info = json.loads(ai_info["content"])
        error_type = error_info['error']
        error_player = error_info['player']
        return_dict["StopReason"] = f"Unexpected behavior of player {error_player}, judger returned error type {ERROR_MAP[error_type]}."

        # 回放文件写入结束信息
        replay_file.write(json.dumps(return_dict, ensure_ascii=False)+"\n")

        send_watch_info(json.dumps(return_dict, ensure_ascii=False)+'\n')

        if player.type == Type.PLAYER.value:
            send_to_judger(
                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), player.id
            )

        if another_player.type == Type.PLAYER.value:
            send_to_judger(
                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), another_player.id
            )

        end_list = ["OK", "OK"]
        error_id = json.loads(ai_info["content"])["player"]
        end_list[error_id] = ERROR_MAP[
            json.loads(ai_info["content"])["error"]
        ]
        end_error_score = [0, 0]
        end_error_score[error_id] = -ERROR_SCORE
        end_error_score[1-error_id] = NORMAL_SCORE

        pacmanscore = env.get_pacman_score()
        ghostscore = env.get_ghosts_score()
        end_info = {}
        if players[0].role == Role.PACMAN.value:
            end_info = {
                "0": pacmanscore + end_error_score[0],
                "1": ghostscore + end_error_score[1],
            }
        else:
            end_info = {
                "0": ghostscore + end_error_score[0],
                "1": pacmanscore + end_error_score[1],
            }
        send_game_end_info(json.dumps(end_info), json.dumps(end_list))
        replay_file.close()
        time.sleep(0.5)
        exit(0)
    else:
        try:
            # 获取操作
            info = json.loads(ai_info["content"])
            role = info["role"]
            action = [int(i) for i in info["action"].split(" ")]

            if role == Role.PACMAN.value:
                # 表明玩家是吃豆人
                if len(action) != 1 or action[0] < 0 or action[0] >= 5 : 
                    raise ValueError("Invalid action for PACMAN.")
            else:
                # 表明玩家是幽灵
                if len(action) != 3 :
                    raise ValueError("Invalid action count for ghost.")
                else :
                    if action[0] < 0 or action[0] >= 5 :
                        raise ValueError("Invalid action for ghost at index 0.")
                    if action[1] < 0 or action[1] >= 5 :
                        raise ValueError("Invalid action for ghost at index 1.")
                    if action[2] < 0 or action[2] >= 5 :
                        raise ValueError("Invalid action for ghost at index 2.")
            return role , action
        except:
            error = traceback.format_exc()
            return_dict = env.render()
            return_dict["StopReason"] = (
                f"{error}"
            )
            # 回放文件写入结束信息
            replay_file.write(json.dumps(return_dict, ensure_ascii=False)+"\n")

            send_watch_info(json.dumps(return_dict, ensure_ascii=False)+'\n')

            if player.type == Type.PLAYER.value:
                send_to_judger(
                    json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), player.id
                )

            if another_player.type == Type.PLAYER.value:
                send_to_judger(
                    json.dumps(return_dict, ensure_ascii=False).encode("utf-8"),
                    another_player.id,
                )

            end_state = ["OK", "OK"]
            end_state[player.id] = "IA"
            end_error_score = [0,0]
            end_error_score[player.id] = -ERROR_SCORE
            end_error_score[1-player.id] = NORMAL_SCORE

            pacmanscore = env.get_pacman_score()
            ghostscore = env.get_ghosts_score()
            end_info = {}
            if players[0].role == Role.PACMAN.value:
                end_info = {
                    "0": pacmanscore + end_error_score[0],
                    "1": ghostscore + end_error_score[1],
                }
            else:
                end_info = {
                    "0": ghostscore + end_error_score[0],
                    "1": pacmanscore + end_error_score[1],
                }

            send_game_end_info(
                json.dumps(end_info, ensure_ascii=False), json.dumps(end_state)
            )
            replay_file.close()
            time.sleep(0.5)
            exit(0)

def interact( env: PacmanEnv, pacman: Player , ghosts: Player ):
    '''
    执行操作，输出要转发给对方的字符串

    env: 游戏逻辑维护的唯一局面
    interact返回五个值: game_continue, info1, info2, level_change, eat_all_beans  info1和info2分别发给吃豆人和幽灵
    '''
    # 执行两个玩家的操作
    try:
        info , pacman_reward , ghosts_reward , level_change , eat_all_beans = env.step(pacman.action[0], ghosts.action)

    except:
        error = traceback.format_exc()
        return_dict = env.render()
        return_dict["StopReason"] = f"Error in executing actions from players, error: {error}"
        replay_file.write(json.dumps(return_dict, ensure_ascii=False) + "\n")

        send_watch_info(json.dumps(return_dict, ensure_ascii=False)+'\n')

        if pacman.type == Type.PLAYER.value:
            send_to_judger(
                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), pacman.id
            )

        if ghosts.type == Type.PLAYER.value:
            send_to_judger(
                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), ghosts.id
            )

        end_state = ["IA", "IA"]
        end_error_score = [0, 0]
        end_error_score[0] = -ERROR_SCORE
        end_error_score[1] = -ERROR_SCORE

        pacmanscore = env.get_pacman_score()
        ghostscore = env.get_ghosts_score()
        end_info = {}
        if pacman.id == 0:
            end_info = {
                "0": pacmanscore + end_error_score[0],
                "1": ghostscore + end_error_score[1],
            }
        else:
            end_info = {
                "0": ghostscore + end_error_score[0],
                "1": pacmanscore + end_error_score[1],
            }

        send_game_end_info(
            json.dumps(end_info, ensure_ascii=False), json.dumps(end_state)
        )
        replay_file.close()
        time.sleep(0.5)
        exit(0)

    # 更新游戏状态
    new_state = env.render()
    replay_file.write(json.dumps(new_state, ensure_ascii=False) + "\n")
    send_watch_info(json.dumps(new_state, ensure_ascii=False)+'\n')
    # 返回新的状态信息
    game_continue = True
    info1 = "" # 返回给吃豆人的信息
    info2 = "" # 返回给幽灵的信息
    if pacman.type == Type.AI.value:
        info_to_ai = {
            "pacman_action" : pacman.action[0],
            "ghosts_action" : ghosts.action
        }
        info1 = json.dumps(info_to_ai, ensure_ascii=False)
    elif pacman.type == Type.PLAYER.value:
        info1 = json.dumps(new_state, ensure_ascii=False) 
    if ghosts.type == Type.AI.value:
        info_to_ai = {
            "pacman_action" : pacman.action[0],
            "ghosts_action" : ghosts.action
        }
        info2 = json.dumps(info_to_ai, ensure_ascii=False)
    elif ghosts.type == Type.PLAYER.value:
        info2 = json.dumps(new_state, ensure_ascii=False)
    return game_continue , info1 , info2 , level_change , eat_all_beans


def choose_max_round( env: PacmanEnv , player: Player , another_player: Player ):
    '''
    获取ai或播放器用户的操作

    env: 游戏逻辑维护的唯一局面
    玩家0和玩家1的类型: 1 为 AI, 2 为网页播放器。
    '''
    ai_info = receive_ai_info()

    while ai_info["player"] != -1 and ai_info["player"] != player.id:
        ai_info = receive_ai_info()
    # 判定交互对象状态
    # 如果交互对象异常则退出
    if ai_info["player"] == -1: 
        # judger 监听列表中的某个 AI 超时或发生错误 -> 终止游戏，返回错误信息
        return_dict = env.render()
        error_info = json.loads(ai_info["content"])
        error_type = error_info['error']
        error_player = error_info['player']
        return_dict["StopReason"] = f"Unexpected behavior of player {error_player}, judger returned error type {ERROR_MAP[error_type]}."

        # 回放文件写入结束信息
        replay_file.write(json.dumps(return_dict, ensure_ascii=False)+"\n")

        send_watch_info(json.dumps(return_dict, ensure_ascii=False)+'\n')

        if player.type == Type.PLAYER.value:
            send_to_judger(
                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), player.id
            )

        if another_player.type == Type.PLAYER.value:
            send_to_judger(
                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), another_player.id
            )

        end_list = ["OK", "OK"]
        error_id = json.loads(ai_info["content"])["player"]
        end_list[error_id] = ERROR_MAP[
            json.loads(ai_info["content"])["error"]
        ]
        end_error_score = [0, 0]
        end_error_score[error_id] = -ERROR_SCORE
        end_error_score[1-error_id] = NORMAL_SCORE

        pacmanscore = env.get_pacman_score()
        ghostscore = env.get_ghosts_score()
        end_info = {}
        if players[0].role == Role.PACMAN.value:
            end_info = {
                "0": pacmanscore + end_error_score[0],
                "1": ghostscore + end_error_score[1],
            }
        else:
            end_info = {
                "0": ghostscore + end_error_score[0],
                "1": pacmanscore + end_error_score[1],
            }
        send_game_end_info(json.dumps(end_info), json.dumps(end_list))
        replay_file.close()
        time.sleep(0.5)
        exit(0)
    else:
        try:
            # 获取关卡轮数信息
            # TODO
            max_round_max = int(ai_info["content"])
            MAX_ROUND[env._level] = ROUND[max_round_max]
            return MAX_ROUND[env._level]
        except:
            error = traceback.format_exc()
            return_dict = env.render()
            return_dict["StopReason"] = (
                f"{error}"
            )
            # 回放文件写入结束信息
            replay_file.write(json.dumps(return_dict, ensure_ascii=False)+"\n")

            send_watch_info(json.dumps(return_dict, ensure_ascii=False)+'\n')

            if player.type == Type.PLAYER.value:
                send_to_judger(
                    json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), player.id
                )

            if another_player.type == Type.PLAYER.value:
                send_to_judger(
                    json.dumps(return_dict, ensure_ascii=False).encode("utf-8"),
                    another_player.id,
                )

            end_state = ["OK", "OK"]
            end_state[player.id] = "IA"
            end_error_score = [0,0]
            end_error_score[player.id] = -ERROR_SCORE
            end_error_score[1-player.id] = NORMAL_SCORE

            pacmanscore = env.get_pacman_score()
            ghostscore = env.get_ghosts_score()
            end_info = {}
            if players[0].role == Role.PACMAN.value:
                end_info = {
                    "0": pacmanscore + end_error_score[0],
                    "1": ghostscore + end_error_score[1],
                }
            else:
                end_info = {
                    "0": ghostscore + end_error_score[0],
                    "1": pacmanscore + end_error_score[1],
                }

            send_game_end_info(
                json.dumps(end_info, ensure_ascii=False), json.dumps(end_state)
            )
            replay_file.close()
            time.sleep(0.5)
            exit(0)

if __name__ == "__main__":
    import traceback
    
    try:
        # 接收judger的初始化信息
        init_info = receive_init_info()
        replay_path = init_info["replay"]
        replay_dir = os.path.dirname(replay_path)
        if not os.path.exists(replay_dir):
            os.makedirs(replay_dir)
        replay_file = open(replay_path, 'w')
        # 设置随机种子
        try:
            seed = init_info["config"]["random_seed"]
        except:
            seed = random.randint(1, 100000000)

        env = PacmanEnv('logic')
        # 每局游戏唯一的游戏状态类，所有的修改应该在此对象中进行

        # playertype 0 表示未正常启动，1 表示本地 AI，2 表示网页播放器
        players = [Player(0,init_info["player_list"][0]),Player(1,init_info["player_list"][1])]

        if players[0].type == Type.ABNORMAL.value or players[1].type == Type.ABNORMAL.value:
            # 状态异常，未正常启动
            end_dict = env.render()
            end_dict["StopReason"] = "player quit unexpectedly"
            end_json = json.dumps(end_dict, ensure_ascii=False)
            replay_file.write(end_json + "\n")

            send_watch_info(end_json+'\n')

            if players[0].type == Type.PLAYER.value:
                send_to_judger(json.dumps(end_dict), 0)

            if players[1].type == Type.PLAYER.value:
                send_to_judger(json.dumps(end_dict), 1)

            end_state = json.dumps(
                ["OK" if players[0].type else "RE",
                    "OK" if players[1].type else "RE"]
            )
            end_error_score = [0, 0]
            if players[0].type == Type.ABNORMAL.value:
                end_error_score[0] = -ERROR_SCORE
            else:
                end_error_score[0] = NORMAL_SCORE
            if players[1].type == Type.ABNORMAL.value:
                end_error_score[1] = -ERROR_SCORE
            else:
                end_error_score[1] = NORMAL_SCORE
            end_info = {
                "0": end_error_score[0],
                "1": end_error_score[1],
            }
            send_game_end_info(json.dumps(end_info), end_state)
            replay_file.close()
            time.sleep(1)
            exit(0)

        # 第一回合发送座位信息
        state = 1
        send_round_config(MAX_PLAYER_TIME, MAX_LENGTH)
        send_round_info(
            state,
            [0],
            [0,1],
            ["0"+'\n',"1"+'\n'],
        )

        choose_max_round(env,players[0],players[1])

        game_continue = True
        level_change = False
        eat_all_beans = False
        first_round = True

        reset_info = env.reset().copy()
        reset_info["pacman_skill_status"] = reset_info["pacman_skill_status"].tolist()
        reset_info["board"] = reset_info["board"].tolist()
        reset_info["pacman_coord"] = reset_info["pacman_coord"].tolist()
        reset_info["ghosts_coord"] = [coord.tolist() for coord in reset_info["ghosts_coord"]]
        reset_info["portal_coord"] = reset_info["portal_coord"].tolist()
        
        init_json = json.dumps(reset_info, ensure_ascii=False)
        replay_file.write(init_json+'\n')

        send_watch_info(init_json+'\n')
        send_to_judger((init_json+'\n').encode("utf-8"), 0)
        send_to_judger((init_json+'\n').encode("utf-8"), 1)

        # 第一次接收ai信息，设定更长的time，为sdk的初始化预留时间
        for i in range(2) :
            state += 1
            if players[i].type == Type.AI.value:
                send_round_config(FIRST_MAX_AI_TIME, MAX_LENGTH)
            elif players[i].type == Type.PLAYER.value:
                send_round_config(MAX_PLAYER_TIME, MAX_LENGTH)

            # 不发送东西
            send_round_info(
                state,
                [players[i].id],
                [],
                [],
            )

            players[i].role , players[i].action = get_ai_info(env,players[i],players[1-i])
            send_to_judger(f"player {i} send info\n".encode("utf-8"), 1-i)
        
        # 两玩家同为卷王或同为幽灵 直接IA
        if players[0].role == players[1].role:
            return_dict = env.render()
            return_dict["StopReason"] = f"Same Role"
            replay_file.write(json.dumps(return_dict, ensure_ascii=False) + "\n")

            send_watch_info(json.dumps(return_dict, ensure_ascii=False)+'\n')

            if players[0].type == Type.PLAYER.value:
                send_to_judger(
                    json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), players[0].id
                )

            if players[1].type == Type.PLAYER.value:
                send_to_judger(
                    json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), players[1].id
                )

            end_state = ["IA", "IA"]
            end_error_score = [0, 0]
            end_error_score[0] = -ERROR_SCORE
            end_error_score[1] = -ERROR_SCORE

            end_info = {}
            end_info = {
                "0": end_error_score[0],
                "1": end_error_score[1],
            }

            send_game_end_info(
                json.dumps(end_info, ensure_ascii=False), json.dumps(end_state)
            )
            replay_file.close()
            time.sleep(0.5)
            exit(0)

        # 一局中包含三个state 1.接收吃豆人消息 2.接收幽灵消息 3.调用step
        while game_continue:
            if first_round != True :
                # 考察是否需要重新渲染，如果level发生改变，重置环境+获取初始化信息
                if level_change == True:
                    if env.get_level() >= MAX_LEVEL :
                        game_continue = False
                        
                    else :
                        reset_info = env.reset().copy()
                        reset_info["pacman_skill_status"] = reset_info["pacman_skill_status"].tolist()
                        reset_info["board"] = reset_info["board"].tolist()
                        reset_info["pacman_coord"] = reset_info["pacman_coord"].tolist()
                        reset_info["ghosts_coord"] = [coord.tolist() for coord in reset_info["ghosts_coord"]]
                        reset_info["portal_coord"] = reset_info["portal_coord"].tolist()
                        
                        init_json = json.dumps(reset_info, ensure_ascii=False)
                        replay_file.write(init_json+'\n')
                        send_watch_info(init_json+'\n')
                        send_to_judger((init_json+'\n').encode("utf-8"), 0)
                        send_to_judger((init_json+'\n').encode("utf-8"), 1)
                        level_change = False

                if not game_continue:
                    break
                
                # 接受吃豆人的消息和幽灵的消息
                for i in range(2) :
                    state += 1
                    if players[i].type == Type.AI.value:
                        send_round_config(MAX_AI_TIME, MAX_LENGTH)
                    elif players[i].type == Type.PLAYER.value:
                        send_round_config(MAX_PLAYER_TIME, MAX_LENGTH)

                    # 不发送东西
                    send_round_info(
                        state,
                        [players[i].id],
                        [],
                        [],
                    )

                    role , players[i].action = get_ai_info(env,players[i],players[1-i])
                    if role != players[i].role:
                        # 角色信息错误
                        return_dict = env.render()
                        return_dict["StopReason"] = (
                            f"Role error."
                        )
                        # 回放文件写入结束信息
                        replay_file.write(json.dumps(return_dict, ensure_ascii=False)+"\n")

                        send_watch_info(json.dumps(return_dict, ensure_ascii=False)+'\n')

                        if players[i].type == Type.PLAYER.value:
                            send_to_judger(
                                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), i
                            )

                        if players[1-i].type == Type.PLAYER.value:
                            send_to_judger(
                                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"),
                                1 - i,
                            )

                        end_state = ["OK", "OK"]
                        end_state[i] = "IA"
                        end_error_score = [0, 0]
                        end_error_score[i] = -ERROR_SCORE
                        end_error_score[1 - i] = NORMAL_SCORE

                        pacmanscore = env.get_pacman_score()
                        ghostscore = env.get_ghosts_score()
                        end_info = {}
                        if players[0].role == Role.PACMAN.value:
                            end_info = {
                                "0": pacmanscore + end_error_score[0],
                                "1": ghostscore + end_error_score[1],
                            }
                        else:
                            end_info = {
                                "0": ghostscore + end_error_score[0],
                                "1": pacmanscore + end_error_score[1],
                            }

                        send_game_end_info(
                            json.dumps(end_info, ensure_ascii=False), json.dumps(end_state)
                        )
                        replay_file.close()
                        time.sleep(0.5)
                        exit(0)
                    send_to_judger(f"player {i} send info\n".encode("utf-8"), 1-i)
            else :
                first_round = False

            # 调用step
            state += 1
            send_round_config(MAX_AI_TIME, MAX_LENGTH)
            
            if players[0].role == Role.PACMAN.value :
                # 0号玩家是吃豆人
                game_continue , info1 , info2 , level_change , eat_all_beans = interact(
                    env, players[0] , players[1]
                )
                send_round_info(
                    state,
                    [],
                    [players[0].id,players[1].id],
                    [info1+'\n',info2+'\n'],
                )
            else :
                # 1号玩家是吃豆人
                game_continue , info1 , info2 , level_change , eat_all_beans = interact(
                    env, players[1] , players[0]
                )
                send_round_info(
                    state,
                    [],
                    [players[1].id,players[0].id],
                    [info1+'\n',info2+'\n'],
                )

        end_state = json.dumps(
            ["OK", "OK"]
        )
        pacmanscore = env.get_pacman_score()
        ghostscore = env.get_ghosts_score()

        end_json = env.render()
        if eat_all_beans == True:
            end_json["StopReason"] = f"Pacman ate all the beans!!!"
        else:
            end_json["StopReason"] = f"time is up"
        end_info = {}
        if players[0].role == Role.PACMAN.value:
            end_info = {
                "0": pacmanscore,
                "1": ghostscore,
            }
        else:
            end_info = {
                "0": ghostscore,
                "1": pacmanscore,
            }
        if players[0].type == Type.PLAYER.value:
            send_to_judger(json.dumps(end_json, ensure_ascii=False).encode("utf-8"), 0)
        if players[1].type == Type.PLAYER.value:
            send_to_judger(json.dumps(end_json, ensure_ascii=False).encode("utf-8"), 1)
        
        send_watch_info(json.dumps(end_json, ensure_ascii=False)+'\n')

        replay_file.write(json.dumps(end_json, ensure_ascii=False) + "\n")
        send_game_end_info(json.dumps(end_info, ensure_ascii=False), end_state)
        replay_file.close()
        time.sleep(10)
        exit(0)

    except Exception as e:
        replay_file.write(traceback.format_exc())
        replay_file.write(str(e))
        replay_file.close()
        quit_running()

    replay_file.close()