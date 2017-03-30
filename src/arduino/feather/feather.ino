/*
   Firmware running on the ATMega328 based Feather on Viridia. This includes the neopixel ring and the
   solenoid kicker control.
*/

#include <I2CHelper.h>
#include <FastLED.h>
#include "Interval.h"

/*
   LED ring configuration. Viridia's lighting is a single 64 pixel ring

   ADDRESS is the I2C address on which we listen for commands.
   NUM_LEDS is the number of neopixels attached to the data pin.
   LED_PIN is the hardware pin used to send data to the neopixel strip.
*/
#define ADDRESS 0x31
#define NUM_LEDS 60
#define LED_PIN 9
#define DISABLE_PIN 5

/*
   Volatile state, the hue and hue_variation are used to configure the light
   show, the Interval instance is used to determine how often it should be
   updated and the CRGB[] contains the actual LED colour data.
*/
byte hue = 0; // Hue, for modes which specify a hue
byte hue_variation = 30; // Hue variation, where applicable
byte mode = 0; // Mode, defines the kind of light show displayed
float direction = 0.0; // For directional displays, this is the angle in radians
Interval ledUpdate(30); // Update for animations
CRGB leds[NUM_LEDS]; // The LEDs

/*
   Setup - starts up the I2CHelper and Serial connections

   Note that this waits for a serial monitor to be started, so you won't see any lights flashing
   until you connect the monitor.
*/
void setup() {
  FastLED.addLeds<NEOPIXEL, LED_PIN>(leds, NUM_LEDS);
  FastLED.setBrightness(100);
  FastLED.setDither(0);
  I2CHelper::begin(ADDRESS);
}

CRGB firstLED;

/*
   Each time round the loop we check to see whether the I2CReader has new data. If it has, then read
   off the first byte and use that to interpret the command, reading subsequent data if needed based
   on the command code.

   Update the LEDs if the interval between updates has expired.
*/
void loop() {
  if (I2CHelper::reader.hasNewData()) {
    if (I2CHelper::reader.checksumValid()) {
      byte command = I2CHelper::reader.getByte();
      Serial.print(F("Command received: "));
      Serial.println(command, DEC);
      switch (command) {
        case 4:
          mode = I2CHelper::reader.getByte();
          break;
        case 1:
          hue = I2CHelper::reader.getByte();
          hue_variation = I2CHelper::reader.getByte();
          break;
        case 2:
          FastLED.setBrightness(I2CHelper::reader.getByte());
          FastLED.setDither(0);
          break;
        case 3:
          direction = I2CHelper::reader.getFloat();
          break;
        default:
          break;
      }
    }
    else {
      Serial.print("Checksum failed");
      I2CHelper::reader.start();
    }
  }
  // Only update the display every 20 milliseconds
  if (ledUpdate.shouldRun()) {
    switch (mode) {
      case 0:
        /*
           Mode 0 is a rotating display with hue variation and random colours around a central
           point. This is handy as a waiting mode, or where we don't actually need to show anything
           on the LED ring and just want a bit of bling.
        */
        for (int i = 0; i < NUM_LEDS; i++) {
          leds[i].fadeToBlackBy(15);
        }
        firstLED = leds[0];
        for (int i = 0; i < NUM_LEDS - 1; i++) {
          leds[i] = leds[i + 1];
        }
        leds[NUM_LEDS - 1] = firstLED;
        leds[random(NUM_LEDS)].setHSV(hue + random(-hue_variation, hue_variation), 255, 255);
        break;
      case 1:
        /*
           Mode 1 shows a single bar at the specified angle. The bar is used to indicate direction
           for e.g. manual control
        */
        for (int i = 0; i < NUM_LEDS; i++) {
          leds[i].fadeToBlackBy(50);
        }
        int centreLED = (int)((direction / (2.0f * PI)) * ((float)NUM_LEDS));
        for (int i = -4; i <= 4; i++) {
          leds[(centreLED + i + NUM_LEDS) % NUM_LEDS].setHSV(hue, 255, 255);
          Serial.print((centreLED + i + NUM_LEDS) % NUM_LEDS);
          Serial.print(F(","));
        }
        Serial.println("");
        break;
    }
    show();
  }
}

void show() {
  //if (digitalRead(DISABLE_PIN) == HIGH)
  //  return;
  FastLED.show();
}

