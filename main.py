import os

from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv('TOKEN', None)

bot = Bot(TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def start_message(message: types.message):
    await message.reply('Hello. I am RandomBot.\nSelect something from the buttons.')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)