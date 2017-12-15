# Tracking + Solver Modules
import  numpy                   as      np              # Import Numpy
from    mayavi                  import  mlab            # Data visualization
from    time                    import  sleep, clock    # Sleep for stability, clock for profiling
from    scipy.optimize          import  root            # Solve System of Eqns for (x, y, z)
from    scipy.linalg            import  norm            # Calculate vector norms (magnitude)
from    usbProtocol             import  createUSBPort   # Create USB port (serial comm. w\ Arduino)
from    threading               import  Thread          # Used to thread processes
from    Queue                   import  Queue           # Used to queue input/output
import  os, platform                                    # Directory/file manipulation
import  math

mlab.figure(size=(1000, 800))

# ___START: Create Cartesian axes___
##xx = yy = zz = np.arange(-0.6,0.7,0.1)
##xy = xz = yx = yz = zx = zy = np.zeros_like(xx)
##
##lensoffset = 0.1
##
##mlab.plot3d( yx, yy+lensoffset, yz, line_width=0.01, tube_radius=0.01)
##mlab.plot3d( zx, zy+lensoffset, zz, line_width=0.01, tube_radius=0.01)
##mlab.plot3d( xx, xy+lensoffset, xz, line_width=0.01, tube_radius=0.01)

K = 101     # Number of lines to plot
N = 5       # Subdivisions (aka K/N lines are drawn)

# Draw horizontal lines on the xy-, yz-, and xz-planes
lvlCurve_H = np.arange( 0, K, N )                       # Horizontal level curve
lvlCurve_V = np.zeros_like( lvlCurve_H )                # Vertical level curve
H, V = np.meshgrid( lvlCurve_H, lvlCurve_V )            # Mesh both arrays to form a matrix (a grid)
lvlCurve_0 = np.zeros_like( H )                         # Force everything into a 2D plane by setting the 3rd plane to 0
##H, V = H.flatten(), V.flatten()                         # Flatten matrices
##lvlCurve_0 = np.zeros_like( H )                         # Force everything into a 2D plane by setting the 3rd plane to 0

for i in range (0, K, N):
    mlab.mesh( H, V+i, lvlCurve_0, representation='mesh',
               tube_radius = 0.25, color=(1., 1., 1.) )
    mlab.mesh( lvlCurve_0, H, V+i, representation='mesh',
               tube_radius = 0.25, color=(1., 1., 1.) )
    mlab.mesh( H, lvlCurve_0, V+i, representation='mesh',
               tube_radius = 0.25, color=(1., 1., 1.) )
    
##    mlab.plot3d( H, V+i, lvlCurve_0 )                   # xy-plane
##    mlab.plot3d( lvlCurve_0, H, V+i )                   # yz-plane
##    mlab.plot3d( H, lvlCurve_0, V+i )                   # xz-plane

# Draw vertical lines on the xy-, yz-, and xz-planes
lvlCurve_V = np.arange(0, K, N)                         # Vertical level curve
lvlCurve_H = np.zeros_like(lvlCurve_V)                  # Horizontal level curve
H, V = np.meshgrid( lvlCurve_H, lvlCurve_V )            # Mesh both arrays to form a matrix (a grid)
lvlCurve_0 = np.zeros_like( H )                         # Force everything into a 2D plane by setting the 3rd plane to 0
##H, V = H.flatten(), V.flatten()                         # Flatten matrices
##lvlCurve_0 = np.zeros_like( H )                         # Force everything into a 2D plane by setting the 3rd plane to 0

for i in range (0, K, N):
    mlab.mesh( H+i, V, lvlCurve_0, representation='mesh',
               tube_radius = 0.25, color=(1., 1., 1.) )
    mlab.mesh( lvlCurve_0, H+i, V, representation='mesh',
               tube_radius = 0.25, color=(1., 1., 1.) )
    mlab.mesh( H+i, lvlCurve_0, V, representation='mesh',
               tube_radius = 0.25, color=(1., 1., 1.) )
    
##    mlab.plot3d( H+i, V, lvlCurve_0 )                   # xy-plane
##    mlab.plot3d( lvlCurve_0, H+i, V )                   # yz-plane
##    mlab.plot3d( H+i, lvlCurve_0, V )                   # xz-plane
    
STLfile="SP_PH02_Torso (1).stl"
f=open(STLfile,'r')

x=[]
y=[]
z=[]

scaleFactor = 15.0
for line in f:
    strarray=line.split()
    if strarray[0]=='vertex':
        x = np.append( x, np.double(strarray[1])/scaleFactor )
        y = np.append( y, np.double(strarray[2])/scaleFactor )
        z = np.append( z, np.double(strarray[3])/scaleFactor )

# Snap to origin
x = x + 50
y = y + 30
z = z - 50
triangles=[(i, i+1, i+2) for i in range(0, len(x),3)]

mlab.triangular_mesh( x, -1*z, y, triangles,
                      representation='fancymesh',
                      tube_radius=0.25 )

# Setup cartesian space
mlab.outline( extent=[0, K-1, 0, K-1, 0, K-1] )
mlab.axes( extent=[0, K-1, 0, K-1, 0, K-1],
           line_width = 1.0,
           x_axis_visibility=True,
           y_axis_visibility=True,
           z_axis_visibility=True )
# ___END: Create Cartesian Axes___

alpha = np.linspace(0, 2*math.pi, 100)  

xs = np.cos(alpha)
ys = np.sin(alpha)
zs = np.zeros_like(xs)
s  = 2+np.sin(alpha) 
##mlab.points3d( 0, 0, 0, resolution=100, scale_factor=5.0 )
##mlab.outline(extent=[0, 100, 0, 100, 0, 100])
##mlab.axes( extent=[0, 100, 0, 100, 0, 100],
##           line_width = 1.0,
##           x_axis_visibility=True,
##           y_axis_visibility=True,
##           z_axis_visibility=True )

plt = mlab.points3d(xs[:1], ys[:1], zs[:1], resolution=100, scale_factor=5.0)

@mlab.animate(delay=25)
def anim():
    global initialGuess
    f = mlab.gcf()
    while True:
        #print('Updating scene...')
        # Data acquisition
        (H1, H2, H3, H4, H5, H6) = getData(IMU)                         # Get data from MCU
        
        # Compute norms
        HNorm = [ float(norm(H1)), float(norm(H2)),                     #
                  float(norm(H3)), float(norm(H4)),                     # Compute L2 vector norms
                  float(norm(H5)), float(norm(H6)) ]                    #
        
        # Solve system of equations
        sol = root(LHS, initialGuess, args=(K, HNorm), method='lm',     # Invoke solver using the
                   options={'ftol':1e-10, 'xtol':1e-10, 'maxiter':1000, # Levenberg-Marquardt 
                            'eps':1e-8, 'factor':0.001})                # Algorithm (aka LMA)

        # Print solution (coordinates) to screen
        position = np.array( (sol.x[0]*1000, sol.x[1]*1000, -1*sol.x[2]*1000), dtype='float64' )
        #print( "(x, y, z): (%.3f, %.3f, %.3f)" %(position[0], position[1], position[2]) )
        
        # Check if solution makes sense
        if (abs(sol.x[0]*1000) > 500) or (abs(sol.x[1]*1000) > 500) or (abs(sol.x[2]*1000) > 500):
            initialGuess = findIG( getData(IMU) )                       # Determine initial guess based on magnet's location
            
        # Update initial guess with current position and feed back to solver
        else:
            initialGuess = np.array( (sol.x[0]+dx, sol.x[1]+dx,         # Update the initial guess as the
                                      sol.x[2]+dx), dtype='float64' )   # current position and feed back to LMA
        plt.mlab_source.set(x=position[0], y=position[1], z=(position[2]-50))
        yield


# ************************************************************************
# =====================> DEFINE NECESSARY FUNCTIONS <====================*
# ************************************************************************


def argsort( seq ):
    '''
    Sort a list's elements from smallest to largest and
    return the sorted INDICES NOT VALUES!
    
    INPUTS:
        - seq: A list whose elements are to be sorted 

    OUTPUT:
        - A list containing the indices of the given list's elements
          arranged from the index of the element with the smallest
          value to the index of the element with the largest value
    '''
    # http://stackoverflow.com/questions/3071415/efficient-method-to-calculate-the-rank-vector-of-a-list-in-python
    return sorted(range(len(seq)), key=seq.__getitem__)

# --------------------------

def bubbleSort( arr, N ):
    '''
    Sort a list's elements from smallest to largest 
    
    INPUTS:
        - arr: List to be sorted
        - N  : Number of elements in said list that need to be sorted
                (i.e list has 5 elements, if N=3, sort the first 3)

    OUTPUT:
        - A sorted list of size N
    '''
    data = []
    for i in range(0, N):
        data.append( arr[i] )

    for i in range(0, len(data)):
        for j in range(0, len(data)-i-1):
            if (data[j] > data[j+1]):
                temp = data[j]
                data[j] = data[j+1]
                data[j+1] = temp
            else:
                continue
    return (data)

# --------------------------

def getData( ser ):
    '''
    Pool the data from the MCU (wheteher it be a Teensy or an Arduino or whatever)
    The data consists of the magnetic field components in the x-, y-, and z-direction
    of all the sensors. The array must begin with '<' as the SOH signal, the compononents
    must be comma delimited, and must end with '>' as the EOT signal.
    
            >$\     <B_{1x}, B_{1y}, B_{1z}, ..., B_{1x}, B_{1y}, B_{1z}> 
    
    INPUTS:
        - ser: a serial object. Note that the serial port MUST be open before
               passing it the to function

    OUTPUT:
        - Individual numpy arrays of all the magnetic field vectors
    '''
    global CALIBRATING

    # Flush buffer
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # Allow data to fill-in buffer
    # sleep(0.1)

    try:
        # Wait for the sensor to calibrate itself to ambient fields.
        while( True ):
            if(CALIBRATING == True):
                print( "Calibrating...\n" )
                CALIBRATING = False
            if ser.in_waiting > 0:  
                inData = ser.read()  
                if inData == '<':
                    break  

        # Read the actual data value. Stop at End of Data specifier '>'. 
        line = ''
        while( True ):
            if ser.in_waiting > 0:
                inData = ser.read()
                if inData == '>':
                    break
                line = line + inData

        # Split line into the constituent components
        col     = (line.rstrip()).split(",")
        if (len(col) == 18):
            #
            # Construct magnetic field array
            #

            # Sensor 1
            Bx = float( col[0] )
            By = float( col[1] )
            Bz = float( col[2] )
            B1 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 2
            Bx = float( col[3] )
            By = float( col[4] )
            Bz = float( col[5] )
            B2 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 3
            Bx = float( col[6] )
            By = float( col[7] )
            Bz = float( col[8] )
            B3 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 4
            Bx = float( col[9]  )
            By = float( col[10] )
            Bz = float( col[11] )
            B4 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 5
            Bx = float( col[12] )
            By = float( col[13] )
            Bz = float( col[14] )
            B5 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 6
            Bx = float( col[15] )
            By = float( col[16] )
            Bz = float( col[17] )
            B6 = np.array( ([Bx],[By],[Bz]), dtype='float64' )# Units { G }
            
            # Return vectors
            return ( B1, B2, B3, B4, B5, B6 )
        else:
            return ( getData(ser) )

    except Exception as e:
        print( "Caught error in getData()"      )
        print( "Error type %s" %str(type(e))    )
        print( "Error Arguments " + str(e.args) )

# --------------------------

def LHS( root, K, norms ):
    '''
    Construct the left hand side (LHS) of the equations
    to numerically solve for.
    Recall that in order to solve a system numerically it
    must have the form of,
    
                >$\  f(x, y, z, ...) = LHS = 0
    
    INPUTS:
        - root  : a numpy array contating the initial guesses of the roots
        - K     : K is a property of the magnet and has units of { G^2.m^6}
        - norms : An array/list of the vector norms of the magnetic field
                  vectors for all the sensors

    OUTPUT:
        - An array of equations that are sorted corresponding to which
          3 sensors' equations are going to be used with the LMA solver.
          The sorting is based on which 3 sensors are closest to the magnet.
    '''
    
    # Extract x, y, and z
    x, y, z = root
    
    # Construct the (r) terms for each sensor
    # NOTE: Relative distance terms are in meters
    #     : Standing on sensor(n), how many units in
    #       the x/y/z direction should I march to get
    #       back to sensor1 (origin)?
    r1 = float( ( (x+0.000)**2. + (y+0.000)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 1 (ORIGIN)
    r2 = float( ( (x+0.000)**2. + (y-0.125)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 2
    r3 = float( ( (x-0.100)**2. + (y+0.050)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 3
    r4 = float( ( (x-0.100)**2. + (y-0.175)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 4
    r5 = float( ( (x-0.200)**2. + (y+0.000)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 5
    r6 = float( ( (x-0.200)**2. + (y-0.125)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 6

    # Construct the equations
    Eqn1 = ( K*( r1 )**(-6.) * ( 3.*( z/r1 )**2. + 1 ) ) - norms[0]**2.     # Sensor 1
    Eqn2 = ( K*( r2 )**(-6.) * ( 3.*( z/r2 )**2. + 1 ) ) - norms[1]**2.     # Sensor 2
    Eqn3 = ( K*( r3 )**(-6.) * ( 3.*( z/r3 )**2. + 1 ) ) - norms[2]**2.     # Sensor 3
    Eqn4 = ( K*( r4 )**(-6.) * ( 3.*( z/r4 )**2. + 1 ) ) - norms[3]**2.     # Sensor 4
    Eqn5 = ( K*( r5 )**(-6.) * ( 3.*( z/r5 )**2. + 1 ) ) - norms[4]**2.     # Sensor 5
    Eqn6 = ( K*( r6 )**(-6.) * ( 3.*( z/r6 )**2. + 1 ) ) - norms[5]**2.     # Sensor 6

    # Construct a vector of the equations
    Eqns = [Eqn1, Eqn2, Eqn3, Eqn4, Eqn5, Eqn6]

    # Determine which sensors to use based on magnetic field value (smallValue==noBueno!)
    sort = argsort( norms )             # Auxiliary function sorts norms from smallest to largest
    sort.reverse()                      # Python built-in function reverses elements of list
    f=[]                                # Declare vector to hold relevant functions

    for i in range(0, 3):               # Fill functions' array with the equations that correspond to
        f.append( Eqns[sort[i]] )       # the sensors with the highest norm, thus closest to magnet
        
    # Return vector
    return ( f )

# --------------------------

def findIG( magFields ):
    '''
    Dynamic search of initial guess for the LMA solver based on magnitude
    of the magnetic field relative to all the sensors.
    A high magnitude reading indicates magnet is close to some 3
    sensors, the centroid of the traingle created by said sensors
    is fed as the initial guess
    
    INPUTS:
        - magfield: a numpy array containing all the magnetic field readings

    OUTPUT:
        - A numpy array containing <x, y, z> values for the initial guess
    '''
    
    # Define IMU positions on the grid
    #      / sensor 1: (x, y, z)
    #     /  sensor 2: (x, y, z)
    # Mat=      :          :
    #     \     :          :
    #      \ sensor 6: (x, y, z)
    IMU_pos = np.array(((0.0  , 0.0  ,   0.0) ,
                        (0.0  , 0.125,   0.0) ,
                        (0.100,-0.050,   0.0) ,
                        (0.100, 0.175,   0.0) ,
                        (0.200, 0.0  ,   0.0) ,
                        (0.200, 0.125,   0.0)), dtype='float64')

    # Read current magnetic field from MCU
    (H1, H2, H3, H4, H5, H6) = magFields

    # Compute L2 vector norms
    HNorm = [ float( norm(H1) ), float( norm(H2) ),
              float( norm(H3) ), float( norm(H4) ),
              float( norm(H5) ), float( norm(H6) ) ]
    
    # Determine which sensors to use based on magnetic field value (smallValue==noBueno!)
    sort = argsort( HNorm )             # Auxiliary function sorts norms from smallest to largest
    sort.reverse()                      # Python built-in function reverses elements of list

    IMUS = bubbleSort( sort, 3 )

    # Return the initial guess as the centroid of the detected triangle
    return ( np.array(((IMU_pos[IMUS[0]][0]+IMU_pos[IMUS[1]][0]+IMU_pos[IMUS[2]][0])/3.,
                       (IMU_pos[IMUS[0]][1]+IMU_pos[IMUS[1]][1]+IMU_pos[IMUS[2]][1])/3.,
                       (IMU_pos[IMUS[0]][2]+IMU_pos[IMUS[1]][2]+IMU_pos[IMUS[2]][2])/3. -0.01), dtype='float64') )

# --------------------------

# ************************************************************************
# ===========================> SETUP PROGRAM <===========================
# ************************************************************************

# Useful variables
global CALIBRATING
global initialGuess

CALIBRATING = True                              # Boolean to indicate that device is calibrating
READY       = False                             # Give time for user to place magnet

#K           = 7.27e-8                           # Small magnet's constant   (K) || Units { G^2.m^6}
K           = 1.09e-6                           # Big magnet's constant     (K) || Units { G^2.m^6}
dx          = 1e-7                              # Differential step size (Needed for solver)
calcPos     = []                                # Empty array to hold calculated positions


# Establish connection with Arduino
DEVC = "Arduino"                                # Device Name (not very important)
PORT = 4                                        # Port number (VERY important)
BAUD = 115200                                   # Baudrate    (VERY VERY important)

# Error handling in case serial communcation fails (1/2)
try:
    IMU = createUSBPort( DEVC, PORT, BAUD )     # Create serial connection
    if IMU.is_open == False:                    # Make sure port is open
        IMU.open()
    print( "Serial Port OPEN" )

    initialGuess = findIG( getData(IMU) )       # Determine initial guess based on magnet's location

# Error handling in case serial communcation fails (2/2)
except Exception as e:
    print( "Could NOT open serial port" )
    print( "Error type %s" %str(type(e)) )
    print( "Error Arguments " + str(e.args) )
    sleep( 2.5 )
    quit()                                      # Shutdown entire program

# ************************************************************************
# =========================> MAKE IT ALL HAPPEN <=========================
# ************************************************************************

# Inform user that system is almost ready
if(READY == False):
    print( "Place magnet on track" )
    sleep( 2.5 )
    print( "Ready in 3" )
    sleep( 1.0 )
    print( "Ready in 2" )
    sleep( 1.0 )
    print( "Ready in 1" )
    sleep( 1.0 )
    print( "GO!" )
    start = clock()
        
    # Set the device to ready!!
    READY = True
    anim()
    mlab.show()

