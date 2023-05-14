from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
import urllib.request
import json
import config
import sqlite3
from googletrans import Translator


bot = Bot(config.api)
dp = Dispatcher(bot)

cb = CallbackData('keyboard', 'action')


keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('Найти калории', callback_data='3')],
    [InlineKeyboardButton('Всего калорий', callback_data='2')],
    [InlineKeyboardButton('Очистить список', callback_data='1')]
])


@dp.message_handler(commands=['start'], content_types=["text"])
async def send_welcome(message: types.Message):

    connect = sqlite3.connect('food.db')
    cursor = connect.cursor()

    people_id = message.from_user.id
    cursor.execute(f"SELECT id FROM food WHERE id = {people_id}")
    data = cursor.fetchone()
    if data is None:
        user_id = [message.from_user.id]
        cursor.execute("INSERT INTO food(id) VALUES(?);", user_id)
        connect.commit()

    await bot.send_message(message.from_user.id, text="Привет, напиши /help, что бы узнать возможности бота")


@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.from_user.id, text="Привет, напиши /calories "
                                                              ", что бы начать подсчет кол-ва калорий"
                                                              "\nЧтобы очистить список продуктов напиши /clear\nЧт"
                                                              "обы найти общее кол-во ккал напиши /allcalories", reply_markup=keyboard)


@dp.message_handler(commands=['clear'])
async def clear(message: types.Message):
    connect = sqlite3.connect('food.db')
    cursor = connect.cursor()
    default_calories = 0
    default_food = 'Список_продуктов'
    people_id = message.from_user.id
    cursor.execute(f"UPDATE food SET allcalories ='{default_calories}'  WHERE id = '{people_id}'")
    cursor.execute(f"UPDATE food SET foodlist ='{default_food}'  WHERE id = '{people_id}'")
    connect.commit()

    await bot.send_message(chat_id=message.from_user.id, text='Список продуктов очистился!')


@dp.message_handler(commands=['allcalories'])
async def allcalories(message: types.Message):
    people_id = message.from_user.id
    connect = sqlite3.connect('food.db')
    cursor = connect.cursor()
    cursor.execute(f"SELECT allcalories FROM food WHERE id = '{people_id}'")
    all_calories = cursor.fetchone()
    all_cal_list = list(all_calories)
    await bot.send_message(chat_id=message.from_user.id, text='Общее кол-во ккал: ' + str(round(all_cal_list[0])))


@dp.message_handler(commands=['calories'])
async def calories_info(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id, text="Введите название продукта и его количество в гр.:")

    @dp.message_handler()
    async def save_product(message: types.Message):
        product = message.text.split()
        if len(product) != 2:
            product.append('100')
            await bot.send_message(chat_id=message.from_user.id, text='Кол-во продукта не указано. Значение по умолчанию 100гр.')

        ratio = int(product[1])/100
        translator = Translator()
        result = translator.translate(product[0], src='ru', dest='en')
        food = result.text
        print(food)

        source = urllib.request.urlopen(
            f'https://api.nal.usda.gov/fdc/v1/foods/search?query={food}&pageSize=2&api_key=72wzzGCIy7uUxJMudJSjrhD2YU5OWbVbfYW3TPna').read()
        list_of_data = json.loads(source)
        lenght = len(list_of_data['foods'][0]['foodNutrients'])
        print(lenght)
        data = {}

        for i in range(0, lenght):
            if list_of_data['foods'][0]['foodNutrients'][i]['nutrientName'] == "Energy":
                data['energy'] = list_of_data['foods'][0]['foodNutrients'][i]['value'] * ratio

            elif list_of_data['foods'][0]['foodNutrients'][i]['nutrientName'] == "Total lipid (fat)":
                data['fat'] = list_of_data['foods'][0]['foodNutrients'][i]['value'] * ratio

            elif list_of_data['foods'][0]['foodNutrients'][i]['nutrientName'] == "Carbohydrate, by difference":
                data['carbohydrate'] = list_of_data['foods'][0]['foodNutrients'][i]['value'] * ratio

            elif list_of_data['foods'][0]['foodNutrients'][i]['nutrientName'] == "Protein":
                data['protein'] = list_of_data['foods'][0]['foodNutrients'][i]['value'] * ratio

        print(data)
        connect = sqlite3.connect('food.db')
        cursor = connect.cursor()

        people_id = message.from_user.id
        cursor.execute(f"SElECT foodlist FROM food WHERE id = '{people_id}'")
        string_food = cursor.fetchone()

        data_food = list(string_food)
        data_food.append(product[0])
        more_food = ', '.join(data_food)
        cursor.execute(f"UPDATE food SET foodlist = '{more_food}' WHERE id = '{people_id}'")

        cursor.execute(f"SElECT allcalories FROM food WHERE id = '{people_id}'")
        string_calories = cursor.fetchone()

        data_calories = list(string_calories)
        data_calories.append(data.get('energy'))

        more_calories = sum(data_calories)
        cursor.execute(f"UPDATE food SET allcalories = '{more_calories}' WHERE id = '{people_id}'")

        connect.commit()

        cursor.execute(f"SElECT foodlist FROM food WHERE id = '{people_id}'")
        print_food = cursor.fetchone()
        string_list = list(print_food)[0][18::]
        print(string_list)

        await bot.send_message(chat_id=message.from_user.id,
                               text='Продукт: ' + product[0] +
                                    '\nПитательные в-ва, г: белки: '+str(round(data.get('protein')))+', жиры: '+str(round(data.get('fat')))+
                                    ', углеводы: '+str(round(data.get('carbohydrate')))+', ккал: '+str(round(data.get('energy')))+
                                    '\nЗначения рассчитаны на '+product[1]+'гр. продукта')
        await bot.send_message(chat_id=message.from_user.id, text='Список продуктов:\n'+string_list, reply_markup=keyboard)


@dp.callback_query_handler(lambda callback: True)
async def callback_inline(callback: types.CallbackQuery):
    if callback.data == '1':
        await clear(callback)
    elif callback.data == '2':
        await allcalories(callback)
    elif callback.data == '3':
        await calories_info(callback)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
