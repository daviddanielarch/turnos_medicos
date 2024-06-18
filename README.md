Este repositorio contiene una automatizacion para tratar de encontrar un "mejor" turno para un medico en el Sanatorio Allende de Cordoba.
Es normal tener que esperar 1 mes o mas para sacar turno con algun medico en particular. La idea principal de esta automatizacion se basa
en que es bastante comun que la gente cancele turnos por diversas razones, utilizando este programa vamos a poder detectar esas cancelacones y obtener turnos
mucho mas rapido. 
El codigo hace uso de Selenium, por lo que es necesario contar con una instalacion de Chrome/Chromium. Para facilitar el proceso, es posible utilizar el browser dockerizado.
Las definiciones se encuentran en docker-compose.

Se realiza un chequeo cada 5 minutos, y se busca un turno para el doctor especificado.
Cuando el codigo encuentra un mejor turno, envia una notificacion a travez de Telegram.
Selenium se utiliza para hacer el login, y para obtener los datos especificos del doctor para el cual queremos buscar turno.
El chequeo periodico por un mejor turno se realiza usando una REST API call a la API del Sanatorio Allende.

Requerimientos:
* Docker
* Docker-compose
* Cuenta de telegram

Argumentos:
Los argumentos se pueden pasar al programa tanto a travez de variables de entorno, como de argumentos de linea de consola.
Los argumentos necesarios son:

* *username*: Nombre de usuario que se utiliza en https://miportal.sanatorioallende.com/
* *password*: Password que se utiliza en https://miportal.sanatorioallende.com/
* *hostname*: Hostname del servidor de Selenium
* *port*: Puerto del servidor de Selenium
* *doctor_name*: Nombre completo del doctor para el cual se busca el turno, tal cual aparece en https://miportal.sanatorioallende.com/ al tratar de sacar un turno
* *telegram_token*: Token de Telegram
* *telegram_chat_id*: Chat ID de Telegram
* *place*: Sucursal del Sanatorio Allende ("CERRO" o "NUEVA CBA")

Como correrlo:
Alternativa 1
Correr el script via docker-compose nos asegura que se levante el chrome dockerizado que vamos a necesitar para correr el script. 
Tambien es posible levantar el contenedor de chrome por separado y correr el script de manera independiente.

Para levantar Chrome en x86
```
make run-chrome-x86
```

Para levantar Chrome en arm
```
make run-chrome-arm
```

Ejemplo:
```
docker-compose run appointment-arm /app/find_appointment.py \
--hostname chrome-arm \ 
--port 4444 \
--username <username> \
--password <password> \
--doctor_name "Dr. Juan Perez" \
--telegram_token <token> \
--telegram_chat_id <chat_id> \
--place "CERRO"
```

Alternativa 2:
Crear un .env file con las variables de entorno necesarias y correr el script a travez de docker-compose 
```
USERNAME=''
PASSWORD=''
TELEGRAM_TOKEN=''
DOCTOR_NAME=''
PLACE='CERRO'
TELEGRAM_ID=123123123
HOSTNAME='chrome-arm'
PORT=4444
```

y despues correr (esto usa un archivo de env llamado .env por defecto)

````
docker-compose run appointment-arm
````

