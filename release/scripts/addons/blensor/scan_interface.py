import math
import sys
import traceback
import os
import struct 
import ctypes
import time
import random
import bpy
from mathutils import Vector, Euler


"""The number of elements per return depends on the version of the blensor
   patch
"""
ELEMENTS_PER_RETURN = 8
SIZEOF_FLOAT = 4

""" rays is an array of vectors that describe the laser direction and also the
         ray origin if the ray_origin field is setp
    max_distance is a float that determines the maximum distance a ray can travel
    keep_render_setup is passed to the blender internal code to keep the renderer
    setup for additional calls
"""
def scan_rays(rays, max_distance, ray_origins=False, keep_render_setup=False):

    elementsPerRay = 3
    if ray_origins == True:
      elementsPerRay = 6
  
    numberOfRays = int(len(rays)/elementsPerRay)


    rays_buffer = (ctypes.c_float * numberOfRays*elementsPerRay)()
    struct.pack_into("%df"%(numberOfRays*elementsPerRay), rays_buffer, 0, *rays[:numberOfRays*elementsPerRay])

    returns_buffer = (ctypes.c_float * (numberOfRays * ELEMENTS_PER_RETURN))()
   
    print ("Raycount: ", numberOfRays)
    
    returns_buffer_uint = ctypes.cast(returns_buffer, ctypes.POINTER(ctypes.c_uint))

    array_of_returns = []

    try:
      bpy.ops.render.blensor(raycount = numberOfRays,maximum_distance = max_distance, vector_strptr="%016X"%(ctypes.addressof(rays_buffer)), return_vector_strptr="%016X"%(ctypes.addressof(returns_buffer)), elements_per_ray = elementsPerRay, keep_render_setup=keep_render_setup)
      


      for idx in range(numberOfRays):
          if returns_buffer[idx*ELEMENTS_PER_RETURN] < max_distance and returns_buffer[idx*ELEMENTS_PER_RETURN]>0.0 :
              #The ray may have been reflecten and refracted. But the laser
              #does not know that so we need to calculate the point which
              #is the measured distance away from the sensor but without
              #beeing reflected/refracted. We use the original ray direction
              vec = [float(rays[idx*elementsPerRay]), 
                     float(rays[idx*elementsPerRay+1]),
                     float(rays[idx*elementsPerRay+2])]
              veclen = math.sqrt(vec[0]**2+vec[1]**2+vec[2]**2)
              raydistance = float(returns_buffer[idx*ELEMENTS_PER_RETURN])
              vec[0] = raydistance * vec[0]/veclen
              vec[1] = raydistance * vec[1]/veclen
              vec[2] = raydistance * vec[2]/veclen


              ret = [ float(returns_buffer[e + idx*ELEMENTS_PER_RETURN]) for e in range(4) ]            
              ret[1] = vec[0]
              ret[2] = vec[1]
              ret[3] = vec[2]
              ret.append(returns_buffer_uint[idx*ELEMENTS_PER_RETURN+4]) #objectid
              ret.append((returns_buffer[idx*ELEMENTS_PER_RETURN+5],
                          returns_buffer[idx*ELEMENTS_PER_RETURN+6],
                          returns_buffer[idx*ELEMENTS_PER_RETURN+7])) # RGB Value of the material
              ret.append(idx) # Store the index per return as the last element
              array_of_returns.append(ret)
    except TypeError as e:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      traceback.print_tb(exc_traceback)
    finally:
      del rays_buffer
      del returns_buffer

    return array_of_returns
    

