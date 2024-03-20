import agentscope
from agentscope.agents import UserAgent, DialogAgent
from agentscope.pipelines.functional import sequentialpipeline
from MyAgent import MyAgent

agentscope.init(
    model_configs="./config/qwen_72b_chat.json",
    save_log=True
)

def main() -> None:
    dialogAgent = MyAgent(name="小娜", model_config_name="qwen_72b", sys_prompt="你是一个二次元的萌妹子")
    userAgent = UserAgent()
    
    x = None
    while x is None or x.content != "exit":
        x = sequentialpipeline([dialogAgent, userAgent], x)
        
if __name__ == "__main__":
    main()
