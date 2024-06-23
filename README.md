# Automatización para encontrar turnos médicos en el Sanatorio Allende

Este repositorio contiene una automatización para tratar de encontrar un "mejor" turno para un médico en el Sanatorio Allende de Córdoba.

Es normal tener que esperar 1 mes o más para obtener turno con algún médico en particular. La idea principal de esta automatización se basa en que es bastante común que la gente cancele turnos por diversas razones. 
Utilizando este programa, vamos a poder detectar esas cancelaciones y obtener turnos mucho más rápido.

El código hace uso de Selenium, por lo que es necesario contar con una instalación de Chrome/Chromium. Para facilitar el proceso, es posible utilizar el navegador en un contenedor Docker. Las definiciones se encuentran en docker-compose.

## Funcionamiento

Inicialmente, se envia una notificación de Telegram con la fecha del primer turno disponible.

Luego, se realiza un chequeo cada 5 minutos y se busca un "mejor" turno para el doctor especificado. 

Cuando el código encuentra un mejor turno, envía una notificación a través de Telegram. 
También se envia una notificación cuando se pierde el "mejor" turno actual.

Selenium se utiliza para hacer el login y para obtener los datos específicos del doctor para el cual queremos buscar turno. 

El chequeo periódico por un mejor turno se realiza usando una llamada REST API a la API del Sanatorio Allende.

## Requerimientos

* Docker
* Docker-compose
* Cuenta de Telegram

## Argumentos

Los argumentos se pueden pasar al programa tanto a través de variables de entorno como de argumentos de línea de consola. 

Los argumentos necesarios son:

* **username**: Nombre de usuario que se utiliza en [https://miportal.sanatorioallende.com/](https://miportal.sanatorioallende.com/)
* **password**: Contraseña que se utiliza en [https://miportal.sanatorioallende.com/](https://miportal.sanatorioallende.com/)
* **hostname**: Nombre del host del servidor de Selenium
* * `chrome-arm` si está usando una computadora arm y corre el script desde docker-compose (appointment-x86)
* * `chrome-x86` si está usando una computadora x86 y corre el script desde docker-compose (appointment-arm)
* * `localhost` si está corriendo el script desde su computadora
* **port**: Puerto del servidor de Selenium
* * 4444 por defecto, no es necesario cambiarlo.
* **doctor_name**: Nombre completo del doctor para el cual se busca el turno, tal como aparece en [https://miportal.sanatorioallende.com/](https://miportal.sanatorioallende.com/) al tratar de sacar un turno
* **telegram_token**: Token de Telegram
* **telegram_chat_id**: ID del chat de Telegram
* **place**: Sucursal del Sanatorio Allende ("CERRO" o "NUEVA CBA")

## Cómo correrlo

Correr el script vía docker-compose nos asegura que se levante Chrome en un contenedor Docker que vamos a necesitar para correr la automatización. 
También es posible levantar el contenedor de Chrome por separado y correr el script de manera independiente.

Para levantar Chrome en x86
```
make run-chrome-x86
```

Para levantar Chrome en arm
```
make run-chrome-arm
```

### Alternativa 1 (usando argumentos de linea de comando)
Este ejemplo asume que estamos usando una computadora arm, si no es el caso remplace `appointment-arm` por `appointment-x86`

Ejemplo:
```
docker-compose run appointment-arm /app/find_appointment.py \
--hostname chrome-arm \ 
--port 4444 \
--username <username> \
--password <password> \
--doctor_name "Dr. Juan Perez" \
--telegram_token <token> \
--telegram_id <chat_id> \
--place "CERRO"
```

### Alternativa 2 (usando un env file)
Primero creamos un env file con las variables de entorno necesarias (lo llamaremos .env porque es el nombre que docker-compose espera por defecto)
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

Luego, ya podemos correr la automatización( nuevamente remplace `appointment-arm` por `appointment-x86` si no está usando una computadora arm)

````
docker-compose run appointment-arm
````

