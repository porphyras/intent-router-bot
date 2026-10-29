from sqlalchemy import select, text

from app.config import get_settings
from app.db.base import Base
from app.db.models import FAQItem, Product
from app.db.session import SessionLocal, engine


PRODUCTS = [
    {'name': 'Детская зубная паста со вкусом клубники', 'sku': '1001', 'price_partner': 150, 'pv': 0.2, 'quantity': 25, 'category': 'Гигиена', 'aliases': 'детская паста,зубная паста,клубника'},
    {'name': 'Зубная щётка мягкая (2 шт.)', 'sku': '1002', 'price_partner': 120, 'pv': 0.2, 'quantity': 40, 'category': 'Гигиена', 'aliases': 'зубная щетка,щетка,мягкая щетка'},
    {'name': 'Ополаскиватель для полости рта 300 мл', 'sku': '1003', 'price_partner': 290, 'pv': 0.2, 'quantity': 12, 'category': 'Гигиена', 'aliases': 'ополаскиватель,полость рта'},
    {'name': 'Зубная нить мятная', 'sku': '1004', 'price_partner': 90, 'pv': 0.1, 'quantity': 30, 'category': 'Гигиена', 'aliases': 'зубная нить,нить для зубов'},
    {'name': 'Освежитель воздуха «Лаванда»', 'sku': '2001', 'price_partner': 380, 'pv': 1, 'quantity': 9, 'category': 'Дом', 'aliases': 'освежитель воздуха,лаванда'},
    {'name': 'Зелёный чай с жасмином', 'sku': '3001', 'price_partner': 420, 'pv': 0.2, 'quantity': 16, 'category': 'Напитки', 'aliases': 'зеленый чай,жасмин,чай'},
    {'name': 'Чёрный чай с бергамотом', 'sku': '3002', 'price_partner': 410, 'pv': 0.2, 'quantity': 18, 'category': 'Напитки', 'aliases': 'черный чай,бергамот,чай'},
    {'name': 'Увлажняющий гель с алоэ вера 180 г', 'sku': '4001', 'price_partner': 360, 'pv': 0.7, 'quantity': 25, 'category': 'Уход', 'aliases': 'алоэ вера,aloe vera,гель'},
    {'name': 'Мыло с маслом ши', 'sku': '4002', 'price_partner': 140, 'pv': 0.2, 'quantity': 100, 'category': 'Уход', 'aliases': 'мыло,масло ши,shea butter'},
    {'name': 'Гель для укладки волос 80 мл', 'sku': '4003', 'price_partner': 180, 'pv': 0.1, 'quantity': 17, 'category': 'Уход', 'aliases': 'гель для волос,укладка'},
    {'name': 'Детские трусики-подгузники, размер L (32 шт.)', 'sku': '5001', 'price_partner': 1200, 'pv': 0.5, 'quantity': 8, 'category': 'Дети', 'aliases': 'подгузники,трусики,pampers,l'},
    {'name': 'Детские трусики-подгузники, размер M (38 шт.)', 'sku': '5002', 'price_partner': 1250, 'pv': 0.5, 'quantity': 8, 'category': 'Дети', 'aliases': 'подгузники,трусики,pampers,m'},
    {'name': 'Солнцезащитные очки', 'sku': '6001', 'price_partner': 1900, 'pv': 7, 'quantity': 20, 'category': 'Аксессуары', 'aliases': 'очки,солнцезащитные очки'},
    {'name': 'Твёрдые духи «Роза»', 'sku': '7001', 'price_partner': 430, 'pv': 0.5, 'quantity': 33, 'category': 'Парфюм', 'aliases': 'духи,роза,твердые духи'},
]


def regular_price(price_partner: float) -> float:
    multiplier = get_settings().partner_price_multiplier
    return round(price_partner * multiplier, 2)


FAQS = [
    {
        'intent': 'greeting',
        'question_patterns': 'привет;здравствуйте;добрый день;добрый вечер;здарова;hi;hello',
        'answer_text': 'Здравствуйте! Я помогу с поиском товара, бронью, заказом или общим вопросом по магазину. Напишите ваш вопрос.',
    },
    {
        'intent': 'gratitude',
        'question_patterns': 'спасибо;благодарю;большое спасибо',
        'answer_text': 'Пожалуйста! Обращайтесь, если будут ещё вопросы.',
    },
    {
        'intent': 'address',
        'question_patterns': 'где вы находитесь;адрес;где находится сц;как добраться;сервисный центр',
        'answer_text': 'Мы находимся по адресу: г. Новосибирск, ул. Примерная, 1 (демо-адрес).',
    },
    {
        'intent': 'schedule',
        'question_patterns': 'график;режим работы;работаете ли вы сегодня;со скольки;до скольки;когда открыты;откроетесь;открываетесь;во сколько работаете;сегодня работаете;в каком часу',
        'answer_text': 'График работы: вт-суб с 14:00 до 19:00. Воскресенье и понедельник — выходной.',
    },
    {
        'intent': 'delivery',
        'question_patterns': 'доставка;как доставляете;можно доставку',
        'answer_text': 'Доставка выполняется через OZON, WILDBERRIES и Яндекс Доставку. После принятия заказа детали доставки согласует менеджер.',
    },
    {
        'intent': 'payment',
        'question_patterns': 'оплата;как оплатить;способы оплаты',
        'answer_text': 'Оплатой занимается менеджер после сборки заказа и расчёта стоимости доставки.',
    },
    {
        'intent': 'guarantee',
        'question_patterns': 'гарантия;есть гарантия',
        'answer_text': 'На этот ассортимент отдельная гарантия не предусмотрена.',
    },
    {
        'intent': 'returns',
        'question_patterns': 'возврат;можно вернуть',
        'answer_text': 'Возврат не предусмотрен.',
    },
    {
        'intent': 'pickup',
        'question_patterns': 'самовывоз;можно забрать;заберу сам',
        'answer_text': 'Самовывоз есть. Можно заранее заказать товары, поставить их в бронь и затем приехать забрать.',
    },
    {
        'intent': 'contacts',
        'question_patterns': 'контакты;телефон;номер;как связаться',
        'answer_text': 'Контакт для связи: +7 000 000-00-00 (демо-номер).',
    },
]


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if engine.dialect.name == 'postgresql':
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm'))
            await conn.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS ix_products_name_trgm '
                    'ON products USING gin (name gin_trgm_ops)'
                )
            )
            await conn.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS ix_products_sku_trgm '
                    'ON products USING gin (sku gin_trgm_ops)'
                )
            )

    async with SessionLocal() as session:
        products_count = len((await session.execute(select(Product.id))).scalars().all())
        if products_count == 0:
            for item in PRODUCTS:
                session.add(Product(**item, price_regular=regular_price(item['price_partner'])))

        faqs_count = len((await session.execute(select(FAQItem.id))).scalars().all())
        if faqs_count == 0:
            for item in FAQS:
                session.add(FAQItem(**item))

        await session.commit()
