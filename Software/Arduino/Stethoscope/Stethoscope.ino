/*
 * Stethoscope
 * 
 * The following program has been built to control the stethoscope module
 * 
 * Michael A Xynidis
 * Fluvio L Lobo Fenoglietto
 * 09/14/2016
 */

#define VERSION  0.05

#include  "TeensyAudio.h"
#include  "Config.h"
#include  "states.h"
#include  "protocol.h"
#include  "FileSD.h"
#include  "parseBtByte.h"

byte      inByte = 0x00;

void setup()
{
  // Serial Communication Initialization
  Serial.begin( SPEED );                                                                            // USB Serial Communication
  BTooth.begin( SPEED );                                                                            // RF/Bluetooth Serial Communication

  // Setup Audio Board
  SetupAudioBoard();

  // Configuration File
  SessionInit( "01" );
  
  // SD Reader and Card Check
  if ( sdCardCheck() )
  {
    rootDir = SD.open( "/" );
    Serial.print( "rootDir: " );
    Serial.println( rootDir );
    printDirectory( rootDir, 1 );
//    if ( SD.exists( "RECORD.RAW" ) )
//    {
//      SD.remove( "RECORD.RAW" );
//      Serial.println( "Deleting 'RECORD.RAW' for testing." );
//      rootDir = SD.open( "/" );
//      printDirectory( rootDir, 1 );
//    }
    readyState = READY;
  }
  else
  {
    readyState = NOTREADY;
  }
} // End of setup()

void loop()
{ // when using a microphone, continuously adjust gain
/*  Instead of the following line of code, Mic Level will be hard-coded in SetupAudioBoard()
  if ( myInput == AUDIO_INPUT_MIC ) adjustMicLevel();
 */

  // if we get a valid byte, read analog from BT:
  if ( BTooth.available() > 0 ) parseBtByte( "RECORD.RAW" );

  // If playing or recording, carry on...
  if ( mode == 1 ) continueRecording();
  if ( mode == 2 ) continuePlaying();
  if ( mode == 3 ) continueTrackingMicStream(); //  <--- refactor name
  if ( mode == 4 ) continueAudioPassThru();     //  <---
  if ( mode == 5 ) continueBlending(); 
  
  // Clear the input byte variable
  inByte = 0x00;                                // this line of code may be unnecessary
}

