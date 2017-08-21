'''
Position tracking of magnet

Author: Danny, Moe
Date: Aug. 4th, 2017th year of our Lord
'''

# Import Modules
#import  serial, random
import  random
import  numpy                   as      np
from    time                    import  sleep, time
from    math                    import  *
from    scipy.optimize          import  fsolve
from    scipy.optimize          import  broyden1
from    scipy.optimize          import  newton_krylov
from    scipy.optimize          import  root
from    scipy.linalg            import  norm
##from    sympy                   import  nsolve
from    usbProtocol             import  createUSBPort
from    sympy.core.symbol       import symbols
from    sympy.solvers.solveset   import nonlinsolve

######################################################
#                   FUNCTION DEFINITIONS
######################################################

# Pool data from Arduino
def getData(ser):
    global check
    # Flush buffer
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    sleep(0.5)
    try:
        line = ser.readline()[:-1]
        col = line.split(",")

        # Wait for the sensor to calibrate itself to ambient fields.
        while( len(col) < 9 ):
            line = ser.readline()[:-1]
            col = line.split(",")
            if(check == True):
                print "Waiting..."
                check = False

        # Construct magnetic field array
        else:
            # Sensor 1
            Bx=float(col[0])#*1e-4
            By=float(col[1])
            Bz=float(col[2])
            B1 = np.array( ([Bx],[By],[Bz]), dtype='f')

            # Sensor 2
            Bx=float(col[3])
            By=float(col[4])
            Bz=float(col[5])
            B2 = np.array( ([Bx],[By],[Bz]), dtype='f')

            # Sensor 3
            Bx=float(col[6])
            By=float(col[7])
            Bz=float(col[8])
            B3 = np.array( ([Bx],[By],[Bz]), dtype='f')
            
            return (B1, B2, B3)

    except Exception as e:
        print( "Caught error in getData()"      )
        print( "Error type %s" %str(type(e))    )
        print( "Error Arguments " + str(e.args) )

# Construct equations to solve for:
def LHS( root ):
    x, y, z = root
    H1_L2, H2_L2, H3_L2 = HNorm
    sensor1 = ( K*( x**2. + y**2. + z**2. )**(-3.) *
              ( 3.*( z**2./(x**2. + y**2. + z**2.) ) + 1 ))
    
    sensor2 = ( K*( (x+.05)**2. + (y-.05)**2. + z**2. )**(-3.) *
              ( 3.*( z**2./((x+.05)**2. + (y-.05)**2. + z**2.) ) + 1 ))
    
    sensor3 = ( K*( (x-.05)**2. + (y-.05)**2. + z**2. )**(-3.) *
              ( 3.*( z**2./((x-.05)**2. + (y-.05)**2. + z**2.) ) + 1 ))
    
    return ( sensor1 - H1_L2**2, sensor2 - H2_L2**2, sensor3 - H3_L2**2 )
    
# Construct equations to solve for:
def LHS1( x ):
    H1_L2, H2_L2, H3_L2 = HNorm
    sensor1 = ( K*( x[0]**2 + x[1]**2 + x[2]**2 )**(-3.) *
              ( 3*( x[2]**2/(x[0]**2 + x[1]**2 + x[2]**2) ) + 1 ))
    
    sensor2 = ( K*( (x[0]+.050)**2 + (x[1]-.050)**2 + x[2]**2 )**(-3.) *
              ( 3*( x[2]**2/((x[0]+.050)**2 + (x[1]-.050)**2 + x[2]**2) ) + 1 ))
    
    sensor3 = ( K*( (x[0]-.050)**2 + (x[1]-.050)**2 + x[2]**2 )**(-3.) *
              ( 3*( x[2]**2/((x[0]-.050)**2 + (x[1]-.050)**2 + x[2]**2) ) + 1 ))

    f = [sensor1 - H1_L2**2, sensor2 - H2_L2**2, sensor3 - H3_L2**2]
    
    return ( f )

######################################################
#                   SETUP PROGRAM
######################################################

# Magnetic field vector components
global B1_x, B1_y, B1_z  # IMU readings from sensor 1
global B2_x, B2_y, B2_z  # IMU readings from sensor 2
global B3_x, B3_y, B3_z  # IMU readings from sensor 3
global K, check, HNorm
check = True

### Sensor 1 readings
##B1_x = 0.0880           #
##B1_y = -0.059           # Units { G }
##B1_z = 2.0600           #
##
### Sensor 2 readings
##B2_x = 0.0030           #
##B2_y = 0.0200           # Units { G }
##B2_z = 0.1890           #
##
### Sensor 3 readings
##B3_x = -0.003           #
##B3_y = 0.0200           # Units { G }
##B3_z = 0.1940           #

# Magnet's constant (K)
K   = 1.09 #(19.081)**2    # Units { T.m^3 }

# Establish connection with Arduino
try:
    IMU = createUSBPort( "Arduino", 39, 115200 )
    if IMU.is_open == False:
        IMU.open()
    print( "Serial Port OPEN" )

except Exception as e:
    print( "Could NOT open serial port" )
    print( "Error type %s" %str(type(e)) )
    print( " Error Arguments " + str(e.args) )
    sleep( 5 )
    quit()

######################################################
#                   START PROGRAM
######################################################
initialGuess = np.array( (.5, .1, .1), dtype='f' )
while( True ):
    # Pool data from Arduino
    (H1, H2, H3) = getData(IMU)

##    ### Sensor 1 readings
##    print( "Sensor 1 readings:" )
##    print( "x = %.4f || y = %.4f || z = %.4f\n"
##           %(H1.item(0), H1.item(1), H1.item(2)) )
##
##
##    ### Sensor 2 readings
##    print( "Sensor 2 readings:" )
##    print( "x = %.4f || y = %.4f || z = %.4f\n"
##           %(H2.item(0), H2.item(1), H2.item(2)) )
##
##    ### Sensor 3 readings
##    print( "Sensor 3 readings:" )
##    print( "x = %.4f || y = %.4f || z = %.4f\n"
##           %(H3.item(0), H3.item(1), H3.item(2)) )
##
    
    # Start iteration
    # Find L2 vector norms
    H1_norm = norm(H1)
    H2_norm = norm(H2)
    H3_norm = norm(H3)
    HNorm = [float(H1_norm), float(H2_norm), float(H3_norm)]

##    # Invoke solver
##    sol = fsolve(LHS, initialGuess)
##    print( "SOLUTION:" )
##    print( "x = %.5f || y = %.5f || z = %.5f" %(sol[0], sol[1], sol[2]) )
##    sleep( .5 )
##    initialGuess = sol

    sol = root(LHS1, initialGuess, method='lm', options={'maxiter':250000})
    print( sol )
    
    print( "SOLUTION:" )
    print( "x = %.5f || y = %.5f || z = %.5f" %(sol.x[0], sol.x[1], sol.x[2]) )
    root = np.array((sol.x[0], sol.x[1], sol.x[2]), dtype='f')
    print( LHS1(root) )
    sleep( .5 )
    #initialGuess = np.array( (sol.x[0], sol.x[1], sol.x[2]), dtype='f' )


######################################################
#                   DEPRACATED
######################################################
'''
'''
