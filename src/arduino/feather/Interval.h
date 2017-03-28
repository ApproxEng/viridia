#ifndef Interval_h
#define Interval_h

#include "Arduino.h"

class Interval {
  public:
    boolean shouldRun();
    Interval(int interval);
  private:
    int _interval;
    long _lastRunTime;
};


#endif
