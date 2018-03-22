test:
	docker-compose run dev python3 -m pytest

clean:
	docker-compose down
