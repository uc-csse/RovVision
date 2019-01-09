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

///constants

#define TRIG_FPS 10
#define IMU_FPS 1
#define TRIGGER_RATE_MICROS (1000000/IMU_FPS)
#define SEND_IMU_RATE_MICROS (1000000/TRIG_FPS)
#define SEND_IMU_RATE_MICROS_HALF (SEND_IMU_RATE_MICROS/2)

#define DEBUG_IMU_MSG

#define SERIAL_BAUD_RATE 460800

#if ARDUINO_ARCH_ESP32
#define LED_PIN 2
#define TRIGER_PIN 4
#define SERIAL Serial
#elif ESP8266
#define SERIAL Serial
#define LED_PIN 2
#define TRIGER_PIN 16
#define LASER1_PIN 14
#else
#define LED_PIN LED_BUILTIN
#define SERIAL SerialUSB
#define TRIGER_PIN 3
#endif


//###########  states
int dump_imu=0; // 01
int start_trig=0; // 02
//############ states end

MS5611 ms5611;
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


void setup() {
    delay(2000);  
    Wire.begin();
    accelgyro.setI2CMasterModeEnabled(false);
    accelgyro.setI2CBypassEnabled(true) ;
    accelgyro.setSleepEnabled(false);

    SERIAL.begin(SERIAL_BAUD_RATE);

    // initialize device
    SERIAL.println("Initializing I2C devices...");
    accelgyro.initialize();
    mag.initialize();
    SERIAL.println(mag.testConnection() ? "HMC5883L connection successful" : "HMC5883L connection failed");

    // verify connection
    SERIAL.println("Testing device connections...");
    SERIAL.println(accelgyro.testConnection() ? "MPU6050 connection successful" : "MPU6050 connection failed");

    ms5611.setOversampling(MS5611_ULTRA_HIGH_RES);
    ms5611.begin();

    // configure Arduino LED for
    pinMode(LED_PIN, OUTPUT);
    pinMode(TRIGER_PIN, OUTPUT);
    pinMode(LASER1_PIN, OUTPUT);
}



void loop() {
    unsigned long time = micros();

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
    
    
    while (SERIAL.available() > 0) {
        int bt = SERIAL.read();
        switch(bt) {
            case 1:
                dump_imu=1;
                start_trig=1;
                break;
            case 2:
                dump_imu=0;
                start_trig=0;
                break;
            case 3:
                digitalWrite(LASER1_PIN,HIGH); 
                break;
            case 4:
                digitalWrite(LASER1_PIN,LOW);
                break;
            default:
                break;
        }
    }
    
    
    // Task to trigger cameras
    static unsigned long trigger_last_time = 0;
    if ((time - trigger_last_time) > SEND_IMU_RATE_MICROS_HALF) {
        static uint8_t trigger_state = false;
        trigger_last_time = time;
        
        if (!trigger_state && start_trig) {
            // trigger low and currently triggering
            digitalWrite(LED_PIN, HIGH);
            digitalWrite(TRIGER_PIN, HIGH);
            trigger_state = true;
        }
        else {
            // trigger high (always bring lines low even if trigger has been turned off)
            digitalWrite(LED_PIN, LOW);
            digitalWrite(TRIGER_PIN, LOW);
            trigger_state = false;
        }
        
    }
    
    // Task to send IMU data to companion computer 
    static unsigned long send_imu_last_time = 0;
    if ((time - send_imu_last_time) > TRIGGER_RATE_MICROS) {
        send_imu_last_time = time;
#ifdef DEBUG_IMU_MSG
        SERIAL.print("a/g:\t");
        SERIAL.print(ds.ax); SERIAL.print("\t");
        SERIAL.print(ds.ay); SERIAL.print("\t");
        SERIAL.print(ds.az); SERIAL.print("\t");
        SERIAL.print(ds.gx); SERIAL.print("\t");
        SERIAL.print(ds.gy); SERIAL.print("\t");
        SERIAL.print(ds.gz);SERIAL.print("\t");

        SERIAL.print("mag:\t");
        SERIAL.print(ds.mx); SERIAL.print("\t");
        SERIAL.print(ds.my); SERIAL.print("\t");
        SERIAL.print(ds.mz); SERIAL.print("\t");

        // To calculate heading in degrees. 0 degree indicates North
        float heading = atan2(ds.my, ds.mx);
        if(heading < 0)
            heading += 2 * M_PI;
        SERIAL.print("heading:\t");
        SERIAL.print(heading * 180/M_PI);SERIAL.print("\t");

        SERIAL.print("alt:\t");
        SERIAL.println( ds.absoluteAltitude );
#else
        chksum();
        if (dump_imu && SERIAL.availableForWrite()>=sizeof(ds)) SERIAL.write((const uint8_t*)&ds,sizeof
#endif
    }
}
