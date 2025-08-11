test:
	pytest

run-chrome-x86:
	docker-compose -f docker-compose-selenium.yml up -d chrome-x86

run-chrome-arm:
	docker-compose -f docker-compose-selenium.yml up -d chrome-arm

psql:
	PGPASSWORD=pgpassword psql -h localhost -p 5433 -U pguser liftoff

# Mobile/Expo commands
expo-start:
	cd mobile/allende && npx expo start

expo-deploy:
	cd mobile/allende && eas build --platform android --auto-submit
