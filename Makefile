up:
	@docker compose up

bash:
	@docker compose run --rm app bash

build:
	@docker compose build

build-up:
	@docker compose up --build

createsuperuser:
	@docker compose run --rm app python manage.py createsuperuser
# winpty removed

down:
	@docker compose down --remove-orphans

flush-db:
	@docker compose run --rm app python manage.py flush
	@make down

reset_db:
	@docker compose run --rm app python manage.py reset_db
	@make down

format:
	@docker compose run --rm app ruff format .
	@docker compose run --rm app ruff check . --fix --select I

install:
	@pipenv install --dev

lint:
	@docker compose run --rm app ruff check . --fix

migrations:
	@docker compose run --rm app python manage.py makemigrations

migrate:
	@docker compose run --rm app python manage.py migrate

resetdb:
	@docker compose run --rm app python manage.py reset_db --noinput

run-command:
	@docker compose run --rm app $(command)

shell:
	@docker compose run --rm app python manage.py shell

test:
	@docker compose run --rm app py.test tests

testcase:
	@docker compose run --rm app py.test $(test)

up-d:
	@docker compose up -d