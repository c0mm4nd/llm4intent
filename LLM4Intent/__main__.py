import dotenv
from LLM4Intent.mas import start_agents

dotenv.load_dotenv()

def start():
    analyze_result = start_agents()
    print("final result:\t", analyze_result)

if __name__ == "__main__":
    start()
