/*
  Code for Viridia's motors, based on the MechaDuino source cloned initially
  from git@github.com:jcchurch13/Mechaduino-Firmware.git
*/
#include <I2CHelper.h>
#include "Utils.h"
#include "Parameters.h"
#include "State.h"
#include "analogFastWrite.h"
#include "Interval.h"

// I2C addresses for each motor
#if defined(MOTOR_A)
#define I2C_ADDRESS 0x61
#elif defined(MOTOR_B)
#define I2C_ADDRESS 0x62
#elif defined(MOTOR_C)
#define I2C_ADDRESS 0x63
#endif

// Comment this out to remove serial terminal functionality
#define SERIAL_ENABLED

#ifdef SERIAL_ENABLED
#define SERIAL(message) DO_SERIAL(message)
#else
#define SERIAL(message)
#endif
#define DO_SERIAL(message) { SerialUSB.print(message); }

Interval printAngle(500);

// Set up interrupts, pins, SPI, I2C etc.
void setup() {
  digitalWrite(ledPin, HIGH);
  vKp = 0.9;
  vKi = 0.001;
  vKd = 0.0;
  vLPF = 100.0;
  setupPins();
  setupTCInterrupts();
#ifdef SERIAL_ENABLED
  SerialUSB.begin(115200);
#endif
  delay(3000);
#ifdef SERIAL_ENABLED
  serialMenu();
#endif
  setupSPI();
  digitalWrite(ledPin, LOW);
  I2CHelper::begin(I2C_ADDRESS);
  I2CHelper::onRequest(readWheelPosition);
  SERIAL(F("Listening for I2C on "))
  SERIAL(I2C_ADDRESS)
  SERIAL(F("\n"))
}

// Loop - check serial if enabled, check I2C
void loop() {
#ifdef SERIAL_ENABLED
  serialCheck();
#endif
  if (I2CHelper::reader.hasNewData()) {
    if (I2CHelper::reader.checksumValid()) {
      switch (I2CHelper::reader.getByte()) {
        // Set velocity mode and setpoint
        case 0:
          setSpeed(I2CHelper::reader.getFloat());
          break;
        // Enable control loop
        case 1:
          enableTCInterrupts();
          break;
        // Disable control loop
        case 2:
          disableTCInterrupts();
          break;
        default:
          break;
      }
    }
  }
#ifdef SERIAL_ENABLED
  if (printAngle.shouldRun()) {
    SerialUSB.print(F("Angle is "));
    SerialUSB.println(yw / 360.0);
  }
#endif
}

// Set the speed, including changing any PID gains based on the speed requested
void setSpeed(float rpm) {
  mode = 'v';
  r = rpm;
  if (r < 5.0) {
    vKi = 0.03;
  } else if (r < 50) {
    vKi = 0.02;
  } else {
    vKi = 0.01;
  }
}

void readWheelPosition() {
  I2CHelper::responder.addFloat(yw / 360.0);
  I2CHelper::responder.write(false);
}

