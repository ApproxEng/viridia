/*
  Code for Viridia's motors, based on the MechaDuino source cloned initially
  from git@github.com:jcchurch13/Mechaduino-Firmware.git
*/
#include <I2CHelper.h>
#include "Utils.h"
#include "Parameters.h"
#include "State.h"
#include "analogFastWrite.h"

#if defined(MOTOR_A)
#define I2C_ADDRESS 0x61
#elif defined(MOTOR_B)
#define I2C_ADDRESS 0x62
#elif defined(MOTOR_C)
#define I2C_ADDRESS 0x63
#endif

void setup() {
  digitalWrite(ledPin, HIGH);
  setupPins();
  setupTCInterrupts();
  SerialUSB.begin(115200);
  delay(3000);
  serialMenu();
  setupSPI();
  digitalWrite(ledPin, LOW);
  I2CHelper::begin(I2C_ADDRESS);
}

void loop() {
  // put your main code here, to run repeatedly:
  serialCheck();
}
