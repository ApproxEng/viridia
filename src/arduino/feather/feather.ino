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
int itemCount = 0;
int itemIndex = 0;
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

/*
   Each time round the loop we check to see whether the I2CReader has new data. If it has, then read
   off the first byte and use that to interpret the command, reading subsequent data if needed based
   on the command code.

   Update the LEDs if the interval between updates has expired.
*/
int centreLED;
void loop() {
  if (I2CHelper::reader.hasNewData()) {
    if (I2CHelper::reader.checksumValid()) {
      byte command = I2CHelper::reader.getByte();
      //Serial.print(F("Command received: "));
      //Serial.println(command, DEC);
      switch (command) {
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
        case 4:
          mode = I2CHelper::reader.getByte();
          break;
        case 5:

        default:
          break;
      }
    }
    else {
      //Serial.print("Checksum failed");
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

        fade(15);
        rotate();
        leds[random(NUM_LEDS)].setHSV(hue + random(-hue_variation, hue_variation), 255, 255);
        break;
      case 1:
        /*
           Mode 1 shows a single bar at the specified angle. The bar is used to indicate direction
           for e.g. manual control
        */
        fade(50);
        centreLED = ledForDirection(direction);
        for (int i = -4; i <= 4; i++) {
          leds[ledIndex(centreLED + i)].setHSV(hue, 255, 255);
        }
        break;
      case 2:
        /*
           Mode 2 shows a range from -1 to 1 with the LED at 'direction' highlighted, if in this range
        */
        fade(50);
        for (int i = -15; i++; i <= 15) {
          leds[ledIndex(i)].setHSV(hue, 255, 255);
        }
        if (direction >= -1 && direction <= 1) {
          leds[ledIndex((int)(direction * 15.0))].setHSV((hue + 128) % 255, 255, 255);
        }
        break;
    }
    show();
  }
}

int ledIndex(int i) {
  return (i + NUM_LEDS + 5) % NUM_LEDS;
}

void fade(int fadeBy) {
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i].fadeToBlackBy(fadeBy);
  }
}

CRGB wrapLED;

void rotate() {
  rotate(0, 59, true);
}

void rotate(int fromLED, int toLED, boolean wrap) {
  CRGB wrapLED = leds[ledIndex(toLED)];
  if (toLED < fromLED) {
    for (int i = toLED; i <= fromLED - 1; i++) {
      leds[ledIndex(i)] = leds[ledIndex(i + 1)];
    }
  } else {
    for (int i = toLED; i >= fromLED + 1; i--) {
      leds[ledIndex(i)] = leds[ledIndex(i - 1)];
    }
  }
  if (wrap) {
    leds[ledIndex(fromLED)] = wrapLED;
  }
}

int ledForDirection(float d) {
  return (int)((direction / (2.0f * PI)) * ((float)NUM_LEDS));
}

void show() {
  //if (digitalRead(DISABLE_PIN) == HIGH)
  //  return;
  FastLED.show();
}

