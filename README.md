[![Build Status](https://github.com/Namari39/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Namari39/foodgram/actions)

# Foodgram

Данный проект представляет собой веб-приложение для комфортной организации процесса готовки с возможностью делиться любимыми рецептами. Пользователи могут регистрироваться с использованием электронной почты и иметь возможность подписываться на других пользователей, добавлять рецепты в избранное, а также формировать корзину для покупок ингредиентов. Есть возможность скачать все игредиенты для выбранных рецептов.

## Основные функции:

- Регистрация и аутентификация пользователей через email.
- Модели для управления подписками между пользователями.
- Управление рецептами, включая добавление ингредиентов и тегов.
- Возможность добавлять рецепты в избранное и в корзину для покупок.

## Ссылка на работающий сайт

[Ссылка на сайт](http://84.201.176.216)

## Автор

ФИО: Князев Денис Владимирович  
Контакт: [GitHub](https://github.com/Namari39)

## Технологический стек

- Python 3.x
- Django 3.x
- PostgreSQL
- Docker
- Docker Compose
- Git

## CI/CD для развертывания

Проект использует GitHub Actions для автоматического развертывания на сервере при каждом пуше в ветку `main`.

## Команды локального развертывания с Docker

1. Клонирование репозитория:


   git clone https://github.com/ivanov/project.git


2. Переход в папку с `docker-compose.yml`:

   cd project

3. Подсказка для заполнения `.env`:
   
   Создайте файл `.env` на основе `example.env`:

   cp example.env .env

4. Подъем контейнера(ов) в Docker:

   docker-compose up -d

5. Подготовка базы: миграции, создание суперпользователя, импорт фикстур:

   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   docker-compose exec web python manage.py loaddata fixtures.json

6. Сборка статики:

   docker-compose exec web python manage.py collectstatic --noinput

7. Запуск сервера:
   
   Сервер будет доступен по адресу `http://localhost:8000`.

## Команды локального развертывания без Docker

1. Клонирование репозитория:

   git clone https://github.com/ivanov/project.git
   
2. Смена папки:

   cd project
   
3. Настройка виртуального окружения:

   python -m venv venv
   source venv/bin/activate  # Для Linux/Mac
   venv\Scripts\activate  # Для Windows

4. Подсказка для заполнения `.env`:
   
   Создайте файл `.env` на основе `example.env`:

   cp example.env .env
   
5. Миграция базы и создание суперпользователя:

   python manage.py migrate
   python manage.py createsuperuser

6. Импорт продуктов из JSON фикстур:

   python manage.py loaddata fixtures.json

7. Запуск сервера:

   python manage.py runserver
   

bash

## Документация API

Полная техническая документация к API доступна по адресу: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
