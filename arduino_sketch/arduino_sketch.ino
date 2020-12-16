
#include <Servo.h> 
#include <FastLED.h>

#include "order.h"
#include "parameters.h"

bool is_connected = false; ///< True if the connection with the master is available

int servo_increment = 5;

CRGB leds[LED_COUNT];
Servo servos[SERVO_COUNT];
int servo_angles[SERVO_COUNT];

void setup() 
{
  Serial.begin(SERIAL_BAUD);

  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, LED_COUNT);

  for (int i = 0; i < LED_COUNT; i++){
    leds[i] = CRGB(0,0,0);
  }
  leds[0] = CRGB(1,0,0);
  FastLED.show();

  // Wait until the arduino is connected to master
  while(!is_connected)
  {
    write_order(HELLO);
    wait_for_bytes(1, 1000);
    get_messages_from_serial();
  }
}
 
void loop() 
{
    get_messages_from_serial();
    increment_servos();
}

void increment_servos()
{
    for (int index = 0; index < SERVO_COUNT; index++ )
    {
       int curr = servos[index].read();
       int end = servo_angles[index];
       if (curr < end)
       {
            if (end - curr < servo_increment)
            {
                servos[index].write(end);
            }
            else servos[index].write(servos[index].read() + servo_increment);
       }
       else if (curr > end)
       {
            if (curr - end < servo_increment)
            {
                servos[index].write(end);
            }
            else servos[index].write(servos[index].read() - servo_increment);
       }
    }
    delay(50);
}

void get_messages_from_serial()
{
  if(Serial.available() > 0)
  {
    // The first byte received is the instruction
    Order order_received = read_order();

    if(order_received == HELLO)
    {
      // If the cards haven't say hello, check the connection
      if(!is_connected)
      {
        is_connected = true;
        write_order(HELLO);
      }
      else
      {
        // If we are already connected do not send "hello" to avoid infinite loop
        write_order(ALREADY_CONNECTED);
      }
    }
    else if(order_received == ALREADY_CONNECTED)
    {
      is_connected = true;
    }
    else
    {
      switch(order_received)
      {
        case STOP:
        {
          //motor_speed = 0;
          //stop();
          if(DEBUG)
          {
            write_order(STOP);
          }
          break;
        }
        case SERVO:
        {
          int servo_identifier = read_i8();
          int servo_angle = read_i16();
          if(DEBUG)
          {
            write_order(SERVO);
            write_i16(servo_angle);
          }
          move_servo(servo_identifier, servo_angle);
          break;
        }
        case MOTOR:
        {
          // between -100 and 100
          //motor_speed = read_i8();
          if(DEBUG)
          {
            write_order(MOTOR);
            //write_i8(motor_speed);
          }
          break;
        }
        case LED:
        {
          int led_count = read_i8();
          int identifiers[led_count];
          for (int i = 0; i < led_count; i++) {
            identifiers[i] = read_i8();
          }
          int led_color_r = read_i8();
          int led_color_g = read_i8();
          int led_color_b = read_i8();
          if(DEBUG)
          {
            write_order(LED);
            write_i8(led_count);
            write_i8(led_color_r);
            write_i8(led_color_g);
            write_i8(led_color_b);
          }
          for (int i = 0; i < led_count; i++) {
            leds[identifiers[i]] = CRGB(led_color_r, led_color_g, led_color_b);
          }

          FastLED.show();
          break;
        }
        case PIN:
        {
            int pin = read_i8();
            int value = read_i8();
            pinMode(pin, OUTPUT);
            digitalWrite(pin, value);
            break;
        }
        case READ:
        {
            int pin = read_i8();
            pinMode(pin, INPUT);
            int value = analogRead(pin);
            write_i8(value);
            break;
        }
        // Unknown order
        default:
        {
          write_order(ERROR);
          write_i16(404);
        }
        return;
      }
    }
    write_order(RECEIVED); // Confirm the receipt
  }
}

void move_servo(int identifier, int angle) {
    int index = identifier - SERVO_PIN_OFFSET;
    servos[index].attach(identifier);
//    servos[index].write(angle);
    servo_angles[index] = angle; // Don't move it but queue the move
}

Order read_order()
{
	return (Order) Serial.read();
}

void wait_for_bytes(int num_bytes, unsigned long timeout)
{
	unsigned long startTime = millis();
	//Wait for incoming bytes or exit if timeout
	while ((Serial.available() < num_bytes) && (millis() - startTime < timeout)){}
}

// NOTE : Serial.readBytes is SLOW
// this one is much faster, but has no timeout
void read_signed_bytes(int8_t* buffer, size_t n)
{
	size_t i = 0;
	int c;
	while (i < n)
	{
		c = Serial.read();
		if (c < 0) break;
		*buffer++ = (int8_t) c; // buffer[i] = (int8_t)c;
		i++;
	}
}

int8_t read_i8()
{
	wait_for_bytes(1, 100); // Wait for 1 byte with a timeout of 100 ms
  return (int8_t) Serial.read();
}

int16_t read_i16()
{
  int8_t buffer[2];
	wait_for_bytes(2, 100); // Wait for 2 bytes with a timeout of 100 ms
	read_signed_bytes(buffer, 2);
  return (((int16_t) buffer[0]) & 0xff) | (((int16_t) buffer[1]) << 8 & 0xff00);
}

int32_t read_i32()
{
  int8_t buffer[4];
	wait_for_bytes(4, 200); // Wait for 4 bytes with a timeout of 200 ms
	read_signed_bytes(buffer, 4);
  return (((int32_t) buffer[0]) & 0xff) | (((int32_t) buffer[1]) << 8 & 0xff00) | (((int32_t) buffer[2]) << 16 & 0xff0000) | (((int32_t) buffer[3]) << 24 & 0xff000000);
}

void write_order(enum Order myOrder)
{
	uint8_t* Order = (uint8_t*) &myOrder;
  Serial.write(Order, sizeof(uint8_t));
}

void write_i8(int8_t num)
{
  Serial.write(num);
}

void write_i16(int16_t num)
{
	int8_t buffer[2] = {(int8_t) (num & 0xff), (int8_t) (num >> 8)};
  Serial.write((uint8_t*)&buffer, 2*sizeof(int8_t));
}

void write_i32(int32_t num)
{
	int8_t buffer[4] = {(int8_t) (num & 0xff), (int8_t) (num >> 8 & 0xff), (int8_t) (num >> 16 & 0xff), (int8_t) (num >> 24 & 0xff)};
  Serial.write((uint8_t*)&buffer, 4*sizeof(int8_t));
}
