# -*- coding: utf-8 -*-

import agentscope
from agentscope.agents import UserAgent, DialogAgent
from agentscope.msghub import msghub
from agentscope.pipelines.functional import sequentialpipeline
from SystemAgent import SystemAgent

import os
import base64
import re
import time
import threading
import traceback
import gradio as gr
import modelscope_studio as mgr

from collections import defaultdict
from multiprocessing import Event
from typing import List
from utils import SYS_MSG_PREFIX, DEFAULT_AGENT_IMG_DIR
from utils import check_uuid, get_chat_msg, cycle_dots, send_chat_msg, send_player_input, send_player_msg
from utils import ResetException, CheckpointArgs
from MainLoop import main_loop

MAX_NUM_DISPLAY_MSG = 20
FAIL_COUNT_DOWN = 30


def init_uid_list():
    return []


def init_uid_dict():
    return {}


glb_signed_user = []
is_init = Event()

glb_history_dict = defaultdict(init_uid_list)
glb_doing_signal_dict = defaultdict(init_uid_dict)
glb_end_choosing_index_dict = defaultdict(lambda: -1)


# 图片本地路径转换为 base64 格式
def covert_image_to_base64(image_path):
    # 获得文件后缀名
    ext = image_path.split(".")[-1]
    if ext not in ["gif", "jpeg", "png"]:
        ext = "jpeg"

    with open(image_path, "rb") as image_file:
        # Read the file
        encoded_string = base64.b64encode(image_file.read())

        # Convert bytes to string
        base64_data = encoded_string.decode("utf-8")

        # 生成base64编码的地址
        base64_url = f"data:image/{ext};base64,{base64_data}"
        return base64_url


def format_cover_html(name="", bot_avatar_path="assets/bg.png"):
    config = {
        'name': f"逃出瘟疫危机",
        'description': '这是一款模拟消灭瘟疫的知识问答类游戏, 快来开始吧😊',
        'introduction_label': "<br>玩法介绍",
        'introduction_context': "在一个热闹的小镇上，居住着一群善良的人们，<br>"
                                "你是一名有梦想的药物学家，经常发明一些有用的药物，<br>"
                                "最近小镇上似乎发生了一些诡异的事情，经常有人莫名的死去，<br>"
                                "......<br>"
                                "通过研发新药物来解决瘟疫吧<br>"
                                "同时也要注意自己的健康，可不能让自己死掉啊😱"
    }
    image_src = covert_image_to_base64(bot_avatar_path)
    return f"""
<div class="bot_cover">
    <div class="bot_avatar">
        <img src={image_src} />
    </div>
    <div class="bot_name">{config.get("name", "逃出瘟疫危机")}</div>
    <div class="bot_desc">{config.get("description", "快来经营你的实验室吧")}</div>
    <div class="bot_intro_label">{config.get("introduction_label", "玩法介绍")}</div>
    <div class="bot_intro_ctx">
    {config.get("introduction_context", "玩法介绍")}</div>
</div>
"""


def get_chat(uid) -> List[List]:
    uid = check_uuid(uid)
    global glb_history_dict
    global glb_doing_signal_dict
    global glb_end_choosing_index_dict
    line = get_chat_msg(uid=uid)
    # TODO: 优化显示效果，目前存在输出显示跳跃的问题
    if line is not None:
        if line[0] and line[0]['text'] == "**i_am_researching**":
            line[0]['text'] = "研发中"
            glb_doing_signal_dict[uid] = line
        elif line[1] and line[1]['text'] == "**speak**":
            line[1]['text'] = "思考中"
            glb_doing_signal_dict[uid] = line
        elif line[1] and line[1]['text'] == "**end_choosing**":
            for idx in range(len(glb_history_dict[uid]) - 1, glb_end_choosing_index_dict[uid], -1):
                if (glb_history_dict[uid][idx][1] and "select-box" in glb_history_dict[uid][idx][1]['text']):
                    pattern = re.compile(r'(<select-box[^>]*?)>')
                    replacement_text = r'\1 disabled="True">'
                    glb_history_dict[uid][idx][1]['text'] = pattern.sub(replacement_text,
                                                                        glb_history_dict[uid][idx][1]['text'])
            glb_end_choosing_index_dict[uid] = len(glb_history_dict[uid]) - 1
        else:
            glb_history_dict[uid] += [line]
            glb_doing_signal_dict[uid] = []
    dial_msg, sys_msg = [], []
    for line in glb_history_dict[uid]:
        _, msg = line
        if isinstance(msg, dict):
            if SYS_MSG_PREFIX not in msg.get("text", ""):
                dial_msg.append(line)
            elif line:
                pattern = re.compile(r'^【系统】(?:\d+秒后进入小镇日常。|发生错误 .+?, 即将在\d+秒后重启)$', re.DOTALL)
                if pattern.match(msg.get("text", "")) and len(sys_msg) >= 1:
                    sys_msg[-1] = line
                else:
                    sys_msg.append(line)
        else:
            # User chat, format: (msg, None)
            dial_msg.append(line)
    if glb_doing_signal_dict[uid]:
        if glb_doing_signal_dict[uid][0]:
            text = cycle_dots(glb_doing_signal_dict[uid][0]['text'])
            glb_doing_signal_dict[uid][0]['text'] = text
        elif glb_doing_signal_dict[uid][1]:
            text = cycle_dots(glb_doing_signal_dict[uid][1]['text'])
            glb_doing_signal_dict[uid][1]['text'] = text

        dial_msg.append(glb_doing_signal_dict[uid])

    return dial_msg[-MAX_NUM_DISPLAY_MSG:], sys_msg[-MAX_NUM_DISPLAY_MSG:]


def reset_glb_var(uid):
    global glb_history_dict, glb_doing_signal_dict, glb_end_choosing_index_dict
    glb_history_dict[uid] = init_uid_list()
    glb_doing_signal_dict[uid] = init_uid_dict()
    glb_end_choosing_index_dict[uid] = -1


def fn_choice(data: gr.EventData, uid):
    uid = check_uuid(uid)
    send_player_input(data._data["value"], uid=uid)


if __name__ == "__main__":
    def init_game():
        if not is_init.is_set():
            register_configs = []
            tongyi_config = {
                "model_type": "dashscope_chat",
                "config_name": "qwen_72b",
                "model_name": "qwen-72b-chat",
                "api_key": "sk-cad0e865892b46cabd421c6758687983",
                "generate_args": {
                    "temperature": 0.5
                },
                "messages_key": "input"
            }
            register_configs.append(tongyi_config)
            agentscope.init(model_configs=register_configs,
                            logger_level="DEBUG")
            is_init.set()


    def check_for_new_session(uid):
        uid = check_uuid(uid)
        if uid not in glb_signed_user:
            glb_signed_user.append(uid)
            print("==========Signed User==========")
            print(f"Total number of users: {len(glb_signed_user)}")
            game_thread = threading.Thread(target=start_game, args=(uid,))
            game_thread.start()


    def start_game(uid):
        is_init.wait()
        uid = check_uuid(uid)
        args = CheckpointArgs()
        args.uid = uid

        while True:
            try:
                main_loop(args)
            except ResetException:
                print(f"重置成功：{uid} ")
            except Exception as e:
                trace_info = ''.join(traceback.TracebackException.from_exception(e).format())
                for i in range(FAIL_COUNT_DOWN, 0, -1):
                    send_chat_msg(
                        f"{SYS_MSG_PREFIX}发生错误 {trace_info}, 即将在{i}秒后重启",
                        uid=uid)
                    time.sleep(1)
            reset_glb_var(uid)


    with gr.Blocks(css="assets/app.css") as env:
        warning_html_code = """
        <div class="hint" style="background-color: rgba(255, 255, 0, 0.15); padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ffcc00;">
            <p>网络有可能不稳定造成界面错误，请刷新浏览器并点击 <strong>🔥 续写情缘</strong> 继续游戏。</p>
            <p>开始新的游戏请点击 <strong>🚀 新的冒险</strong>并刷新浏览器。</p>
        </div>
        """
        gr.HTML(warning_html_code)
        uuid = gr.Textbox(label='modelscope_uuid', visible=False)
        tabs = gr.Tabs(visible=True)
        with tabs:
            welcome_tab = gr.Tab('游戏界面', id=0)
            with welcome_tab:
                user_chat_bot_cover = gr.HTML(format_cover_html())
                with gr.Row():
                    with gr.Column():
                        new_button = gr.Button(value='🚀新的探险', )
                    with gr.Column():
                        resume_button = gr.Button(value='🔥续写情缘', )

        game_tabs = gr.Tabs(visible=False)
        with game_tabs:
            main_tab = gr.Tab('主界面', id=0)
            status_tab = gr.Tab('角色状态', id=1)
            formula_tab = gr.Tab('配方', id=2)
            with main_tab:
                with gr.Row():
                    with gr.Column(min_width=270):
                        chatbot = mgr.Chatbot(
                            elem_classes="app-chatbot",
                            label="Dialog",
                            show_label=False,
                            bubble_full_width=False,
                        )
                    with gr.Column(min_width=270):
                        chatsys = mgr.Chatbot(
                            elem_classes="app-chatbot",
                            label="系统栏",
                            show_label=True,
                            bubble_full_width=False,
                            layout="panel",
                        )

                with gr.Row():
                    with gr.Column():
                        user_chat_input = gr.Textbox(
                            label="user_chat_input",
                            placeholder="想说点什么",
                            show_label=False,
                        )

                with gr.Column():
                    with gr.Row():
                        send_button = gr.Button(value="📣发送")
            with status_tab:
                with gr.Row():
                    with gr.Column():
                        user = gr.Blocks()

            with gr.Row():
                return_welcome_button = gr.Button(value="↩️返回首页")


        def send_message(msg, uid):
            uid = check_uuid(uid)
            send_player_input(msg, uid=uid)
            send_player_msg(msg, "我", uid=uid)
            return ""


        def send_reset_message(uid):
            uid = check_uuid(uid)
            send_player_input("**Reset**", uid=uid)
            return ""


        def game_ui():
            return gr.update(visible=False), gr.update(visible=True)


        def welcome_ui():
            return gr.update(visible=True), gr.update(visible=False)


        new_button.click(game_ui, outputs=[tabs, game_tabs])
        resume_button.click(game_ui, outputs=[tabs, game_tabs])
        return_welcome_button.click(welcome_ui, outputs=[tabs, game_tabs])

        new_button.click(send_reset_message, inputs=[uuid]).then(check_for_new_session, inputs=[uuid])
        resume_button.click(check_for_new_session, inputs=[uuid])

        send_button.click(
            send_message,
            [user_chat_input, uuid],
            user_chat_input,
        )
        user_chat_input.submit(
            send_message,
            [user_chat_input, uuid],
            user_chat_input,
        )

        chatbot.custom(fn=fn_choice, inputs=[uuid])
        chatsys.custom(fn=fn_choice, inputs=[uuid])

        env.load(init_game)
        env.load(get_chat,
                 inputs=[uuid],
                 outputs=[chatbot, chatsys],
                 every=0.5)

    env.queue()
    env.launch()
