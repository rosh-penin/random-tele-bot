import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import requests

TOKEN = os.getenv('TG_TOKEN', None)
WEATHER_API = os.getenv('WR_TOKEN', None)
EXCHANGE_API = os.getenv('EX_TOKEN', None)

bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class MyStates(StatesGroup):
    clean = State()
    money = State()


class SomethingGoneWrong(Exception):
    pass


async def error_message(message):
    await message.reply('unexpected error, sorry.')


async def get_response(url, message):
    response = requests.get(url)
    if not response or response.status_code != 200:
        await error_message(message)
        raise SomethingGoneWrong
    response = response.json()
    if 'weather' not in response and 'success' not in response:
        await error_message(message)
        raise SomethingGoneWrong
    return response


@dp.message_handler(lambda message: message.text == 'All available currencies', state=MyStates.money)
async def currency_show_all(message: types.Message, state: FSMContext):
    url = f'https://api.apilayer.com/exchangerates_data/symbols?apikey={EXCHANGE_API}'
    response = await get_response(url, message)
    symbols = response['symbols']
    res_mes = ''
    for key, value in symbols.items():
        res_mes += f'{key}: {value}\n'
    await message.reply(res_mes)


@dp.message_handler(state=MyStates.money)
async def currency_convert(message: types.Message, state: FSMContext):
    await MyStates.clean.set()
    am, c_f, c_t = message.text.split()
    url = f'https://api.apilayer.com/exchangerates_data/convert?to={c_t}&from={c_f}&amount={am}&apikey={EXCHANGE_API}'
    response = await get_response(url, message)
    amount_req = response['query']['amount']
    cur_fr = response['query']['from']
    cur_to = response['query']['to']
    amount_res = response['result']
    await message.reply(
        f'{amount_req} {cur_fr} converts to\n'
        f'{amount_res} {cur_to}'
    )


@dp.message_handler(lambda message: message.text == 'Convert Money')
async def currency_convert_start(message: types.Message):
    await MyStates.money.set()
    sym_but = types.KeyboardButton('All available currencies')
    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    ).add(sym_but)
    await message.reply('Type the currency like this (AMOUNT CURRENCY_FROM CURRENCY_TO)', reply_markup=kb)


@dp.message_handler(content_types=['location'])
async def handle_location(message: types.Message):
    lat, lon = message.location.latitude, message.location.longitude
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API}&units=metric'
    response = await get_response(url, message)
    city = response['name']
    weather = response['weather'][0]['main'] + ', ' + response['weather'][0]['description']
    temp = response['main']['temp']
    temp_feels = response['main']['feels_like']
    await message.reply(
        f'Your city: {city}\n'
        f'Current weather: {weather}\n'
        f'Temperature: {temp}\n'
        f'Feels like: {temp_feels}'
    )


@dp.message_handler(state='*')
async def start_message(message: types.Message, state: FSMContext):
    wea_but = types.KeyboardButton('Weather', request_location=True)
    cur_but = types.KeyboardButton('Convert Money')
    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    ).add(wea_but, cur_but)
    await message.reply('Hello. I am RandomBot.\nSelect something from the buttons.', reply_markup=kb)


if __name__ == '__main__':
    if None in (TOKEN, WEATHER_API, EXCHANGE_API):
        raise Exception('No token')
    executor.start_polling(dp, skip_updates=True)
