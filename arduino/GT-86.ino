#include "Wire.h"
//#include "I2Cdev.h"
#include "MPU6050.h"
#include "HMC5883L.h"
#include <MS5611.h>
//// Importent in order for it to work
//// must do changes in http://www.stm32duino.com/viewtopic.php?t=1000
//The way I got it going was to modify two lines in the Arduino_STM32-Master files. In ..\Arduino\hardware\Arduino_STM32-master\STM32F1\libraries\ I added #define's to Wire.h:

//in Wire.h
//#define SDA PB11   // Added for STM32F103C8T6 Minimum Development Board
//#define SCL PB10

//in Wire.cpp
//TwoWire Wire(PB10, PB11, SOFT_STANDARD);




MS5611 ms5611;


uint32_t time;

MPU6050 accelgyro;
HMC5883L mag;


typedef struct {
  uint16_t header;
  int16_t ax, ay, az;
  int16_t gx, gy, gz;
  int16_t mx, my, mz;
  float absoluteAltitude;
  uint32_t t_stemp;
  uint16_t footer; 
} data_struct;

data_struct ds;

void chksum()
{
  uint16_t tsum=0;
  ds.header=0xa5a5;
  ds.t_stemp=millis();
  for(int i=1;i<(sizeof(ds)/2-1);i++)
  {
    uint16_t* pds=(uint16_t*)&ds;
    tsum+=pds[i];
  }
  ds.footer=tsum;
}

#define LED_PIN LED_BUILTIN
#define TRIGER_PIN 3
bool blinkState = false;
int iters=0;

void setup() {
  
   Wire.begin();
   accelgyro.setI2CMasterModeEnabled(false);
   accelgyro.setI2CBypassEnabled(true) ;
   accelgyro.setSleepEnabled(false);

   SerialUSB.begin(115200);

   // initialize device
   SerialUSB.println("Initializing I2C devices...");
   accelgyro.initialize();
   mag.initialize();
   SerialUSB.println(mag.testConnection() ? "HMC5883L connection successful" : "HMC5883L connection failed");

   // verify connection
   SerialUSB.println("Testing device connections...");
   SerialUSB.println(accelgyro.testConnection() ? "MPU6050 connection successful" : "MPU6050 connection failed");

   ms5611.setOversampling(MS5611_ULTRA_HIGH_RES);
   ms5611.begin();

   // configure Arduino LED for
   pinMode(LED_PIN, OUTPUT);
   pinMode(TRIGER_PIN, OUTPUT);
   

}


void loop() {
   unsigned long tdiff,toc,tic=micros();   
   accelgyro.getMotion6(&ds.ax, &ds.ay, &ds.az, &ds.gx, &ds.gy, &ds.gz);
   mag.getHeading(&ds.mx, &ds.my, &ds.mz);
     // Read raw values
   //uint32_t rawTemp = ms5611.readRawTemperature();
   //uint32_t rawPressure = ms5611.readRawPressure();

   // Read true temperature & Pressure
   //double realTemperature = ms5611.readTemperature();
   int32_t realPressure = ms5611.readPressure();

   // Calculate altitude
   ds.absoluteAltitude = ms5611.getAltitude(realPressure);
   //float relativeAltitude = ms5611.getAltitude(realPressure, referencePressure);


   // display tab-separated accel/gyro x/y/z values
#if 0
   SerialUSB.print("a/g:\t");
   SerialUSB.print(ds.ax); SerialUSB.print("\t");
   SerialUSB.print(ds.ay); SerialUSB.print("\t");
   SerialUSB.print(ds.az); SerialUSB.print("\t");
   SerialUSB.print(ds.gx); SerialUSB.print("\t");
   SerialUSB.print(ds.gy); SerialUSB.print("\t");
   SerialUSB.print(ds.gz);SerialUSB.print("\t");
   
   SerialUSB.print("mag:\t");
   SerialUSB.print(ds.mx); SerialUSB.print("\t");
   SerialUSB.print(ds.my); SerialUSB.print("\t");
   SerialUSB.print(ds.mz); SerialUSB.print("\t");

// To calculate heading in degrees. 0 degree indicates North
   float heading = atan2(ds.my, ds.mx);
   if(heading < 0)
     heading += 2 * M_PI;
   SerialUSB.print("heading:\t");
   SerialUSB.print(heading * 180/M_PI);SerialUSB.print("\t");

   SerialUSB.print("alt:\t");
   SerialUSB.println( ds.absoluteAltitude );
#else

   chksum();
   SerialUSB.write((const uint8_t*)&ds,sizeof(ds));
#endif
   // blink LED to indicate activity
   iters+=1;
   if(iters%1==0){
       blinkState = !blinkState;
       digitalWrite(LED_PIN, blinkState);
       digitalWrite(TRIGER_PIN, blinkState);
   }
   toc=micros();
   tdiff=(toc-tic)/1000;
   if (tdiff>0 & tdiff<50) delay(50-tdiff); 
}
