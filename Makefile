run-chrome-x86:
	docker-compose up -d chrome-x86

run-chrome-arm:
	docker-compose up -d chrome-arm

run-appointment-finder-x86:
	docker-compose build
	docker-compose up appointment-x86

run-appointment-finder-arm:
	docker-compose build
	docker-compose up appointment-arm

psql:
	PGPASSWORD=pgpassword psql -h localhost -p 5433 -U pguser liftoff

# Mobile/Expo commands
expo-start:
	cd mobile/allende && npx expo start

expo-deploy:
	cd mobile/allende && eas workflow:run .eas/workflows/submit-android.yml
