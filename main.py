import sqlite3
import asyncio
import logging
from aiogram import Dispatcher, Bot, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import Token  


ADMIN_ID = 8386329255


class Database:
    def __init__(self):
        self.conn = sqlite3.connect("kinobot1.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS kinolar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nomi TEXT,
                tili TEXT,
                sifati TEXT,
                yili TEXT,
                davlat TEXT,
                url TEXT
            )
        """)
        
        self.conn.commit()

    def add_user(self, user_id, full_name):
        self.cursor.execute("INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", (user_id, full_name))
        self.conn.commit()

    def add_kino(self, nomi, tili, sifati, yili, davlat, url):
        self.cursor.execute("INSERT INTO kinolar (nomi, tili, sifati, yili, davlat, url) VALUES (?, ?, ?, ?, ?, ?)", 
                            (nomi, tili, sifati, yili, davlat, url))
        self.conn.commit()

    def get_kino(self, kino_id):
        self.cursor.execute("SELECT * FROM kinolar WHERE id = ?", (int(kino_id),))
        return self.cursor.fetchone()
    
    def get_all_users(self):
        self.cursor.execute("SELECT user_id FROM users")
        return self.cursor.fetchall()


db = Database()
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=Token)


class AddKinoState(StatesGroup):
    nomi = State()
    tili = State()
    sifati = State()
    yili = State()
    davlati = State()
    url = State()

class ReklamaState(StatesGroup):
    text = State()


@dp.message(Command("start"))
async def start_bot(message: Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    db.add_user(user_id, full_name)
    await message.answer("🎬 Salom! Kino botga xush kelibsiz!\n\n📥 Kino olish uchun kinoning ID raqamini yuboring.")


@dp.message(Command("addkino"))
async def start_add_kino(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Siz admin emassiz!")
    
    await message.answer("📌 Kino nomini kiriting:")
    await state.set_state(AddKinoState.nomi)

@dp.message(AddKinoState.nomi)
async def get_kino_nomi(message: Message, state: FSMContext):
    await state.update_data(nomi=message.text.strip())
    await message.answer("🌍 Kino tilini kiriting (Masalan: O'zbek tilida):")
    await state.set_state(AddKinoState.tili)


@dp.message(AddKinoState.tili)
async def get_kino_tili(message: Message, state: FSMContext):
    await state.update_data(tili=message.text.strip())
    await message.answer("💾 Kino sifatini kiriting (Masalan: 720p):")
    await state.set_state(AddKinoState.sifati)


@dp.message(AddKinoState.sifati)
async def get_kino_sifati(message: Message, state: FSMContext):
    await state.update_data(sifati=message.text.strip())
    await message.answer("📆 Kino yilini kiriting (Masalan: 2009):")
    await state.set_state(AddKinoState.yili)


@dp.message(AddKinoState.yili)
async def get_kino_yili(message: Message, state: FSMContext):
    await state.update_data(yili=message.text.strip())
    await message.answer("🌍 Kino qaysi davlatniki? (Masalan: AQSH, Buyuk Britaniya):")
    await state.set_state(AddKinoState.davlati)

@dp.message(AddKinoState.davlati)
async def get_kino_davlati(message: Message, state: FSMContext):
    await state.update_data(davlat=message.text.strip())
    await message.answer("🔗 Kino yuklash uchun video linkini yuboring:")
    await state.set_state(AddKinoState.url)


@dp.message(AddKinoState.url)
async def get_kino_url(message: Message, state: FSMContext):
    data = await state.get_data()
    nomi, tili, sifati, yili, davlat = data.values()
    url = message.text.strip()

    if not url.startswith("http"):
        return await message.answer("⚠ Noto‘g‘ri link! Iltimos, to‘g‘ri URL kiriting.")

    db.add_kino(nomi, tili, sifati, yili, davlat, url)
    await message.answer(f"✅ Kino qo‘shildi!\n\n🎬 *{nomi}*\n🇺🇿 *{tili}*\n💾 *{sifati}*\n📆 *{yili}*\n🌍 *{davlat}*\n🔗 {url}")
    
    await state.clear()  


@dp.message(lambda message: message.text.isdigit())
async def kinolar_bot(message: Message):
    kino_id = message.text.strip()
    kino = db.get_kino(kino_id)
    if kino:
        caption = f"🎬 {kino[1]}\n🇺🇿 {kino[2]}\n💾 {kino[3]}\n📆 {kino[4]}\n🌍 {kino[5]}"
        await message.answer_video(video=kino[6], caption=caption)
    else:
        await message.answer("❌ Bunday kino topilmadi.")


@dp.message(Command("reklama"))
async def reklama_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Siz admin emassiz!")
    
    await message.answer("📢 Reklama matnini kiriting:")
    await state.set_state(ReklamaState.text)

@dp.message(ReklamaState.text)
async def send_reklama(message: Message, state: FSMContext):
    reklama_matni = message.text
    foydalanuvchilar = db.get_all_users()
    for user in foydalanuvchilar:
        try:
            await bot.send_message(chat_id=user[0], text=reklama_matni)
            await asyncio.sleep(0.3)
        except Exception as e:
            logging.error(f"Xatolik: {e}")
    await message.reply("📢 Reklama yuborildi!")
    await state.clear()


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
