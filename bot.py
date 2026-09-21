import logging
import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

API_TOKEN = '8326047270:AAGsK8vfQ_CDNxFzRGMbtk9bhmJrNEjzJ2I'

# ដាក់ Telegram User ID ផ្ទាល់ខ្លួនของคุณ (អ្នកជា Admin តែម្នាក់គត់ដែលមានសិទ្ធិបញ្ចូល Key /addkey)
ADMIN_ID = 123456789  # <-- ផ្លាស់ប្តូរលេខនេះជា User ID របស់អ្នកពិតប្រាកដ

# Username សម្រាប់ឱ្យអតិថិជនទំនាក់ទំនងទិញ Key (បង្ហាញតែម្នាក់នេះគត់ក្នុង Bot)
CONTACT_ADMIN_USERNAME = "HeLyJing" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ឈ្មោះဖိုင်សម្រាប់រក្សាទុកទិន្នន័យកុំឱ្យបាត់បង់ពេល Restart Bot
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
        print(f"Error saving database: {e}")

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

class VPNState(StatesGroup):
    waiting_for_name = State()
    selected_server = State()
    key_cost = State()

VLESS_CONFIGS = {
    "jp": "vless://c0254460-5f0c-4298-a0d2-6f413e1ccf1c@104.18.36.89:443?mode=auto&path=%2Fapi&security=tls&alpn=h2%2Chttp%2F1.1&encryption=none&host=jp.ngapiseik.com&fp=chrome&type=xhttp&sni=jp.ngapiseik.com#",
    "sg": "vless://c0254460-5f0c-4298-a0d2-6f413e1ccf1c@104.18.36.89:443?mode=auto&path=%2Fapi&security=tls&alpn=h3%2Ch2%2Chttp%2F1.1&encryption=none&host=sg.ngapiseik.com&fp=chrome&type=xhttp&sni=sg.ngapiseik.com#",
    "th": "vless://c0254460-5f0c-4298-a0d2-6f413e1ccf1c@104.18.36.89:443?security=reality&encryption=none&pbk=0VKg459-p0F_dfD2dkD_vui4mdNXKwL4lCGf1rDPQWo&headerType=none&fp=chrome&spx=%2Fdbad9a6e871c781&type=tcp&flow=xtls-rprx-vision&sni=google.com&sid=8ee747b1e178fb6d#"
}

SERVERS = {
    "jp": {"name": "🇯🇵 Japan Server (ជប៉ុន)", "cost": 10},
    "sg": {"name": "🇸🇬 Singapore Server (សិង្ហបុរី)", "cost": 10},
    "th": {"name": "🇹🇭 Thailand Server (ថៃ)", "cost": 10},
    "kh": {"name": "🇰🇭 Cambodia Server (ខ្មែរ)", "cost": 50},
    "us": {"name": "🇺🇸 United States (អាមេរិក)", "cost": 50},
    "kr": {"name": "🇰🇷 South Korea (កូរ៉េខាងត្បូង)", "cost": 50},
    "vn": {"name": "🇻🇳 Vietnam (វៀតណាម)", "cost": 50},
    "my": {"name": "🇲🇾 Malaysia (ម៉ាឡេស៊ី)", "cost": 50},
    "id": {"name": "🇮🇩 Indonesia (ឥណ្ឌូនេស៊ី)", "cost": 50},
    "ph": {"name": "🇵🇭 Philippines (ហ្វីលីពីន)", "cost": 50},
    "cn": {"name": "🇨🇳 China (ចិន)", "cost": 50},
    "hk": {"name": "🇰🇭 Hong Kong (ហុងកុង)", "cost": 50},
    "tw": {"name": "🇹🇼 Taiwan (តៃវ៉ាន់)", "cost": 50},
    "in": {"name": "🇮🇳 India (ឥណ្ឌា)", "cost": 50},
    "gb": {"name": "🇬🇧 United Kingdom (អង់គ្លេស)", "cost": 50},
    "de": {"name": "🇩🇪 Germany (អាល្លឺម៉ង់)", "cost": 50},
    "fr": {"name": "🇫🇷 France (បារាំង)", "cost": 50},
    "ca": {"name": "🇨🇦 Canada (កាណាដា)", "cost": 50},
    "au": {"name": "🇦🇺 Australia (អូស្ត្រាលី)", "cost": 50},
    "ru": {"name": "🇷🇺 Russia (រុស្ស៊ី)", "cost": 50},
    "br": {"name": "🇧🇷 Brazil (ប្រេស៊ីល)", "cost": 50},
    "nl": {"name": "🇳🇱 Netherlands (ហុល្លង់)", "cost": 50},
    "ch": {"name": "🇨🇭 Switzerland (ស្វ៊ីស)", "cost": 50},
    "se": {"name": "🇸🇪 Sweden (ស៊ុយអែត)", "cost": 50},
    "ae": {"name": "🇦🇪 UAE (អារ៉ាប់រួម)", "cost": 50}
}

# មុខងារសម្រាប់ Admin តែម្នាក់គត់បញ្ចូល Key (វាយ: /addkey [User_ID] [ចំនួនKey])
@dp.message(Command(commands=["addkey"]))
async def admin_add_key(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ អ្នកមិនមែនជា Admin ទេ មិនអាចប្រើប្រាស់បញ្ជាទិញនេះបានឡើយ!")
        return
        
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ ទម្រង់មិនត្រឹមត្រូវ! សូមប្រើប្រាស់៖\n`/addkey [User_ID] [ចំនួនKey]`", parse_mode="Markdown")
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
    
    await message.answer(f"✅ បានបន្ថែម **{add_amount} Keys** ជូន User ID: `{target_user_id}` ជោគជ័យ!\n🔑 Key សរុបរបស់គាត់៖ **{user_keys[target_user_id]} Keys**", parse_mode="Markdown")
    
    try:
        await bot.send_message(target_user_id, f"🎉 **Admin បានបញ្ចូល Key ជូនអ្នកជោគជ័យហើយ!**\n💎 បានបន្ថែម៖ **+{add_amount} Keys**\n🔑 Key សរុបរបស់អ្នក៖ **{user_keys[target_user_id]} Keys**", parse_mode="Markdown")
    except Exception:
        pass

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    total_users_set.add(user_id)
    
    # ចងចាំ User ធ្លាប់ចូលហើយ មិនអាចយក 10 Keys ហ្វ្រីសាថ្មីបានទេ
    if user_id not in registered_users:
        registered_users.add(user_id)
        user_keys[user_id] = 10  # ហ្វ្រី 10 Keys លើកដំបូងបង្អស់
    elif user_id not in user_keys:
        user_keys[user_id] = 0
        
    update_db()
    
    current_keys = user_keys.get(user_id, 0)
    total_count = len(total_users_set)
    
    welcome_caption = (
        f"⚡ **SYSTEM SECURE VIP VLESS BOT** ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👋 **សួស្តី! សូមស្វាគមន៍មកកាន់ប្រព័ន្ធបង្កើត VPN ស្វ័យប្រវត្តិ។**\n\n"
        f"💎 **លក្ខណៈពិសេស៖**\n"
        f"• បង្កើតប្រភេទ **VLESS** ល្បឿនលឿនអស្ចារ្យ\n"
        f"• កម្រិត **Ping ទាប** ស្រួលលេងហ្គេម និងទស្សនាវីដេអូ\n"
        f"• ទំហំផ្ទុក **500 GB** | រយៈពេល **៣០ ថ្ងៃ**\n\n"
        f"📊 **ស្ថិតិប្រព័ន្ធ៖**\n"
        f"👥 អ្នកប្រើប្រាស់សរុប៖ **{total_count} នាក់**\n"
        f"🔑 Key របស់អ្នក៖ **{current_keys} Keys**\n"
        f"🆔 User ID របស់អ្នក៖ `{user_id}` *(ផ្ញើលេខនេះទៅ Admin ដើម្បីទិញ Key)*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👇 **សូមជ្រើសរើសស៊ើវើប្រទេសដែលអ្នកចង់បង្កើត៖**"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇯🇵 Japan (10 Keys)", callback_data="srv_jp"),
         InlineKeyboardButton(text="🇸🇬 Singapore (10 Keys)", callback_data="srv_sg")],
        [InlineKeyboardButton(text="🇹🇭 Thailand (10 Keys)", callback_data="srv_th"),
         InlineKeyboardButton(text="🌐 មើលស៊ើវើទាំងអស់ (២៥ ប្រទេស)", callback_data="all_servers")],
        [InlineKeyboardButton(text="💎 ទិញ Key បន្ថែម (២,០០០៛ = 1,000 Keys)", callback_data="buy_key"),
         InlineKeyboardButton(text="ℹ️ ជំនួយ & ទំនាក់ទំនង", callback_data="help_info")]
    ])
    
    await message.answer(welcome_caption, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "all_servers")
async def show_all_servers(call: types.CallbackQuery):
    buttons = []
    row = []
    for code, info in SERVERS.items():
        row.append(InlineKeyboardButton(text=f"{info['name']} ({info['cost']}K)", callback_data=f"srv_{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ ត្រឡប់ក្រោយ", callback_data="back_home")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("🌍 **បញ្ជីស៊ើវើទាំង ២៥ ប្រទេស៖**\nសូមជ្រើសរើសប្រទេសដែលអ្នកចង់បង្កើត៖", reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("srv_"))
async def choose_server(call: types.CallbackQuery, state: FSMContext):
    srv_code = call.data.replace("srv_", "")
    srv_info = SERVERS.get(srv_code)
    
    user_id = call.from_user.id
    current_keys = user_keys.get(user_id, 0)
    
    if current_keys < srv_info['cost']:
        await call.answer(f"⛔️ អ្នកមាន Key មិនគ្រប់គ្រាន់ទេ! ស៊ើវើនេះត្រូវការ {srv_info['cost']} Keys។ សូមទិញ Key បន្ថែមជាមួយ Admin @{CONTACT_ADMIN_USERNAME}!", show_alert=True)
        return
        
    await state.update_data(selected_server=srv_code, key_cost=srv_info['cost'])
    
    await call.message.answer(f"📍 អ្នកបានជ្រើសរើស៖ **{srv_info['name']}** (ចំណាយ {srv_info['cost']} Keys)\n\n✏️ **សូមវាយបញ្ចូលឈ្មោះឯកសារ (Profile Name) របស់អ្នក៖**\n*(ឧទាហរណ៍៖ MyGame-VPN ឬ ឈ្មោះរបស់អ្នក)*", parse_mode="Markdown")
    await VPNState.waiting_for_name.set() if hasattr(VPNState.waiting_for_name, 'set') else await state.set_state(VPNState.waiting_for_name)
    await call.answer()

@dp.message(VPNState.waiting_for_name)
async def generate_vless_config(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    custom_name = message.text.strip()
    data = await state.get_data()
    
    srv_code = data.get("selected_server")
    cost = data.get("key_cost")
    srv_info = SERVERS.get(srv_code)
    
    current_keys = user_keys.get(user_id, 0)
    if current_keys < cost:
        await message.answer(f"❌ Key របស់អ្នកមិនគ្រប់គ្រាន់សម្រាប់ការបង្កើតទេ! សូមទាក់ទង @{CONTACT_ADMIN_USERNAME} ។")
        await state.clear()
        return
        
    # បង្ហាញសកម្មភាព Bot កំពុងសរសេរឆ្លើយតប (Typing Action)
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await asyncio.sleep(1.5)
    
    user_keys[user_id] = current_keys - cost
    update_db()
    
    remaining_keys = user_keys[user_id]
    
    base_config = VLESS_CONFIGS.get(srv_code, VLESS_CONFIGS["sg"])
    final_config = f"{base_config}{custom_name}"
    
    success_text = (
        f"✅ **បង្កើត VLESS Config បានដោយជោគជ័យ!**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📍 **ស៊ើវើ:** {srv_info['name']}\n"
        f"🏷 **ឈ្មោះឯកសារ:** `{custom_name}`\n"
        f"⚙️ **ប្រភេទ:** VLESS (High Speed)\n"
        f"📊 **ទំហំផ្ទុក:** `500 GB`\n"
        f"⏳ **រយៈពេល:** `៣០ ថ្ងៃ`\n"
        f"📉 **កាត់ Key អស់:** `-{cost} Keys`\n"
        f"🔑 **Key សល់ក្នុងគណនី:** `{remaining_keys} Keys`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📥 **Config របស់អ្នក៖**\n`{final_config}`\n\n"
        f"💡 *ចម្លងអត្ថបទខាងលើដាក់ចូលក្នុងកម្មវិធី V2RayNG ជាការស្រេច!*"
    )
    
    await message.answer(success_text, parse_mode="Markdown")
    await state.clear()

@dp.callback_query(lambda c: c.data == "buy_key")
async def process_buy_key(call: types.CallbackQuery):
    user_id = call.from_user.id
    buy_text = (
        "💎 **ទិញ Key / បន្ថែម VIP Server**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "💰 **តម្លៃពិសេស៖** ២,០០០ រៀល ទទួលបាន **១,០០០ Keys**!\n\n"
        "📱 **វិធីទិញ៖**\n"
        f"1. កូពី User ID របស់អ្នក៖ `{user_id}`\n"
        f"2. ទំនាក់ទំនងផ្ញើលុយ និង User ID ទៅកាន់ Admin ខាងក្រោម៖\n\n"
        f"👉 **Telegram Admin:** @{CONTACT_ADMIN_USERNAME}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💬 ឆាតរក Admin (@{CONTACT_ADMIN_USERNAME})", url=f"https://t.me/{CONTACT_ADMIN_USERNAME}")],
        [InlineKeyboardButton(text="⬅️ ត្រឡប់ក្រោយ", callback_data="back_home")]
    ])
    await call.message.edit_text(buy_text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(lambda c: c.data == "help_info")
async def process_help(call: types.CallbackQuery):
    help_text = (
        "ℹ️ **ការណែនាំពីប្រព័ន្ធ Bot៖**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "1. អ្នកទទួលបាន **10 Keys** ស្រាប់ពេលចូល Bot ដំបូង។\n"
        "2. ស៊ើវើ ជប៉ុន, សិង្ហបុរី និងថៃ ចំណាយត្រឹម **10 Keys** (បាន 500GB, 30ថ្ងៃ)។\n"
        "3. ស៊ើវើប្រទេសផ្សេងទៀតចំណាយ **50 Keys**។\n"
        f"4. ទំនាក់ទំនងទិញ Key បន្ថែមជាមួយ @{CONTACT_ADMIN_USERNAME} ។"
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
        f"👇 **សូមជ្រើសរើសស៊ើវើប្រទេសដែលអ្នកចង់បង្កើត៖**"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇯🇵 Japan (10 Keys)", callback_data="srv_jp"),
         InlineKeyboardButton(text="🇸🇬 Singapore (10 Keys)", callback_data="srv_sg")],
        [InlineKeyboardButton(text="🇹🇭 Thailand (10 Keys)", callback_data="srv_th"),
         InlineKeyboardButton(text="🌐 មើលស៊ើវើទាំងអស់ (២៥ ប្រទេស)", callback_data="all_servers")],
        [InlineKeyboardButton(text="💎 ទិញ Key បន្ថែម (២,០០០៛ = 1,000 Keys)", callback_data="buy_key"),
         InlineKeyboardButton(text="ℹ️ ជំនួយ & ទំនាក់ទំនង", callback_data="help_info")]
    ])
    await call.message.edit_text(welcome_caption, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
