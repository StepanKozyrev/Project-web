from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Command
import urllib.request
import json
import config


bot = Bot(config.api)
dp = Dispatcher(bot)

energy_list = []
food_list = []

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id, text="Привет, напиши /help, что бы узнать возможности бота")

@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id, text="Привет, напиши /calories + название продукта на аглийкс"
                                                              "ком, что бы узнать его характеристики(Пример: /calories "
                                                              "milk)\nЧтобы очистить список продуктов напиши /clear\nЧт"
                                                              "обы найти общее кол-во ккал напиши /allcalories")

@dp.message_handler(commands=['calories'])
async def calories_info(message: types.Message, command=Command):
    food = command.args
    source = urllib.request.urlopen(
        'https://api.nal.usda.gov/fdc/v1/foods/search?query='+food+'&pageSize=2&api_key=72wzzGCIy7uUxJMudJSjrhD2YU5OWbVbfYW3TPna').read()
    list_of_data = json.loads(source)
    data = {
        'fruit_name': str(list_of_data['foodSearchCriteria']['query']),
        'description': list_of_data['foods'][0]['description'],
        'protein': list_of_data['foods'][0]['foodNutrients'][0]['value'],
        'fat': list_of_data['foods'][0]['foodNutrients'][1]['value'],
        'carbohydrate': list_of_data['foods'][0]['foodNutrients'][2]['value'],
        'energy': list_of_data['foods'][0]['foodNutrients'][3]['value']
        }
    energy_list.append(data.get('energy'))
    food_list.append(data.get('fruit_name'))
    print(food)
    print(data)
    print(food_list)
    print(energy_list)
    await bot.send_message(chat_id=message.from_user.id, text='Продукт: '+data.get('fruit_name')+'\nОписание продукта: '+data.get('description')+'\nПитательные в-ва, г: белки: '+str(data.get('protein'))+', жиры: '+str(data.get('fat'))+', углеводы: '+str(data.get('carbohydrate'))+', ккал: '+str(data.get('energy'))+'\nЗначения рассчитаны на 100г. продукта')
    await bot.send_message(chat_id=message.from_user.id, text='Список продуктов:\n'+'\n'.join(food_list))

@dp.message_handler(commands=['clear'])
async def clear(message: types.Message):
    energy_list.clear()
    food_list.clear()
    await bot.send_message(chat_id=message.from_user.id, text='Список продуктов очистился!')

@dp.message_handler(commands=['allcalories'])
async def clear(message: types.Message):
    total = 0
    for number in energy_list:
        total += number
    await bot.send_message(chat_id=message.from_user.id, text='Общее кол-во ккал: '+str(total))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)