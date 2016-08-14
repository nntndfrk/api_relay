# API документація для керування реле та rgb-led стрічкою

Для авторизованого доступу використовується метод HTTP Basic Auth.

### Реле

**Одержати стан всіх реле**

    curl -u username:password http://raspberryip/api/v1.0/relays
Повертає інформацію про стан усіх реле в json:

    {
      "relays": [
        {
          "id": 1, 
          "name": "test_1", 
          "state": "off"
        }, 
        {
          "id": 2, 
          "name": "test_2", 
          "state": "off"
        }
    }
    
    
**Одержати стан одиночного реле**

    curl -u username:password  http://***raspberryip***/api/v1.0/relays/***<int:relay_id>***
    
Повертає інформацію про стан одиночного реле в json.
raspberryip - ip-адреса пристрою.

**Тригерна зміна стану реле**

    curl -u username:password -i -H "Content-Type: application/json" -X PUT -d '{"state":"off"}' http://raspberryip/api/v1.0/relays/<int:relay_id>

state - стан реле

<int: relay_id> - номер реле   
    
**Таймерна зміна стану реле**

    curl -u username:password -i -H "Content-Type: application/json" -X PUT -d '{***"timer"***:"<float:time_in_seconds>"}' http://raspberryip/api/v1.0/relays_t/<int:relay_id>

timer - час переключення    

    
### RGB-led стрічка

**Очистити стрічку і заповнити кольором**

    curl -u username:password -i -H "Content-Type: application/json" -X PUT -d '{"color":"255 255 255", "wait_ms":"<int:time_in_milliseconds>"}' http://raspberryip/api/v1.0/led/colorWipe

*color* - колір передається у вигляді рядка в форматі ~~RGB~~ (точніше BRG), де інтенсивність для складових кольору розділюється пробілом. Для прикладу зелений "0 0 255". Є обов'язковим параметром.

Час задається у вигляді цілого числа мілісекунд. Не є обов'язковим параметром, по замовчуванню рівний 50.

**Додаткові демо-пресети**

1-й (theaterChase)

*Щось схоже на ілюмінацію вивісок в казино і т.д.*

    curl -u username:password -i -H "Content-Type: application/json" -X PUT -d '{"color":"255 255 255", "wait_ms":"<int:time_in_seconds>"}' http://raspberryip/api/v1.0/led/theaterChase

*color* - обов'язковий параметр

*wait_ms* - час затримки в мілісекундах, не обов'язковий параметр, по замовчуванню рівний 50

*iterations* - к-сть ітерацій не обов'язковий параметр, по замовчуванню рівний 10.


3-й (rainbow) 

    curl -u username:password -i -H "Content-Type: application/json" -X PUT -d '{"wait_ms":"<int:time_in_milliseconds>"}' http://raspberryip/api/v1.0/led/rainbow

Малює веселку, що зникає через всі пікселі за один раз.

*wait_ms* - час затримки в мілісекундах, не обов'язковий параметр, по замовчуванню рівний 20.

*iterations* - к-сть ітерацій не обов'язковий параметр, по замовчуванню рівний 1.


4-й (rainbowCycle)

    curl -u username:password -i -H "Content-Type: application/json" -X PUT -d '{"wait_ms":"<int:time_in_milliseconds>"}' http://raspberryip/api/v1.0/led/rainbowCycle

Малює веселку, яка рівномірно розподіляє себе через всі пікселі.

*wait_ms* - час затримки в мілісекундах, не обов'язковий параметр, по замовчуванню рівний 20.

*iterations* - к-сть ітерацій не обов'язковий параметр, по замовчуванню рівний 5.

5-й (theaterChaseRainbow)

    curl -u username:password -i -H "Content-Type: application/json" -X PUT -d '{"wait_ms":"<int:time_in_milliseconds>"}' http://raspberryip/api/v1.0/led/theaterChaseRainbow


*wait_ms* - час затримки в мілісекундах, не обов'язковий параметр, по замовчуванню рівний 20.
