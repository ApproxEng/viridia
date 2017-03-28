#include "Interval.h"

Interval::Interval(int interval) {
  _interval = interval;
  _lastRunTime = 0;
}

boolean Interval::shouldRun() {
  unsigned long now = millis();
  if (now - _lastRunTime >= _interval) {
    _lastRunTime = now;
    return true;
  }
  return false;
}

