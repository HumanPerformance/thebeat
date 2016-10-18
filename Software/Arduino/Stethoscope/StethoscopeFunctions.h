/*
 *	StethoscopeFunctions.h
 *
 *	The following script contains all the functions used by the Stethoscope prototype
 *
 *	Michael Xynidis
 *	Fluvio L Lobo Fenoglietto
 *	10/18/2016
 *
 */


//
// *** Variables
//

File          frec;
File          hRate;

elapsedMillis msecs;
elapsedMillis triggered;
elapsedMillis elapsed;
elapsedMillis timeStamp;

boolean       beat          = false;
boolean       captured      = false;

int           ndx           = 0;
static int    heartRate     = 0;
const int     myInput       = AUDIO_INPUT_MIC;
unsigned int  hrSample[3]   = { 0, 0, 0 };

String        lineOut       = "";

//
// *** Adjust Microphone Gain Level
//
void adjustMicLevel()
{
  // TODO: read the peak1 object and adjust sgtl5000_1.micGain()
  // if anyone gets this working, please submit a github pull request :-)
}

//
// *** Wave Amplitude Peaks
//
void waveAmplitudePeaks()
{
  float   vol         = analogRead( 15 ) / 1024.0;
  float   sensitivity = 1.0 - vol;
//
//if ( recordState != RECORDING ) break; 

//
// Assume sound is coming from mic at this point.
//

  if ( msecs > 40 )
  {
    if ( peak1.available() )
    {
      msecs             = 0;
      float peakNumber  = 0.0;

      peakNumber        = peak1.read();

      int   leftPeak    = peakNumber  * 30.0;
      int   count;
      char  fillChar    = ' ';

      for ( count = 0; count < 30 - leftPeak; count++ )
        Serial.print( " " );

      if ( peakNumber >= sensitivity )
      {
        fillChar  = '<';
        triggered = 0;
        beat      = false;
        captured  = false;
      }
      else
      {
        fillChar = ' ';
        if ( ( triggered > 250 ) && ( !captured ) )    // this interval needs to be a calculated value....
        {
          beat      = true;
          captured  = true;
          triggered = 0;
          hrSample[ndx] = elapsed;  // - timestamp;
          if ( ndx == 2 )
          {
            heartRate = 60000 / ((hrSample[0] + hrSample[1] + hrSample[2]) / 3);
            for ( int i = 0; i < 3; i++ ) hrSample[i] = 0;
            ndx = 0;
          }
          else ndx++;
          elapsed   = 0;
        }
        else beat   = false;
      }
 
      while ( count++ < 30 )
        Serial.print( fillChar );

      Serial.print( "||" );

      if ( peakNumber >= sensitivity )
        fillChar = '>';
      else
        fillChar = ' ';
 
      for ( count = 0; count < leftPeak; count++ )
        Serial.print( fillChar );

      while ( count++ < 30 )
        Serial.print( " " );
 
      if ( beat ) Serial.print( "* " );
      Serial.print( "Sens: " );
      Serial.print( vol );
      Serial.print( "\tHR: " );
      Serial.println( heartRate );
    }
  }
} // */

//
// *** Start Recording
//
boolean startRecording()
{
  Serial.println( "startRecording" );
  if ( SD.exists( "RECORD.RAW" ) )          // if the file exists on the SD...
  {
    SD.remove( "RECORD.RAW" );              // delete it
  }
  if ( SD.exists( "HRATE.DAT" ) )           // if the file exists on the SD...
  {
    SD.remove( "HRATE.DAT" );               // delete it
  }
  frec  = SD.open( "RECORD.RAW", FILE_WRITE );
  Serial.println( frec );
  hRate = SD.open( "HRATE.DAT",  FILE_WRITE );
  Serial.println( hRate );
  if ( frec )
  {
    queue1.begin();
    recordState = RECORDING;
    timeStamp   = 0;
    return true;
  }
  else
    return false;
}

//
// *** Continue Recording
//
void continueRecording()
{
  if ( queue1.available() >= 2 )
  {
    byte buffer[512];
    // Fetch 2 blocks from the audio library and copy
    // into a 512 byte buffer.  The Arduino SD library
    // is most efficient when full 512 byte sector size
    // writes are used.
    memcpy( buffer, queue1.readBuffer(), 256 );
    queue1.freeBuffer();
    memcpy( buffer + 256, queue1.readBuffer(), 256 );
    queue1.freeBuffer();
    // write all 512 bytes to the SD card
    frec.write( buffer, 512 );
    waveAmplitudePeaks();
    //write HR and time to file at each heart beat
    if ( beat )
    {
      lineOut = heartRate + "," + String( timeStamp, DEC ) + "\r\n";
      hRate.println( lineOut );
    }
  }
}

//
// *** Stop Recording
//
boolean stopRecording()
{
  Serial.println( "stopRecording" );
  queue1.end();
  if ( recordState == RECORDING )
  {
    while ( queue1.available() > 0 )
    {
      frec.write( (byte*)queue1.readBuffer(), 256 );
      queue1.freeBuffer();
    }
    frec.close();
    hRate.close();
  }
  recordState = STANDBY;
  return true;
}

//
// *** Start Playing
//
boolean startPlaying()
{
  if ( SD.exists( "RECORD.RAW" ) )
  {
    Serial.println( "startPlaying" );
    playRaw1.play( "RECORD.RAW" );
    recordState = PLAYING;
    return true;
  }
  else
    return false;
}

//
// *** Continue Playing
//
void continuePlaying() 
{
  if ( !playRaw1.isPlaying() )
  {
    playRaw1.stop();
    mode = 0;
  }
}

//
// *** Stop Playing
//
boolean stopPlaying()
{
  Serial.println( "stopPlaying" );
  if ( recordState == PLAYING ) playRaw1.stop();
  recordState = STANDBY;
  return true;
}
