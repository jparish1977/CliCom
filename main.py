import asyncio
import aiohttp
import json
import os
import time
import re
from colorama import Fore, Style, init

init(autoreset=True)

SERVER_URL = "wss://clicom.onrender.com/ws"
SETTINGS_FILE = "user_settings.json"
MEMORY_FILE = "clicom_memory.json"

NAMED_COLORS = {
    1: ("Cyan", Fore.CYAN),
    2: ("Green", Fore.GREEN),
    3: ("Magenta", Fore.MAGENTA),
    4: ("Yellow", Fore.YELLOW),
    5: ("Blue", Fore.BLUE),
    6: ("White", Fore.LIGHTWHITE_EX)
}
SYSTEM_COLOR = Fore.LIGHTBLACK_EX + Style.BRIGHT

# === Utility Functions ===
def clear(): os.system("cls" if os.name=="nt" else "clear")
def save_json(path, data):
    with open(path,"w") as f: json.dump(data,f,indent=2)
def load_json(path,default): 
    return json.load(open(path,"r")) if os.path.exists(path) else default

def ansi_from_hex(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6: return Fore.WHITE
    r,g,b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    return f"\033[38;2;{r};{g};{b}m"

def pick_color():
    print("\nAvailable colors:")
    for num,(name,color) in NAMED_COLORS.items():
        print(f"{num}. {color}{name}")
    print("Or type a custom HEX color (e.g. #ff6600)")
    choice = input("Pick a color number or HEX: ").strip().lower()
    if re.match(r"^#[0-9a-f]{6}$", choice):
        return ansi_from_hex(choice), choice
    elif choice.isdigit() and int(choice) in NAMED_COLORS:
        name,color = NAMED_COLORS[int(choice)]
        return color,str(int(choice))
    else:
        print("Invalid input, using default white.")
        return Fore.WHITE,"6"

# === Banner Function ===
def show_banner(user_color=Fore.CYAN):
    clear()
    banner_lines = [
        f"{user_color}╔══════════════════════════════════════════════════════╗",
        f"{user_color}║{Fore.WHITE}   ██████╗██╗      ██████╗ ██╗   ██╗███╗   ███╗       {user_color}║",
        f"{user_color}║{Fore.WHITE}  ██╔════╝██║     ██╔═══██╗██║   ██║████╗ ████║       {user_color}║",
        f"{user_color}║{Fore.WHITE}  ██║     ██║     ██║   ██║██║   ██║██╔████╔██║       {user_color}║",
        f"{user_color}║{Fore.WHITE}  ██║     ██║     ██║   ██║██║   ██║██║╚██╔╝██║       {user_color}║",
        f"{user_color}║{Fore.WHITE}  ╚██████╗███████╗╚██████╔╝╚██████╔╝██║ ╚═╝ ██║       {user_color}║",
        f"{user_color}║{Fore.LIGHTWHITE_EX}               🌐 C L I C O M   C H A T 🌐            {user_color}║",
        f"{user_color}╚══════════════════════════════════════════════════════╝"
    ]
    for line in banner_lines:
        print(line)
        time.sleep(0.05)
    print(SYSTEM_COLOR + "\nConnecting to CLI Com servers...\n")
    time.sleep(0.5)

# === Chat Client ===
async def chat_client(name, color_code):
    memory = load_json(MEMORY_FILE,{"met":{},"sent":0,"received":0})
    print(SYSTEM_COLOR + f"🌐 Connecting as {name}...")
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(SERVER_URL) as ws:
            await ws.send_json({"type":"join","name":name})
            print(SYSTEM_COLOR+"✅ Connected! Type '/exit' to leave, '/stats' for stats, '/who' to see users.\n")

            async def recv():
                async for msg in ws:
                    if msg.type != aiohttp.WSMsgType.TEXT: continue
                    data = json.loads(msg.data)
                    t = data.get("type")
                    if t=="system":
                        print(SYSTEM_COLOR+"💡 "+data["text"])
                    elif t=="message":
                        sender,text,color = data['name'],data['text'],data.get('color','6')
                        if color.startswith("#"):
                            color_seq = ansi_from_hex(color)
                        else:
                            color_seq = NAMED_COLORS.get(int(color),(None,Fore.WHITE))[1]
                        met = "★ " if sender in memory["met"] else ""
                        if sender != name:
                            memory["received"]+=1
                            memory["met"][sender]=True
                            save_json(MEMORY_FILE,memory)
                        else:
                            memory["sent"]+=1
                            save_json(MEMORY_FILE,memory)
                        print(f"{color_seq}{met}{sender}: {text}{Style.RESET_ALL}")
                    elif t=="active_users":
                        users = ", ".join(data["users"])
                        print(SYSTEM_COLOR+f"👥 Active users: {users}")
                    elif t=="who":
                        print(SYSTEM_COLOR+f"📜 Users online: {', '.join(data['users'])}")

            async def send():
                while True:
                    msg = await asyncio.to_thread(input, f"{name}> ")
                    if msg.strip().lower()=="/exit":
                        await ws.send_json({"type":"leave","name":name})
                        save_json(MEMORY_FILE,memory)
                        print(SYSTEM_COLOR+"👋 Left the chat.")
                        await ws.close()
                        break
                    elif msg.strip().lower()=="/stats":
                        print(SYSTEM_COLOR+f"📊 Sent: {memory['sent']}, Received: {memory['received']}, Met: {len(memory['met'])}")
                    elif msg.strip().lower()=="/who":
                        await ws.send_json({"type":"who"})
                    elif msg.strip():
                        await ws.send_json({"type":"message","name":name,"color":color_code,"text":msg})

            await asyncio.gather(recv(),send())

# === Main Function ===
def main():
    settings = load_json(SETTINGS_FILE,{})
    if settings:
        name = settings.get("name","Guest")
        color_code = settings.get("color_code","6")
        user_color = ansi_from_hex(color_code) if color_code.startswith("#") else NAMED_COLORS.get(int(color_code),(None,Fore.CYAN))[1]
    else:
        name = input("Enter your chat name: ").strip() or "Guest"
        user_color, color_code = pick_color()
        save_json(SETTINGS_FILE,{"name":name,"color_code":color_code})

    show_banner(user_color)
    asyncio.run(chat_client(name,color_code))

if __name__=="__main__":
    main()
