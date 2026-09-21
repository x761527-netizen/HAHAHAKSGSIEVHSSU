
import logging
import asyncio
import json
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# 1. ដំណើរការទាញយកទិន្នន័យពី File .env
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

# ទាញយក ADMIN_IDS រួចបំបែកវាជាបញ្ជីលេខ (List of Integers)
raw_admin_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in raw_admin_ids.split(",") if x.strip().isdigit()]

# បង្ហាញការព្រមានបើភ្លេចដាក់ API_TOKEN ក្នុង .env
if not API_TOKEN:
    raise ValueError("❌ រកមិនឃើញ API_TOKEN ក្នុងឯកសារ .env ទេ! សូមពិនិត្យមើលឯកសារ .env របស់អ្នកឡើងវិញ។")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

DB_FILE = "bot_database.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}, "keys": {}}

def save_data(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"កំហុសក្នុងការរក្សាទុកទិន្នន័យ: {e}")

db = load_data()
total_users_set = set(map(int, db.get("users", {}).keys()))
user_keys = {int(k): v for k, v in db.get("keys", {}).items()}
registered_users = set(map(int, db.get("users", {}).keys()))

def update_db():
    data = {
        "users": {str(uid): True for uid in registered_users},
        "keys": {str(uid): keys for uid, keys in user_keys.items()}
    }
    save_data(data)

class ChatState(StatesGroup):
    chatting_with_admin = State()
    waiting_for_name = State()

# បញ្ជី VLESS Configs សម្រាប់ Server
VLESS_CONFIGS = {
    "jp": "vless://c0254460-5f0c-4298-a0d2-6f413e1ccf1c@104.18.36.89:443?mode=auto&path=%2Fapi&security=tls&alpn=h2%2Chttp%2F1.1&encryption=none&host=jp.ngapiseik.com&fp=chrome&type=xhttp&sni=jp.ngapiseik.com#",
    "sg": "vless://c0254460-5f0c-4298-a0d2-6f413e1ccf1c@104.18.36.89:443?mode=auto&path=%2Fapi&security=tls&alpn=h3%2Ch2%2Chttp%2F1.1&encryption=none&host=sg.ngapiseik.com&fp=chrome&type=xhttp&sni=sg.ngapiseik.com#",
    "th": "vless://c0254460-5f0c-4298-a0d2-6f413e1ccf1c@104.18.36.89:443?security=reality&encryption=none&pbk=0VKg459-p0F_dfD2dkD_vui4mdNXKwL4lCGf1rDPQWo&headerType=none&fp=chrome&spx=%2Fdbad9a6e871c781&type=tcp&flow=xtls-rprx-vision&sni=google.com&sid=8ee747b1e178fb6d#",
    "default": "vless://c0254460-5f0c-4298-a0d2-6f413e1ccf1c@104.18.36.89:443?mode=auto&path=%2Fapi&security=tls&alpn=h2%2Chttp%2F1.1&encryption=none&host=vip.ngapiseik.com&fp=chrome&type=xhttp&sni=vip.ngapiseik.com#"
}

# 1. បញ្ជី Server Free (10 Keys)
SERVERS = {
    "jp": {"name": "🇯🇵 Japan Free (ជប៉ុន)", "cost": 10},
    "sg": {"name": "🇸🇬 Singapore Free (សិង្ហបុរី)", "cost": 10},
    "th": {"name": "🇹🇭 Thailand Free (ថៃ)", "cost": 10},
}

# 2. បន្ថែម Server ខ្មែរ ១០ Server (50 Keys)
for i in range(1, 11):
    SERVERS[f"kh_{i}"] = {"name": f"🇰🇭 Cambodia {i:02d} VIP (ខ្មែរ)", "cost": 50}

# 3. បន្ថែម VIP Servers អន្តរជាតិ (50 Keys)
vip_country_list = [
    ("us", "🇺🇸 USA VIP"), ("uk", "🇬🇧 UK VIP"), ("hk", "🇭🇰 Hong Kong VIP"),
    ("kr", "🇰🇷 Korea VIP"), ("de", "🇩🇪 Germany VIP"), ("fr", "🇫🇷 France VIP"),
    ("au", "🇦🇺 Australia VIP"), ("ca", "🇨🇦 Canada VIP"), ("tw", "🇹🇼 Taiwan VIP"),
    ("vn", "🇻🇳 Vietnam VIP"), ("id", "🇮🇩 Indonesia VIP"), ("my", "🇲🇾 Malaysia VIP"),
    ("ph", "🇵🇭 Philippines VIP"), ("in", "🇮🇳 India VIP"), ("br", "🇧🇷 Brazil VIP"),
    ("nl", "🇳🇱 Netherlands VIP"), ("se", "🇸🇪 Sweden VIP"), ("ch", "🇨🇭 Switzerland VIP"),
    ("fi", "🇫🇮 Finland VIP"), ("no", "🇳🇴 Norway VIP"), ("ru", "🇷🇺 Russia VIP"),
    ("ua", "🇺🇦 Ukraine VIP"), ("tr", "🇹🇷 Turkey VIP"), ("sa", "🇸🇦 Saudi Arabia VIP"),
    ("ae", "🇦🇪 UAE VIP"), ("za", "🇿🇦 South Africa VIP"), ("mx", "🇲🇽 Mexico VIP"),
    ("ar", "🇦🇷 Argentina VIP"), ("cl", "🇨🇱 Chile VIP"), ("co", "🇨🇴 Colombia VIP"),
    ("nz", "🇳🇿 New Zealand VIP"), ("pl", "🇵🇱 Poland VIP"), ("it", "🇮🇹 Italy VIP"),
    ("es", "🇪🇸 Spain VIP"), ("pt", "🇵🇹 Portugal VIP"), ("be", "🇧🇪 Belgium VIP"),
    ("at", "🇦🇹 Austria VIP"), ("dk", "🇩🇰 Denmark VIP")
]

for code, name in vip_country_list:
    SERVERS[code] = {"name": name, "cost": 50}

# បង្កើត Keyboard បង្ហាញ Server តាមទំព័រ
def build_server_keyboard(page: int = 1):
    items_per_page = 6
    keys = list(SERVERS.keys())
    total_pages = (len(keys) + items_per_page - 1) // items_per_page
    
    start = (page - 1) * items_per_page
    end = start + items_per_page
    page_keys = keys[start:end]
    
    keyboard = []
    
    row = []
    for k in page_keys:
        srv = SERVERS[k]
        btn_text = f"{srv['name']} ({srv['cost']} Keys)"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"srv_{k}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ ថយក្រោយ", callback_data=f"page_{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"📄 ទំព័រ {page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="ទៅមុខ ➡️", callback_data=f"page_{page+1}"))
        
    keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton(text="💬 ឆាតផ្ញើសារ/វ៉យ រកអ្នកគ្រប់គ្រង (Live Chat)", callback_data="start_support_chat")])
    keyboard.append([InlineKeyboardButton(text="ℹ️ ជំនួយ & ទំនាក់ទំនង", callback_data="help_info")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command(commands=["addkey"]))
async def admin_add_key(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ អ្នកមិនមែនជា អ្នកគ្រប់គ្រង (Admin) ទេ!")
        return
        
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ ទម្រង់មិនត្រឹមត្រូវ! សូមប្រើ៖ `/addkey [User_ID] [ចំនួនKey]`", parse_mode="Markdown")
        return
        
    try:
        target_user_id = int(args[1])
        add_amount = int(args[2])
    except ValueError:
        await message.answer("❌ User ID និង ចំនួន Key ត្រូវតែជាតួលេខ!")
        return
        
    current_keys = user_keys.get(target_user_id, 0)
    user_keys[target_user_id] = current_keys + add_amount
    update_db()
    
    await message.answer(f"✅ បានបន្ថែម **{add_amount} Keys** ជូន User ID: `{target_user_id}` ជោគជ័យ!\n🔑 Key សរុប៖ **{user_keys[target_user_id]} Keys**", parse_mode="Markdown")
    
    try:
        await bot.send_message(target_user_id, f"🎉 **អ្នកគ្រប់គ្រងបានបញ្ចូល Key ជូនអ្នកជោគជ័យហើយ!**\n💎 បានបន្ថែម៖ **+{add_amount} Keys**\n🔑 Key សរុបរបស់អ្នក៖ **{user_keys[target_user_id]} Keys**", parse_mode="Markdown")
    except Exception:
        pass

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    total_users_set.add(user_id)
    
    if user_id not in registered_users:
        registered_users.add(user_id)
        user_keys[user_id] = 10
    elif user_id not in user_keys:
        user_keys[user_id] = 0
        
    update_db()
    
    current_keys = user_keys.get(user_id, 0)
    total_count = len(total_users_set)
    
    welcome_caption = (
        f"⚡ **SYSTEM SECURE VIP VLESS BOT** ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👋 **សួស្តី! សូមស្វាគមន៍មកកាន់ប្រព័ន្ធបង្កើត VPN ស្វ័យប្រវត្តិ។**\n\n"
        f"💎 **លក្ខណៈពិសេសរបស់ Server VIP (50 Keys)៖**\n"
        f"• ប្រភេទ **VLESS** ល្បឿនលឿនអស្ចារ្យ\n"
        f"• ទំហំ Data ប្រើប្រាស់៖ **500 GB**\n"
        f"• រយៈពេលប្រើប្រាស់៖ **៣០ ថ្ងៃ**\n"
        f"• កម្រិត **Ping ទាប** ស្រួលលេងហ្គេម និងទស្សនាវីដេអូ\n\n"
        f"📊 **ស្ថិតិប្រព័ន្ធ៖**\n"
        f"👥 អ្នកប្រើប្រាស់សរុប៖ **{total_count} នាក់**\n"
        f"🔑 Key របស់អ្នក៖ **{current_keys} Keys**\n"
        f"🆔 User ID របស់អ្នក៖ `{user_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👇 **សូមជ្រើសរើសស៊ើវើ (Server) ខាងក្រោម៖**"
    )
    
    await message.answer(welcome_caption, reply_markup=build_server_keyboard(1), parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("page_"))
async def change_page(call: types.CallbackQuery):
    page = int(call.data.replace("page_", ""))
    await call.message.edit_reply_markup(reply_markup=build_server_keyboard(page))
    await call.answer()

@dp.callback_query(lambda c: c.data == "ignore")
async def ignore_click(call: types.CallbackQuery):
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("srv_"))
async def choose_server(call: types.CallbackQuery, state: FSMContext):
    srv_code = call.data.replace("srv_", "")
    srv_info = SERVERS.get(srv_code)
    user_id = call.from_user.id
    current_keys = user_keys.get(user_id, 0)
    
    if current_keys < srv_info['cost']:
        await call.answer(f"⛔️ អ្នកមាន Key មិនគ្រប់គ្រាន់ទេ! ស៊ើវើនេះត្រូវការ {srv_info['cost']} Keys។ សូមឆាតទៅអ្នកគ្រប់គ្រងដើម្បីទិញ Key បន្ថែម។", show_alert=True)
        return
        
    await state.update_data(selected_server=srv_code, key_cost=srv_info['cost'])
    await call.message.answer(f"📍 អ្នកបានជ្រើសរើស៖ **{srv_info['name']}**\n\n✏️ **សូមវាយបញ្ចូលឈ្មោះឯកសារ (Profile Name) របស់អ្នក៖**", parse_mode="Markdown")
    await state.set_state(ChatState.waiting_for_name)
    await call.answer()

@dp.message(ChatState.waiting_for_name)
async def generate_vless_config(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    custom_name = message.text.strip() if message.text else "VIP_User"
    data = await state.get_data()
    
    srv_code = data.get("selected_server")
    cost = data.get("key_cost")
    srv_info = SERVERS.get(srv_code)
    
    current_keys = user_keys.get(user_id, 0)
    if current_keys < cost:
        await message.answer("❌ Key មិនគ្រប់គ្រាន់ទេ!")
        await state.clear()
        return
        
    user_keys[user_id] = current_keys - cost
    update_db()
    
    base_config = VLESS_CONFIGS.get(srv_code, VLESS_CONFIGS["default"])
    final_config = f"{base_config}{custom_name}"
    
    success_text = (
        f"✅ **បង្កើត Config បានជោគជ័យ!**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📍 ស៊ើវើ៖ {srv_info['name']}\n"
        f"🏷 ឈ្មោះ៖ `{custom_name}`\n"
        f"📦 ទំហំ Data: **500 GB** | ⏳ រយៈពេល៖ **៣០ ថ្ងៃ**\n"
        f"🔑 Key នៅសល់៖ `{user_keys[user_id]} Keys`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📥 **Config របស់អ្នក៖**\n`{final_config}`"
    )
    await message.answer(success_text, parse_mode="Markdown")
    await state.clear()

@dp.callback_query(lambda c: c.data == "start_support_chat")
async def start_support_chat(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(ChatState.chatting_with_admin)
    chat_intro = (
        "💬 **ប្រព័ន្ធជជែកជាមួយអ្នកគ្រប់គ្រង (Live Chat)**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✍️ **អ្នកអាច៖**\n"
        "• វាយជាសារអក្សរ (Text)\n"
        "• ផ្ញើជាសារសំឡេង (Voice Message) 🎙\n"
        "• ផ្ញើរូបភាព ឬវិក្កយបត្រ (Photo/Document) 🖼\n\n"
        "សារ និងសំឡេងរបស់អ្នកនឹងផ្ញើទៅកាន់អ្នកគ្រប់គ្រងភ្លាមៗ!\n\n"
        "*(បើចង់ត្រឡប់ទៅមឺនុយដើមវិញ សូមចុច /start)*"
    )
    await call.message.answer(chat_intro, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(lambda c: c.data == "help_info")
async def process_help(call: types.CallbackQuery):
    help_text = (
        "ℹ️ **ជំនួយ & ទំនាក់ទំនង៖**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "• អ្នកទទួលបាន **10 Keys ឥតគិតថ្លៃ** ពេលចូលប្រើដំបូង។\n"
        "• Server Free (10 Keys): ជប៉ុន, សិង្ហបុរី, ថៃ\n"
        "• Server VIP (50 Keys): មាន **Server ខ្មែរ ១០ Server** និង VIP អន្តរជាតិជាច្រើន\n"
        "• គ្រប់ Server VIP (50 Keys) ទទួលបាន Data **500 GB** និងរយៈពេល **៣០ ថ្ងៃ**\n"
        "• អាចផ្ញើសារ ឬ **វ៉យ (Voice)** រកអ្នកគ្រប់គ្រងបានដោយសេរី។"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ ត្រឡប់ក្រោយ", callback_data="back_home")]
    ])
    await call.message.edit_text(help_text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(lambda c: c.data == "back_home")
async def back_home(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    current_keys = user_keys.get(user_id, 0)
    total_count = len(total_users_set)
    
    welcome_caption = (
        f"⚡ **SYSTEM SECURE VIP VLESS BOT** ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👋 **សួស្តី! សូមស្វាគមន៍មកកាន់ប្រព័ន្ធបង្កើត VPN ស្វ័យប្រវត្តិ។**\n\n"
        f"📊 **ស្ថិតិប្រព័ន្ធ៖**\n"
        f"👥 អ្នកប្រើប្រាស់សរុប៖ **{total_count} នាក់**\n"
        f"🔑 Key របស់អ្នក៖ **{current_keys} Keys**\n"
        f"🆔 User ID របស់អ្នក៖ `{user_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👇 **សូមជ្រើសរើសស៊ើវើ (Server) ខាងក្រោម៖**"
    )
    
    await call.message.edit_text(welcome_caption, reply_markup=build_server_keyboard(1), parse_mode="Markdown")
    await call.answer()

# ប្រព័ន្ធបញ្ជូនសារ / វ៉យ / រូបភាព ទៅមករវាងអតិថិជន និង Admin
@dp.message()
async def global_message_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    
    # ករណី Admin ជាអ្នក Reply សារ/វ៉យ/រូបភាព ទៅអតិថិជនវិញ
    if user_id in ADMIN_IDS:
        if message.reply_to_message:
            reply_text = message.reply_to_message.text or message.reply_to_message.caption or ""
            target_uid = None
            for line in reply_text.split("\n"):
                if "🆔 User ID:" in line:
                    try:
                        target_uid = int(line.replace("🆔 User ID:", "").strip().replace("`", ""))
                    except ValueError:
                        pass
            
            if target_uid:
                try:
                    if message.voice:
                        await bot.send_voice(target_uid, message.voice.file_id, caption="🎙 **សារសំឡេងពីអ្នកគ្រប់គ្រង (Admin)**", parse_mode="Markdown")
                    elif message.text:
                        await bot.send_message(target_uid, f"💬 **សារពីអ្នកគ្រប់គ្រង (Admin):**\n{message.text}", parse_mode="Markdown")
                    elif message.photo:
                        await bot.send_photo(target_uid, message.photo[-1].file_id, caption=f"🖼 **រូបភាពពី Admin:**\n{message.caption or ''}", parse_mode="Markdown")
                    elif message.document:
                        await bot.send_document(target_uid, message.document.file_id, caption=f"📁 **ឯកសារពី Admin:**\n{message.caption or ''}", parse_mode="Markdown")
                    
                    await message.answer("✅ បានផ្ញើតបទៅកាន់អតិថិជនជោគជ័យ!")
                except Exception as e:
                    await message.answer(f"❌ បរាជ័យក្នុងការផ្ញើ៖ {e}")
            else:
                await message.answer("⚠️ រកមិនឃើញ User ID ក្នុងសារនេះទេ! សូម Reply ចំសាររបស់អតិថិជនដែលមាន User ID។")
        return

    # ករណីអតិថិជនកំពុងស្ថិតក្នុង Chat ជាមួយ Admin (ផ្ញើសារ / វ៉យ / រូបភាព)
    if current_state == ChatState.chatting_with_admin.state:
        user = message.from_user
        user_info = (
            f"📩 **មានសារ/វ៉យ ថ្មីពីអតិថិជន៖**\n"
            f"👤 ឈ្មោះ៖ {user.full_name}\n"
            f"🏷 Username: @{user.username if user.username else 'គ្មាន'}\n"
            f"🆔 User ID: `{user.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                if message.voice:
                    await bot.send_voice(admin_id, message.voice.file_id, caption=f"{user_info}\n🎙 **សារសំឡេង (Voice)**", parse_mode="Markdown")
                elif message.text:
                    await bot.send_message(admin_id, f"{user_info}\n💬 សារ៖ {message.text}", parse_mode="Markdown")
                elif message.photo:
                    await bot.send_photo(admin_id, message.photo[-1].file_id, caption=f"{user_info}\n🖼 Caption: {message.caption or ''}", parse_mode="Markdown")
                elif message.document:
                    await bot.send_document(admin_id, message.document.file_id, caption=f"{user_info}\n📁 Caption: {message.caption or ''}", parse_mode="Markdown")
            except Exception as e:
                print(f"កំហុសក្នុងការផ្ញើទៅកាន់ admin {admin_id}: {e}")
                
        await message.answer("✅ **បានផ្ញើទៅកាន់អ្នកគ្រប់គ្រងរួចរាល់ហើយ!**\nសូមរង់ចាំការតបសារ ឬវ៉យ មកវិញ។ 🙏")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    