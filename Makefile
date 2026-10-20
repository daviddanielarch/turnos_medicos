test:
	pytest

# Pre-commit commands
precommit-setup:
	./setup-precommit.sh

precommit-run:
	pre-commit run --all-files

precommit-install:
	pre-commit install

format:
	black .

typecheck:
	mypy --ignore-missing-imports .

psql:
	PGPASSWORD=pgpassword psql -h localhost -p 5433 -U pguser liftoff

# Mobile/Expo commands
expo-start:
	cd mobile/allende && npx expo start

expo-deploy:
	cd mobile/allende && eas build --platform android --auto-submit
