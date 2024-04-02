
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

DATABASE_URL = "sqlite:///mydatabase.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class NewUser(BaseModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=150)
    email: str = Field(max_length=150)
    password: str = Field(min_length=6)


class User(NewUser):
    id: int


class NewProduct(BaseModel):
    name: str = Field(max_length=100)
    description: str = Field(max_length=1000)
    price: float = Field(gt=0)


class Product(NewProduct):
    id: int


class NewOrder(BaseModel):
    user_id: int
    product_id: int
    date: datetime = Field(default=datetime.now())
    status: str = Field(default='created')


class Order(NewOrder):
    id: int


users = sqlalchemy.Table(
    'users',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('first_name', sqlalchemy.String(50)),
    sqlalchemy.Column('last_name', sqlalchemy.String(150)),
    sqlalchemy.Column('email', sqlalchemy.String(150)),
    sqlalchemy.Column('password', sqlalchemy.String)
)

products = sqlalchemy.Table(
    'products',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('name', sqlalchemy.String(100)),
    sqlalchemy.Column('description', sqlalchemy.String(1000)),
    sqlalchemy.Column('price', sqlalchemy.Float)
)

orders = sqlalchemy.Table(
    'orders',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('user_id', sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('product_id', sqlalchemy.ForeignKey('products.id')),
    sqlalchemy.Column('date', sqlalchemy.String),
    sqlalchemy.Column('status', sqlalchemy.String(100)),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={'check_same_thread': False})

metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)


@app.get('/users/', response_model=List[User])
async def read_all_users():
    return await database.fetch_all(users.select())


@app.get('/users/{user_id}', response_model=User)
async def read_user(user_id: int):
    if user := await database.fetch_one(
            users.select().where(users.c.id == user_id)):
        return user
    return JSONResponse({'error': 'ID not found'}, 404)


@app.get('/products/', response_model=List[Product])
async def read_all_products():
    return await database.fetch_all(products.select())


@app.get('/products/{product_id}', response_model=Product)
async def read_product(product_id: int):
    if product := await database.fetch_one(
            products.select().where(products.c.id == product_id)):
        return product
    return JSONResponse({'error': 'ID not found'}, 404)


@app.get('/orders/', response_model=List[Order])
async def read_all_orders():
    return await database.fetch_all(orders.select())


@app.get('/orders/{order_id}', response_model=Order)
async def read_order_(order_id: int):
    if order := await database.fetch_one(
            orders.select().where(orders.c.id == order_id)):
        return order
    return JSONResponse({'error': 'ID not found'}, 404)


@app.post('/users/', response_model=User)
async def create_user(user: NewUser):
    query = users.insert().values(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=user.password)
    last_id = await database.execute(query)
    return {**user.model_dump(), 'id': last_id}


@app.post('/products/', response_model=Product)
async def create_product(product: NewProduct):
    query = products.insert().values(
        name=product.name,
        description=product.description,
        price=product.price)
    last_id = await database.execute(query)
    return {**product.model_dump(), 'id': last_id}


@app.post('/orders/', response_model=Order)
async def create_order(order: NewOrder):
    query = orders.insert().values(
        user_id=order.user_id,
        product_id=order.product_id,
        date=order.date,
        status=order.status

    )
    last_id = await database.execute(query)
    return {**order.model_dump(), 'id': last_id}


@app.put('/users/{user_id}', response_model=User)
async def update_user(user_id: int, new_user: NewUser):
    query = users.update().where(users.c.id == user_id).values(
        **new_user.model_dump())
    await database.execute(query)
    return {**new_user.model_dump(), 'id': user_id}


@app.put('/products/{product_id}', response_model=Product)
async def update_product(product_id: int, new_product: NewProduct):
    query = products.update().where(products.c.id == product_id).values(
        **new_product.model_dump())
    await database.execute(query)
    return {**new_product.model_dump(), 'id': product_id}


@app.put('/orders/{order_id}', response_model=Order)
async def update_order(order_id: int, new_order: NewOrder):
    query = orders.update().where(orders.c.id == order_id).values(
        **new_order.model_dump())
    await database.execute(query)
    return {**new_order.model_dump(), 'id': order_id}


@app.delete('/users/{user_id}')
async def delete_user(user_id: int):
    await database.execute(users.delete().where(users.c.id == user_id))
    return {'message': 'User deleted'}


@app.delete('/products/{product_id}')
async def delete_product(product_id: int):
    await database.execute(products.delete().where(
        products.c.id == product_id))
    return {'message': 'Product deleted'}


@app.delete('/orders/{order_id}')
async def delete_order(order_id: int):
    await database.execute(orders.delete().where(orders.c.id == order_id))
    return {'message': 'Order deleted'}


if __name__ == '__main__':
    uvicorn.run('main:app', port=8000)
