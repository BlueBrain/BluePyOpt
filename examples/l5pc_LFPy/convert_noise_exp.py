"""Read exp data for validation"""

import igorpy
import numpy

voltages = []

# import matplotlib.pyplot as plt
# fig, axes = plt.subplots(11)

for i in range(436, 447):
    # header, voltage = igorpy.read('exp_data/X_NoiseSpiking_ch1_%d.ibw' % i)
    header, current = igorpy.read('exp_data/X_NoiseSpiking_ch0_%d.ibw' % i)
    # axes[i - 436].plot(voltage)
# header, voltage = igorpy.read('exp_data/X_APThreshold_ch1_262.ibw')
# header, current = igorpy.read('exp_data/X_APThreshold_ch0_262.ibw')
# plt.show()
# voltage *= 1000
# voltage -= 14.0
current *= 1e9

time = numpy.arange(len(current)) * header.dx * 1000

numpy.savetxt('exp_data/noise_i.txt', numpy.vstack((time, current)).T)

# import matplotlib.pyplot as plt

# fig, ax = plt.subplots(2)
# ax[0].plot(time, current)
# ax[1].plot(time, voltage)

# plt.show()
